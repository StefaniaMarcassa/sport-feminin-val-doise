# Sport féminin en Val d'Oise

Cartographie des associations sportives aidées par le Département du Val d'Oise, sous l'angle de la pratique féminine. Échelles : commune, canton, intercommunalité. Période : état des lieux 2025, avec des évolutions depuis 2019.

## Résultats

| Fichier | Contenu |
| --- | --- |
| [`outputs/Atlas_sport_feminin_Val_d_Oise.html`](outputs/Atlas_sport_feminin_Val_d_Oise.html) | Carte interactive (à ouvrir dans un navigateur). Même page dans [`docs/index.html`](docs/index.html) pour GitHub Pages. |
| [`outputs/Atlas_sport_feminin_Val_d_Oise.pdf`](outputs/Atlas_sport_feminin_Val_d_Oise.pdf) | Version imprimable de la carte (vue par canton). |
| [`outputs/Note_sport_feminin_Val_d_Oise.md`](outputs/Note_sport_feminin_Val_d_Oise.md) | Note d'analyse (lisible directement sur GitHub). |
| [`outputs/Note_sport_feminin_Val_d_Oise.docx`](outputs/Note_sport_feminin_Val_d_Oise.docx) | Note d'analyse (Word). |
| [`outputs/Base_sport_feminin_Val_d_Oise.xlsx`](outputs/Base_sport_feminin_Val_d_Oise.xlsx) | Base consolidée : communes, cantons, intercommunalités, associations 2025, évolutions, comités, gouvernance. Les ratios sont des formules. |

Chiffres clés 2025 : 551 associations civiles aidées, 68 623 adhérentes pour 91 352 adhérents, soit 42,9 % de femmes. Selon le canton, la part des femmes va de 37,1 % (Fosses) à 54,3 % (Ermont).

## Sources

Fichiers de la Direction des Sports du Département (dossier [`data/raw`](data/raw)) :

- associations civiles (01) et scolaires (02), 2019 à 2025 ;
- liste des associations subventionnées 2025 ;
- associations subventionnées et manifestations, 2023 à 2025 ;
- comités départementaux, 2019 à 2026 ;
- enquête « Le sport féminin en Val d'Oise » 2021 et sa présentation ;
- répartition femmes/hommes des élu·es et directeur·rices des sports ;
- installations sportives du département ;
- carte des sections sportives scolaires 2026-2027 (Rectorat de Versailles).

Référentiel géographique ([`data/ref/communes_95.json`](data/ref/communes_95.json)) : code officiel géographique, extrait des paquets npm `@etalab/decoupage-administratif` 6.0.0 (communes, population, intercommunalités) et `@etalab/fr-bounding-boxes` 0.1.3 (emprise des communes).

## Méthode

- **Champ.** Associations aidées par le Département. Ce n'est pas un recensement de tous les clubs.
- **Part des femmes.** Adhérentes / (adhérentes + adhérents), déclarée par chaque association en 2024 et 2025.
- **Colonnes trompeuses.** En 2023-2025, plusieurs colonnes marquées « F » contiennent en fait le total femmes + hommes. Elles ne sont pas utilisées comme données féminines.
- **Séries temporelles.** Part des femmes par discipline sur 5 saisons (enquête 2020/21, puis comités 2022/23 à 2025/26). Effectifs 2019-2025 suivis sur les 336 associations aidées chaque année, rapprochées par leur nom.
- **Cantons.** Argenteuil 1-2-3 et Cergy 1-2 sont regroupés. Le canton vient de la liste des subventions 2025 pour 108 communes. Pour les 75 autres, il est attribué d'après la commune voisine : à vérifier.
- **Fond de carte.** Schématique : cellules de Voronoï autour du centre de chaque commune, limitées à son emprise. Les contours officiels (IGN) n'étaient pas accessibles.

Les limites sont détaillées dans la note et dans l'onglet « Lisez-moi » de l'Excel.

## Reproduire l'analyse

```bash
pip install -r requirements.txt   # + pdftotext (poppler-utils)
./run_all.sh
```

Les scripts sont dans [`scripts`](scripts) et s'exécutent dans cet ordre :

1. `build.py` : lecture et harmonisation des fichiers sources, rattachement aux communes.
2. `aggregate.py` : indicateurs par commune, canton et intercommunalité.
3. `tess.py` : fond de carte schématique.
4. `evo.py` : séries 2019-2025 et part des femmes par discipline sur 5 saisons.
5. `mapdata.py` puis `build_page.py` : carte interactive.
6. `excel.py` puis `excel_evo.py` : base Excel.

LibreOffice (recalcul des formules Excel) et pandoc (note Word) sont optionnels.

## Auteur

Stefania Marcassa, CY Cergy Paris Université.
