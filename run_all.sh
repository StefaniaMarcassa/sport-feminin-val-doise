#!/usr/bin/env bash
# Reconstruit toute l'analyse à partir des fichiers de data/raw.
# Prérequis : Python 3.10+, pip install -r requirements.txt, pdftotext (poppler-utils).
# Optionnel : LibreOffice (recalcul des formules Excel) et pandoc (note Word).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build outputs docs
python scripts/build.py          # lecture et harmonisation des fichiers sources
python scripts/aggregate.py      # agrégats commune / canton / EPCI
python scripts/tess.py           # fond de carte schématique
python scripts/evo.py            # séries temporelles 2019-2025 et 5 saisons
python scripts/mapdata.py        # données de la carte
python scripts/build_page.py     # carte interactive (outputs/ et docs/)
python scripts/excel.py          # base Excel
python scripts/excel_evo.py      # onglets d'évolution
if command -v soffice >/dev/null; then
  soffice --headless --convert-to xlsx --outdir build outputs/Base_sport_feminin_Val_d_Oise.xlsx >/dev/null && \
  cp build/Base_sport_feminin_Val_d_Oise.xlsx outputs/ && echo "Formules Excel recalculées"
fi
if command -v pandoc >/dev/null; then
  (cd outputs && pandoc ../scripts/note.md -o Note_sport_feminin_Val_d_Oise.docx --resource-path=../outputs/figures) && echo "Note Word générée"
fi
