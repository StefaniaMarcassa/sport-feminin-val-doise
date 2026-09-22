import pickle, json, numpy as np
from shapely.geometry import box, Point, MultiPoint
from shapely.ops import voronoi_diagram, unary_union

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'build'

A = pickle.load(open(B / 'agg.pkl', 'rb'))
com = A['com']
lat0 = np.radians(49.1)
kx = np.cos(lat0)
P = lambda lon, lat: ((lon - 2.2) * kx * 111, (lat - 49.1) * 111)
pts = [Point(*P(r.lon, r.lat)) for r in com.itertuples()]
bbs = [box(*P(r.bbox[0], r.bbox[1]), *P(r.bbox[2], r.bbox[3])) for r in com.itertuples()]
env = unary_union(bbs).envelope.buffer(5)
vor = voronoi_diagram(MultiPoint(pts), envelope=env)
cells = {}
for poly in vor.geoms:
    for i, p in enumerate(pts):
        if i not in cells and poly.contains(p):
            cells[i] = poly
            break
outline = unary_union([b.buffer(0.4) for b in bbs]).buffer(-0.4).simplify(0.2)
geoms = []
for i in range(len(pts)):
    g = cells[i].intersection(bbs[i].buffer(0.6)).intersection(outline)
    geoms.append(g)
pickle.dump(dict(geoms=geoms, outline=outline, pts=pts), open(B / 'tess.pkl', 'wb'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.plotting import plot_polygon
fig, ax = plt.subplots(figsize=(11, 7))
cols = {k: plt.cm.tab20(i % 20) for i, k in enumerate(sorted(com.canton.unique()))}
for g, c in zip(geoms, com.canton):
    plot_polygon(g, ax=ax, add_points=False, facecolor=cols[c], edgecolor='k', linewidth=0.4)
ax.set_aspect('equal')
plt.savefig(B / 'tess.png', dpi=80)
print(len(cells), sum(g.is_empty for g in geoms))
