import pickle
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.table import Table, TableStyleInfo

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'build'

A = pickle.load(open(B / 'agg.pkl', 'rb'))
D = pickle.load(open(B / 'data.pkl', 'rb'))
com = A['com'].sort_values('commune').reset_index(drop=True)

FONT = 'Arial'
HFILL = PatternFill('solid', start_color='1F3A5F')
HFONT = Font(name=FONT, bold=True, color='FFFFFF', size=10)
BFONT = Font(name=FONT, size=10)
TFONT = Font(name=FONT, bold=True, size=14, color='1F3A5F')
NFONT = Font(name=FONT, italic=True, size=9, color='555555')
PCT = '0.0%;-0.0%;"-"'
INT = '#,##0;-#,##0;"-"'
DEC = '0.0;-0.0;"-"'

wb = Workbook()


def header(ws, row, cols, widths=None):
    for j, c in enumerate(cols, 1):
        cell = ws.cell(row=row, column=j, value=c)
        cell.font, cell.fill = HFONT, HFILL
        cell.alignment = Alignment(wrap_text=True, vertical='center')
    ws.row_dimensions[row].height = 42
    if widths:
        for j, w in enumerate(widths, 1):
            ws.column_dimensions[L(j)].width = w
    ws.freeze_panes = ws.cell(row=row + 1, column=3)


def title(ws, t, note):
    ws['A1'] = t
    ws['A1'].font = TFONT
    ws['A2'] = note
    ws['A2'].font = NFONT


def write_rows(ws, r0, df, fmts):
    for i, row in enumerate(df.itertuples(index=False), r0):
        for j, v in enumerate(row, 1):
            if isinstance(v, float) and np.isnan(v):
                v = None
            if isinstance(v, (np.integer,)):
                v = int(v)
            if isinstance(v, (np.floating,)):
                v = float(v)
            c = ws.cell(row=i, column=j, value=v)
            c.font = BFONT
            if fmts.get(j):
                c.number_format = fmts[j]


def add_table(ws, name, r0, r1, ncol):
    t = Table(displayName=name, ref=f'A{r0}:{L(ncol)}{r1}')
    t.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True)
    ws.add_table(t)


