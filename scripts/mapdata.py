import pickle, json, math
import numpy as np
import pandas as pd
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'build'

A = pickle.load(open(B / 'agg.pkl', 'rb'))
D = pickle.load(open(B / 'data.pkl', 'rb'))
T = pickle.load(open(B / 'tess.pkl', 'rb'))
com = A['com']
geoms = T['geoms']

# SVG coords: x km -> px, y inverted
allb = unary_union(geoms).bounds
S = 12.0
pad = 6
X0, Y1 = allb[0], allb[3]
W = (allb[2] - allb[0]) * S + 2 * pad
H = (allb[3] - allb[1]) * S + 2 * pad


def path(g, tol=0.05):
    g = g.simplify(tol)
    polys = [g] if isinstance(g, Polygon) else list(getattr(g, 'geoms', []))
    out = []
    for p in polys:
        if not isinstance(p, Polygon) or p.is_empty:
            continue
        for ring in [p.exterior] + list(p.interiors):
            pts = [(pad + (x - X0) * S, pad + (Y1 - y) * S) for x, y in ring.coords]
            out.append('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + 'Z')
    return ''.join(out)


def centroid(g):
    c = g.representative_point()
    return [round(pad + (c.x - X0) * S, 1), round(pad + (Y1 - c.y) * S, 1)]


def rnd(v, n=4):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    return round(float(v), n)


def rec(r):
    at = r['asso_civ_2025']
    return dict(
        pop=int(r['population']), asso=int(at), adhF=int(r['adh_F_2025']), adhH=int(r['adh_H_2025']),
        partF=rnd(r['part_F_2025']), partF24=rnd(r['part_F_2024']), evol=rnd(r['evol_part_F_pts'], 2),
        adhF1000=rnd(r['adh_F_pour_1000hab'], 2), asso10k=rnd(r['asso_civ_pour_10000hab'], 2),
        sites10k=rnd(r['sites_pour_10000hab'], 2), sites=int(r['sites_sportifs']),
        benev=int(r['benevoles_F_2025']), benev100=rnd(r['benevoles_F_pour_100_adh_F'], 2),
        sal=int(r['salariees_F_2025']),
        masc=int(r['asso_tres_masc_2025']), fem=int(r['asso_dom_fem_2025']),
        mascShare=rnd(r['asso_tres_masc_2025'] / at if at > 0 else None),
        scol=int(r['asso_scol_2025']), sss=int(r['sss_2026']), manif=int(r['manifestations_2025']),
    )


out = {'W': round(W, 1), 'H': round(H, 1), 'levels': {}}
feats = []
for i, r in com.iterrows():
    d = rec(r)
    d.update(id=r['code_insee'], name=r['commune'], canton=r['canton'], epci=r['epci'], dens=r['densite_insee'] if isinstance(r['densite_insee'], str) else None,
             cantonImp=r['canton_source'] != 'liste subventions 2025', d=path(geoms[i]), c=centroid(geoms[i]))
    feats.append(d)
out['levels']['commune'] = feats

for lvl, key in (('canton', 'canton'), ('epci', 'epci')):
    ag = A[lvl].set_index(key)
    fs = []
    for name, idx in com.groupby(key).groups.items():
        g = unary_union([geoms[j].buffer(0.02) for j in idx]).buffer(-0.02)
        r = ag.loc[name]
        d = rec(r)
        d.update(id=name, name=name, ncom=int(r['n_communes']), sans=int(r['communes_sans_asso_civ']),
                 d=path(g, 0.08), c=centroid(g))
        fs.append(d)
    out['levels'][lvl] = fs

E = pickle.load(open(B / 'evo.pkl', 'rb'))
AS = E['assos']
YRS = list(range(2019, 2026))
for lvl, key in (('commune', 'code_insee'), ('canton', 'canton'), ('epci', 'epci')):
    k2 = 'code_ref' if lvl == 'commune' else key
    n = AS.groupby([key, 'annee']).k.size().unstack().reindex(columns=YRS).fillna(0)
    pv = AS[AS.constante].groupby([k2 if lvl == 'commune' else key, 'annee']).vol.sum().unstack().reindex(columns=YRS).fillna(0)
    for u in out['levels'][lvl]:
        uid = u['id']
        u['nS'] = [int(n.loc[uid, y]) if uid in n.index else 0 for y in YRS]
        u['pS'] = [int(pv.loc[uid, y]) if uid in pv.index else 0 for y in YRS]
        p19, p25 = u['pS'][0], u['pS'][-1]
        u['evoPanel'] = round(p25 / p19 - 1, 4) if p19 >= 100 else None
        u['evoN'] = u['nS'][-1] - u['nS'][0]
        u['p19'] = p19
out['outline'] = path(unary_union(geoms).buffer(0.02), 0.1)
dept = A['dept'].iloc[0]
out['dept'] = rec(dept)
out['dept'].update(ncom=183, sans=int(dept['communes_sans_asso_civ']))

# charts
comi = D['comites']
c26 = comi[(comi.saison == '2025/2026') & comi.feminines.notna() & (comi.licencies >= 300)].copy()
c26['p'] = c26.feminines / c26.licencies
NAMES = {'COMITE DE JUDO DU VAL D\'OISE': 'Judo', 'KARATE ET DISCIPLINES ASSOCIEES': 'Karaté',
         'FFD CD 95 COMITE DEPARTEMENTAL DANSE 95': 'Danse', 'PETANQUE ET JEU PROVENCAL': 'Pétanque',
         'EPGV-GYMNASTIQUE VOLONTAIRE (EDUCATION PHYSIQUE et GYMNASTIQUE VOLONTAIRE)': 'Gym. volontaire (EPGV)',
         'FSCF (FEDERATION SPORTIVE ET CULTURELLE DE France)': 'FSCF', 'FSGT (FEDERATION SPORTIVE ET GYMNIQUE DU TRAVAIL)': 'FSGT',
         'PLONGEE SOUS-MARINE': 'Plongée', 'SAVATE BOXE FRANCAISE': 'Savate boxe française', 'MONTAGNE ET ESCALADE': 'Montagne-escalade',
         'ROLLER SKATEBOARD': 'Roller-skate', 'TIR A L\'ARC': "Tir à l'arc", 'SPORTS DE GLACE': 'Sports de glace',
         'TENNIS DE TABLE': 'Tennis de table', 'BASKET BALL': 'Basket-ball', 'VOLLEY BALL': 'Volley-ball', 'AIKIDO ET BUDO': 'Aïkido-budo',
         'SPORT ADAPTE': 'Sport adapté', 'BOXE ANGLAISE': 'Boxe anglaise', 'ATHLETISME': 'Athlétisme', 'EQUITATION': 'Équitation',
         'ECHECS': 'Échecs', 'HANDISPORT': 'Handisport', 'UNSS': 'UNSS', 'USEP': 'USEP', 'UFOLEP': 'UFOLEP'}
c26['nm'] = c26.comite.map(lambda s: NAMES.get(s, s.capitalize()))
out['comites'] = [dict(n=r.nm, lic=int(r.licencies), f=int(r.feminines), p=round(r.p, 4)) for r in c26.sort_values('p').itertuples()]
out['ladder'] = [
    dict(n='Adhérentes des associations aidées (2025)', t=int(dept.adh_F_2025 + dept.adh_H_2025), f=int(dept.adh_F_2025), src='Associations civiles 2025'),
    dict(n='Licenciées des comités (2025/26)', t=237466, f=None, src='Comités'),
]
cl = D['clubs21']
cl2 = cl[cl.president_sexe.isin(['H', 'F'])]
rec21 = D['rec21']


def s21(a, b):
    x = rec21[[a, b]].apply(pd.to_numeric, errors='coerce').dropna()
    x = x[x[a] > 0]
    return int(x[a].sum()), int(x[b].sum())


lad = []
for lab, (t, f), src in [
    ('Pratiquantes', s21('pratiquants', 'pratiquantes_F'), 'Enquête 2021'),
    ('Bénévoles', s21('benevoles', 'benevoles_F'), 'Enquête 2021'),
    ('Éducatrices', s21('educateurs', 'educatrices_F'), 'Enquête 2021'),
    ('Arbitres', s21('arbitres', 'arbitres_F'), 'Enquête 2021'),
    ('Présidentes de club', (len(cl2), int((cl2.president_sexe == 'F').sum())), 'Enquête 2021'),
    ('Élues aux sports (communes)', (68, 21), 'Fichier élu·es'),
    ('Directrices des sports (communes)', (47, 8), 'Postes pourvus'),
]:
    lad.append(dict(n=lab, t=t, f=f, p=round(f / t, 4), src=src))
out['ladder'] = lad
out['zones'] = [dict(z=z, t=int((cl2.zone == z).sum()), f=int(((cl2.zone == z) & (cl2.president_sexe == 'F')).sum())) for z in ['Centre', 'Est', 'Vexin']]
# saison totals
v = comi[comi.feminines.notna() & comi.licencies.notna() & (comi.licencies > 0)]
out['saisons'] = [dict(s=s, p=round(g.feminines.sum() / g.licencies.sum(), 4), n=int(len(g))) for s, g in v.groupby('saison')]
# evolution
ev = []
for y in range(2019, 2026):
    ev.append(dict(y=y, asso=int(com[f'asso_civ_{y}'].sum()), lic=int(com[f'licencies_civ_{y}'].sum())))
out['evo'] = ev
# profil mixite (Excel convention: <0.2, <0.4, <0.6)
c25 = A['c25']
c25 = c25[c25.code_insee != 'HORS95']
p = c25.part_F
out['profils'] = dict(tres_masc=int((p < 0.2).sum()), masc=int(((p >= 0.2) & (p < 0.4)).sum()), mixte=int(((p >= 0.4) & (p < 0.6)).sum()), fem=int((p >= 0.6).sum()))
yr, yrp = E['yr'], E['yrp']
out['dept'].update(nS=[int(yr.loc[y, 'n']) for y in YRS], pS=[int(yrp.loc[y, 'vol']) for y in YRS],
                   evoPanel=round(yrp.loc[2025, 'vol'] / yrp.loc[2019, 'vol'] - 1, 4), evoN=int(out['dept']['asso']) - int(yr.loc[2019, 'n']), p19=int(yrp.loc[2019, 'vol']))
out['n7'] = E['n7']
out['deptSeries'] = [dict(y=y, n=int(yr.loc[y, 'n']), vol=int(yr.loc[y, 'vol']), pvol=int(yrp.loc[y, 'vol'])) for y in YRS]
tot = E['tot']
out['discTot'] = [dict(s=s_, p=round(float(tot.loc[s_, 'p']), 4), lic=int(tot.loc[s_, 'lic']), f=int(tot.loc[s_, 'f'])) for s_ in tot.index]
ev = E['ev']
ev = ev[ev.lic26 >= 1000].sort_values('p26')
out['discEvo'] = [dict(n=r.nom, a=round(float(r.p21), 4), b=round(float(r.p26), 4), lic=int(r.lic26)) for r in ev.itertuples()]
out['ndisc5'] = len(E['okall'])
bt = E['bt']
out['panel45'] = dict(n=E['nb45'], p24=round(float(bt.loc[2024, 'F'] / (bt.loc[2024, 'F'] + bt.loc[2024, 'H'])), 4), p25=round(float(bt.loc[2025, 'F'] / (bt.loc[2025, 'F'] + bt.loc[2025, 'H'])), 4))
json.dump(out, open(B / 'mapdata.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(round(W), round(H), len(json.dumps(out)) / 1e3, 'kB', out['profils'], out['saisons'], out['zones'])
