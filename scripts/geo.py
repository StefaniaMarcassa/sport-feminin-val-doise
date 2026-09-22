import json, re, unicodedata, difflib
import pandas as pd

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'build'

SRC = str(ROOT / 'data' / 'raw') + '/'


def norm(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ''
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()
    s = s.replace('’', ' ')
    s = re.sub(r'[^A-Z0-9]+', ' ', s).strip()
    s = re.sub(r'\bCEDEX\b.*$', '', s).strip()
    s = re.sub(r'\bSTE\b', 'SAINTE', s)
    s = re.sub(r'\bST\b', 'SAINT', s)
    return s


ALIASES = {
    'CERGY PONTOISE': 'CERGY', 'CERGY SAINT CHRISTOPHE': 'CERGY', 'CERGY PREFECTURE': 'CERGY',
    'FRANCONVILLE LA GARENNE': 'FRANCONVILLE', 'HERBLAY': 'HERBLAY SUR SEINE',
    'ERAGNY': 'ERAGNY SUR OISE', 'OMERVIELLE': 'OMERVILLE', 'SAINT CRY EN ARTHIES': 'SAINT CYR EN ARTHIES',
    'MAUDETOUR EN VEXIN': 'MAUDETOUR EN VEXIN', 'HAUTE ILSE': 'HAUTE ISLE', 'L ISLE ADAM': 'L ISLE ADAM',
    'ISLE ADAM': 'L ISLE ADAM', 'ECOUAN': 'ECOUEN', 'PERSELES': 'PRESLES', 'LE MESNIL AUBRY': 'LE MESNIL AUBRY', 'CHERENCE': 'CHERENCE',
    'VILLIERS LE SEC': 'VILLIERS LE SEC', 'BRAY ET LU': 'BRAY ET LU', 'AMENUCOURT': 'AMENUCOURT',
}
OUT_OF_DEPT = {'CONFLANS SAINTE HONORINE', 'SACY LE GRAND', 'BELLE EGLISE'}


def load_communes():
    """Communes du Val d'Oise (code officiel géographique, paquets npm etalab
    @etalab/decoupage-administratif 6.0.0 et @etalab/fr-bounding-boxes 0.1.3),
    extraites dans data/ref/communes_95.json."""
    rows = []
    for x in json.load(open(ROOT / 'data' / 'ref' / 'communes_95.json', encoding='utf-8')):
        bb = x['bbox']
        rows.append(dict(code_insee=x['code'], commune=x['nom'], population=x['population'],
                         epci_code=x['epci_code'], epci=x['epci'],
                         lon=(bb[0] + bb[2]) / 2, lat=(bb[1] + bb[3]) / 2, bbox=bb))
    df = pd.DataFrame(rows)
    df['key'] = df.commune.map(norm)
    return df


class Matcher:
    def __init__(self, communes):
        self.map = dict(zip(communes.key, communes.code_insee))
        self.keys = list(self.map)
        self.unmatched = {}
        self.fuzzy = {}

    def __call__(self, name, src=''):
        k = norm(name)
        if not k:
            return None
        k = ALIASES.get(k, k)
        if k in OUT_OF_DEPT:
            return 'HORS95'
        if k in self.map:
            return self.map[k]
        m = difflib.get_close_matches(k, self.keys, n=1, cutoff=0.85)
        if m:
            self.fuzzy[(src, name)] = m[0]
            return self.map[m[0]]
        self.unmatched[(src, name)] = self.unmatched.get((src, name), 0) + 1
        return None
