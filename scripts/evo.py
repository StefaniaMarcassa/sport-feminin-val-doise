import pickle, json
import numpy as np
import pandas as pd
from geo import norm, load_communes, Matcher

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'build'

D = pickle.load(open(B / 'data.pkl', 'rb'))
A = pickle.load(open(B / 'agg.pkl', 'rb'))
com = A['com']
F = str(ROOT / 'data' / 'raw' / 'Association civil type 01 et scolaire type 02.xlsx')

# ---------------- 1. Disciplines : part F sur 5 saisons
MAP21 = {'Aïkido et Budo': 'AIKIDO ET BUDO', 'Athlétisme': 'ATHLETISME', 'Aviron': 'AVIRON', 'Badminton': 'BADMINTON',
         'BaseBall': 'BASE BALL - SOFTBALL et CRICKET', 'BasketBall': 'BASKET BALL', 'Billard': 'BILLARD', 'Boxe Anglaise': 'BOXE ANGLAISE',
         "Course d'orientation": "COURSE D'ORIENTATION", 'Cyclisme': 'CYCLISME', 'Cyclotourisme': 'CYCLOTOURISME',
         'Danse': 'FFD CD 95 COMITE DEPARTEMENTAL DANSE 95', 'Echecs': 'ECHECS',
         'EPGV': 'EPGV-GYMNASTIQUE VOLONTAIRE (EDUCATION PHYSIQUE et GYMNASTIQUE VOLONTAIRE)', 'Equitation': 'EQUITATION',
         'Escrime': 'ESCRIME', 'Flying Disc': 'FLYING DISC', 'Football': 'FOOTBALL', 'Football Américain': 'FOOT AMERICAIN',
         'FSCF': 'FSCF (FEDERATION SPORTIVE ET CULTURELLE DE France)', 'FSGT': 'FSGT (FEDERATION SPORTIVE ET GYMNIQUE DU TRAVAIL)',
         'Golf': 'GOLF', 'Gymnastique': 'GYMNASTIQUE', 'Haltérophilie': 'HALTEROPHILIE et MUSCULATION', 'Handball': 'HANDBALL',
         'Handisport': 'HANDISPORT', 'Hockey sur Glace': 'HOCKEY SUR GLACE', 'Judo': "COMITE DE JUDO DU VAL D'OISE",
         'Karaté': 'KARATE ET DISCIPLINES ASSOCIEES', 'Montagne et Escalade': 'MONTAGNE ET ESCALADE', 'Natation': 'NATATION',
         'Pétanque et Jeu provençal': 'PETANQUE ET JEU PROVENCAL', 'Plongée Sous-Marine': 'PLONGEE SOUS-MARINE',
         'Randonnée Pédestre': 'RANDONNEE PEDESTRE', 'Retraite Sportive': 'RETRAITE SPORTIVE', 'Roller sports et Skateboard': 'ROLLER SKATEBOARD',
         'Rugby': 'RUGBY', 'Spéléologie': 'SPELEOLOGIE', 'Sport Adapté': 'SPORT ADAPTE', 'Sports de Glace': 'SPORTS DE GLACE',
         'Squash': 'SQUASH', 'Taekwendo': 'TAEKWONDO', 'Tennis': 'TENNIS', 'Tennis de Table': 'TENNIS DE TABLE', 'Tir': 'TIR',
         "Tir à l'Arc": "TIR A L'ARC", 'Triathlon': 'TRIATHLON', 'UFOLEP': 'UFOLEP', 'UNSS': 'UNSS', 'USEP': 'USEP', 'Voile': 'VOILE',
         'VolleyBall': 'VOLLEY BALL'}