# ============ 1. Lisez-moi
ws = wb.active
ws.title = 'Lisez-moi'
ws.column_dimensions['A'].width = 30
ws.column_dimensions['B'].width = 110
title(ws, 'Cartographie du sport associatif et du sport féminin en Val d\'Oise', 'Base consolidée construite à partir des fichiers de la Direction des Sports. Version du 21/09/2026.')
lines = [
    ('Onglet', 'Contenu'),
    ('Communes', '183 communes du Val d\'Oise. Volumes 2025 (associations civiles, adhérent·es F/H, bénévoles F, salariées F), scolaires, subventions, équipements, manifestations, sections sportives, séries 2019-2025. Les ratios sont des formules.'),
    ('Cantons', '18 cantons regroupés (Argenteuil 1-2-3 et Cergy 1-2 fusionnés, car ils découpent une même commune). Sommes par SUMIFS sur l\'onglet Communes.'),
    ('EPCI', '12 intercommunalités (rattachement au code officiel géographique). Sommes par SUMIFS sur l\'onglet Communes.'),
    ('Associations_2025', 'Liste des 553 associations civiles 2025 avec commune, canton, EPCI, adhérent·es F/H, part F et profil de mixité.'),
    ('Evolution', 'Totaux départementaux 2019-2025 : nombre d\'associations civiles et volume de licencié·es / adhérent·es.'),
    ('Comites', 'Comités départementaux : licencié·es et féminines par saison (2022/23 à 2025/26), actions « pratique féminine ».'),
    ('Gouvernance', 'Enquête 2021 (pratiquantes, bénévoles, éducatrices, arbitres, présidentes) et répartition F/H des élu·es et directeur·rices des sports.'),
    ('Sections_sportives', 'Sections sportives scolaires 2026-2027 du Val d\'Oise (extrait du PDF académique).'),
    ('Installations', 'Liste des 1 543 lieux de pratique, avec code commune.'),
    ('', ''),
    ('Définitions et limites', ''),
    ('Champ', 'Les fichiers « associations civiles (01) et scolaires (02) » portent sur les associations aidées par le Département. Ce n\'est pas un recensement de tous les clubs. Une commune « sans association » peut avoir des clubs non aidés.'),
    ('Part F 2025', 'Adhérentes féminines / (adhérentes + adhérents masculins), déclaré par les associations en 2025. Même calcul pour 2024.'),
    ('Libellés trompeurs', 'Dans les fichiers 2023-2025, plusieurs colonnes libellées « F » contiennent en fait des totaux F+H. Ex. 2025 : « Licencié F » = adhérents F+H dans 99 % des cas ; « Moins 18 F » + « Plus 18 F » = total F+H dans 95 % des cas. Ces colonnes ne sont pas utilisées comme données féminines. Idem pour « licencié Feminine » en 2023, traité comme un total.'),
    ('Rupture de série', 'Jusqu\'en 2023 le volume est un nombre de licencié·es ; en 2024-2025 c\'est un nombre d\'adhérent·es (F+H). La hausse 2023-2024 reflète en partie ce changement de mesure.'),
    ('Scolaires 2025', 'La colonne s\'intitule « Nombre Licencié F ». Le libellé n\'est pas vérifiable ; le chiffre est probablement un total. À confirmer avec la Direction des Sports.'),
    ('Cantons', 'Canton connu pour 108 communes (liste des subventions 2025). Pour les 75 autres, canton imputé à partir de la commune voisine la plus proche (colonne « canton_source »). À vérifier avec la liste officielle INSEE.'),
    ('Population', 'Population municipale du code officiel géographique (paquet etalab « découpage administratif », mars 2026).'),
    ('Taux pour 1 000 hab.', 'Les adhérent·es sont comptés dans la commune du siège de l\'association, pas dans leur commune de résidence. Les taux par habitant indiquent une offre locale, pas une pratique des habitantes.'),
    ('Effectifs faibles', 'Une part F calculée sur moins de 100 adhérent·es est fragile (colonne « fiabilite_part_F »).'),
    ('Installations', 'Chaque ligne est un lieu. La colonne source « installation Nombre » n\'est pas documentée ; elle est reprise sans être interprétée.'),
    ('Hors département', '2 associations civiles 2025 et 2 associations subventionnées ont leur siège hors Val d\'Oise (Conflans-Sainte-Honorine, Sacy-le-Grand, Belle-Église). Elles sont exclues des agrégats communaux.'),
]
for i, (a, b) in enumerate(lines, 4):
    ws.cell(row=i, column=1, value=a).font = Font(name=FONT, bold=True, size=10)
    c = ws.cell(row=i, column=2, value=b)
    c.font = BFONT
    c.alignment = Alignment(wrap_text=True, vertical='top')
ws['A4'].font = HFONT; ws['A4'].fill = HFILL; ws['B4'].font = HFONT; ws['B4'].fill = HFILL
ws['A15'].font = Font(name=FONT, bold=True, size=12, color='1F3A5F')

# ============ 2. Communes
SUMS = ['population', 'asso_civ_2025', 'adh_F_2025', 'adh_H_2025', 'benevoles_F_2025', 'salariees_F_2025',
        'asso_tres_masc_2025', 'asso_dom_fem_2025', 'asso_civ_2024', 'adh_F_2024', 'adh_H_2024',
        'asso_scol_2025', 'licencies_scol_2025', 'sections_scol_2025', 'asso_subv_civ_2025', 'asso_subv_scol_2025',
        'sites_sportifs', 'sites_scolaires', 'piscines', 'manifestations_2023', 'manifestations_2024', 'manifestations_2025',
        'sss_2026', 'sss_feminines_2026'] + [f'asso_civ_{y}' for y in range(2019, 2026)] + [f'licencies_civ_{y}' for y in range(2019, 2026)]
SUMS = list(dict.fromkeys(SUMS))
ID = ['code_insee', 'commune', 'canton', 'canton_source', 'epci', 'densite_insee']
RAT = ['adh_tot_2025', 'part_F_2025', 'part_F_2024', 'evol_part_F_pts', 'adh_F_pour_1000hab', 'asso_civ_pour_10000hab',
       'sites_pour_10000hab', 'benevoles_F_pour_100_adh_F', 'fiabilite_part_F']
