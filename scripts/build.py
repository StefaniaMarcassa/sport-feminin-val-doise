import re, json, pickle
import numpy as np
import pandas as pd
from geo import load_communes, Matcher, norm, SRC

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'build'

com = load_communes()
M = Matcher(com)
F_ASSO = SRC + 'Association civil type 01 et scolaire type 02.xlsx'


def clean(d):
    d = d.loc[:, ~d.columns.astype(str).str.startswith('Unnamed')]
    d = d[d.Association.notna()]
    d = d[d.Association.astype(str).str.strip().str.upper() != 'TOTAL']
    return d


def read(sheet, header):
    d = clean(pd.read_excel(F_ASSO, sheet_name=sheet, header=header))
    city = [c for c in d.columns if c.lower() in ('ville', 'commune')][0]
    d = d.rename(columns={city: 'ville'})
    d['code_insee'] = [M(v, sheet) for v in d.ville]
    return d


# ---------- Associations civiles 2025 (base de l'etat des lieux F/H)
c25 = read('2025 ASS CIVILES', 1)
c25 = c25.rename(columns={'Nombre Adherents Feminines': 'adh_F', 'Nombre Adherents Masculins': 'adh_H',
                          'Nombre Adherents Moins 18 F': 'adh_moins18', 'Nombre Adherents Plus 18F': 'adh_plus18',
                          'Nombre Benevoles F': 'benevoles_F', 'Nombre Licencie F': 'licencies_tot',
                          'Nombre de Salaries féminin': 'salariees_F'})
c25['adh_tot'] = c25.adh_F + c25.adh_H
c25['part_F'] = np.where(c25.adh_tot > 0, c25.adh_F / c25.adh_tot, np.nan)
c25['Association'] = c25.Association.str.strip()

c24 = read('2024 ASS CIVILES', 1).rename(columns={'Nombre Adherents Feminines': 'adh_F', 'Nombre Adherents Masculins': 'adh_H',
                                                  'Nombre Sections Feminine': 'sections_F'})
c24['adh_tot'] = c24.adh_F + c24.adh_H

# ---------- Evolution des associations civiles 2019-2025 (volume total)
evo_spec = {2019: ('2019 ASS CIVILES', 1, 'Nombre de licenciés'), 2020: ('2020 ASS CIVILES', 1, 'Nombre de licencies'),
            2021: ('2021 ASS CIVILES', 1, 'Nombre de licenciés'), 2022: ('2022 ASS CIVILES', 1, 'Nombre de licenciés'),
            2023: ('2023 ASS CIVILES', 2, 'Nombre de licencié Feminine')}
evo = {}
for y, (s, h, col) in evo_spec.items():
    d = read(s, h)
    evo[y] = d.groupby('code_insee').agg(n_asso=('Association', 'size'), licencies=(col, 'sum'))
evo[2024] = c24.groupby('code_insee').agg(n_asso=('Association', 'size'), licencies=('adh_tot', 'sum'))
evo[2025] = c25.groupby('code_insee').agg(n_asso=('Association', 'size'), licencies=('adh_tot', 'sum'))

# ---------- Associations scolaires
s25 = read('2025 ASS SCOLAIRE', 2).rename(columns={'Nombre Licencié F': 'licencies', 'Nombre SectionsF': 'sections'})

# ---------- Subventions 2025
sub = pd.read_excel(SRC + 'Liste des associations subventionnées 2025.xlsx')
sub['code_insee'] = [M(v, 'subv2025') for v in sub.Commune]
sub['Canton'] = sub.Canton.str.strip()
sub['type'] = np.where(sub.Dispositif.str.startswith('01'), 'civile', 'scolaire')

