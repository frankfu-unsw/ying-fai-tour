#!/usr/bin/env python3
# NOTE: already applied. Plans A and C were swapped afterwards in index.src.html (A is now four bedrooms, C the sea-view bedrooms); edit the page directly.
"""Replace the furnished layouts of both flat types with three plans of three or four bedrooms, and correct the Block B shell from the
HA sales brochure (bay opening, second side window, east-window pier and stubs, side/gap/bath windows).

The plans are drawn for Block B flats 9/10; they are traced into the B frame (mm) and adapted onto
the Block A flat 2/3 shell. Run from src/: python3 tools/patch_layouts_v2.py
"""
import json, re, sys, os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'index.src.html')
s = open(SRC, encoding='utf-8').read()


# ---------------------------------------------------------------- helpers
def fmt(v):
    if isinstance(v, str):
        return "'" + v + "'"
    if isinstance(v, float):
        t = ('%.3f' % v).rstrip('0').rstrip('.')
        if t.startswith('0.'): t = t[1:]
        if t.startswith('-0.'): t = '-' + t[2:]
        return t
    return str(v)


def row(a):
    return '[' + ', '.join(fmt(x) for x in a) + ']'


def rows(lst, ind='  '):
    return ',\n'.join(ind + row(r) for r in lst)


def js(v):
    return json.dumps(v, ensure_ascii=False)


def bed(X0, X1, Y0, Y1, head, duvet, hb=1.05):
    """A bed with frame, mattress, duvet over the foot end, pillows and a headboard at `head`."""
    out = [[X0, X1, Y0, Y1, 0, .3, 'oak', 1], [X0 + 20, X1 - 20, Y0 + 20, Y1 - 20, .3, .5, 'linen']]
    alongY = head in ('Y0', 'Y1')
    L = (Y1 - Y0) if alongY else (X1 - X0)
    W = (X1 - X0) if alongY else (Y1 - Y0)
    dl = round(L * .66)
    if alongY:
        a0, a1 = X0, X1
        pw = [(a0 + 70, round((a0 + a1) / 2) - 35), (round((a0 + a1) / 2) + 35, a1 - 70)] if W >= 1000 else [(a0 + 80, a1 - 80)]
        if head == 'Y1':
            out.append([X0 + 10, X1 - 10, Y0 + 10, Y0 + dl, .5, .56, duvet])
            out += [[p, q, Y1 - 470, Y1 - 90, .5, .62, 'linen'] for p, q in pw]
            out.append([X0, X1, Y1 - 50, Y1, .3, hb, 'fabric'])
        else:
            out.append([X0 + 10, X1 - 10, Y1 - dl, Y1 - 10, .5, .56, duvet])
            out += [[p, q, Y0 + 90, Y0 + 470, .5, .62, 'linen'] for p, q in pw]
            out.append([X0, X1, Y0, Y0 + 50, .3, hb, 'fabric'])
    else:
        a0, a1 = Y0, Y1
        pw = [(a0 + 70, round((a0 + a1) / 2) - 35), (round((a0 + a1) / 2) + 35, a1 - 70)] if W >= 1000 else [(a0 + 80, a1 - 80)]
        if head == 'X1':
            out.append([X0 + 10, X0 + dl, Y0 + 10, Y1 - 10, .5, .56, duvet])
            out += [[X1 - 470, X1 - 90, p, q, .5, .62, 'linen'] for p, q in pw]
            out.append([X1 - 50, X1, Y0, Y1, .3, hb, 'fabric'])
        else:
            out.append([X1 - dl, X1 - 10, Y0 + 10, Y1 - 10, .5, .56, duvet])
            out += [[X0 + 90, X0 + 470, p, q, .5, .62, 'linen'] for p, q in pw]
            out.append([X0, X0 + 50, Y0, Y1, .3, hb, 'fabric'])
    return out


def wardrobe(X0, X1, Y0, Y1, front, h=2.1, mat='white'):
    """Built-in wardrobe with door handles on the `front` face."""
    out = [[X0, X1, Y0, Y1, 0, h, mat, 1]]
    if front in ('X0', 'X1'):
        n = 1 if Y1 - Y0 < 1300 else 2
        cs = [round(Y0 + (Y1 - Y0) * (i + .5) / n) for i in range(n)]
        x = [X0 - 10, X0] if front == 'X0' else [X1, X1 + 10]
        out += [[x[0], x[1], c - 30, c + 30, .9, 1.3, 'steel'] for c in cs]
    else:
        n = 1 if X1 - X0 < 1300 else 2
        cs = [round(X0 + (X1 - X0) * (i + .5) / n) for i in range(n)]
        y = [Y0 - 10, Y0] if front == 'Y0' else [Y1, Y1 + 10]
        out += [[c - 30, c + 30, y[0], y[1], .9, 1.3, 'steel'] for c in cs]
    return out


def sofa(X0, X1, Y0, Y1, back):
    """Three-seat sofa with its back on side `back`."""
    out = [[X0, X1, Y0, Y1, .12, .42, 'fabric', 1]]
    if back in ('X0', 'X1'):
        bx = [X1 - 230, X1] if back == 'X1' else [X0, X0 + 230]
        sx = [X0 + 20, X1 - 230] if back == 'X1' else [X0 + 230, X1 - 20]
        px = [X1 - 360, X1 - 230] if back == 'X1' else [X0 + 230, X0 + 360]
        m = round((Y0 + Y1) / 2)
        out += [[bx[0], bx[1], Y0, Y1, .42, .86, 'fabric'],
                [X0, X1, Y0, Y0 + 160, .42, .62, 'fabric'], [X0, X1, Y1 - 160, Y1, .42, .62, 'fabric'],
                [sx[0], sx[1], Y0 + 170, m - 10, .42, .52, 'fabric2'], [sx[0], sx[1], m + 10, Y1 - 170, .42, .52, 'fabric2'],
                [px[0], px[1], Y0 + 220, Y0 + 590, .52, .84, 'terracotta'], [px[0], px[1], Y1 - 590, Y1 - 220, .52, .84, 'sage']]
    else:
        by = [Y0, Y0 + 230] if back == 'Y0' else [Y1 - 230, Y1]
        sy = [Y0 + 230, Y1 - 20] if back == 'Y0' else [Y0 + 20, Y1 - 230]
        py = [Y0 + 230, Y0 + 360] if back == 'Y0' else [Y1 - 360, Y1 - 230]
        m = round((X0 + X1) / 2)
        out += [[X0, X1, by[0], by[1], .42, .86, 'fabric'],
                [X0, X0 + 160, Y0, Y1, .42, .62, 'fabric'], [X1 - 160, X1, Y0, Y1, .42, .62, 'fabric'],
                [X0 + 170, m - 10, sy[0], sy[1], .42, .52, 'fabric2'], [m + 10, X1 - 170, sy[0], sy[1], .42, .52, 'fabric2'],
                [X0 + 220, X0 + 590, py[0], py[1], .52, .84, 'terracotta'], [X1 - 590, X1 - 220, py[0], py[1], .52, .84, 'sage']]
    return out


def table(X0, X1, Y0, Y1):
    return [[X0, X1, Y0, Y1, .72, .76, 'oak', 1],
            [X0 + 30, X0 + 80, Y0 + 30, Y0 + 80, 0, .72, 'oak'], [X1 - 80, X1 - 30, Y0 + 30, Y0 + 80, 0, .72, 'oak'],
            [X0 + 30, X0 + 80, Y1 - 80, Y1 - 30, 0, .72, 'oak'], [X1 - 80, X1 - 30, Y1 - 80, Y1 - 30, 0, .72, 'oak']]


def desk(X0, X1, Y0, Y1):
    """Desk with solid end panels at both ends of its longer side."""
    out = [[X0, X1, Y0, Y1, .72, .76, 'oak', 1]]
    if Y1 - Y0 >= X1 - X0:
        out += [[X0 + 20, X1 - 20, Y0, Y0 + 30, 0, .72, 'oak'], [X0 + 20, X1 - 20, Y1 - 30, Y1, 0, .72, 'oak']]
    else:
        out += [[X0, X0 + 30, Y0 + 20, Y1 - 20, 0, .72, 'oak'], [X1 - 30, X1, Y0 + 20, Y1 - 20, 0, .72, 'oak']]
    return out


def tv(con, scr):
    """Low TV console `con` and a wall-mounted screen `scr` (both [X0, X1, Y0, Y1])."""
    return [con + [0, .45, 'oak', 1], scr + [.8, 1.55, 'black']]


def cab(X0, X1, Y0, Y1, h=2.2):
    return [[X0, X1, Y0, Y1, 0, h, 'white', 1]]


def low(X0, X1, Y0, Y1, h=.85):
    return [[X0, X1, Y0, Y1, 0, h, 'white', 1], [X0, X1, Y0, Y1, h, h + .03, 'oak']]


def rug(X0, X1, Y0, Y1):
    return [[X0, X1, Y0, Y1, 0, .008, 'rug']]


def fridge(X0, X1, Y0, Y1):
    return [[X0, X1, Y0, Y1, 0, 1.75, 'steel', 1]]


def chairs(xw, xe, ys):
    return [[xw, y, 'W'] for y in ys] + [[xe, y, 'E'] for y in ys]


def furn_js(name, items, comment=''):
    return f'const {name} = [\n' + rows(items) + '\n];' + (f'   // {comment}' if comment else '')