LABEL = {
    'code_insee': 'Code INSEE', 'commune': 'Commune', 'canton': 'Canton', 'canton_source': 'Source du canton', 'epci': 'EPCI',
    'densite_insee': 'Grille de densité INSEE', 'population': 'Population', 'asso_civ_2025': 'Asso. civiles 2025',
    'adh_F_2025': 'Adhérentes F 2025', 'adh_H_2025': 'Adhérents H 2025', 'benevoles_F_2025': 'Bénévoles F 2025',
    'salariees_F_2025': 'Salariées F 2025', 'asso_tres_masc_2025': 'Asso. <20 % F (2025)', 'asso_dom_fem_2025': 'Asso. ≥60 % F (2025)',
    'asso_civ_2024': 'Asso. civiles 2024', 'adh_F_2024': 'Adhérentes F 2024', 'adh_H_2024': 'Adhérents H 2024',
    'asso_scol_2025': 'Asso. scolaires 2025', 'licencies_scol_2025': 'Licencié·es scolaires 2025 (libellé F)',
    'sections_scol_2025': 'Sections scolaires 2025', 'asso_subv_civ_2025': 'Asso. civiles subventionnées 2025',
    'asso_subv_scol_2025': 'Asso. scolaires subventionnées 2025', 'sites_sportifs': 'Lieux de pratique',
    'sites_scolaires': 'dont établissements scolaires', 'piscines': 'dont piscines', 'manifestations_2023': 'Manifestations 2023',
    'manifestations_2024': 'Manifestations 2024', 'manifestations_2025': 'Manifestations 2025',
    'sss_2026': 'Sections sportives scolaires 2026-27', 'sss_feminines_2026': 'dont sections féminines',
    'adh_tot_2025': 'Adhérent·es total 2025', 'part_F_2025': 'Part F 2025', 'part_F_2024': 'Part F 2024',
    'evol_part_F_pts': 'Évolution part F (points)', 'adh_F_pour_1000hab': 'Adhérentes F pour 1 000 hab.',
    'asso_civ_pour_10000hab': 'Asso. civiles pour 10 000 hab.', 'sites_pour_10000hab': 'Lieux pour 10 000 hab.',
    'benevoles_F_pour_100_adh_F': 'Bénévoles F pour 100 adhérentes', 'fiabilite_part_F': 'Fiabilité part F',
    'n_communes': 'Nb communes', 'communes_sans_asso_civ': 'Communes sans asso. civile aidée',
}
for y in range(2019, 2026):
    LABEL[f'asso_civ_{y}'] = f'Asso. civiles {y}'
    LABEL[f'licencies_civ_{y}'] = f'Licencié·es / adhérent·es {y}'


def ratio_formulas(ws, r, col):
    """col: dict name -> column letter. writes ratio formulas at row r"""
    c = col
    f = {
        'adh_tot_2025': f'={c["adh_F_2025"]}{r}+{c["adh_H_2025"]}{r}',
        'part_F_2025': f'=IF({c["adh_tot_2025"]}{r}>0,{c["adh_F_2025"]}{r}/{c["adh_tot_2025"]}{r},"")',
        'part_F_2024': f'=IF(({c["adh_F_2024"]}{r}+{c["adh_H_2024"]}{r})>0,{c["adh_F_2024"]}{r}/({c["adh_F_2024"]}{r}+{c["adh_H_2024"]}{r}),"")',
        'evol_part_F_pts': f'=IF(AND(ISNUMBER({c["part_F_2025"]}{r}),ISNUMBER({c["part_F_2024"]}{r})),({c["part_F_2025"]}{r}-{c["part_F_2024"]}{r})*100,"")',
        'adh_F_pour_1000hab': f'=IF({c["population"]}{r}>0,{c["adh_F_2025"]}{r}/{c["population"]}{r}*1000,"")',
        'asso_civ_pour_10000hab': f'=IF({c["population"]}{r}>0,{c["asso_civ_2025"]}{r}/{c["population"]}{r}*10000,"")',
        'sites_pour_10000hab': f'=IF({c["population"]}{r}>0,{c["sites_sportifs"]}{r}/{c["population"]}{r}*10000,"")',
        'benevoles_F_pour_100_adh_F': f'=IF({c["adh_F_2025"]}{r}>0,{c["benevoles_F_2025"]}{r}/{c["adh_F_2025"]}{r}*100,"")',
        'fiabilite_part_F': f'=IF({c["adh_tot_2025"]}{r}>=100,"ok",IF({c["adh_tot_2025"]}{r}>0,"effectif faible (<100)","aucune association"))',
    }
    fm = {'part_F_2025': PCT, 'part_F_2024': PCT, 'evol_part_F_pts': DEC, 'adh_F_pour_1000hab': DEC,
          'asso_civ_pour_10000hab': DEC, 'sites_pour_10000hab': DEC, 'benevoles_F_pour_100_adh_F': DEC, 'adh_tot_2025': INT}
    for k in RAT:
        cell = ws[f'{c[k]}{r}']
        cell.value = f[k]
        cell.font = BFONT
        if k in fm:
            cell.number_format = fm[k]


