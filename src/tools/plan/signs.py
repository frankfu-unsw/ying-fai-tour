"""Way-finding signs for the corridors. Built on the corridor grid (corridor.py): its centre line, the shortest ways
along it from the lift lobby to every front door, and the points where those ways part.
  - in the lift lobby, on the wall between two lifts of each row, a directory: which way out of the lobby for which flats
  - where the way on from the lobby splits, a sign hangs facing you as you come from the lifts, with an arrow and the
    flat numbers for each way (a split that only parts the last two doors of a corridor gets none)
Adds `signs` to each block in plan.json: [kind, x, y, heading, [[arrow, [flat numbers]], ...]], kind 'w' on a wall or
'h' hanging, heading the way you face it (degrees from north), each arrow relative to that (-90 left, 0 ahead, 90 right)."""
import sys, json, math
import numpy as np, networkx as nx
from skimage.morphology import skeletonize

plan = json.load(open('plan.json'))
SHOW = '--show' in sys.argv
MERGE = 1.6       # two splits closer than this along the way are one junction, with one sign
AHEAD = 2.5       # how far down each way its arrow looks
NEAR = 3.0        # a way whose doors are all this close to the split needs no sign


def grid(c):
    g = np.zeros((c['h'], c['w']), bool)
    for j, row in enumerate(c['r'].split('|')):
        for run in filter(None, row.split(',')):
            s, n = map(int, run.split('+')); g[j, s:s + n] = True
    return g


def front_doors(blk):
    """Each flat's front door: a point in the corridor just outside it (as flatDoors in the tour)."""
    out = {}
    for no, f in plan[blk]['f'].items():
        d = next((q for q in f['d'] if q[0] == 'd' and q[5] == 2.1), None); e = f.get('e')
        if not d or not e: continue
        _, X0, X1, Y0, Y1, _h = d; along = X1 - X0 > Y1 - Y0; cX, cY = (X0 + X1) / 2, (Y0 + Y1) / 2
        oX = 0 if along else math.copysign(1, cX - e[0]); oY = math.copysign(1, cY - e[1]) if along else 0
        t = math.radians(f['th']); ex, ey = (math.cos(t), math.sin(t)), (math.sin(t), -math.cos(t)); O = f['O']
        w = lambda X, Y: (O[0] + (X * ex[0] + Y * ey[0]) / 1000, O[1] + (X * ex[1] + Y * ey[1]) / 1000)
        (cx, cy), (px, py) = w(cX, cY), w(cX + oX * 100, cY + oY * 100)
        l = math.hypot(px - cx, py - cy); out[int(no)] = (cx + (px - cx) / l * .7, cy + (py - cy) / l * .7)
    return out


def bearing(a, b): return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360


def in_wall(blk, x, y):
    for rx, ry, lx, ly, a, *_ in plan[blk]['r']:
        t = math.radians(a); dx, dy = x - rx, y - ry
        if abs(dx * math.cos(t) + dy * math.sin(t)) <= lx / 2 and abs(-dx * math.sin(t) + dy * math.cos(t)) <= ly / 2: return True
    return False


def rows_for(ex, head):
    """[arrow, flats] for each way, the arrow to the nearest 45 degrees, left to right"""
    rows = [[int(round(((b - head + 540) % 360 - 180) / 45) * 45), nos] for b, nos, _ in ex]
    return sorted(rows, key=lambda r: (r[0], r[1][0]))