def sub(pattern_start, pattern_end, new, include_end=True, start_at=0):
    """Replace the text from pattern_start up to (and incl.) pattern_end, searching from start_at."""
    global s
    i = s.index(pattern_start, start_at)
    j = s.index(pattern_end, i + len(pattern_start))
    if include_end: j += len(pattern_end)
    s = s[:i] + new + s[j:]


ZH, MIR = {}, {}       # new translations; new flat-3 mirror wording (English -> English)


def zh(en, cn):
    ZH[en] = cn


def mir(en, en3, cn, cn3):
    """A flat-2 string with its flat-3 mirror and both translations."""
    MIR[en] = en3; ZH[en] = cn; ZH[en3] = cn3


# ================================================================ Block B shell (from the HA brochure)
PIECES_B = '''const PIECES_B = [
  ['wall', -250, 0, -250, 4450],
  ['wall', 0, 380, -250, 0],
  ['win', 380, 1140, -250, 0, { sill: .9, head: 2.3, id: 'sideW' }],
  ['wall', 1140, 1375, -250, 0],
  ['win', 1375, 1850, -250, 0, { sill: .9, head: 2.3, id: 'sideW2' }],
  ['wall', 1850, 3680, -250, 0],
  ['open', 3680, 4800, -250, 0, { head: 2.3 }],
  ['wall', 4800, 6000, -250, 0],
  ['win', 6000, 6745, -250, 0, { sill: .9, head: 2.3, id: 'sideE' }],
  ['wall', 6745, 8115, -250, 0],
  ['wall', 2440, 2690, -2610, -250],
  ['wall', 2440, 5080, -2610, -2360],
  ['wall', 4830, 5080, -2360, -2200],
  ['win', 4830, 5080, -2200, -400, { sill: .9, head: 2.3, id: 'bay' }],
  ['wall', 4830, 5080, -400, -250],
  ['wall', 7965, 8115, 0, 205],
  ['win', 7965, 8115, 205, 2425, { sill: .55, head: 2.3, id: 'eastN' }],
  ['wall', 7965, 8115, 2425, 2680],
  ['win', 7965, 8115, 2680, 4320, { sill: .55, head: 2.3, id: 'eastS' }],
  ['wall', 7965, 8115, 4320, 4775],
  ['wall', 5065, 6730, 4525, 4775],
  ['win', 6730, 7455, 4525, 4775, { sill: .9, head: 2.3, id: 'gapW' }],
  ['wall', 7455, 7965, 4525, 4775],
  ['wall', 3425, 3510, 2440, 2525], ['door', 3510, 4260, 2440, 2525, { head: 2.05 }], ['wall', 4260, 5065, 2440, 2525],
  ['wall', 3425, 3510, 2525, 3765], ['wall', 4980, 5065, 2525, 4525],
  ['wall', 3425, 3965, 4525, 4775], ['win', 3965, 4185, 4525, 4775, { sill: 1.5, head: 2.2, id: 'bathW' }], ['wall', 4185, 5065, 4525, 4775],
  ['wall', 1615, 2600, 3765, 3850], ['door', 2600, 3350, 3765, 3850, { head: 2.05 }], ['wall', 3350, 3510, 3765, 4525],
  ['wall', 3350, 3435, 4525, 4775], ['win', 3350, 3435, 4775, 5700, { sill: 1.05, head: 2.2, id: 'kitW' }], ['wall', 3350, 3435, 5700, 6165],
  ['wall', 1615, 1700, 3850, 5915], ['wall', 1615, 3435, 5915, 6165],
  ['wall', 0, 530, 4200, 4450], ['door', 530, 1420, 4200, 4450, { head: 2.1 }], ['wall', 1420, 1615, 4200, 4450]
];'''
sub('const PIECES_B = [', '\n];', PIECES_B)
s = re.sub(r"const WIN_NAMES_B = \{[^\n]*\};",
           "const WIN_NAMES_B = { eastN: 'east window (bay side)', eastS: 'east window (gap side)', bay: 'bay window', "
           "sideW: 'small side window', sideW2: 'second small side window', sideE: 'side window', gapW: 'window onto the gap', "
           "bathW: 'bathroom window', kitW: 'kitchen window' };", s)
zh('east window (bay side)', '東窗（近凸位一邊）'); zh('east window (gap side)', '東窗（近空隙一邊）')
zh('second small side window', '第二扇細側窗')

sub('const FURN_COMMON_B = [', '\n];', '''const FURN_COMMON_B = [
  [1720, 2320, 5302, 5315, .05, .82, 'white']   // washing machine (the fridge and shoe cabinet move with each plan)
];''')

# ================================================================ Block B layouts (traced from the three plans)
BAY_B = wardrobe(2690, 3290, -1100, -250, 'X1') + bed(2700, 4650, -2350, -1130, 'X0', 'terracotta')
# plan A: the two sea-view bedrooms side by side, living by the entrance
A_B = (cab(0, 350, 2550, 4180) + tv([0, 400, 250, 2350], [20, 60, 650, 1950]) + sofa(1900, 2700, 150, 1950, 'X1')
       + fridge(1500, 2100, 3120, 3765) + table(3650, 4450, 600, 2300)
       + wardrobe(5065, 5600, 3350, 4525, 'X1') + bed(6290, 7660, 2560, 4515, 'Y1', 'navy', .85)
       + wardrobe(5775, 7640, 2100, 2475, 'Y0', 2.2, 'oak') + desk(5775, 6250, 100, 1250) + bed(6440, 7660, 30, 1930, 'Y0', 'sage', .85)
       + BAY_B)
# plans B and C share the south half: living at the sea window, master on the gap side
BC_B = (fridge(1720, 2330, 3870, 4480) + table(3800, 4600, 600, 2300)
        + sofa(5970, 7710, 30, 830, 'Y0') + tv([6330, 7710, 2080, 2440], [6370, 7670, 2395, 2435]) + rug(6100, 7600, 950, 1950)
        + wardrobe(5065, 5600, 2515, 4525, 'X1') + bed(6350, 7720, 2525, 4515, 'Y1', 'navy', .85)
        + BAY_B)
B_B = (cab(0, 390, 2800, 4180) + cab(0, 1420, 2425, 2800)
       + wardrobe(0, 600, 1350, 2350, 'X1') + bed(0, 1950, 60, 1280, 'X0', 'sage') + BC_B)
C_B = (cab(0, 350, 2535, 4180)
       + low(0, 1240, 30, 430) + bed(35, 1205, 450, 2420, 'Y0', 'sage', .85)
       + bed(1340, 2510, 30, 2000, 'Y0', 'terracotta', .85) + wardrobe(1315, 2130, 2075, 2460, 'Y0', 2.1, 'oak')
       + BC_B)