cols = ID + SUMS + RAT
colL = {k: L(i + 1) for i, k in enumerate(cols)}
ws = wb.create_sheet('Communes')
title(ws, 'Indicateurs par commune', 'Colonnes grises = données sources agrégées ; colonnes de droite = ratios calculés par formule. Voir Lisez-moi pour les définitions.')
header(ws, 4, [LABEL[k] for k in cols], [10, 26, 20, 20, 30, 24] + [11] * (len(SUMS) + len(RAT)))
dfc = com[ID + SUMS].copy()
fm = {len(ID) + i + 1: INT for i in range(len(SUMS))}
write_rows(ws, 5, dfc, fm)
n = len(com)
for r in range(5, 5 + n):
    ratio_formulas(ws, r, colL)
add_table(ws, 'T_Communes', 4, 4 + n, len(cols))
COM_LAST = 4 + n


# ============ 3/4. Cantons, EPCI via SUMIFS
def agg_sheet(name, key, label, df):
    ws = wb.create_sheet(name)
    title(ws, f'Indicateurs par {label}', f'Sommes calculées par SUMIFS sur l\'onglet Communes ; ratios par formule.')
    acols = [key, 'n_communes', 'communes_sans_asso_civ'] + SUMS + RAT
    aL = {k: L(i + 1) for i, k in enumerate(acols)}
    header(ws, 4, [LABEL.get(k, label.capitalize()) for k in acols], [30, 9, 12] + [11] * (len(SUMS) + len(RAT)))
    keys = sorted(df[key].unique())
    kc = colL[key]
    for i, k in enumerate(keys, 5):
        ws.cell(row=i, column=1, value=k).font = BFONT
        rng = f"Communes!${kc}$5:${kc}${COM_LAST}"
        c = ws.cell(row=i, column=2, value=f'=COUNTIF({rng},A{i})'); c.font = BFONT
        c = ws.cell(row=i, column=3, value=f'=COUNTIFS({rng},A{i},Communes!${colL["asso_civ_2025"]}$5:${colL["asso_civ_2025"]}${COM_LAST},0)'); c.font = BFONT
        for s in SUMS:
            c = ws[f'{aL[s]}{i}']
            c.value = f'=SUMIFS(Communes!${colL[s]}$5:${colL[s]}${COM_LAST},{rng},A{i})'
            c.font = BFONT
            c.number_format = INT
        ratio_formulas(ws, i, aL)
    last = 4 + len(keys)
    tr = last + 1
    ws.cell(row=tr, column=1, value='Total Val d\'Oise').font = Font(name=FONT, bold=True, size=10)
    for k in ['n_communes', 'communes_sans_asso_civ'] + SUMS:
        c = ws[f'{aL[k]}{tr}']
        c.value = f'=SUM({aL[k]}5:{aL[k]}{last})'
        c.font = Font(name=FONT, bold=True, size=10)
        c.number_format = INT
    ratio_formulas(ws, tr, aL)
    for k in RAT:
        ws[f'{aL[k]}{tr}'].font = Font(name=FONT, bold=True, size=10)
    add_table(ws, 'T_' + name, 4, last, len(acols))


agg_sheet('Cantons', 'canton', 'canton', com)
agg_sheet('EPCI', 'epci', 'EPCI', com)

