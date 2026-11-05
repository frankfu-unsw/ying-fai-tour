"""Trace a tower's outer footprint from a floor-plan image (walls black, flats tinted, dimensions red)."""
import sys, json
import cv2, numpy as np

def trace(path, roi, open_px, close_px, eps_px, out_png, min_area=3000, bridge_px=81, fill=()):
    im = cv2.imread(path)
    b, g, r = [im[:, :, i].astype(int) for i in range(3)]
    dark = np.maximum(np.maximum(r, g), b) < 110
    teal = (g > 160) & (b > 160) & (g - r > 25) & (r < 200)
    green = (g > 205) & (r > 180) & (g - r > 6) & (g - b > 6) & (r < 240)
    ink = (dark | teal | green).astype(np.uint8) * 255
    x0, y0, x1, y1 = roi
    m = np.zeros_like(ink); m[y0:y1, x0:x1] = ink[y0:y1, x0:x1]
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (open_px, open_px)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_px, close_px)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    keep = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= min_area]
    m = np.isin(lab, keep).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (bridge_px, bridge_px)))
    for poly in fill:
        cv2.fillPoly(m, [np.array(poly, np.int32)], 255)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    blob = (lab == k).astype(np.uint8) * 255
    cs, _ = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    poly = cv2.approxPolyDP(c, eps_px, True)[:, 0, :]
    vis = im.copy()
    vis[blob > 0] = (vis[blob > 0] * .6 + np.array([0, 160, 255]) * .4).astype(np.uint8)
    cv2.polylines(vis, [poly.reshape(-1, 1, 2)], True, (255, 0, 0), 3)
    cv2.imwrite(out_png, cv2.resize(vis[y0:y1, x0:x1], None, fx=.5, fy=.5))
    return poly.tolist()

if __name__ == '__main__':
    a = json.loads(sys.argv[1])
    print(json.dumps(trace(**a)))