LAYOUTS_B_JS = furn_js('B_A_FURN', A_B, 'plan A: two sea-view bedrooms, living by the entrance') + '\n' + \
    furn_js('B_B_FURN', B_B, 'plan B: corner bedroom, living at the sea window') + '\n' + \
    furn_js('B_C_FURN', C_B, 'plan C: two small bedrooms in the corner') + '\n' + '''
const KITCHEN_B = { id: 'kitchen', name: 'Kitchen', rects: [[1700, 3350, 3850, 5915]], at: [2525, 4900], win: 'Into the gap' };
const BATH_B = { id: 'bath', name: 'Bathroom', rects: [[3510, 4980, 2525, 4525]], at: [4245, 3500], win: 'Small window, into the gap', only: ['bathW'] };
const BAYBED_B = { id: 'bay', name: 'Bay bedroom', rects: [[2690, 4830, -2360, -250]], at: [3760, -1300], win: 'East (bay)', sea: true, only: ['bay'], role: 'bay' };
const BAY_PARTS_B = [['pdoor', 3680, 4480, -175, -100, { head: 2.1 }], ['part', 4480, 4800, -175, -100]];
const BAY_LEAF_B = [3680, 3720, -975, -175, 0, 2.05, 'white'];
const MASTER_BC_B = { id: 'master', name: 'Master bedroom', rects: [[5065, 7965, 2515, 4525]], at: [6520, 3520], win: 'East, sea', sea: true, only: ['eastS', 'gapW'], role: 'master' };
const MASTER_BC_PARTS_B = [['part', 5065, 5680, 2440, 2515], ['pdoor', 5680, 6340, 2440, 2515, { head: 2.1 }], ['part', 6340, 7965, 2440, 2515]];
const KITCHEN_ROW_B = ['Kitchen', 'onto the gap', 2900, 5000, ['kitW']];
const BC_WINS_B = [
  ['Master bedroom', 'east window (gap side)', 6800, 3500, ['eastS', 'gapW'], 'master'],
  ['Living & dining', 'east window (bay side)', 6500, 1300, ['eastN', 'sideE'], 'living'],
  ['Bay bedroom', 'faces east', 3760, -1250, ['bay'], 'bay']
];
const B_OPEN_RECTS = [[0, 1615, 0, 4200], [1615, 3425, 0, 3765], [3425, 5065, 0, 2440], [5065, 7965, 0, 4525]];
const LAYOUTS_B = {
  A: {
    name: 'Plan A', sub: 'Three bedrooms · sea-view bedrooms', furnished: true,
    desc: 'Three bedrooms: the two by the big east window split the sea view between them, divided by a wardrobe wall, and the bay becomes the third. The living room stays by the front door, with the TV on the end wall and only the two small side windows, so it has no sea view.',
    parts: [
      ['pdoor', 5065, 5780, 2475, 2550, { head: 2.1 }], ['part', 5780, 7965, 2475, 2550],
      ['part', 5700, 5775, 0, 1300], ['pdoor', 5700, 5775, 1300, 2000, { head: 2.1 }], ['part', 5700, 5775, 2000, 2475],
      ...BAY_PARTS_B
    ],
    leaves: [[5065, 5105, 2550, 3265, 0, 2.05, 'white'], [5775, 6475, 1960, 2000, 0, 2.05, 'white'], BAY_LEAF_B],
    rooms: [
      { id: 'master', name: 'Master bedroom', rects: [[5065, 7965, 2550, 4525]], at: [6520, 3540], win: 'East, sea', sea: true, only: ['eastS', 'gapW'], role: 'master' },
      { id: 'bed3', name: 'Sea-view bedroom', rects: [[5775, 7965, 0, 2475]], at: [6870, 1240], win: 'East, sea', sea: true, only: ['eastN', 'sideE'], role: 'bed3' },
      BAYBED_B,
      { id: 'living', name: 'Living & dining', rects: [[0, 1615, 0, 4200], [1615, 3425, 0, 3765], [3425, 5065, 0, 2440], [5065, 5700, 0, 2475]], at: [2400, 1500], win: 'Two small side windows', only: ['sideW', 'sideW2'], role: 'living' },
      KITCHEN_B, BATH_B
    ],
    furn: B_A_FURN, chairs: [[3400, 900, 'W'], [3400, 1450, 'W'], [3400, 2000, 'W'], [4700, 900, 'E'], [4700, 1450, 'E'], [4700, 2000, 'E']], pend: [4050, 1450], plant: [3050, 350],
    stops: ['door', 'kitchen', 'bath', 'dining', 'living', 'master', 'bed3', 'bay', 'doll'],
    over: {
      door: { text: 'Inside the front door. Tall cabinets and the TV run along the end wall, with the sofa facing them, and the fridge stands against the kitchen wall beside you. The dining table is further in, with the three bedroom doors beyond it.' },
      kitchen: { text: 'Counters along two walls, with the sink under a small window into the gap between flats 9 and 10. In this plan the fridge stands outside, against the kitchen wall by the front door.' },
      living: { sub: 'TV on the end wall', X: 3050, Y: 1050, yaw: 270, pitch: -6,
        text: 'Behind the sofa, facing the TV on the end wall. The living room is about 3.4 × 4 m by the entrance and is lit by the two small side windows. In this plan the sea window belongs to the bedrooms.' },
      master: { X: 5450, Y: 2950, yaw: 120,
        text: 'A 4′6″ double bed with its head under the window onto the gap, a tall wardrobe against the bathroom wall, and the gap-side pane of the east window. The wardrobe wall to the next bedroom meets the window at its middle pier.' },
      bed3: { name: 'Sea-view bedroom', sub: '2.2 × 2.5 m', X: 6050, Y: 1650, yaw: 85, pitch: -10,
        text: 'A 4′ bed with its head under the side window, a desk by the door and a wall of wardrobe shared with the master bedroom. It gets the bay-side pane of the east window, the wider of the two.' }
    },
    wins: [
      ['Master bedroom', 'east window (gap side)', 6800, 3500, ['eastS', 'gapW'], 'master'],
      ['Sea-view bedroom', 'east window (bay side)', 6800, 1250, ['eastN', 'sideE'], 'bed3'],
      ['Bay bedroom', 'faces east', 3760, -1250, ['bay'], 'bay'],
      ['Living & dining', 'two small side windows', 1100, 1300, ['sideW', 'sideW2'], 'living'],
      KITCHEN_ROW_B
    ]
  },
  B: {
    name: 'Plan B', sub: 'Three bedrooms · sea-view living room', furnished: true,
    desc: 'Three bedrooms. The living room moves to the big east window, with the sofa against the side wall and the TV on the master bedroom wall. A bedroom goes in the corner by the front door, under the two small side windows, and the bay is the third bedroom.',
    parts: [
      ['part', 0, 1950, 2350, 2425], ['part', 1950, 2025, 0, 1400], ['pdoor', 1950, 2025, 1400, 2100, { head: 2.1 }], ['part', 1950, 2025, 2100, 2425],
      ...MASTER_BC_PARTS_B, ...BAY_PARTS_B
    ],
    leaves: [[1250, 1950, 1400, 1440, 0, 2.05, 'white'], [5680, 5720, 2515, 3175, 0, 2.05, 'white'], BAY_LEAF_B],
    rooms: [
      MASTER_BC_B,
      { id: 'bed3', name: 'Corner bedroom', rects: [[0, 1950, 0, 2350]], at: [975, 1175], win: 'Two small side windows', only: ['sideW', 'sideW2'], role: 'bed3' },
      BAYBED_B,
      { id: 'living', name: 'Living & dining', rects: [[0, 1615, 2425, 4200], [1615, 1950, 2425, 3765], [1950, 3425, 0, 3765], [3425, 5065, 0, 2440], [5065, 7965, 0, 2440]], at: [5900, 1500], win: 'East, sea', sea: true, only: ['eastN', 'sideE'], role: 'living' },
      KITCHEN_B, BATH_B
    ],
    furn: B_B_FURN, chairs: [[3550, 900, 'W'], [3550, 1450, 'W'], [3550, 2000, 'W'], [4850, 900, 'E'], [4850, 1450, 'E'], [4850, 2000, 'E']], pend: [4200, 1450], plant: [5300, 300],
    stops: ['door', 'kitchen', 'bath', 'dining', 'living', 'window', 'master', 'bed3', 'bay', 'doll'],
    over: {},
    wins: [...BC_WINS_B, ['Corner bedroom', 'two small side windows', 1000, 1000, ['sideW', 'sideW2'], 'bed3'], KITCHEN_ROW_B]
  },
  C: {
    name: 'Plan C', sub: 'Four bedrooms', furnished: true,
    desc: 'Four bedrooms. As in plan B, but the corner by the front door is split into two small bedrooms, one under each small side window, each just big enough for a 4′ bed and with a sliding door.',
    parts: [
      ['part', 0, 480, 2460, 2535], ['pdoor', 480, 1240, 2460, 2535, { head: 2.1 }], ['part', 1240, 1315, 0, 2535],
      ['part', 1315, 2605, 2460, 2535], ['part', 2530, 2605, 0, 1170], ['pdoor', 2530, 2605, 1170, 1975, { head: 2.1 }], ['part', 2530, 2605, 1975, 2460],
      ...MASTER_BC_PARTS_B, ...BAY_PARTS_B
    ],
    leaves: [[5680, 5720, 2515, 3175, 0, 2.05, 'white'], BAY_LEAF_B],
    rooms: [
      MASTER_BC_B,
      { id: 'bed3', name: 'Small bedroom 1', rects: [[0, 1240, 0, 2460]], at: [620, 1300], win: 'Small side window', only: ['sideW'], role: 'bed3' },
      { id: 'bed4', name: 'Small bedroom 2', rects: [[1315, 2530, 0, 2460]], at: [1920, 1300], win: 'Small side window', only: ['sideW2'], role: 'bed4' },
      BAYBED_B,
      { id: 'living', name: 'Living & dining', rects: [[0, 1615, 2535, 4200], [1615, 2605, 2535, 3765], [2605, 3425, 0, 3765], [3425, 5065, 0, 2440], [5065, 7965, 0, 2440]], at: [5900, 1500], win: 'East, sea', sea: true, only: ['eastN', 'sideE'], role: 'living' },
      KITCHEN_B, BATH_B
    ],
    furn: B_C_FURN, chairs: [[3550, 900, 'W'], [3550, 1450, 'W'], [3550, 2000, 'W'], [4850, 900, 'E'], [4850, 1450, 'E'], [4850, 2000, 'E']], pend: [4200, 1450], plant: [5300, 300],
    stops: ['door', 'kitchen', 'bath', 'dining', 'living', 'window', 'master', 'bed3', 'bed4', 'bay', 'doll'],
    over: {
      door: { text: 'Inside the front door. Tall cabinets line the end wall beside the sliding door of the first small bedroom. The second small bedroom, the kitchen and the dining table are further in, and the living room is at the sea window.' },
      bed3: { name: 'Small bedroom 1', sub: '1.25 × 2.45 m', X: 860, Y: 2850, yaw: 0, pitch: -20,
        text: 'A small room about 1.25 × 2.45 m, filled by a 4′ bed, with low storage under its own small side window. A sliding door opens onto the entrance.' }
    },
    wins: [...BC_WINS_B, ['Small bedroom 1', 'small side window', 620, 1250, ['sideW'], 'bed3'], ['Small bedroom 2', 'second small side window', 1920, 1250, ['sideW2'], 'bed4'], KITCHEN_ROW_B]
  },
  bare: {
    name: 'Bare', sub: 'As handed over', furnished: false,
    desc: 'The flat as the HA hands it over: one long open room with a bay, with only the kitchen and bathroom enclosed.',
    parts: [], leaves: [],
    rooms: [
      { id: 'open', name: 'Open-plan living', rects: B_OPEN_RECTS, at: [5900, 1500], win: 'East, sea', sea: true, role: 'living' },
      { id: 'bay', name: 'Bay', rects: [[2690, 4830, -2360, -250], [3680, 4800, -250, 0]], at: [3760, -1150], win: 'East (bay)', sea: true, role: 'bay' },
      KITCHEN_B, BATH_B
    ],
    furn: [], chairs: [], pend: null, plant: null,
    stops: ['door', 'kitchen', 'bath', 'bed3', 'dining', 'living', 'window', 'bay', 'doll'],
    over: {
      door: { text: 'Inside the front door. As handed over, the flat is one long open room with a bay; only the kitchen and bathroom are enclosed.' },
      kitchen: { text: 'The HA hands over the sink and the gas and washing-machine connections. The window looks into the gap between flats 9 and 10.' },
      bed3: { name: 'West end', sub: 'By the front door', X: 1650, Y: 1800, yaw: 320, pitch: -10,
        text: 'The west end of the room, about 3.4 × 4 m, with two small side windows. Plans B and C put one or two bedrooms here.' },
      dining: { name: 'Middle of the room', sub: 'Open plan', text: 'The middle of the room, with the bay straight ahead.' },
      living: { sub: 'Main room', text: 'The east end of the room with the full-width sea window, before any furniture.' },
      bay: { name: 'The bay', sub: '2.1 × 2.1 m', text: 'A deep bay off the middle of the room with its own east-facing window.' }
    },
    wins: [
      ['Living area', 'east window', 6800, 1300, ['eastN', 'eastS'], 'living'],
      ['Living area', 'side window', 6250, 1150, ['sideE'], 'living'],
      ['Bay', 'faces east', 3760, -1250, ['bay'], 'bay'],
      ['West end', 'two small side windows', 1100, 1250, ['sideW', 'sideW2'], 'bed3'],
      ['Living area', 'window onto the gap', 6975, 3500, ['gapW'], 'living'],
      KITCHEN_ROW_B
    ]
  }
};
const STOPDEF_B = {
  door: { name: 'Front door', sub: 'Entrance', X: 1000, Y: 3650, yaw: 40, pitch: -6,
    text: 'Inside the front door. An L of tall cabinets wraps round the corner bedroom ahead and the kitchen is beside you. The dining table and the sea-view living room lie beyond.' },
  kitchen: { name: 'Kitchen', sub: '1.65 × 2.07 m', X: 2500, Y: 4200, yaw: 160, pitch: -22,
    text: 'Counters along two walls, with the fridge by the door and the sink under a small window into the gap between flats 9 and 10.' },
  bath: { name: 'Bathroom', sub: '1.47 × 2.0 m', X: 4300, Y: 2850, yaw: 150, pitch: -20,
    text: 'Shower, toilet and basin, with a small high window into the gap between flats 9 and 10.' },
  dining: { name: 'Dining', sub: 'Table for six', X: 3000, Y: 3050, yaw: 45, pitch: -8,
    text: 'The table for six sits between the bathroom and the bay. Its end runs right up to the bathroom door, so in practice a shorter table would be needed to get into the bathroom. The bay bedroom door is straight ahead.' },
  living: { name: 'Living room', sub: 'At the sea window', X: 5300, Y: 1350, yaw: 90, pitch: -6,
    text: 'The living room takes the wider, bay-side pane of the east window and is about 2.9 × 2.4 m. The sofa sits against the side wall under the side window, and the TV faces it from the master bedroom wall, with a rug between.' },
  window: { name: 'East window', sub: 'Best view', X: 7300, Y: 1300, yaw: 95, pitch: -7,
    text: 'Close to the glass of the wider, bay-side pane of the east window. There is no acoustic fin beside flats 9 and 10; only the window frame and the pier limit the view.' },
  master: { name: 'Master bedroom', sub: '2.9 × 2.0 m', X: 5900, Y: 2850, yaw: 115, pitch: -14,
    text: 'A 4′6″ double bed with its head under the window onto the gap, and a full-width wardrobe along the bathroom wall. It gets the gap-side pane of the east window; its wall meets the glass at the window’s middle pier.' },
  bed3: { name: 'Corner bedroom', sub: '1.95 × 2.35 m', X: 1650, Y: 1800, yaw: 320, pitch: -12,
    text: 'A 4′ bed along the side wall under both small side windows, with a wardrobe at the far end. It sits by the front door, away from the living room.' },
  bed4: { name: 'Small bedroom 2', sub: '1.2 × 2.45 m', X: 2850, Y: 1550, yaw: 270, pitch: -16,
    text: 'The second small room, the same size: a 4′ bed under the other small side window and a wardrobe at its foot, with a sliding door onto the dining area.' },
  bay: { name: 'Bay bedroom', sub: '2.1 × 2.1 m', X: 4250, Y: -550, yaw: 330, pitch: -14,
    text: 'The bay becomes a bedroom about 2.1 × 2.1 m: a 4′ bed with its head on the end wall, a wardrobe beside the door, and the bay window at the foot of the bed.' },
  doll: { name: 'Dollhouse', sub: 'Whole flat from above', doll: true,
    text: 'The whole flat with the walls cut at chest height. Drag to turn it; tap a room to step inside.' }
};

'''
sub('const B_OPEN_FURN = [', '// ---------------- flat 3: flat 2', LAYOUTS_B_JS + '// ---------------- flat 3: flat 2', include_end=True)