SHORT = {'AIKIDO ET BUDO': 'Aïkido-budo', 'ATHLETISME': 'Athlétisme', 'AVIRON': 'Aviron', 'BADMINTON': 'Badminton',
         'BASE BALL - SOFTBALL et CRICKET': 'Baseball-softball', 'BASKET BALL': 'Basket-ball', 'BILLARD': 'Billard', 'BOXE ANGLAISE': 'Boxe anglaise',
         "COURSE D'ORIENTATION": "Course d'orientation", 'CYCLISME': 'Cyclisme', 'CYCLOTOURISME': 'Cyclotourisme',
         'FFD CD 95 COMITE DEPARTEMENTAL DANSE 95': 'Danse', 'ECHECS': 'Échecs',
         'EPGV-GYMNASTIQUE VOLONTAIRE (EDUCATION PHYSIQUE et GYMNASTIQUE VOLONTAIRE)': 'Gym. volontaire (EPGV)', 'EQUITATION': 'Équitation',
         'ESCRIME': 'Escrime', 'FLYING DISC': 'Flying disc', 'FOOTBALL': 'Football', 'FOOT AMERICAIN': 'Football américain',
         'FSCF (FEDERATION SPORTIVE ET CULTURELLE DE France)': 'FSCF', 'FSGT (FEDERATION SPORTIVE ET GYMNIQUE DU TRAVAIL)': 'FSGT',
         'GOLF': 'Golf', 'GYMNASTIQUE': 'Gymnastique', 'HALTEROPHILIE et MUSCULATION': 'Haltérophilie', 'HANDBALL': 'Handball',
         'HANDISPORT': 'Handisport', 'HOCKEY SUR GLACE': 'Hockey sur glace', "COMITE DE JUDO DU VAL D'OISE": 'Judo',
         'KARATE ET DISCIPLINES ASSOCIEES': 'Karaté', 'MONTAGNE ET ESCALADE': 'Montagne-escalade', 'NATATION': 'Natation',
         'PETANQUE ET JEU PROVENCAL': 'Pétanque', 'PLONGEE SOUS-MARINE': 'Plongée', 'RANDONNEE PEDESTRE': 'Randonnée pédestre',
         'RETRAITE SPORTIVE': 'Retraite sportive', 'ROLLER SKATEBOARD': 'Roller-skate', 'RUGBY': 'Rugby', 'SPELEOLOGIE': 'Spéléologie',
         'SPORT ADAPTE': 'Sport adapté', 'SPORTS DE GLACE': 'Sports de glace', 'SQUASH': 'Squash', 'TAEKWONDO': 'Taekwondo',
         'TENNIS': 'Tennis', 'TENNIS DE TABLE': 'Tennis de table', 'TIR': 'Tir', "TIR A L'ARC": "Tir à l'arc", 'TRIATHLON': 'Triathlon',
         'UFOLEP': 'UFOLEP', 'UNSS': 'UNSS', 'USEP': 'USEP', 'VOILE': 'Voile', 'VOLLEY BALL': 'Volley-ball',
         'SAVATE BOXE FRANCAISE': 'Savate boxe française', 'MEDAILLES JEUNESSE ET SPORTS et ENGAGEMENT ASSOCIATIF': 'Médailles jeunesse et sports'}
rows = []
rec = D['rec21'].copy()
for r in rec.itertuples():
    key = MAP21.get(str(r.comite).strip())
    lic = pd.to_numeric(r.pratiquants, errors='coerce')
    f = pd.to_numeric(r.pratiquantes_F, errors='coerce')
    if key:
        rows.append(dict(comite=key, saison='2020/2021', licencies=lic, feminines=f))
cm = D['comites']
for r in cm.itertuples():
    rows.append(dict(comite=r.comite, saison=r.saison, licencies=r.licencies, feminines=r.feminines))
disc = pd.DataFrame(rows)
disc['nom'] = disc.comite.map(lambda s: SHORT.get(s, s.title()))
disc['valide'] = disc.licencies.gt(0) & disc.feminines.notna() & (disc.feminines <= disc.licencies)
disc['p'] = np.where(disc.valide, disc.feminines / disc.licencies, np.nan)
SEAS = ['2020/2021', '2022/2023', '2023/2024', '2024/2025', '2025/2026']
wide = disc.pivot_table(index='nom', columns='saison', values=['licencies', 'feminines', 'p'], aggfunc='first')
okall = [n for n in wide.index if all(pd.notna(wide.loc[n, ('p', s)]) for s in SEAS)]
panel = disc[disc.nom.isin(okall) & disc.valide]
tot = panel.groupby('saison').agg(lic=('licencies', 'sum'), f=('feminines', 'sum'))
tot['p'] = tot.f / tot.lic
print('disciplines panel 5 saisons:', len(okall))
print(tot)
# evolution per discipline 2020/21 -> 2025/26 (>=300 lic in 2025/26)
ev = []
for n in okall:
    a, b = wide.loc[n, ('p', '2020/2021')], wide.loc[n, ('p', '2025/2026')]
    ev.append(dict(nom=n, p21=a, p26=b, d=(b - a) * 100, lic26=wide.loc[n, ('licencies', '2025/2026')],
                   f21=wide.loc[n, ('feminines', '2020/2021')], f26=wide.loc[n, ('feminines', '2025/2026')]))