# ---------- Cantons : source = liste des subventions 2025, Argenteuil et Cergy regroupes
CANTON_FIX = {'ARGENTEUIL': 'Argenteuil (1-2-3)', 'ARGENTEUIL 1': 'Argenteuil (1-2-3)', 'ARGENTEUIL 3': 'Argenteuil (1-2-3)',
              'CERGY': 'Cergy (1-2)', 'CERGY 1': 'Cergy (1-2)', 'CERGY 2': 'Cergy (1-2)'}
PRETTY = {'DEUIL-LA-BARRE': 'Deuil-la-Barre', 'DOMONT': 'Domont', 'ERMONT': 'Ermont', 'FOSSES': 'Fosses',
          'FRANCONVILLE': 'Franconville', 'GARGES-LES-GONESSE': 'Garges-lès-Gonesse', 'GOUSSAINVILLE': 'Goussainville',
          'HERBLAY-SUR-SEINE': 'Herblay-sur-Seine', "L'ISLE ADAM": "L'Isle-Adam", 'MONTMORENCY': 'Montmorency',
          'PONTOISE': 'Pontoise', 'SAINT-OUEN-L’AUMONE': "Saint-Ouen-l'Aumône", 'SARCELLES': 'Sarcelles',
          'TAVERNY': 'Taverny', 'VAUREAL': 'Vauréal', 'VILLIERS-LE-BEL': 'Villiers-le-Bel'}
sub['canton_n'] = sub.Canton.map(lambda c: CANTON_FIX.get(c, PRETTY.get(c, c)))
cmap = (sub[sub.code_insee.notna() & (sub.code_insee != 'HORS95')]
        .groupby('code_insee').canton_n.agg(lambda s: s.mode().iloc[0]))
com['canton'] = com.code_insee.map(cmap)
com['canton_source'] = np.where(com.canton.notna(), 'liste subventions 2025', 'imputé (commune voisine la plus proche)')
# imputation par plus proche voisin (distance en km approx)
known = com[com.canton.notna()]
lat0 = np.radians(49.05)
for i, r in com[com.canton.isna()].iterrows():
    dx = (known.lon - r.lon) * np.cos(lat0) * 111
    dy = (known.lat - r.lat) * 111
    com.loc[i, 'canton'] = known.loc[(dx ** 2 + dy ** 2).idxmin(), 'canton']

# ---------- Installations sportives
ins = pd.read_excel(SRC + "Installations sportives présentes sur Département du Val d'Oise.xlsx", header=1).iloc[:, 1:]
ins.columns = ['nom', 'adresse', 'commune', 'type_particulier', 'installation_nombre', 'densite']
ins['code_insee'] = [M(v, 'installations') for v in ins.commune]
dens = ins.dropna(subset=['code_insee']).groupby('code_insee').densite.agg(lambda s: s.mode().iloc[0])
com['densite_insee'] = com.code_insee.map(dens)
tp = ins.type_particulier.fillna('')
ins['scolaire'] = tp.str.contains('scolaire')
ins['piscine'] = tp.str.contains('Piscine')
ins['complexe'] = tp.str.contains('Complexe')

# ---------- Manifestations par commune (2023-2025)
man = pd.read_excel(SRC + 'Association subventionnée et leur manifestation.xlsx', sheet_name=0, header=None)
mrows = []
for blk, (cn, cs, cc, ca, cm, cnm) in {2023: (1, 2, 3, 4, 5, 6), 2024: (9, 10, 11, 12, 13, 14), 2025: (17, 18, 19, 20, 21, 22)}.items():
    for i in range(2, len(man)):
        name = man.iloc[i, cn]
        if pd.isna(name) or str(name).strip().lower() == 'total':
            continue
        mrows.append(dict(annee=blk, commune_src=str(name).strip(), code_insee=M(name, f'manif{blk}'),
                          n_manif=pd.to_numeric(man.iloc[i, cm], errors='coerce'),
                          noms_manif=man.iloc[i, cnm] if pd.notna(man.iloc[i, cnm]) else ''))