# Block B translations (texts are neutral: flats 9 and 10 share them)
for en, cn in [
    ('Three bedrooms · sea-view bedrooms', '三房 · 睡房向海'),
    ('Three bedrooms · sea-view living room', '三房 · 客廳向海'),
    ('Four bedrooms', '四房'),
    ('Three bedrooms: the two by the big east window split the sea view between them, divided by a wardrobe wall, and the bay becomes the third. The living room stays by the front door, with the TV on the end wall and only the two small side windows, so it has no sea view.',
     '三房：大東窗旁的兩間睡房以一幅衣櫃牆分隔，平分海景，凸位就成為第三間睡房。客廳留在大門旁，電視靠尾牆，只有兩扇細側窗，看不到海。'),
    ('Three bedrooms. The living room moves to the big east window, with the sofa against the side wall and the TV on the master bedroom wall. A bedroom goes in the corner by the front door, under the two small side windows, and the bay is the third bedroom.',
     '三房。客廳搬到大東窗前，梳化靠側牆，電視掛在主人房的牆上。大門旁的角落間出一間睡房，有兩扇細側窗，凸位就是第三間睡房。'),
    ('Four bedrooms. As in plan B, but the corner by the front door is split into two small bedrooms, one under each small side window, each just big enough for a 4′ bed and with a sliding door.',
     '四房。與方案B相同，但大門旁的角落再分成兩間細睡房，每間各有一扇細側窗，剛好放得下一張4呎床，用趟門出入。'),
    ('Bay bedroom', '凸位睡房'), ('Sea-view bedroom', '海景睡房'), ('Corner bedroom', '角落睡房'),
    ('Small bedroom 1', '細睡房一'), ('Small bedroom 2', '細睡房二'), ('Bed 3', '睡房三'), ('Bed 4', '睡房四'),
    ('Small window, into the gap', '細窗，望向單位之間的空隙'), ('Two small side windows', '兩扇細側窗'), ('Small side window', '細側窗'),
    ('two small side windows', '兩扇細側窗'),
    ('Entrance', '入口'), ('Table for six', '六人餐桌'), ('TV on the end wall', '電視靠尾牆'), ('TV on the west wall', '電視靠西牆'),
    ('2.2 × 2.5 m', '2.2 × 2.5米'), ('2.1 × 2.5 m', '2.1 × 2.5米'), ('1.95 × 2.35 m', '1.95 × 2.35米'), ('1.25 × 2.45 m', '1.25 × 2.45米'),
    ('1.2 × 2.45 m', '1.2 × 2.45米'), ('2.1 × 2.1 m', '2.1 × 2.1米'), ('2.15 × 2.1 m', '2.15 × 2.1米'),
    ('Bedrooms', '睡房數目'), ('Third bedroom', '第三間睡房'), ('Fourth bedroom', '第四間睡房'),
    ('Inside the front door. Tall cabinets and the TV run along the end wall, with the sofa facing them, and the fridge stands against the kitchen wall beside you. The dining table is further in, with the three bedroom doors beyond it.',
     '剛進大門。高櫃和電視沿尾牆排開，梳化面向它們，雪櫃就在你身旁靠著廚房牆。再走進去是餐桌，三間睡房的門在餐桌後面。'),
    ('Counters along two walls, with the sink under a small window into the gap between flats 9 and 10. In this plan the fridge stands outside, against the kitchen wall by the front door.',
     '兩邊牆都有工作枱，洗滌盆在小窗下，窗外是9室與10室之間的空隙。這個方案把雪櫃放在廚房外，靠著大門旁的廚房牆。'),
    ('Behind the sofa, facing the TV on the end wall. The living room is about 3.4 × 4 m by the entrance and is lit by the two small side windows. In this plan the sea window belongs to the bedrooms.',
     '站在梳化後面，面向尾牆上的電視。客廳在入口旁，約3.4 × 4米，靠兩扇細側窗採光。這個方案的海景窗歸睡房所有。'),
    ('A 4′6″ double bed with its head under the window onto the gap, a tall wardrobe against the bathroom wall, and the gap-side pane of the east window. The wardrobe wall to the next bedroom meets the window at its middle pier.',
     '4呎6雙人床床頭靠望向空隙的窗，浴室牆前放高衣櫃，房間取得東窗近空隙一邊的一格。與隔壁睡房之間的衣櫃牆，剛好在窗中間的牆柱處與窗相接。'),
    ('A 4′ bed with its head under the side window, a desk by the door and a wall of wardrobe shared with the master bedroom. It gets the bay-side pane of the east window, the wider of the two.',
     '4呎床床頭靠側窗，門邊放書桌，與主人房之間是一整幅衣櫃牆。房間取得東窗近凸位一邊的一格，是較闊的一格。'),
    ('Inside the front door. Tall cabinets line the end wall beside the sliding door of the first small bedroom. The second small bedroom, the kitchen and the dining table are further in, and the living room is at the sea window.',
     '剛進大門。尾牆排著高櫃，旁邊是第一間細睡房的趟門。再走進去是第二間細睡房、廚房和餐桌，客廳在海景窗前。'),
    ('A small room about 1.25 × 2.45 m, filled by a 4′ bed, with low storage under its own small side window. A sliding door opens onto the entrance.',
     '一間約1.25 × 2.45米的小房，一張4呎床已經放滿，自己那扇細側窗下有矮儲物櫃。趟門開向入口。'),
    ('The HA hands over the sink and the gas and washing-machine connections. The window looks into the gap between flats 9 and 10.',
     '交樓時已有洗滌盆，並預留煤氣和洗衣機接駁位。窗口望向9室與10室之間的空隙。'),
    ('The west end of the room, about 3.4 × 4 m, with two small side windows. Plans B and C put one or two bedrooms here.',
     '房間西端，約3.4 × 4米，有兩扇細側窗。方案B和C在這裡間出一至兩間睡房。'),
    ('Inside the front door. An L of tall cabinets wraps round the corner bedroom ahead and the kitchen is beside you. The dining table and the sea-view living room lie beyond.',
     '剛進大門。一列L形高櫃包著前面角落睡房的外牆，廚房就在你身旁。再走進去是餐桌和向海的客廳。'),
    ('Counters along two walls, with the fridge by the door and the sink under a small window into the gap between flats 9 and 10.',
     '兩邊牆都有工作枱，雪櫃在門邊，洗滌盆在小窗下，窗外是9室與10室之間的空隙。'),
    ('Shower, toilet and basin, with a small high window into the gap between flats 9 and 10.',
     '有企缸、座廁和洗手盆，另有一扇高位細窗望向9室與10室之間的空隙。'),
    ('The table for six sits between the bathroom and the bay. Its end runs right up to the bathroom door, so in practice a shorter table would be needed to get into the bathroom. The bay bedroom door is straight ahead.',
     '六人餐桌放在浴室與凸位之間。桌尾緊貼浴室門，實際上要用短一點的餐桌才進得了浴室。凸位睡房的門在正前方。'),
    ('The living room takes the wider, bay-side pane of the east window and is about 2.9 × 2.4 m. The sofa sits against the side wall under the side window, and the TV faces it from the master bedroom wall, with a rug between.',
     '客廳取得東窗較闊、近凸位一邊的一格，約2.9 × 2.4米。梳化靠側牆放在側窗下，電視掛在主人房的牆上與梳化相對，中間鋪地氈。'),
    ('Close to the glass of the wider, bay-side pane of the east window. There is no acoustic fin beside flats 9 and 10; only the window frame and the pier limit the view.',
     '貼近東窗較闊、近凸位一邊的玻璃。9室和10室旁邊沒有隔音鰭，只有窗框和窗中間的牆柱限制視野。'),
    ('A 4′6″ double bed with its head under the window onto the gap, and a full-width wardrobe along the bathroom wall. It gets the gap-side pane of the east window; its wall meets the glass at the window’s middle pier.',
     '4呎6雙人床床頭靠望向空隙的窗，沿浴室牆放一整排衣櫃。房間取得東窗近空隙一邊的一格；間牆剛好在窗中間的牆柱處與窗相接。'),
    ('A 4′ bed along the side wall under both small side windows, with a wardrobe at the far end. It sits by the front door, away from the living room.',
     '4呎床沿側牆放在兩扇細側窗下，盡頭有衣櫃。房間在大門旁，與客廳分開。'),
    ('The second small room, the same size: a 4′ bed under the other small side window and a wardrobe at its foot, with a sliding door onto the dining area.',
     '第二間小房，大小一樣：4呎床放在另一扇細側窗下，床尾有衣櫃，趟門開向飯廳。'),
    ('The bay becomes a bedroom about 2.1 × 2.1 m: a 4′ bed with its head on the end wall, a wardrobe beside the door, and the bay window at the foot of the bed.',
     '凸位變成一間約2.1 × 2.1米的睡房：4呎床床頭靠盡頭的牆，門旁有衣櫃，凸位窗就在床尾。'),
]:
    zh(en, cn)