# ============ 5. Associations 2025
c25 = A['c25'].copy()
cm = com.set_index('code_insee')
c25['commune'] = c25.code_insee.map(cm.commune).fillna('Hors Val d\'Oise')
c25['canton'] = c25.code_insee.map(cm.canton)
c25['epci'] = c25.code_insee.map(cm.epci)
out = c25[['Association', 'ville', 'code_insee', 'commune', 'canton', 'epci', 'adh_F', 'adh_H', 'benevoles_F', 'salariees_F']].copy()
out['code_insee'] = out.code_insee.replace('HORS95', '')
out = out.sort_values(['commune', 'Association'])
ws = wb.create_sheet('Associations_2025')
title(ws, 'Associations sportives civiles aidées, 2025', 'Source : onglet « 2025 ASS CIVILES ». Part F et profil calculés par formule.')
hdr = ['Association', 'Ville (source)', 'Code INSEE', 'Commune', 'Canton', 'EPCI', 'Adhérentes F', 'Adhérents H', 'Bénévoles F', 'Salariées F', 'Adhérent·es total', 'Part F', 'Profil de mixité']
header(ws, 4, hdr, [44, 22, 10, 24, 20, 30, 11, 11, 11, 11, 11, 9, 28])
write_rows(ws, 5, out, {7: INT, 8: INT, 9: INT, 10: INT})
for r in range(5, 5 + len(out)):
    ws[f'K{r}'] = f'=G{r}+H{r}'; ws[f'K{r}'].number_format = INT
    ws[f'L{r}'] = f'=IF(K{r}>0,G{r}/K{r},"")'; ws[f'L{r}'].number_format = PCT
    ws[f'M{r}'] = f'=IF(K{r}=0,"",IF(L{r}<0.2,"Très masculine (<20 % F)",IF(L{r}<0.4,"Plutôt masculine (20-40 %)",IF(L{r}<0.6,"Mixte (40-60 %)","À dominante féminine (≥60 %)"))))'
    for x in 'KLM':
        ws[f'{x}{r}'].font = BFONT
add_table(ws, 'T_Assos', 4, 4 + len(out), len(hdr))

# ============ 6. Evolution
ws = wb.create_sheet('Evolution')
title(ws, 'Évolution 2019-2025 des associations civiles aidées (Val d\'Oise)', 'Rupture de mesure en 2024 : licencié·es jusqu\'en 2023, adhérent·es ensuite. Totaux par formule sur l\'onglet Communes.')
header(ws, 4, ['Année', 'Associations civiles', 'Licencié·es / adhérent·es', 'Mesure', 'Adhérentes F', 'Part F'], [10, 16, 20, 22, 14, 10])
for i, y in enumerate(range(2019, 2026), 5):
    ws.cell(row=i, column=1, value=str(y)).font = BFONT
    ws.cell(row=i, column=2, value=f'=SUM(Communes!{colL[f"asso_civ_{y}"]}5:{colL[f"asso_civ_{y}"]}{COM_LAST})').number_format = INT
    ws.cell(row=i, column=3, value=f'=SUM(Communes!{colL[f"licencies_civ_{y}"]}5:{colL[f"licencies_civ_{y}"]}{COM_LAST})').number_format = INT
    ws.cell(row=i, column=4, value='licencié·es' if y <= 2023 else 'adhérent·es F+H')
    if y >= 2024:
        k = 'adh_F_2025' if y == 2025 else 'adh_F_2024'
        ws.cell(row=i, column=5, value=f'=SUM(Communes!{colL[k]}5:{colL[k]}{COM_LAST})').number_format = INT
        ws.cell(row=i, column=6, value=f'=E{i}/C{i}').number_format = PCT
    else:
        ws.cell(row=i, column=5, value='n.d.')
    for j in range(1, 7):
        ws.cell(row=i, column=j).font = BFONT
ws['A13'] = 'n.d. : pas de ventilation F/H fiable avant 2024 dans ce fichier.'
ws['A13'].font = NFONT

