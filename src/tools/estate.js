  // ---------------- Ying Fai Court itself: towers, lobbies, podium deck, lifts and refuse rooms ----------------
  // Tower outlines are traced from the HA typical floor plans (Block A 3/F-39/F, Block B 4/F-38/F) and placed so that
  // flats 2/3 and 9/10 sit where the view pages put them. Lift cores and the refuse rooms (RS & MRR) are read off the same
  // plans; the deck's planters, trellises and play areas come from the layout plan in the HA sales booklet. Levels below
  // 2/F are estimates: the podium deck (1/F, garden and lift lobbies) is taken at +52 mPD.
  const EST = %%EST%%;
  const LEVEL2 = 57.55, STOREY = 2.75, DECK = 52;
  const floorZ = F => LEVEL2 + (F - 2) * STOREY;
  const BLOCKS = {
    A: { foot: EST.A, low: 2, high: 39, lobbyTop: floorZ(2), roof: floorZ(39) + 2.79, label: [-26, 2],
      lobby: [-27.75, -3.5], lift: [[-27.9, .25], [-25.9, -1.7], [-23.8, -3.65], [-31.6, -3.25], [-29.6, -5.35], [-27.5, -7.25]], rs: [-26.2, 8.05] },
    B: { foot: EST.B, low: 3, high: 38, lobbyTop: floorZ(3), roof: floorZ(38) + 2.75, label: [-42, -76],
      lobby: [-43.15, -75.8], lift: [[-45.8, -76.05], [-44.9, -74.9], [-43.9, -73.9], [-42.4, -77.6], [-41.4, -76.75], [-40.5, -75.8]], rs: [-54.5, -76.4] }
  };
  // the four flats these pages cover: the part of the floor plate each one takes (a box, world metres), its front door
  // and, for flats 2 and 3, the acoustic fin (top floor it reaches)
  const FLATKEY = {
    A2: { block: 'A', no: 2, box: [-8.45, 3, -1.5, 14], door: [-7.07, -.34], fin: [0, 1.5, 5.3375, 5.5875, 39] },
    A3: { block: 'A', no: 3, box: [-8.45, 3, -16, -1.5], door: [-7.07, -2.66], fin: [0, 1.5, -8.5875, -8.3375, 25] },
    B9: { block: 'B', no: 9, box: [-31.5, -20, -79.55, -66], door: [-29.74, -77.96] },
    B10: { block: 'B', no: 10, box: [-31.5, -20, -94, -79.55], door: [-29.74, -81.14] }
  };
  const inBox = (b, x, y) => x > b[0] && x < b[1] && y > b[2] && y < b[3];
  // Sutherland-Hodgman: clip a polygon to the half-plane where f(x, y) >= 0 (f linear)
  function clipHalf(poly, f) {
    const out = [];
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i], b = poly[(i + 1) % poly.length], fa = f(a[0], a[1]), fb = f(b[0], b[1]);
      if (fa >= 0) out.push(a);
      if ((fa >= 0) !== (fb >= 0)) { const t = fa / (fa - fb); out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]); }
    }
    return out;
  }
  function polyInBox(poly, b) {
    let p = clipHalf(poly, (x, y) => x - b[0]); p = clipHalf(p, (x, y) => b[1] - x);
    p = clipHalf(p, (x, y) => y - b[2]); return clipHalf(p, (x, y) => b[3] - y);
  }
  // the floor plate without one flat's box: west of it, east of it, and north and south of it within its x range
  function polyMinusBox(poly, b) {
    const parts = [clipHalf(poly, (x, y) => b[0] - x), clipHalf(poly, (x, y) => x - b[1])];
    let mid = clipHalf(clipHalf(poly, (x, y) => x - b[0]), (x, y) => b[1] - x);
    parts.push(clipHalf(mid, (x, y) => b[2] - y), clipHalf(mid, (x, y) => y - b[3]));
    return parts.filter(p => p.length >= 3);
  }
  function triangulate(pts) {
    const tris = THREE_.ShapeUtils.triangulateShape(pts.map(([x, y]) => new THREE_.Vector2(x, y)), []), out = [];
    for (const [i, j, k] of tris) {
      const [ax, ay] = pts[i], [bx, by] = pts[j], [qx, qy] = pts[k];
      if ((bx - ax) * (qy - ay) - (qx - ax) * (by - ay) >= 0) out.push(i, j, k); else out.push(i, k, j);
    }
    return out;
  }
  let THREE_ = null;
  function canvasTex(w, h, paint) {
    const c = document.createElement('canvas'); c.width = w; c.height = h; paint(c.getContext('2d'), w, h);
    const t = new THREE_.CanvasTexture(c); t.wrapS = t.wrapT = THREE_.RepeatWrapping; t.anisotropy = 4; return t;
  }
  // o.clip: clipping planes for every material (the tour's dollhouse); o.fins: draw the acoustic fins of flats 2 and 3
  function makeEstate(THREE, P, o) {
    THREE_ = THREE; o = o || {};
    const clip = o.clip ? { clippingPlanes: o.clip } : {};
    const lam = (extra) => new THREE.MeshLambertMaterial(Object.assign({}, clip, extra));
    // one bay of facade, 3 m wide and one storey (2.75 m) high: cream wall, a tall window with a mullion and transom,
    // and a thin slab band; the walls of the narrow recesses between flats are a darker taupe, as on the HA's model
    const facadeTex = canvasTex(128, 128, (g, w, h) => {
      g.fillStyle = '#eee7d8'; g.fillRect(0, 0, w, h);
      const gr = g.createLinearGradient(0, 14, 0, 92); gr.addColorStop(0, '#9fb3bd'); gr.addColorStop(.55, '#7d95a3'); gr.addColorStop(1, '#647d8b');
      g.fillStyle = gr; g.fillRect(20, 14, 88, 76);
      g.fillStyle = '#e4e1da'; g.fillRect(62, 14, 4, 76); g.fillRect(20, 40, 88, 3);
      g.fillStyle = '#d8d0bf'; g.fillRect(20, 90, 88, 5);
      g.fillStyle = '#e2dac9'; g.fillRect(0, 118, w, 10);
    });
    const lobbyTex = canvasTex(128, 128, (g, w, h) => {
      const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#c8d3d7'); gr.addColorStop(1, '#9fb0b7');
      g.fillStyle = gr; g.fillRect(0, 0, w, h);
      g.fillStyle = '#f3f0e9'; for (let u = 0; u < w; u += 32) g.fillRect(u, 0, 5, h);
      g.fillStyle = '#7c817f'; g.fillRect(0, 0, w, 14);
      g.fillStyle = '#e9e4d8'; g.fillRect(0, h - 10, w, 10);
    });
    const podiumTex = canvasTex(128, 128, (g, w, h) => {
      g.fillStyle = '#e1dacb'; g.fillRect(0, 0, w, h);
      g.fillStyle = '#727c80'; g.fillRect(8, 40, 112, 34);
      g.fillStyle = '#d2c9b6'; g.fillRect(0, 0, w, 8); g.fillRect(0, 100, w, 4);
      g.fillStyle = '#c9c0ad'; for (let u = 0; u < w; u += 64) g.fillRect(u, 0, 3, h);
    });
    const M = {
      facade: lam({ map: facadeTex }), recess: lam({ color: 0x9c8f79 }), lobby: lam({ map: lobbyTex }),
      roof: lam({ color: 0xcbc3b2 }), crown: lam({ color: 0xa39580 }), crownDark: lam({ color: 0x8c7f6b }),
      podium: lam({ map: podiumTex }), deck: lam({ color: 0xd8d1c2 }), green: lam({ color: 0x7c9d5e }),
      tree: lam({ color: 0x5d8849 }), wood: lam({ color: 0xa9825e }), play: lam({ color: 0x9fc3d6 }), fin: lam({ color: 0xd5cdbf }),
      drum: lam({ color: 0xd9dfe0 })
    };
    const group = new THREE.Group(), blocks = { A: new THREE.Group(), B: new THREE.Group() }, base = new THREE.Group(), fins = new THREE.Group();
    group.add(blocks.A, blocks.B, base, fins);
    const towerWalls = { A: new THREE.Group(), B: new THREE.Group() };
    blocks.A.add(towerWalls.A); blocks.B.add(towerWalls.B);

    // geometry helpers: wall quads along a polyline, with u running along the wall and v up the storeys
    function Geo() { return { pos: [], nor: [], uv: [], idx: [] }; }
    function quad(G, x1, y1, x2, y2, z0, z1, u0, u1, v0, v1) {
      const l = Math.hypot(x2 - x1, y2 - y1) || 1, nx = (y2 - y1) / l, ny = -(x2 - x1) / l, b = G.pos.length / 3;
      for (const [x, y, z, u, v] of [[x1, y1, z0, u0, v0], [x2, y2, z0, u1, v0], [x2, y2, z1, u1, v1], [x1, y1, z1, u0, v1]]) {
        const p = P(x, y, z); G.pos.push(p.x, p.y, p.z); G.nor.push(nx, 0, -ny); G.uv.push(u, v);
      }
      G.idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
    }
    function flat(G, pts, z) {
      const b = G.pos.length / 3;
      for (const [x, y] of pts) { const p = P(x, y, z); G.pos.push(p.x, p.y, p.z); G.nor.push(0, 1, 0); G.uv.push(x / 4, y / 4); }
      for (const i of triangulate(pts)) G.idx.push(b + i);
    }
    function mesh(G, m) {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(G.pos, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(G.nor, 3));
      g.setAttribute('uv', new THREE.Float32BufferAttribute(G.uv, 2)); g.setIndex(G.idx);
      return new THREE.Mesh(g, m);
    }
    function boxAt(parent, x, y, z0, sx, sy, sz, m, rot) {
      const b = new THREE.Mesh(new THREE.BoxGeometry(sx, sz, sy), m); b.position.copy(P(x, y, z0 + sz / 2)); b.rotation.y = rot || 0; parent.add(b); return b;
    }
    const clear = g => { while (g.children.length) { const c = g.children.pop(); c.traverse(n => n.geometry && n.geometry.dispose()); } };

    // tower walls, rebuilt when the tour moves to another floor: below and above the cut floor every wall is drawn;
    // on the cut floor itself the walls inside the flat's box are left out so the flat's own walls and windows show
    function buildTower(k, cut) {
      const B = BLOCKS[k], foot = B.foot, top = B.roof + 1.2, Gf = Geo(), Gr = Geo();
      const bands = cut && cut.block === k ? [[B.lobbyTop, cut.lo, null], [cut.lo, cut.hi, cut.box], [cut.hi, top, null]] : [[B.lobbyTop, top, null]];
      for (let i = 0; i < foot.length; i++) {
        const [x1, y1] = foot[i], [x2, y2] = foot[(i + 1) % foot.length], l = Math.hypot(x2 - x1, y2 - y1);
        const recess = l < 1.6, n = Math.max(1, Math.round(l / 3)), mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
        for (const [z0, z1, skip] of bands) {
          if (z1 <= z0 || (skip && inBox(skip, mx, my))) continue;
          if (recess) quad(Gr, x1, y1, x2, y2, z0, z1, 0, 1, 0, 1);
          else quad(Gf, x1, y1, x2, y2, z0, z1, 0, n, (z0 - LEVEL2) / STOREY, (z1 - LEVEL2) / STOREY);
        }
      }
      const g = towerWalls[k]; clear(g);
      g.add(mesh(Gf, M.facade), mesh(Gr, M.recess));
    }
    // roofs, crowns (lift machine room and water tanks, as on the model) and the lobby storeys
    for (const k of ['A', 'B']) {
      const B = BLOCKS[k], G = Geo(), Gl = Geo();
      flat(G, B.foot, B.roof);
      blocks[k].add(mesh(G, M.roof));
      for (let i = 0; i < B.foot.length; i++) {
        const [x1, y1] = B.foot[i], [x2, y2] = B.foot[(i + 1) % B.foot.length], l = Math.hypot(x2 - x1, y2 - y1);
        quad(Gl, x1, y1, x2, y2, DECK - .2, B.lobbyTop, 0, Math.max(1, Math.round(l / 1.5)) / 4, 0, 1);
      }
      blocks[k].add(mesh(Gl, M.lobby));
      const [lx, ly] = B.lobby, rot = k === 'A' ? -Math.PI / 4 : Math.PI / 4;
      boxAt(blocks[k], lx, ly, B.roof, 15, 9, 7.5, M.crown, rot);
      boxAt(blocks[k], lx, ly, B.roof + 7.5, 10, 6, 2.5, M.crownDark, rot);
      boxAt(blocks[k], B.rs[0], B.rs[1] - (k === 'A' ? 3 : 0), B.roof, 7, 5, 4.5, M.crown);
    }
    buildTower('A', null); buildTower('B', null);
    // Block A's round entrance drum at the foot of the north-east corner, as on the model
    { const d = new THREE.Mesh(new THREE.CylinderGeometry(4.2, 4.2, BLOCKS.A.lobbyTop - DECK, 32), M.drum); d.position.copy(P(-11.3, 12.6, (DECK + BLOCKS.A.lobbyTop) / 2)); blocks.A.add(d);
      const c = new THREE.Mesh(new THREE.CylinderGeometry(4.6, 4.6, .4, 32), M.crownDark); c.position.copy(P(-11.3, 12.6, BLOCKS.A.lobbyTop)); blocks.A.add(c); }
    // acoustic fins beside flats 2 (2/F-39/F) and 3 (2/F-25/F)
    if (o.fins) for (const f of ['A2', 'A3']) { const [x0, x1, y0, y1, F1] = FLATKEY[f].fin; boxAt(fins, (x0 + x1) / 2, (y0 + y1) / 2, LEVEL2, x1 - x0, y1 - y0, floorZ(F1 + 1) - LEVEL2, M.fin); }

    // podium: the site, walled down to below the ground, with the 1/F deck on top
    {
      const S = SITE.pts.slice(); let a = 0; for (let i = 0; i < S.length; i++) { const p = S[i], q = S[(i + 1) % S.length]; a += p[0] * q[1] - q[0] * p[1]; }
      if (a < 0) S.reverse();
      const Gw = Geo(), Gd = Geo();
      for (let i = 0; i < S.length; i++) {
        const [x1, y1] = S[i], [x2, y2] = S[(i + 1) % S.length], l = Math.hypot(x2 - x1, y2 - y1);
        quad(Gw, x1, y1, x2, y2, 24, DECK, 0, l / 8, (24 - DECK) / 5.5, 0);
      }
      flat(Gd, S, DECK);
      base.add(mesh(Gw, M.podium), mesh(Gd, M.deck));
      // planters with a tree, the round planter in the courtyard, two trellises, the play areas and the covered
      // escalator and lift lobby up from Ying Yip Road
      const tree = (x, y, r) => { const s = new THREE.Mesh(new THREE.SphereGeometry(r, 10, 8), M.tree); s.position.copy(P(x, y, DECK + .9 + r * .9)); s.scale.set(1, .85, 1); base.add(s); };
      for (const [x, y] of EST.trees) { boxAt(base, x, y, DECK, 4, 4, .9, M.green); tree(x, y, 2.1); }
      const F = EST.feat;
      { const c = new THREE.Mesh(new THREE.CylinderGeometry(5, 5, .9, 28), M.green); c.position.copy(P(F.circle[0], F.circle[1], DECK + .45)); base.add(c); tree(F.circle[0], F.circle[1], 2.8); }
      for (const t of [F.trellis1, F.trellis2]) {
        for (const [dx, dy] of [[-4, -1.4], [4, -1.4], [-4, 1.4], [4, 1.4]]) boxAt(base, t[0] + dx, t[1] + dy, DECK, .3, .3, 3, M.wood);
        for (let s = -4; s <= 4; s += 1) boxAt(base, t[0] + s, t[1], DECK + 3, .18, 3.4, .25, M.wood);
      }
      for (const p of [F.play1, F.play2]) boxAt(base, p[0], p[1], DECK, 14, 7, .08, M.play, .05);
      boxAt(base, F.pavilion[0], F.pavilion[1], DECK, 8, 6, 4.5, M.lobby); boxAt(base, F.pavilion[0], F.pavilion[1], DECK + 4.5, 9, 7, .5, M.green);
    }

    // the dollhouse cut through one block at one floor: the floor plate under the corridors, a solid cap over the rest of
    // the floor with the lift banks, lift lobby and refuse room marked on it, and a plain cap on the other block
    const capMat = new THREE.MeshBasicMaterial({ color: 0xa8a397 }), plateMat = new THREE.MeshLambertMaterial({ color: 0xcfc9bd });
    const liftMat = new THREE.MeshBasicMaterial({ color: 0x2a363d }), lobbyMat = new THREE.MeshBasicMaterial({ color: 0xe3ddd0 }), rsMat = new THREE.MeshBasicMaterial({ color: 0xd9a441 });
    function capGroup(flatId, fl, cutZ) {
      const g = new THREE.Group(), K = FLATKEY[flatId], B = BLOCKS[K.block];
      const plate = Geo(); flat(plate, B.foot, fl - .16); g.add(mesh(plate, plateMat));
      const cap = Geo(); for (const part of polyMinusBox(B.foot, K.box)) flat(cap, part, cutZ - .02); g.add(mesh(cap, capMat));
      const [lx, ly] = B.lobby, rot = K.block === 'A' ? -Math.PI / 4 : Math.PI / 4;
      boxAt(g, lx, ly, cutZ - .01, 10, 3.4, .03, lobbyMat, rot);
      for (const [x, y] of B.lift) boxAt(g, x, y, cutZ - .01, 2.2, 2.2, .05, liftMat, Math.PI / 4);
      boxAt(g, B.rs[0], B.rs[1], cutZ - .01, 3, 3, .05, rsMat);
      const other = BLOCKS[K.block === 'A' ? 'B' : 'A'];
      if (cutZ < other.roof) { const oc = Geo(); flat(oc, other.foot, cutZ - .02); g.add(mesh(oc, capMat)); }
      return g;
    }
    return {
      group, blocks, base, fins, M,
      cut(c) { buildTower('A', c && c.block === 'A' ? c : null); buildTower('B', c && c.block === 'B' ? c : null); },
      capGroup
    };
  }
  // the terrain under the podium is kept below the deck, so the deck is not buried in the old hillside
  function siteClamp(x, y, h) { return h > DECK - 1.5 && inPoly(SITE.pts, x, y) ? DECK - 1.5 : h; }
  function inPoly(P, x, y) {
    let c = false;
    for (let i = 0, j = P.length - 1; i < P.length; j = i++) {
      const [x1, y1] = P[j], [x2, y2] = P[i];
      if ((y1 > y) !== (y2 > y) && x < (x2 - x1) * (y - y1) / (y2 - y1) + x1) c = !c;
    }
    return c;
  }
  // tower outline segments for 2D sight lines: [x1, y1, x2, y2]; on the flat's own block the walls inside its box are left out
  function towerSegments(flatId) {
    const K = flatId ? FLATKEY[flatId] : null, out = [];
    for (const k of ['A', 'B']) {
      const f = BLOCKS[k].foot;
      for (let i = 0; i < f.length; i++) {
        const [x1, y1] = f[i], [x2, y2] = f[(i + 1) % f.length];
        if (K && K.block === k && inBox(K.box, (x1 + x2) / 2, (y1 + y2) / 2)) continue;
        out.push([x1, y1, x2, y2]);
      }
    }
    return out;
  }
  // a small plan of the whole floor: the tower outline, your flat, the lift banks, the lift lobby and the refuse room,
  // with straight-line distances from your front door
  function keyPlan(flatId, F) {
    const K = FLATKEY[flatId], B = BLOCKS[K.block], f = B.foot;
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9; for (const [x, y] of f) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
    const pad = 4, W = x1 - x0 + 2 * pad, H = y1 - y0 + 2 * pad + 6;
    const pts = p => p.map(([x, y]) => `${(x - x0 + pad).toFixed(2)},${(y1 - y + pad).toFixed(2)}`).join(' ');
    const X = x => (x - x0 + pad).toFixed(2), Y = y => (y1 - y + pad).toFixed(2);
    const sib = Object.keys(FLATKEY).find(k => k !== flatId && FLATKEY[k].block === K.block);
    const mine = polyInBox(f, K.box), theirs = polyInBox(f, FLATKEY[sib].box);
    const dL = Math.hypot(B.lobby[0] - K.door[0], B.lobby[1] - K.door[1]), dR = Math.hypot(B.rs[0] - K.door[0], B.rs[1] - K.door[1]);
    const rot = K.block === 'A' ? 45 : -45, [lx, ly] = B.lobby;
    let s = `<svg viewBox="0 0 ${W.toFixed(1)} ${H.toFixed(1)}" role="img" aria-label="${t('Floor plan of Block ' + K.block + ' with the lifts and refuse room', K.block + '座樓層平面圖，標示升降機及垃圾房')}">`;
    s += `<polygon class="kp-foot" points="${pts(f)}"/>`;
    s += `<polygon class="kp-sib" points="${pts(theirs)}"/><polygon class="kp-mine" points="${pts(mine)}"/>`;
    s += `<rect class="kp-lobby" x="${(+X(lx) - 5).toFixed(2)}" y="${(+Y(ly) - 1.7).toFixed(2)}" width="10" height="3.4" transform="rotate(${rot} ${X(lx)} ${Y(ly)})"/>`;
    for (const [x, y] of B.lift) s += `<rect class="kp-lift" x="${(+X(x) - 1.1).toFixed(2)}" y="${(+Y(y) - 1.1).toFixed(2)}" width="2.2" height="2.2" transform="rotate(45 ${X(x)} ${Y(y)})"/>`;
    s += `<rect class="kp-rs" x="${(+X(B.rs[0]) - 1.5).toFixed(2)}" y="${(+Y(B.rs[1]) - 1.5).toFixed(2)}" width="3" height="3"/>`;
    s += `<line class="kp-path" x1="${X(K.door[0])}" y1="${Y(K.door[1])}" x2="${X(lx)}" y2="${Y(ly)}"/><line class="kp-path" x1="${X(K.door[0])}" y1="${Y(K.door[1])}" x2="${X(B.rs[0])}" y2="${Y(B.rs[1])}"/>`;
    s += `<circle class="kp-door" cx="${X(K.door[0])}" cy="${Y(K.door[1])}" r=".9"/>`;
    const lab = (x, y, txt, cls, anchor) => `<text class="kp-t ${cls || ''}" x="${X(x)}" y="${Y(y)}" text-anchor="${anchor || 'middle'}">${txt}</text>`;
    const mc = mine.reduce((a, p) => [a[0] + p[0] / mine.length, a[1] + p[1] / mine.length], [0, 0]);
    s += lab(mc[0] + (K.block === 'A' ? 1 : 0), mc[1] - .8, t(`Flat ${K.no}`, `${K.no}室`), 'kp-tm');
    s += lab(lx, ly - (K.block === 'A' ? 6.3 : 5.5), t('Lifts', '升降機'));
    s += lab(B.rs[0] + (K.block === 'A' ? 0 : 0), B.rs[1] + 2.6, t('Refuse room', '垃圾房'));
    // north arrow and a 10 m bar
    const nx = W - 3, ny = 3;
    s += `<path class="kp-n" d="M${nx} ${ny} l-1.4 3.6 l2.8 0 z"/><text class="kp-t" x="${nx}" y="${ny + 6.4}" text-anchor="middle">${t('N', '北')}</text>`;
    s += `<line class="kp-bar" x1="${pad}" y1="${H - 2.5}" x2="${pad + 10}" y2="${H - 2.5}"/><text class="kp-t" x="${pad + 11}" y="${H - 1.8}">${t('10 m', '10米')}</text>`;
    s += '</svg>';
    const note = t(`About <b>${Math.round(dL)} m</b> from your front door to the lift lobby and <b>${Math.round(dR)} m</b> to the refuse room (RS &amp; MRR), in straight lines. Block ${K.block} has 6 lifts; 3 of them stop at each floor.`,
      `由大門到升降機大堂直線距離約 <b>${Math.round(dL)}米</b>，到垃圾及物料回收室約 <b>${Math.round(dR)}米</b>。${K.block}座共有6部升降機，每層有3部停。`);
    return { svg: s, note, lobby: dL, refuse: dR };
  }
