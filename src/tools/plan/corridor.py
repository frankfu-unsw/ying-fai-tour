"""The common parts of the typical floor you can walk through: the lift lobby, the corridors and the thresholds of the
flats' front doors, as a 0.1 m grid in the site frame (run-length rows), plus the six lift cars and which way each one's
doors face. Adds `cor`, `lifts` and `lobby` to each block in plan.json."""
import sys, os, json, pickle, math
sys.path.insert(0, '.')
import numpy as np, cv2
from scipy import ndimage as ndi
import wmask
from masks import d
from wmask import PAGE, tf, Grid, R
plan = json.load(open('plan.json'))
for blk in 'AB':
    D = pickle.load(open(f'blk_{blk}.pkl', 'rb')); G = Grid(blk); T = tf(blk); pn = PAGE[blk]
    W, B, lab = D['W'], D['B'], D['lab_all']; del D
    px = lambda x, y: (int((x - G.x0) * R), int((G.y1 - y) * R))
    # the lift cars and the lobby from the plan's own labels: "LIFT" under each car's Chinese name, "LIFT LOBBY" in the lobby
    ws = [w for w in d[pn]['words'] if 0 <= w['x0'] <= d[pn]['w']]
    lob = next(w for w in ws if w['text'] == 'LOBBY')
    up = (0, .2) if blk == 'A' else (-.2, 0)          # the label's first line sits above, i.e. north (A) or west (B)
    lp = T((lob['x0'] + lob['x1']) / 2, (lob['top'] + lob['bottom']) / 2); lobby = (lp[0] + up[0], lp[1] + up[1])
    lifts = []
    for w in ws:
        if w['text'] != 'LIFT' or abs(w['top'] - lob['top']) < 2 and abs(w['x1'] - lob['x0']) < 8: continue
        x, y = T((w['x0'] + w['x1']) / 2, (w['top'] + w['bottom']) / 2); x += up[0]; y += up[1]
        if any(math.hypot(x - a, y - b) < .5 for a, b, *_ in lifts): continue
        if math.hypot(x - lobby[0], y - lobby[1]) > 6: continue
        lifts.append([x, y])
    C = B & ~W & ~(lab > 0)
    seed = px(*lobby)
    cl, n = ndi.label(C); C = cl == cl[seed[1], seed[0]]
    # doors face the lobby: of the four diagonals, the one that reaches open floor first
    diag = [(math.sqrt(.5) * sx, math.sqrt(.5) * sy) for sx in (1, -1) for sy in (1, -1)]
    for L in lifts:
        best = max(diag, key=lambda q: (q[0] * (lobby[0] - L[0]) + q[1] * (lobby[1] - L[1])))
        L += [round(best[0], 4), round(best[1], 4)]
    # the shafts are not floor
    M = np.zeros(C.shape, np.uint8)
    for x, y, dx, dy in lifts:
        hs = 1.05; ex, ey = (dx, dy), (-dy, dx)
        pts = [px(x + (a * ex[0] + b * ey[0]) * hs, y + (a * ex[1] + b * ey[1]) * hs) for a, b in ((-1.2, -1), (1, -1), (1, 1), (-1.2, 1))]
        cv2.fillPoly(M, [np.array(pts, np.int32)], 1)
    C &= ~(M > 0)
    C = cv2.morphologyEx(C.astype(np.uint8), cv2.MORPH_OPEN, np.ones((40, 40), np.uint8)) > 0
    cl, n = ndi.label(C); C = cl == cl[seed[1], seed[0]]
    # 0.1 m cells: walkable where most of the cell is
    c = 10; H, Wd = C.shape[0] // c, C.shape[1] // c
    grid = C[:H * c, :Wd * c].reshape(H, c, Wd, c).mean(axis=(1, 3)) >= .5
    rows = []
    for j in range(H):
        r = grid[j]; dd = np.diff(np.concatenate([[0], r.astype(np.int8), [0]]))
        s = np.nonzero(dd == 1)[0]; e = np.nonzero(dd == -1)[0]
        rows.append(','.join(f'{a}+{b - a}' for a, b in zip(s, e)))
    plan[blk]['cor'] = dict(x0=G.x0, y1=G.y1, c=.1, w=int(Wd), h=int(H), r='|'.join(rows))
    plan[blk]['lifts'] = [[round(v, 3) for v in L] for L in lifts]
    plan[blk]['lobby'] = [round(lobby[0], 3), round(lobby[1], 3)]
    print(blk, 'lifts', len(lifts), 'lobby', plan[blk]['lobby'], 'cells', int(grid.sum()), 'chars', len(plan[blk]['cor']['r']))
    cv2.imwrite(f'cor_{blk}.png', (np.dstack([W * 120, C * 255, (lab > 0) * 120])[::4, ::4]).astype(np.uint8))
json.dump(plan, open('plan.json', 'w'), separators=(',', ':'))