# ============ 7. Comites
comi = D['comites'].copy()
piv = comi.pivot_table(index='comite', columns='saison', values=['licencies', 'feminines'], aggfunc='first')
ws = wb.create_sheet('Comites')
title(ws, 'Comités départementaux : licencié·es et féminines par saison', 'Source : « Comité départementaux.xlsx », onglet Bilan. Part F par formule ; vide si la féminisation n\'est pas renseignée.')
seasons = ['2022/2023', '2023/2024', '2024/2025', '2025/2026']
hdr = ['Comité'] + sum([[f'Licencié·es {s}', f'Féminines {s}', f'Part F {s}'] for s in seasons], [])
det = D['det'].copy()
det.columns = [str(c) for c in det.columns]
hdr += ['Actions pratique féminine (2025/26)']
header(ws, 4, hdr, [40] + [11] * (len(hdr) - 1))
acts = {}
for _, r in det.iterrows():
    nm = str(r.iloc[0])
    lic = pd.to_numeric(r['licenciés 2025/2026'], errors='coerce')
    a = pd.to_numeric(r["Nombre d'actions Pratique féminine"], errors='coerce')
    if 'total' in nm.lower() or pd.isna(lic) or lic <= 0:
        continue
    acts[float(lic)] = a


def find_act(cname):
    lv = piv.loc[cname, ('licencies', '2025/2026')]
    return None if pd.isna(lv) else acts.get(float(lv))


rows = [r for r in piv.index if pd.notna(piv.loc[r, ('licencies', '2025/2026')]) or pd.notna(piv.loc[r, ('licencies', '2024/2025')])]
for i, cname in enumerate(sorted(rows), 5):
    ws.cell(row=i, column=1, value=cname).font = BFONT
    for j, s in enumerate(seasons):
        cl, cf, cp = 2 + 3 * j, 3 + 3 * j, 4 + 3 * j
        lv, fv = piv.loc[cname, ('licencies', s)], piv.loc[cname, ('feminines', s)]
        ws.cell(row=i, column=cl, value=None if pd.isna(lv) else float(lv)).number_format = INT
        ws.cell(row=i, column=cf, value=None if pd.isna(fv) else float(fv)).number_format = INT
        ws.cell(row=i, column=cp, value=f'=IF(AND(ISNUMBER({L(cl)}{i}),ISNUMBER({L(cf)}{i}),N({L(cl)}{i})>0),{L(cf)}{i}/{L(cl)}{i},"")').number_format = PCT
        for x in (cl, cf, cp):
            ws.cell(row=i, column=x).font = BFONT
    a = find_act(cname)
    c = ws.cell(row=i, column=len(hdr), value=None if a is None or pd.isna(a) else float(a))
    c.font = BFONT
    c.number_format = INT
last = 4 + len(rows)
add_table(ws, 'T_Comites', 4, last, len(hdr))
tr = last + 2
ws.cell(row=tr, column=1, value='Total des comités qui renseignent les féminines').font = Font(name=FONT, bold=True, size=10)
for j, s in enumerate(seasons):
    cl, cf, cp = 2 + 3 * j, 3 + 3 * j, 4 + 3 * j
    Lc, Fc = L(cl), L(cf)
    ws.cell(row=tr, column=cl, value=f'=SUMPRODUCT(({Fc}5:{Fc}{last}<>"")*N(+{Lc}5:{Lc}{last}))').number_format = INT
    ws.cell(row=tr, column=cf, value=f'=SUM({Fc}5:{Fc}{last})').number_format = INT
    ws.cell(row=tr, column=cp, value=f'={Fc}{tr}/{Lc}{tr}').number_format = PCT
ws.cell(row=tr + 1, column=1, value='Actions « pratique féminine » : onglet « Détail 2024 2026 », rapproché par le nombre de licencié·es 2025/26 ; vide = non renseigné.').font = NFONT

# ============ 8. Gouvernance
ws = wb.create_sheet('Gouvernance')
title(ws, 'Place des femmes dans l\'encadrement et la gouvernance', 'Sources : enquête « Le sport féminin en Val d\'Oise 2021 » ; fichier « Répartition homme et femme élu et dirigeant ».')
header(ws, 4, ['Fonction', 'Total', 'Femmes', 'Part F', 'Champ'], [44, 12, 12, 10, 60])
rec = D['rec21']
rows = []
for a, b, lab in [('pratiquants', 'pratiquantes_F', 'Pratiquant·es (enquête 2021)'), ('benevoles', 'benevoles_F', 'Bénévoles (enquête 2021)'),
                  ('educateurs', 'educatrices_F', 'Éducateur·rices (enquête 2021)'), ('arbitres', 'arbitres_F', 'Arbitres (enquête 2021)')]:
    x = rec[[a, b]].apply(pd.to_numeric, errors='coerce').dropna()
    x = x[x[a] > 0]
    rows.append((lab, float(x[a].sum()), float(x[b].sum()), f'{len(x)} comités ayant renseigné les deux valeurs'))