# ================================================================ Block A layouts (adapted onto flat 2/3)
BAY_A = wardrobe(2750, 3350, -1100, -250, 'X1') + bed(2760, 4700, -2240, -1120, 'X0', 'terracotta')
HALL_A = cab(0, 350, 2650, 3800)
A_A = (HALL_A + tv([0, 400, 300, 2300], [20, 60, 650, 1950]) + sofa(1900, 2700, 150, 1950, 'X1') + table(3650, 4450, 600, 2300)
       + wardrobe(5080, 5620, 3350, 4525, 'X1') + bed(6300, 7670, 2615, 4515, 'Y1', 'navy', .85)
       + wardrobe(5875, 7640, 2135, 2525, 'Y0', 2.2, 'oak') + desk(5875, 6350, 80, 1250) + bed(6440, 7660, 30, 1930, 'Y0', 'sage')
       + BAY_A)
BC_A = (HALL_A + table(3800, 4600, 600, 2300)
        + sofa(5970, 7710, 30, 830, 'Y0') + tv([6330, 7710, 2165, 2525], [6370, 7670, 2480, 2520]) + rug(6100, 7600, 950, 2050)
        + wardrobe(5080, 5620, 2600, 4525, 'X1') + bed(6420, 7790, 2615, 4515, 'Y1', 'navy', .85)
        + BAY_A)
B_A = wardrobe(0, 600, 1350, 2350, 'X1') + bed(0, 1950, 60, 1280, 'X0', 'sage') + BC_A
C_A = (low(0, 1240, 30, 430) + bed(35, 1205, 450, 2420, 'Y0', 'sage', .85)
       + bed(1340, 2510, 30, 2000, 'Y0', 'terracotta', .85) + wardrobe(1315, 2130, 2075, 2460, 'Y0', 2.1, 'oak') + BC_A)

