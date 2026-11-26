"""Read every flat on the typical residential floors off the HA sales brochure for Ying Fai Court, and write them into
the shared runtime (src/common.js.html, the `const PLAN = ...;` line).

Run it from a scratch folder holding the brochure as brochure.pdf, with this folder on the path:
    cd work && cp .../Sales-Brochure-YingFai.pdf brochure.pdf && PYTHONPATH=.. python3 -I ../pipeline.py
It needs pdfplumber, numpy, scipy, opencv-python and Pillow; the whole run takes ten minutes or so.

Steps (each leaves its result in the scratch folder):
  1 extract   the vector paths and text of the two typical floor plans (pages 26 and 30) -> vec.pkl
  2 fit       scale and place each plan on the site frame by matching its walls to flats 2/3 and 9/10 -> reg.json
  3 masks     walls, flat fills and line work drawn at 10 mm a pixel in the site frame -> m_A.pkl, m_B.pkl
  4 analyze   the floor's outline, the flats (fill + number), windows along the outline, fins -> blk_*.pkl
  5 rects     the walls cut into rectangles, square to the main wings and to the 45-degree wings -> rects_*.pkl
  6 flats     each flat in its own frame: doors, rooms (from the room labels), windows and their sills -> flats_all.pkl
  7 export    everything in each flat's millimetres plus the floor's walls in metres -> export.pkl, plan.json
  8 inject    plan.json into src/common.js.html
"""
import os, sys, json, pickle, subprocess, re
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
# `pipeline.py flats` starts again from that step, reusing what the earlier steps left in the folder
STEPS = ['extract', 'fit', 'masks', 'analyze', 'rects', 'flats', 'export', 'inject']
start = STEPS.index(sys.argv[1]) if len(sys.argv) > 1 else 0
run = lambda name: subprocess.run([sys.executable, os.path.join(here, name)] + ([] if name != 'extract.py' else ['vec.pkl']), check=True, env=dict(os.environ, PYTHONPATH=here))

def fit():
    import numpy as np, cv2, register
    from register import K, worldrects, raster_rects, raster_walls
    register.PXM = 100
    def best_fit(pn, blk, fids, box, mk, scales, pad_m=.6):
        ref = raster_rects(worldrects(fids[0], blk) + worldrects(fids[1], blk), box); best = None
        for sc in scales:
            img = raster_walls(pn, mk(K * sc, 0, 0), box); pad = int(pad_m * 100)
            r = cv2.matchTemplate(cv2.copyMakeBorder(ref, pad, pad, pad, pad, cv2.BORDER_CONSTANT, 0).astype(np.float32), img.astype(np.float32), cv2.TM_CCORR_NORMED)
            _, mv, _, ml = cv2.minMaxLoc(r); dx = (ml[0] - pad) / 100; dy = -(ml[1] - pad) / 100
            if not best or mv > best[0]: best = (mv, sc, dx, dy)
        return best
    sc = [1.006 + i * .001 for i in range(13)]
    _, sA, dxA, dyA = best_fit(26, 'A', ('A2', 'A3'), (-12, 3, -19, 9), lambda k, dx, dy: (lambda px, py: ((px - 1035.25) / k + dx, (356.6 - py) / k + dy)), sc)
    py0 = (-22.6 + 73.1214) * K; px0 = (-79.55 + 121.632) * K
    _, sB, dxB, dyB = best_fit(30, 'B', ('B9', 'B10'), (-35, -19, -98, -62), lambda k, dx, dy: (lambda px, py: (-22.6 + (py - py0) / k + dx, -79.55 + (px - px0) / k + dy)), sc)
    kA, kB = K * sA, K * sB
    json.dump(dict(A=dict(o=[-1035.25 / kA + dxA, 356.6 / kA + dyA], ex=[1 / kA, 0], ey=[0, -1 / kA]),
                   B=dict(o=[-22.6 - py0 / kB + dxB, -79.55 - px0 / kB + dyB], ex=[0, 1 / kB], ey=[1 / kB, 0])), open('reg.json', 'w'), indent=1)

def masks():
    import wmask
    for blk in 'AB':
        G, m = wmask.masks(blk); pickle.dump((G.__dict__, m), open(f'm_{blk}.pkl', 'wb'))

def rects():
    import numpy as np, cv2
    from rects import wall_rects
    for blk in 'AB':
        D = pickle.load(open(f'blk_{blk}.pkl', 'rb'))
        W = D['W'] & cv2.dilate(D['B'].astype(np.uint8), np.ones((41, 41), np.uint8)).astype(bool)
        del D
        r0, r1, M, _ = wall_rects(W); pickle.dump((r0, r1, M), open(f'rects_{blk}.pkl', 'wb'))

def inject():
    cj = os.path.join(here, '..', '..', 'common.js.html'); s = open(cj).read(); plan = open('plan.json').read()
    i = s.index('  const PLAN = '); j = s.index('\n', i)
    open(cj, 'w').write(s[:i] + '  const PLAN = ' + plan + ';' + s[j:]); print('PLAN written,', len(plan), 'bytes')

DO = {'extract': lambda: run('extract.py'), 'fit': fit, 'masks': masks, 'analyze': lambda: run('analyze.py'), 'rects': rects,
      'flats': lambda: run('runall.py'), 'export': lambda: (run('export.py'), run('tojson.py')), 'inject': inject}
for name in STEPS[start:]:
    print('--', name, flush=True); DO[name]()