man = pd.DataFrame(mrows)
sss_col = pd.to_numeric(pd.read_excel(SRC + 'Association subventionnée et leur manifestation.xlsx', sheet_name=0, header=None).iloc[2:, 23], errors='coerce')

# ---------- Sections sportives scolaires 2026-2027 (PDF, dept 95)
import subprocess
txt = subprocess.run(['pdftotext', '-layout', SRC + 'Liste SSS 26 27.pdf', '-'], capture_output=True, text=True).stdout
lines = txt.splitlines()
sss = []
for i, l in enumerate(lines):
    m = re.match(r'\s*95\s+(\d{7}[A-Z])\s+(\w+)\s+(.+?)\s{2,}(.+?)\s{2,}(.+?)\s*$', l)
    if m:
        sss.append(dict(uai=m.group(1), cat=m.group(2), etab=m.group(3).strip(), ville=m.group(4).strip(), section=m.group(5).strip()))
    elif re.match(r'\s*95\s+\d{7}[A-Z]', l):
        print('SSS PARSE?', l)
sss = pd.DataFrame(sss)
sss['code_insee'] = [M(v, 'sss') for v in sss.ville]
sss['feminine'] = sss.section.str.contains('FEMININ')

# ---------- Comites departementaux
bil = pd.read_excel(SRC + 'Comité départementaux.xlsx', sheet_name='Bilan ', header=None)
crow = []
for i in range(3, len(bil)):
    name = bil.iloc[i, 1]
    if pd.isna(name):
        continue
    for y, (ca, cl, cf) in {'2022/2023': (8, 9, 10), '2023/2024': (14, 15, 16), '2024/2025': (20, 21, 22), '2025/2026': (26, 27, 28)}.items():
        crow.append(dict(comite=re.sub(r'\s+', ' ', str(name)).strip(), saison=y,
                         n_asso=pd.to_numeric(bil.iloc[i, ca], errors='coerce'),
                         licencies=pd.to_numeric(bil.iloc[i, cl], errors='coerce'),
                         feminines=pd.to_numeric(bil.iloc[i, cf], errors='coerce')))
comites = pd.DataFrame(crow)
det = pd.read_excel(SRC + 'Comité départementaux.xlsx', sheet_name='Détail 2024 2026', header=2)
det = det.loc[:, ~det.columns.astype(str).str.startswith('Unnamed')]
det = det[det.iloc[:, 0].notna()]
det.columns = [re.sub(r'\s+', ' ', str(c)).strip() for c in det.columns]

# ---------- Enquete 2021
F21 = SRC + "le Sport Féminin en Val d'Oise 2021.xlsx"
rec21 = pd.read_excel(F21, sheet_name='Recap Général 2021', header=3).iloc[:, 1:]
rec21.columns = ['comite', 'clubs', 'pratiquants', 'pratiquantes_F', 'benevoles', 'benevoles_F', 'educateurs', 'educatrices_F', 'arbitres', 'arbitres_F', 'pct_arb']
rec21 = rec21[rec21.comite.notna()]
clubs21 = pd.read_excel(F21, sheet_name='Recap par clubs 2021', header=1).iloc[:, 1:6]
clubs21.columns = ['discipline', 'club', 'zone', 'feminines', 'president_sexe']
clubs21 = clubs21[clubs21.club.notna()]

# ---------- Elus / directeurs
gouv = pd.DataFrame([
    dict(fonction='Élu·es aux sports des communes', femmes=21, hommes=47, vacant=0),
    dict(fonction='Directeur·rices des sports des communes', femmes=8, hommes=39, vacant=3)])

print('UNMATCHED', M.unmatched)
print('FUZZY', M.fuzzy)
pickle.dump(dict(com=com, c25=c25, c24=c24, evo=evo, s25=s25, sub=sub, ins=ins, man=man, sss=sss, comites=comites,
                 det=det, rec21=rec21, clubs21=clubs21, gouv=gouv), open(B / 'data.pkl', 'wb'))