LAYOUTS_A_JS = '''// ---------------- layouts ----------------
// Three plans with three or four bedrooms, drawn first for flats 9 and 10 and adapted here onto flat 2's shell. Each adds light 75 mm partitions: [kind, X0, X1, Y0, Y1, opts]
//   part = partition, pdoor = door opening in it, jamb = frame post where a partition meets the window
// furniture rows: [X0, X1, Y0, Y1, z0, z1, material, drawOnPlan]
const FURN_COMMON_A = [
  [1810, 2480, 3930, 4600, 0, 1.75, 'steel', 1], [1820, 2420, 5322, 5335, .05, .82, 'white'],   // fridge, washing machine
  [0, 380, 3950, 5150, 0, 1.0, 'oak', 1]                                                          // shoe cabinet
];
''' + furn_js('A_A_FURN', A_A, 'plan A: two sea-view bedrooms, living by the hall') + '\n' + \
    furn_js('A_B_FURN', B_A, 'plan B: north-west bedroom, living at the sea window') + '\n' + \
    furn_js('A_C_FURN', C_A, 'plan C: two small bedrooms in the north-west corner') + '\n' + '''
const KITCHEN_ROOM = { id: 'kitchen', name: 'Kitchen', rects: [[1800, 3440, 3920, 5935]], at: [2620, 4950], win: 'East, into the gap' };
const BATH_ROOM = { id: 'bath', name: 'Bathroom', rects: [[3525, 4995, 2525, 4525]], at: [4260, 3420], win: 'South, into the gap', only: ['bathW'] };
const FOYER_ROOM = { id: 'foyer', name: 'Foyer', rects: [[0, 1600, 2600, 5555], [1600, 3440, 2600, 3835]], at: [800, 4650] };
const KITCHEN_ROW = ['Kitchen', 'east, down the gap', 2950, 5475, ['kitW']];
const BAYBED_A = { id: 'bay', name: 'Bay bedroom', rects: [[2750, 4900, -2250, -250]], at: [3825, -1300], win: 'East (bay), sea slice', sea: true, only: ['bay'], role: 'bay' };
const BAY_PARTS_A = [['pdoor', 3650, 4400, -175, -100, { head: 2.1 }], ['part', 4400, 4800, -175, -100]];
const BAY_LEAF_A = [3650, 3690, -925, -175, 0, 2.05, 'white'];
const MASTER_A = { id: 'master', name: 'Master bedroom', rects: [[5080, 7965, 2600, 4525]], at: [6520, 3560], win: 'East, sea', sea: true, only: ['eastS', 'south'], role: 'master' };
const MASTER_BC_PARTS_A = [['part', 5080, 5700, 2525, 2600], ['pdoor', 5700, 6400, 2525, 2600, { head: 2.1 }], ['part', 6400, 7965, 2525, 2600]];
const BC_WINS_A = [
  ['Master bedroom', 'east, south half', 6540, 3547, ['eastS', 'south'], 'master'],
  ['Living & dining', 'east, north half', 6540, 1255, ['eastN'], 'living'],
  ['Bay bedroom', 'bay, faces east', 4037, -1250, ['bay'], 'bay']
];
// rows: [room, window, X, Y, windows counted, role]; X null = no window
const LAYOUTS_A = {
  A: {
    name: 'Plan A', sub: 'Three bedrooms · sea-view bedrooms', furnished: true,
    desc: 'Three bedrooms. Two of them share the big east window, split at its middle post with a wardrobe wall between them, and the bay becomes the third. The living room stays by the hall, with the TV on the west wall and only the north window, so it has no sea view.',
    parts: [
      ['pdoor', 5080, 5800, 2525, 2600, { head: 2.1 }], ['part', 5800, 7965, 2525, 2600],
      ['part', 5800, 5875, 0, 1300], ['pdoor', 5800, 5875, 1300, 2000, { head: 2.1 }], ['part', 5800, 5875, 2000, 2525],
      ...BAY_PARTS_A
    ],
    leaves: [[5080, 5120, 2600, 3320, 0, 2.05, 'white'], [5875, 6575, 1960, 2000, 0, 2.05, 'white'], BAY_LEAF_A],
    rooms: [
      MASTER_A,
      { id: 'bed3', name: 'Sea-view bedroom', rects: [[5875, 7965, 0, 2525]], at: [6920, 1250], win: 'East, sea', sea: true, only: ['eastN'], role: 'bed3' },
      BAYBED_A,
      { id: 'living', name: 'Living & dining', rects: [[0, 3440, 0, 2600], [3440, 5080, 0, 2440], [5080, 5800, 0, 2525]], at: [2400, 1400], win: 'North, hillside', only: ['north'], role: 'living' },
      KITCHEN_ROOM, BATH_ROOM, FOYER_ROOM
    ],
    furn: A_A_FURN, chairs: [[3400, 900, 'W'], [3400, 1450, 'W'], [3400, 2000, 'W'], [4700, 900, 'E'], [4700, 1450, 'E'], [4700, 2000, 'E']], pend: [4050, 1450], plant: [3050, 350],
    stops: ['door', 'hall', 'kitchen', 'bath', 'dining', 'living', 'master', 'bed3', 'bay', 'doll'],
    over: {
      hall: { text: 'The hall at the end of the foyer. The kitchen door is on your right and the bathroom is straight ahead. The living room opens on the left, with the TV on the west wall.' },
      dining: { text: 'The table for six sits between the bathroom and the bay, with the bay bedroom door straight ahead. The two sea-view bedrooms open off the far end, by the east window.' },
      living: { sub: 'TV on the west wall', X: 3050, Y: 1100, yaw: 270, pitch: -6,
        text: 'Behind the sofa, facing the TV on the west wall. The living room keeps the north window, which looks onto the hillside; in this plan the sea window belongs to the bedrooms.' },
      master: { X: 5450, Y: 2950, yaw: 125,
        text: 'A 4′6″ double bed with its head on the south wall, a tall wardrobe against the bathroom wall, and the south half of the east window plus the small south window. The new wall meets the window at its middle post.' },
      bed3: { name: 'Sea-view bedroom', sub: '2.1 × 2.5 m', X: 6100, Y: 1650, yaw: 80, pitch: -10,
        text: 'A 4′ bed with its head on the north wall, a desk by the door and a wall of wardrobe shared with the master bedroom. It gets the north half of the east window. The acoustic fin is just outside.' }
    },
    wins: [
      ['Master bedroom', 'east, south half', 6540, 3547, ['eastS', 'south'], 'master'],
      ['Sea-view bedroom', 'east, north half', 6540, 1200, ['eastN'], 'bed3'],
      ['Bay bedroom', 'bay, faces east', 4037, -1250, ['bay'], 'bay'],
      ['Living & dining', 'north', 1125, 1375, ['north'], 'living'],
      KITCHEN_ROW
    ]
  },
  B: {
    name: 'Plan B', sub: 'Three bedrooms · sea-view living room', furnished: true,
    desc: 'Three bedrooms. The living room takes the north half of the east window, with the sofa against the north wall and the TV on the master bedroom wall. A bedroom goes in the north-west corner under the north window, and the bay is the third bedroom.',
    parts: [
      ['part', 0, 1950, 2350, 2425], ['part', 1950, 2025, 0, 1400], ['pdoor', 1950, 2025, 1400, 2100, { head: 2.1 }], ['part', 1950, 2025, 2100, 2425],
      ...MASTER_BC_PARTS_A, ...BAY_PARTS_A
    ],
    leaves: [[1250, 1950, 1400, 1440, 0, 2.05, 'white'], [5700, 5740, 2600, 3300, 0, 2.05, 'white'], BAY_LEAF_A],
    rooms: [
      MASTER_A,
      { id: 'bed3', name: 'Corner bedroom', rects: [[0, 1950, 0, 2350]], at: [975, 1175], win: 'North, hillside', only: ['north'], role: 'bed3' },
      BAYBED_A,
      { id: 'living', name: 'Living & dining', rects: [[1950, 3440, 0, 2600], [3440, 5080, 0, 2440], [5080, 7965, 0, 2525], [0, 1950, 2425, 2600]], at: [5400, 1250], win: 'East, sea', sea: true, only: ['eastN'], role: 'living' },
      KITCHEN_ROOM, BATH_ROOM, FOYER_ROOM
    ],
    furn: A_B_FURN, chairs: [[3550, 900, 'W'], [3550, 1450, 'W'], [3550, 2000, 'W'], [4850, 900, 'E'], [4850, 1450, 'E'], [4850, 2000, 'E']], pend: [4200, 1450], plant: [5300, 300],
    stops: ['door', 'hall', 'kitchen', 'bath', 'dining', 'living', 'window', 'master', 'bed3', 'bay', 'doll'],
    over: {},
    wins: [...BC_WINS_A, ['Corner bedroom', 'north', 1000, 1375, ['north'], 'bed3'], KITCHEN_ROW]
  },
  C: {
    name: 'Plan C', sub: 'Four bedrooms', furnished: true,
    desc: 'Four bedrooms. As in plan B, but the north-west corner becomes two small bedrooms, each just big enough for a 4′ bed, sharing the north window: the wall between them needs a new frame post where it meets the glass. Both have sliding doors.',
    parts: [
      ['part', 0, 480, 2460, 2535], ['pdoor', 480, 1240, 2460, 2535, { head: 2.1 }], ['part', 1240, 1315, 0, 2535], ['jamb', 1240, 1315, -250, 0, { sill: .9, head: 2.3 }],
      ['part', 1315, 2605, 2460, 2535], ['part', 2530, 2605, 0, 1170], ['pdoor', 2530, 2605, 1170, 1975, { head: 2.1 }], ['part', 2530, 2605, 1975, 2460],
      ...MASTER_BC_PARTS_A, ...BAY_PARTS_A
    ],
    leaves: [[5700, 5740, 2600, 3300, 0, 2.05, 'white'], BAY_LEAF_A],
    rooms: [
      MASTER_A,
      { id: 'bed3', name: 'Small bedroom 1', rects: [[0, 1240, 0, 2460]], at: [620, 1300], win: 'North, hillside', only: ['north'], role: 'bed3' },
      { id: 'bed4', name: 'Small bedroom 2', rects: [[1315, 2530, 0, 2460]], at: [1920, 1300], win: 'North, hillside', only: ['north'], role: 'bed4' },
      BAYBED_A,
      { id: 'living', name: 'Living & dining', rects: [[2605, 3440, 0, 2600], [3440, 5080, 0, 2440], [5080, 7965, 0, 2525], [0, 2605, 2535, 2600]], at: [5400, 1250], win: 'East, sea', sea: true, only: ['eastN'], role: 'living' },
      KITCHEN_ROOM, BATH_ROOM, FOYER_ROOM
    ],
    furn: A_C_FURN, chairs: [[3550, 900, 'W'], [3550, 1450, 'W'], [3550, 2000, 'W'], [4850, 900, 'E'], [4850, 1450, 'E'], [4850, 2000, 'E']], pend: [4200, 1450], plant: [5300, 300],
    stops: ['door', 'hall', 'kitchen', 'bath', 'dining', 'living', 'window', 'master', 'bed3', 'bed4', 'bay', 'doll'],
    over: {
      hall: { text: 'The hall at the end of the foyer. The kitchen door is on your right and the bathroom is straight ahead. The two small bedrooms open off the left, one with a sliding door onto the hall.' },
      bed3: { name: 'Small bedroom 1', sub: '1.25 × 2.45 m', X: 860, Y: 2950, yaw: 0, pitch: -20,
        text: 'A small room about 1.25 × 2.45 m, filled by a 4′ bed, with low storage under its part of the north window. A sliding door opens onto the hall.' }
    },
    wins: [...BC_WINS_A, ['Small bedroom 1', 'north', 620, 1375, ['north'], 'bed3'], ['Small bedroom 2', 'north', 1920, 1375, ['north'], 'bed4'], KITCHEN_ROW]
  },
'''
# replace from the layouts header to (not incl.) LAYOUTS_A's bare entry
i = s.index('// ---------------- layouts ----------------')
j = s.index('\n  bare: {', s.index('const LAYOUTS_A = {'))
s = s[:i] + LAYOUTS_A_JS + s[j + 1:]

# A bare: new stop ids
i = s.index('const LAYOUTS_A = {'); i = s.index('  bare: {', i)
j = s.index('\n};', i)
bare = s[i:j]
bare = bare.replace("stops: ['door', 'hall', 'kitchen', 'bath', 'dining', 'living', 'window', 'kids', 'master', 'helper', 'doll'],",
                    "stops: ['door', 'hall', 'kitchen', 'bath', 'dining', 'living', 'window', 'master', 'bed3', 'bay', 'doll'],")
bare = re.sub(r"      kids: \{ name: 'South-east corner'[^\n]*\n",
              "      master: { name: 'South-east corner', sub: '2.9 × 2.0 m', text: 'The south half of the east window. All three plans make this the master bedroom.' },\n", bare)
