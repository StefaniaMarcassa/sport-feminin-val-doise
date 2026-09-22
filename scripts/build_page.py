"""Assemble la carte interactive : page_template.html + build/mapdata.json."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
t = (ROOT / 'scripts' / 'page_template.html').read_text(encoding='utf-8')
d = (ROOT / 'build' / 'mapdata.json').read_text(encoding='utf-8')
page = ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1"></head><body>'
        + t.replace('__DATA__', d) + '</body></html>')
for p in (ROOT / 'outputs' / 'Atlas_sport_feminin_Val_d_Oise.html', ROOT / 'docs' / 'index.html'):
    p.write_text(page, encoding='utf-8')
print('ok')