cl = D['clubs21']
cl2 = cl[cl.president_sexe.isin(['H', 'F'])]
rows.append(('Présidences de club (enquête 2021)', float(len(cl2)), float((cl2.president_sexe == 'F').sum()), f'{len(cl2)} clubs dont le sexe de la présidence est connu'))
for z in ['Centre', 'Est', 'Vexin']:
    s = cl2[cl2.zone == z]
    rows.append((f'  dont zone {z}', float(len(s)), float((s.president_sexe == 'F').sum()), 'Découpage « Partie du VO » de l\'enquête'))
rows.append(('Élu·es aux sports des communes', 68.0, 21.0, 'Fichier Répartition H/F'))
rows.append(('Directeur·rices des sports des communes (postes pourvus)', 47.0, 8.0, '50 postes dont 3 vacants'))
for i, (a, t, f, ch) in enumerate(rows, 5):
    ws.cell(row=i, column=1, value=a)
    ws.cell(row=i, column=2, value=t).number_format = INT
    ws.cell(row=i, column=3, value=f).number_format = INT
    ws.cell(row=i, column=4, value=f'=IF(B{i}>0,C{i}/B{i},"")').number_format = PCT
    ws.cell(row=i, column=5, value=ch)
    for j in range(1, 6):
        ws.cell(row=i, column=j).font = BFONT
r = 5 + len(rows) + 1
ws.cell(row=r, column=1, value='Présentation 2021 (rappel) : 20 % de présidentes de comités départementaux ; 17 % de présidentes de fédérations françaises.').font = NFONT

# ============ 9. Sections sportives
sss = D['sss'].copy()
sss['commune'] = sss.code_insee.map(cm.commune)
sss['canton'] = sss.code_insee.map(cm.canton)
ws = wb.create_sheet('Sections_sportives')
title(ws, 'Sections sportives scolaires 2026-2027, Val d\'Oise', 'Source : « Liste SSS 26 27.pdf » (Rectorat de Versailles), lignes du département 95.')
hdr = ['UAI', 'Type', 'Établissement', 'Ville (source)', 'Code INSEE', 'Commune', 'Canton', 'Section', 'Section féminine']
header(ws, 4, hdr, [11, 6, 30, 24, 10, 24, 20, 32, 10])
o = sss[['uai', 'cat', 'etab', 'ville', 'code_insee', 'commune', 'canton', 'section']].copy()
o['fem'] = np.where(sss.feminine, 'oui', 'non')
write_rows(ws, 5, o, {})
add_table(ws, 'T_SSS', 4, 4 + len(o), len(hdr))

# ============ 10. Installations
ins = D['ins'].copy()
ins['commune_cog'] = ins.code_insee.map(cm.commune)
ins['canton'] = ins.code_insee.map(cm.canton)
ins['epci'] = ins.code_insee.map(cm.epci)
ws = wb.create_sheet('Installations')
title(ws, 'Lieux de pratique sportive du Val d\'Oise', 'Source : « Installations sportives présentes sur Département du Val d\'Oise.xlsx ».')
hdr = ['Nom', 'Adresse', 'Commune', 'Code INSEE', 'Canton', 'EPCI', 'Type particulier', 'installation Nombre (source, non documenté)', 'Grille de densité']
header(ws, 4, hdr, [36, 34, 22, 10, 20, 30, 22, 14, 24])
o = ins[['nom', 'adresse', 'commune', 'code_insee', 'canton', 'epci', 'type_particulier', 'installation_nombre', 'densite']]
write_rows(ws, 5, o, {})
add_table(ws, 'T_Installations', 4, 4 + len(o), len(hdr))

for s in wb.worksheets:
    s.sheet_view.showGridLines = False
wb.save(ROOT / 'outputs' / 'Base_sport_feminin_Val_d_Oise.xlsx')
print('ok')