ev = pd.DataFrame(ev).sort_values('d')
print(ev[ev.lic26 >= 300].to_string())
excluded = disc[(~disc.valide) & disc.feminines.notna()]
print('exclus (F > total):', excluded[['nom', 'saison', 'licencies', 'feminines']].to_string())

# ---------------- 2. Territoires 2019-2025
YEARS = list(range(2019, 2026))
SPEC = {2019: ('2019 ASS CIVILES', 1, 'Nombre de licenciés'), 2020: ('2020 ASS CIVILES', 1, 'Nombre de licencies'),
        2021: ('2021 ASS CIVILES', 1, 'Nombre de licenciés'), 2022: ('2022 ASS CIVILES', 1, 'Nombre de licenciés'),
        2023: ('2023 ASS CIVILES', 2, 'Nombre de licencié Feminine'), 2024: ('2024 ASS CIVILES', 1, 'Nombre Adherents Total'),
        2025: ('2025 ASS CIVILES', 1, None)}
M = Matcher(load_communes())
assos = []
for y, (s, h, col) in SPEC.items():
    d = pd.read_excel(F, sheet_name=s, header=h)
    d = d.loc[:, ~d.columns.astype(str).str.startswith('Unnamed')]
    d = d[d.Association.notna()]
    d = d[d.Association.astype(str).str.strip().str.upper() != 'TOTAL']
    city = [c for c in d.columns if c.lower() in ('ville', 'commune')][0]
    vol = d['Nombre Adherents Feminines'] + d['Nombre Adherents Masculins'] if col is None else pd.to_numeric(d[col], errors='coerce')
    x = pd.DataFrame(dict(annee=y, asso=d.Association.astype(str).str.strip(), k=d.Association.astype(str).str.strip().map(norm),
                          code_insee=[M(v) for v in d[city]], vol=vol.values))
    if y >= 2024:
        x['F'] = d['Nombre Adherents Feminines'].values
        x['H'] = d['Nombre Adherents Masculins'].values
    assos.append(x)
assos = pd.concat(assos, ignore_index=True)
assos = assos[assos.code_insee.notna() & (assos.code_insee != 'HORS95')]
# duplicates of name within a year: keep sum by (annee,k)
pres = assos.groupby('k').annee.nunique()
constant = set(pres[pres == 7].index)
assos['constante'] = assos.k.isin(constant)
# commune of reference for panel = 2025 commune
ref = assos[assos.annee == 2025].drop_duplicates('k').set_index('k').code_insee
assos['code_ref'] = np.where(assos.constante, assos.k.map(ref), assos.code_insee)
cinfo = com.set_index('code_insee')[['commune', 'canton', 'epci']]
assos = assos.join(cinfo, on='code_insee')
print('panel 7 ans:', len(constant), 'assos')
yr = assos.groupby('annee').agg(n=('k', 'size'), vol=('vol', 'sum'))
yrp = assos[assos.constante].groupby('annee').agg(n=('k', 'size'), vol=('vol', 'sum'))
print(yr.join(yrp, rsuffix='_panel'))

def terr(level):
    a = assos.groupby([level, 'annee']).agg(n=('k', 'size'), vol=('vol', 'sum')).unstack('annee')
    p = assos[assos.constante].groupby([level, 'annee']).vol.sum().unstack('annee')
    return a, p

T = {}
for lvl in ('canton', 'epci', 'commune'):
    T[lvl] = terr(lvl)
a, p = T['canton']
out = pd.DataFrame({'n2019': a[('n', 2019)], 'n2025': a[('n', 2025)], 'vol2019': a[('vol', 2019)], 'vol2023': a[('vol', 2023)],
                    'vol2025': a[('vol', 2025)], 'pvol2019': p[2019], 'pvol2023': p[2023], 'pvol2024': p[2024], 'pvol2025': p[2025]})
out['evol_panel_19_23'] = (out.pvol2023 / out.pvol2019 - 1) * 100
print(out.sort_values('evol_panel_19_23').round(1).to_string())
# F panel 2024-2025
f45 = assos[assos.annee >= 2024]
both = f45.groupby('k').annee.nunique()
b = f45[f45.k.isin(both[both == 2].index)]
bt = b.groupby('annee')[['F', 'H']].sum()
print('panel 2024-2025:', both.eq(2).sum(), (bt.F / (bt.F + bt.H)).round(4).to_dict())

pickle.dump(dict(disc=disc, wide=wide, okall=okall, tot=tot, ev=ev, assos=assos, T=T, yr=yr, yrp=yrp, bt=bt,
                 nb45=int(both.eq(2).sum()), n7=len(constant)), open(B / 'evo.pkl', 'wb'))
