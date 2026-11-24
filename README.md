# Ying Fai Court flat views

3D pages for Ying Fai Court (影輝苑), Tseung Kwan O, HOS 2025:

- `index.html`: walk-through of flats 2 and 3 (Block A) and 9 and 10 (Block B) on any floor, with three furnished layouts of three or four bedrooms plus the bare flat, the real view from each window, the sun at any time of day (its path, the light and shadows it casts inside, and when each window gets direct sun), where the lifts and refuse room are on the floor, and an area view that zooms out to the rest of Hong Kong (terrain, coastline, main roads and place names, loaded at runtime from the AWS Terrain Tiles and OpenStreetMap via OpenFreeMap). Links can pick the flat and floor, e.g. `index.html#A3-24`.
- `block-a.html`: what Block A flats 2 and 3 can see from every floor, including the acoustic fins.
- `block-b.html`: what Block B flats 9 and 10 can see from every floor.

Each page is a single self-contained HTML file (three.js and fonts load from public CDNs). The towers are traced from the Housing Authority typical floor plans; room layouts, window heights, podium levels and partition positions are estimates from the HA sales brochure and booklet. Any partition needs HA approval before it is built.