def signs_for(blk):
    P = plan[blk]; c = P['cor']; g = grid(c); cs = c['c']
    xy = lambda n: (c['x0'] + (n[1] + .5) * cs, c['y1'] - (n[0] + .5) * cs)
    sk = skeletonize(g)
    G = nx.Graph()
    for j, i in zip(*np.nonzero(sk)):
        for dj, di in ((0, 1), (1, -1), (1, 0), (1, 1)):
            jj, ii = j + dj, i + di
            if 0 <= jj < sk.shape[0] and 0 <= ii < sk.shape[1] and sk[jj, ii]: G.add_edge((j, i), (jj, ii), w=math.hypot(dj, di) * cs)
    nodes = np.array(list(G.nodes)); pts = np.array([xy(n) for n in G.nodes])
    near = lambda p: tuple(nodes[np.argmin(((pts - p) ** 2).sum(1))])
    root = near(P['lobby'])
    doors = {no: near(p) for no, p in front_doors(blk).items()}
    dist, path = nx.single_source_dijkstra(G, root, weight='w')
    # the tree of ways from the lobby to the doors: each pixel's next step down, and the flats each pixel leads to
    kids, flats = {}, {}
    for no, n in doors.items():
        p = path[n]
        for a, b in zip(p, p[1:]): kids.setdefault(a, set()).add(b)
        for q in p: flats.setdefault(q, set()).add(no)
    parent = {b: a for a, bs in kids.items() for b in bs}
    def walk(n, ahead):   # down one way from n (towards the farthest flat) for `ahead` metres, or to a split
        d = 0
        while True:
            ks = kids.get(n, ())
            if len(ks) != 1: return n, d, len(ks) > 1
            k = next(iter(ks)); d += G[n][k]['w']; n = k
            if d >= ahead: return n, d, False
    def exits(n, at):     # the ways out of a split at n, folding in any split just beyond it
        out = []
        for k in kids[n]:
            end, d, split = walk(k, MERGE)
            d += G[n][k]['w']
            if split and d < MERGE and math.dist(xy(end), xy(at)) < MERGE: out += exits(end, at); continue
            # the way's direction: a point AHEAD metres on along it, or past the next split if that comes first
            q, dd = k, G[n][k]['w']
            while dd < AHEAD and kids.get(q):
                nxt = max(kids[q], key=lambda z: max(dist[doors[f]] for f in flats[z])); dd += G[q][nxt]['w']; q = nxt
            far = max(dist[doors[f]] for f in flats[k]) - dist[at]
            out.append((bearing(xy(at), xy(q)), sorted(flats[k]), far))
        return out
    splits = [n for n, ks in kids.items() if len(ks) > 1 and n != root]
    out = []
    for n in sorted(splits, key=lambda n: dist[n]):
        # a split just beyond an earlier one is folded into that one's sign
        q, d, prev = parent[n], 0, n
        covered = False
        while q is not None:
            d += G[q][prev]['w']
            if d >= MERGE: break
            if q in kids and len(kids[q]) > 1 and q != root and math.dist(xy(q), xy(n)) < MERGE: covered = True; break
            prev, q = q, parent.get(q)
        if covered: continue
        # the way you come in: from a point a couple of metres back towards the lifts
        q, d, prev = n, 0, None
        while q != root and d < 2:
            p = parent[q]; d += G[p][q]['w']; q = p
        head = bearing(xy(q), xy(n))
        ex = exits(n, n)
        if sum(far > NEAR for *_, far in ex) < 2: continue
        x, y = xy(n)
        out.append(['h', round(x, 2), round(y, 2), round(head, 1), rows_for(ex, head)])
    # the lobby directories: on each row of lifts, on the wall between the two lifts nearest the middle of the lobby
    ex = exits(root, root); rx, ry = xy(root)
    rows_of = {}
    for L in P['lifts']: rows_of.setdefault((L[2], L[3]), []).append(L)
    for (dx, dy), row in rows_of.items():
        ux, uy = -dy, dx
        row.sort(key=lambda L: (L[0] - rx) * ux + (L[1] - ry) * uy)
        gaps = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(row, row[1:])]
        gx, gy = min(gaps, key=lambda p: abs((p[0] - rx) * ux + (p[1] - ry) * uy))
        # from the middle of the lobby towards the row, to the face of the wall
        t0 = (rx - gx) * dx + (ry - gy) * dy; px0, py0 = gx + dx * t0, gy + dy * t0
        t = 0
        while t < 4 and not in_wall(blk, px0 - dx * t, py0 - dy * t): t += .005
        if t >= 4: continue
        x, y = px0 - dx * (t - .015), py0 - dy * (t - .015); head = bearing((0, 0), (-dx, -dy))
        out.append(['w', round(x, 3), round(y, 3), round(head, 1), rows_for(ex, head)])
    out.sort(key=lambda s: s[0] != 'w')
    if SHOW: show(blk, g, sk, kids, root, doors, out, xy)
    return out


def show(blk, g, sk, kids, root, doors, out, xy):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    c = plan[blk]['cor']; ext = [c['x0'], c['x0'] + c['w'] * c['c'], c['y1'] - c['h'] * c['c'], c['y1']]
    fig, ax = plt.subplots(figsize=(13, 13))
    ax.imshow(g, extent=ext, cmap='Greens', alpha=.35, origin='upper')
    ys, xs = np.nonzero(sk); ax.plot([xy((j, i))[0] for j, i in zip(ys, xs)], [xy((j, i))[1] for j, i in zip(ys, xs)], ',', color='0.6')
    for a, bs in kids.items():
        for b in bs: ax.plot(*zip(xy(a), xy(b)), '-', color='tab:blue', lw=1.5)
    ax.plot(*xy(root), 'r*', ms=14)
    for no, n in doors.items(): ax.annotate(str(no), xy(n), color='k', fontsize=9, ha='center')
    for kind, x, y, h, rows in out:
        ax.plot(x, y, 'o' if kind == 'h' else 's', color='tab:orange', ms=10)
        t = math.radians(h); ax.arrow(x - 1.2 * math.sin(t), y - 1.2 * math.cos(t), .8 * math.sin(t), .8 * math.cos(t), color='tab:orange', head_width=.3)
        for k, (rel, nos) in enumerate(rows):
            b = math.radians(h + rel); ax.arrow(x, y, 1.4 * math.sin(b), 1.4 * math.cos(b), color='tab:red', head_width=.25)
            ax.annotate(','.join(map(str, nos)), (x + 1.9 * math.sin(b), y + 1.9 * math.cos(b)), color='tab:red', fontsize=8, ha='center')
    ax.set_aspect('equal'); ax.grid(alpha=.2); plt.savefig(f'signs_{blk}.png', dpi=60, bbox_inches='tight')


for blk in 'AB':
    s = signs_for(blk); plan[blk]['signs'] = s
    print(blk, len(s), 'signs'); [print('  ', r) for r in s]
if '--dry' not in sys.argv: json.dump(plan, open('plan.json', 'w'), separators=(',', ':'))