bare = re.sub(r"      master: \{ name: 'North-west corner'[^\n]*\n",
              "      bed3: { name: 'North-west corner', sub: '2.45 × 2.5 m', text: 'The north window corner. Plan A keeps it in the living room; plan B makes it a bedroom and plan C two small ones.' },\n", bare)
bare = bare.replace("      helper: { name: 'The bay'", "      bay: { name: 'The bay'")
s = s[:i] + bare + s[j:]

# A stops
STOPDEF_A = '''const STOPDEF_A = {
  door: { name: 'Front door', sub: 'Foyer', X: 700, Y: 5330, yaw: 18, pitch: -6,
    text: 'Inside the front door. A 1.6 m-wide foyer runs ahead, with the shoe cabinet on the left and the kitchen wall on the right. At the end it turns right into a short hall.' },
  hall: { name: 'Hall', sub: 'Kitchen, bath, living', X: 1050, Y: 3250, yaw: 90, pitch: -8,
    text: 'The hall at the end of the foyer. The kitchen door is on your right and the bathroom is straight ahead. The living and dining room opens on the left, and the north-west bedroom door is just round that corner.' },
  kitchen: { name: 'Kitchen', sub: '1.6 × 2.0 m', X: 2650, Y: 3980, yaw: 165, pitch: -22,
    text: 'Counter and sink along the east wall under the window, hob and washing machine on the south counter, fridge by the door. The kitchen window looks east down the gap between flats 2 and 3.' },
  bath: { name: 'Bathroom', sub: '1.5 × 2.0 m', X: 3680, Y: 2780, yaw: 140, pitch: -18,
    text: 'Shower on the right, toilet under a small south window, basin and mirror by the door.' },
  dining: { name: 'Dining', sub: 'Table for six', X: 3000, Y: 2950, yaw: 50, pitch: -8,
    text: 'The table for six sits between the bathroom and the bay, with the bay bedroom door straight ahead. Its end runs up to the bathroom wall, so the way through to the living room is round the bay end of the table.' },
  living: { name: 'Living room', sub: 'At the sea window', X: 5300, Y: 1350, yaw: 90, pitch: -6,
    text: 'The living room takes the north half of the east window and is about 2.9 × 2.5 m. The sofa sits against the north wall and the TV faces it from the master bedroom wall, with a rug between. The acoustic fin is just outside the window’s north edge.' },
  window: { name: 'Living-room window', sub: 'Best view', X: 7300, Y: 1300, yaw: 92, pitch: -7,
    text: 'Close to the glass. Silverstrand Bay sits beyond the ridge in front; Port Shelter opens to the left of it. The fin cuts off the view to the north-east.' },
  master: { name: 'Master bedroom', sub: '2.9 × 1.9 m', X: 5900, Y: 2900, yaw: 115, pitch: -14,
    text: 'A 4′6″ double bed with its head on the south wall, a full-width wardrobe along the bathroom wall, and the south half of the east window plus the small south window.' },
  bed3: { name: 'Corner bedroom', sub: '1.95 × 2.35 m', X: 1600, Y: 1800, yaw: 320, pitch: -12,
    text: 'A 4′ bed along the north wall under the north window, with a wardrobe at the far end. The window looks onto the wooded hillside: no sea, but it is the quietest room.' },
  bed4: { name: 'Small bedroom 2', sub: '1.2 × 2.45 m', X: 2850, Y: 1550, yaw: 270, pitch: -16,
    text: 'The second small room: a 4′ bed under the rest of the north window and a wardrobe at its foot, with a sliding door onto the dining area.' },
  bay: { name: 'Bay bedroom', sub: '2.15 × 2.1 m', X: 4250, Y: -550, yaw: 330, pitch: -14,
    text: 'The bay becomes a bedroom about 2.15 × 2.1 m: a 4′ bed with its head on the end wall, a wardrobe beside the door, and the bay window at the foot of the bed.' },
  doll: { name: 'Dollhouse', sub: 'Whole flat from above', doll: true,
    text: 'The whole flat with the walls cut at chest height. Drag to turn it; tap a room to step inside.' }
};'''
sub('const STOPDEF_A = {', '\n};', STOPDEF_A)

# Block A texts: flat 2 wording, its flat 3 mirror, and both translations
mir('Three bedrooms. Two of them share the big east window, split at its middle post with a wardrobe wall between them, and the bay becomes the third. The living room stays by the hall, with the TV on the west wall and only the north window, so it has no sea view.',
    'Three bedrooms. Two of them share the big east window, split at its middle post with a wardrobe wall between them, and the bay becomes the third. The living room stays by the hall, with the TV on the west wall and only the south window, so it has no sea view.',
    '三房：兩間睡房分享大東窗，在窗的中間直料處以一幅衣櫃牆分隔，凸位就成為第三間睡房。客廳留在走廊旁，電視靠西牆，只有北窗，看不到海。',
    '三房：兩間睡房分享大東窗，在窗的中間直料處以一幅衣櫃牆分隔，凸位就成為第三間睡房。客廳留在走廊旁，電視靠西牆，只有南窗，看不到海。')
mir('Three bedrooms. The living room takes the north half of the east window, with the sofa against the north wall and the TV on the master bedroom wall. A bedroom goes in the north-west corner under the north window, and the bay is the third bedroom.',
    'Three bedrooms. The living room takes the south half of the east window, with the sofa against the south wall and the TV on the master bedroom wall. A bedroom goes in the south-west corner under the south window, and the bay is the third bedroom.',
    '三房。客廳取得東窗北半，梳化靠北牆，電視掛在主人房的牆上。西北角間出一間睡房，有北窗，凸位就是第三間睡房。',
    '三房。客廳取得東窗南半，梳化靠南牆，電視掛在主人房的牆上。西南角間出一間睡房，有南窗，凸位就是第三間睡房。')
mir('Four bedrooms. As in plan B, but the north-west corner becomes two small bedrooms, each just big enough for a 4′ bed, sharing the north window: the wall between them needs a new frame post where it meets the glass. Both have sliding doors.',
    'Four bedrooms. As in plan B, but the south-west corner becomes two small bedrooms, each just big enough for a 4′ bed, sharing the south window: the wall between them needs a new frame post where it meets the glass. Both have sliding doors.',
    '四房。與方案B相同，但西北角再分成兩間細睡房，每間剛好放得下一張4呎床，共用北窗：兩房之間的間牆碰到玻璃的位置要加一條新窗框直料。兩間都用趟門。',
    '四房。與方案B相同，但西南角再分成兩間細睡房，每間剛好放得下一張4呎床，共用南窗：兩房之間的間牆碰到玻璃的位置要加一條新窗框直料。兩間都用趟門。')
mir('The hall at the end of the foyer. The kitchen door is on your right and the bathroom is straight ahead. The living room opens on the left, with the TV on the west wall.',
    'The hall at the end of the foyer. The kitchen door is on your left and the bathroom is straight ahead. The living room opens on the right, with the TV on the west wall.',
    '玄關盡頭的走廊。廚房門在你右邊，浴室在正前方。左邊是客廳，電視靠西牆。',
    '玄關盡頭的走廊。廚房門在你左邊，浴室在正前方。右邊是客廳，電視靠西牆。')
zh('The table for six sits between the bathroom and the bay, with the bay bedroom door straight ahead. The two sea-view bedrooms open off the far end, by the east window.',
   '六人餐桌放在浴室與凸位之間，凸位睡房的門在正前方。兩間海景睡房在盡頭東窗旁。')
zh('The table for six sits between the bathroom and the bay, with the bay bedroom door straight ahead. Its end runs up to the bathroom wall, so the way through to the living room is round the bay end of the table.',
   '六人餐桌放在浴室與凸位之間，凸位睡房的門在正前方。桌尾貼著浴室牆，所以要從近凸位那一端繞過餐桌才到客廳。')
mir('Behind the sofa, facing the TV on the west wall. The living room keeps the north window, which looks onto the hillside; in this plan the sea window belongs to the bedrooms.',
    'Behind the sofa, facing the TV on the west wall. The living room keeps the south window, which faces Block B across the podium; in this plan the sea window belongs to the bedrooms.',
    '站在梳化後面，面向西牆上的電視。客廳保留北窗，窗外是山坡；這個方案的海景窗歸睡房所有。',
    '站在梳化後面，面向西牆上的電視。客廳保留南窗，隔著平台望向B座；這個方案的海景窗歸睡房所有。')
mir('A 4′6″ double bed with its head on the south wall, a tall wardrobe against the bathroom wall, and the south half of the east window plus the small south window. The new wall meets the window at its middle post.',
    'A 4′6″ double bed with its head on the north wall, a tall wardrobe against the bathroom wall, and the north half of the east window plus the small north window. The new wall meets the window at its middle post.',
    '4呎6雙人床床頭靠南牆，浴室牆前放高衣櫃，房間取得東窗南半和細南窗。新間牆在窗的中間直料處與窗相接。',
    '4呎6雙人床床頭靠北牆，浴室牆前放高衣櫃，房間取得東窗北半和細北窗。新間牆在窗的中間直料處與窗相接。')
mir('A 4′ bed with its head on the north wall, a desk by the door and a wall of wardrobe shared with the master bedroom. It gets the north half of the east window. The acoustic fin is just outside.',
    'A 4′ bed with its head on the south wall, a desk by the door and a wall of wardrobe shared with the master bedroom. It gets the south half of the east window. The acoustic fin is just outside.',
    '4呎床床頭靠北牆，門邊放書桌，與主人房之間是一整幅衣櫃牆。房間取得東窗北半。窗外就是隔音鰭。',
    '4呎床床頭靠南牆，門邊放書桌，與主人房之間是一整幅衣櫃牆。房間取得東窗南半。窗外就是隔音鰭。')
