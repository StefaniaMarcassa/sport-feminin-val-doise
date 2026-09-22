import pickle
import numpy as np
import pandas as pd

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'build'

D = pickle.load(open(B / 'data.pkl', 'rb'))
com = D['com'].copy()
c25, c24, s25, sub, ins, man, sss, evo = D['c25'], D['c24'], D['s25'], D['sub'], D['ins'], D['man'], D['sss'], D['evo']

IN = lambda d: d[d.code_insee.notna() & (d.code_insee != 'HORS95')]

# Tag des associations 2025
c25 = c25.copy()
c25['profil'] = pd.cut(c25.part_F, [-0.01, 0.2, 0.4, 0.6, 1.01],
                       labels=['Très masculine (<20 % F)', 'Plutôt masculine (20-40 %)', 'Mixte (40-60 %)', 'À dominante féminine (≥60 %)'])

g = IN(c25).groupby('code_insee')
base = pd.DataFrame(index=pd.Index(com.code_insee, name='code_insee'))
base = base.join(pd.DataFrame({
    'asso_civ_2025': g.size(),
    'adh_F_2025': g.adh_F.sum(), 'adh_H_2025': g.adh_H.sum(),
    'benevoles_F_2025': g.benevoles_F.sum(), 'salariees_F_2025': g.salariees_F.sum(),
    'asso_tres_masc_2025': g.profil.apply(lambda s: (s == 'Très masculine (<20 % F)').sum()),
    'asso_dom_fem_2025': g.profil.apply(lambda s: (s == 'À dominante féminine (≥60 %)').sum()),
}))
g4 = IN(c24).groupby('code_insee')
base['asso_civ_2024'] = g4.size()
base['adh_F_2024'] = g4.adh_F.sum()
base['adh_H_2024'] = g4.adh_H.sum()
gs = IN(s25).groupby('code_insee')
base['asso_scol_2025'] = gs.size()
base['licencies_scol_2025'] = gs.licencies.sum()
base['sections_scol_2025'] = gs.sections.sum()
gsub = IN(sub).groupby(['code_insee', 'type']).size().unstack(fill_value=0)
base['asso_subv_civ_2025'] = gsub.get('civile')
base['asso_subv_scol_2025'] = gsub.get('scolaire')
gi = IN(ins).groupby('code_insee')
base['sites_sportifs'] = gi.size()
base['sites_scolaires'] = gi.scolaire.sum()
base['piscines'] = gi.piscine.sum()
for y in (2023, 2024, 2025):
    base[f'manifestations_{y}'] = IN(man[man.annee == y]).groupby('code_insee').n_manif.sum()
gss = IN(sss).groupby('code_insee')
base['sss_2026'] = gss.size()
base['sss_feminines_2026'] = gss.feminine.sum()
for y in range(2019, 2026):
    e = evo[y]
    e = e[(e.index.notna()) & (e.index != 'HORS95')]
    base[f'asso_civ_{y}'] = e.n_asso
    base[f'licencies_civ_{y}'] = e.licencies

com = com.set_index('code_insee').join(base)
num = [c for c in base.columns]
com[num] = com[num].fillna(0)

SUM_COLS = ['population'] + num


def ratios(d):
    d = d.copy()
    d['adh_tot_2025'] = d.adh_F_2025 + d.adh_H_2025
    d['part_F_2025'] = np.where(d.adh_tot_2025 > 0, d.adh_F_2025 / d.adh_tot_2025, np.nan)
    tot24 = d.adh_F_2024 + d.adh_H_2024
    d['part_F_2024'] = np.where(tot24 > 0, d.adh_F_2024 / tot24, np.nan)
    d['evol_part_F_pts'] = (d.part_F_2025 - d.part_F_2024) * 100
    d['adh_F_pour_1000hab'] = d.adh_F_2025 / d.population * 1000
    d['adh_pour_1000hab'] = d.adh_tot_2025 / d.population * 1000
    d['asso_civ_pour_10000hab'] = d.asso_civ_2025 / d.population * 1e4
    d['sites_pour_10000hab'] = d.sites_sportifs / d.population * 1e4
    d['benevoles_F_pour_100_adh_F'] = np.where(d.adh_F_2025 > 0, d.benevoles_F_2025 / d.adh_F_2025 * 100, np.nan)
    d['evol_asso_civ_2019_2025'] = d.asso_civ_2025 - d.asso_civ_2019
    d['fiabilite_part_F'] = np.where(d.adh_tot_2025 >= 100, 'ok', np.where(d.adh_tot_2025 > 0, 'effectif faible (<100)', 'aucune association'))
    return d


com = ratios(com.reset_index())
agg = {}
for lvl in ('canton', 'epci'):
    a = com.groupby(lvl)[SUM_COLS].sum()
    a['n_communes'] = com.groupby(lvl).size()
    a['communes_sans_asso_civ'] = com[com.asso_civ_2025 == 0].groupby(lvl).size()
    a = ratios(a.reset_index().fillna({'communes_sans_asso_civ': 0}))
    agg[lvl] = a

dept = com[SUM_COLS].sum().to_frame().T
dept['n_communes'] = len(com)
dept['communes_sans_asso_civ'] = (com.asso_civ_2025 == 0).sum()
dept = ratios(dept)
# Out-of-department counts for transparency
hors = dict(c25=int((c25.code_insee == 'HORS95').sum()), s25=int((s25.code_insee == 'HORS95').sum()),
            sub=int((sub.code_insee == 'HORS95').sum()))

# profil par densite
prof_dens = com.groupby('densite_insee')[SUM_COLS].sum()
prof_dens['n_communes'] = com.groupby('densite_insee').size()
prof_dens = ratios(prof_dens.reset_index())

pickle.dump(dict(com=com, canton=agg['canton'], epci=agg['epci'], dept=dept, hors=hors, c25=c25,
                 prof_dens=prof_dens), open(B / 'agg.pkl', 'wb'))
print(dept.T.to_string())
print(hors)
print(agg['canton'][['canton', 'n_communes', 'population', 'asso_civ_2025', 'adh_tot_2025', 'part_F_2025', 'adh_F_pour_1000hab']].sort_values('part_F_2025').to_string())
print(agg['epci'][['epci', 'n_communes', 'population', 'asso_civ_2025', 'adh_tot_2025', 'part_F_2025', 'adh_F_pour_1000hab']].sort_values('part_F_2025').to_string())
print(prof_dens[['densite_insee', 'n_communes', 'population', 'asso_civ_2025', 'part_F_2025', 'adh_F_pour_1000hab', 'sites_pour_10000hab']].to_string())
print(c25.profil.value_counts())