mir('The living room takes the north half of the east window and is about 2.9 × 2.5 m. The sofa sits against the north wall and the TV faces it from the master bedroom wall, with a rug between. The acoustic fin is just outside the window’s north edge.',
    'The living room takes the south half of the east window and is about 2.9 × 2.5 m. The sofa sits against the south wall and the TV faces it from the master bedroom wall, with a rug between. The acoustic fin is just outside the window’s south edge.',
    '客廳取得東窗北半，約2.9 × 2.5米。梳化靠北牆，電視掛在主人房的牆上與梳化相對，中間鋪地氈。隔音鰭就在窗的北邊外面。',
    '客廳取得東窗南半，約2.9 × 2.5米。梳化靠南牆，電視掛在主人房的牆上與梳化相對，中間鋪地氈。隔音鰭就在窗的南邊外面。')
mir('A 4′6″ double bed with its head on the south wall, a full-width wardrobe along the bathroom wall, and the south half of the east window plus the small south window.',
    'A 4′6″ double bed with its head on the north wall, a full-width wardrobe along the bathroom wall, and the north half of the east window plus the small north window.',
    '4呎6雙人床床頭靠南牆，沿浴室牆放一整排衣櫃，房間取得東窗南半和細南窗。',
    '4呎6雙人床床頭靠北牆，沿浴室牆放一整排衣櫃，房間取得東窗北半和細北窗。')
mir('A 4′ bed along the north wall under the north window, with a wardrobe at the far end. The window looks onto the wooded hillside: no sea, but it is the quietest room.',
    'A 4′ bed along the south wall under the south window, with a wardrobe at the far end. The window faces south over the podium towards Block B rather than the hillside.',
    '4呎床沿北牆放在北窗下，盡頭有衣櫃。窗外是樹木茂密的山坡：看不到海，但最寧靜。',
    '4呎床沿南牆放在南窗下，盡頭有衣櫃。窗口向南，望向平台和B座，而不是山坡。')
mir('The hall at the end of the foyer. The kitchen door is on your right and the bathroom is straight ahead. The two small bedrooms open off the left, one with a sliding door onto the hall.',
    'The hall at the end of the foyer. The kitchen door is on your left and the bathroom is straight ahead. The two small bedrooms open off the right, one with a sliding door onto the hall.',
    '玄關盡頭的走廊。廚房門在你右邊，浴室在正前方。左邊是兩間細睡房，其中一間的趟門開向走廊。',
    '玄關盡頭的走廊。廚房門在你左邊，浴室在正前方。右邊是兩間細睡房，其中一間的趟門開向走廊。')
mir('A small room about 1.25 × 2.45 m, filled by a 4′ bed, with low storage under its part of the north window. A sliding door opens onto the hall.',
    'A small room about 1.25 × 2.45 m, filled by a 4′ bed, with low storage under its part of the south window. A sliding door opens onto the hall.',
    '一間約1.25 × 2.45米的小房，一張4呎床已經放滿，分到的一段北窗下有矮儲物櫃。趟門開向走廊。',
    '一間約1.25 × 2.45米的小房，一張4呎床已經放滿，分到的一段南窗下有矮儲物櫃。趟門開向走廊。')
mir('The second small room: a 4′ bed under the rest of the north window and a wardrobe at its foot, with a sliding door onto the dining area.',
    'The second small room: a 4′ bed under the rest of the south window and a wardrobe at its foot, with a sliding door onto the dining area.',
    '第二間小房：4呎床放在北窗餘下一段之下，床尾有衣櫃，趟門開向飯廳。',
    '第二間小房：4呎床放在南窗餘下一段之下，床尾有衣櫃，趟門開向飯廳。')
zh('The bay becomes a bedroom about 2.15 × 2.1 m: a 4′ bed with its head on the end wall, a wardrobe beside the door, and the bay window at the foot of the bed.',
   '凸位變成一間約2.15 × 2.1米的睡房：4呎床床頭靠盡頭的牆，門旁有衣櫃，凸位窗就在床尾。')
mir('The south half of the east window. All three plans make this the master bedroom.',
    'The north half of the east window. All three plans make this the master bedroom.',
    '東窗的南半。三個方案都把這裡做主人房。', '東窗的北半。三個方案都把這裡做主人房。')
mir('The north window corner. Plan A keeps it in the living room; plan B makes it a bedroom and plan C two small ones.',
    'The south window corner. Plan A keeps it in the living room; plan B makes it a bedroom and plan C two small ones.',
    '北窗所在的角落。方案A把這裡留作客廳；方案B間成一間睡房，方案C間成兩間細房。',
    '南窗所在的角落。方案A把這裡留作客廳；方案B間成一間睡房，方案C間成兩間細房。')

# ================================================================ types, chairs, comparison, short labels
s = s.replace("layouts: LAYOUTS_A, keys: ['A', 'B', 'C', 'bare'], def: 'B',", "layouts: LAYOUTS_A, keys: ['A', 'B', 'C', 'bare'], def: 'A',")
s = s.replace("layouts: LAYOUTS_B, keys: ['open', 'bare'], def: 'open',", "layouts: LAYOUTS_B, keys: ['A', 'B', 'C', 'bare'], def: 'A',")
# the kitchen door swings into the kitchen, so it no longer clashes with plan A's fridge outside
s = s.replace("[1850, 2600, 3720, 3765, 0, 2.05, 'white'], [3510, 3550, 2525, 3275, 0, 2.05, 'white']] }",
              "[2600, 2640, 3850, 4600, 0, 2.05, 'white'], [3510, 3550, 2525, 3275, 0, 2.05, 'white']] }")

old_ch = '''      const by = side === 'N' ? [cy - 210, cy - 170] : [cy + 170, cy + 210];
      box(g, cx - 210, cx + 210, by[0], by[1], .48, .88, M.charcoal);'''
new_ch = '''      // the side is where the back is: N/S backs run along X, W/E backs along Y
      if (side === 'N' || side === 'S') { const by = side === 'N' ? [cy - 210, cy - 170] : [cy + 170, cy + 210]; box(g, cx - 210, cx + 210, by[0], by[1], .48, .88, M.charcoal); }
      else { const bx = side === 'W' ? [cx - 210, cx - 170] : [cx + 170, cx + 210]; box(g, bx[0], bx[1], cy - 210, cy + 210, .48, .88, M.charcoal); }'''
assert old_ch in s; s = s.replace(old_ch, new_ch)

i = s.index('function compareTable() {'); j = s.index('\n}\n', i) + 3
s = s[:i] + '''const BED_ROLES = ['master', 'bay', 'bed3', 'bed4'];
function compareTable() {
  const keys = ['A', 'B', 'C'];
  $('cmpCard').hidden = !keys.every(k => LAYOUTS[k]);
  if ($('cmpCard').hidden) return;
  const on = k => k === st.layout ? 'on' : '';
  const cell = (k, role) => {
    const rs = LAYOUTS[k].rooms.filter(r => r.role === role);
    if (!rs.length) return `<td class="${on(k)}">–</td>`;
    const area = rs.reduce((t, r) => t + rectArea(r), 0), r = winRows(k).find(w => w.role === role);
    const view = !r || r.deg == null ? T('no window', '沒有窗') : r.deg ? T(`${r.deg}° sea`, `海景 ${r.deg}°`)
      : r.north ? (FLAT.mirror ? T('south side', '向南') : T('hillside', '山景')) : T('window, no sea', '有窗，沒有海景');
    return `<td class="${on(k)}"><b>${area.toFixed(1)}${T(' m²', '平方米')}</b><br>${view}</td>`;
  };
  const head = `<tr><th></th>${keys.map(k => `<th class="${on(k)}">${tr(LAYOUTS[k].name)}</th>`).join('')}</tr>`;
  const count = `<tr><td>${tr('Bedrooms')}</td>${keys.map(k => `<td class="${on(k)}"><b>${LAYOUTS[k].rooms.filter(r => BED_ROLES.includes(r.role)).length}</b></td>`).join('')}</tr>`;
  const rows = [['Master bedroom', 'master'], ['Bay bedroom', 'bay'], ['Third bedroom', 'bed3'], ['Fourth bedroom', 'bed4'], ['Living & dining', 'living']]
    .map(([n, role]) => `<tr><td>${tr(n)}</td>${keys.map(k => cell(k, role)).join('')}</tr>`);
  $('cmp').innerHTML = head + count + rows.join('');
}
''' + s[j:]

s = re.sub(r"const SHORT = \{[^\n]*\};",
           "const SHORT = { 'Living & dining': 'Living', 'Master bedroom': 'Master', 'Bay bedroom': 'Bay', 'Sea-view bedroom': 'Bed 3', "
           "'Corner bedroom': 'Bed 3', 'Small bedroom 1': 'Bed 3', 'Small bedroom 2': 'Bed 4', 'Open-plan living': 'Open plan' };", s)

# ================================================================ dictionaries
def upd(name, add):
    global s
    m = re.search(r'const ' + name + r' = (\{.*?\});\n', s)
    d = json.loads(m.group(1)); d.update(add)
    s = s[:m.start(1)] + json.dumps(d, ensure_ascii=False) + s[m.end(1):]


upd('ZH', ZH)
upd('MIRROR_A', MIR)
open(SRC, 'w', encoding='utf-8').write(s)
print('patched:', len(ZH), 'translations,', len(MIR), 'mirror strings')
