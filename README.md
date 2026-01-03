# DoomMe
<p align="center">
<a href="menu/episode_1.md">
<img src="https://github.com/Kuberwastaken/DoomMe/blob/main/static/start-visual.gif" alt="Click to Play DOOM" width="640">
</a>
<br>
<sub><strong>Click to Play DOOM</strong></sub>
</p>

---

## **Overview**
**DoomMe** is **Doom (1993)** in spectator mode — the classic E1M1 map rendered entirely within GitHub's markdown viewer.

Navigate through the level by clicking directional arrows. Every view is pre-rendered; every movement is a hyperlink. No JavaScript, no WASM, no backend — just 4,356 interlinked screenshots forming a explorable graph of the original level geometry.

<p align="center">
<img src="static/e1m1_map.png" alt="E1M1 Map Layout via DoomWiki" width="600">
<br>
<sub><em>Map layout of E1M1 (Hangar) — fully explorable in this project.</em></sub>
</p>

---

## **How It Works**

### **1. Map Extraction (Omgifol)**
The first challenge was accurately mapping the entire playable area.

- **Initial Failure (BFS)**: Early attempts used a "Blind Walk" algorithm where an agent bumped into walls to discover paths. This failed to find areas behind closed doors.
- **The WAD Solution**: I edited the original `doom1.wad` to remove all doors/gates, then used **[Omgifol](https://github.com/devinacker/omgifol)** to parse the level geometry:
  - Extract **Linedefs** and **Sectors** from the WAD
  - Filter for walkable sectors (floor height > 56 units)
  - Apply **Point-in-Polygon** ray-casting to generate a 64-unit grid
  - **Result**: 1,089 valid positions covering the entire map

### **2. Visual Capture (VizDoom)**
**[VizDoom](http://vizdoom.cs.put.poznan.pl/)** renders each position at 4 angles (0°, 90°, 180°, 270°).

- **Teleportation**: Warp to each coordinate via console command
- **Rotation Fix**: Early versions used `angle X` console commands which were unreliable due to physics tick interference. The fix was implementing **closed-loop control**:
  - Read current angle via `GameVariable.ANGLE`
  - Calculate rotation delta
  - Apply via `TURN_LEFT_RIGHT_DELTA` button
  - Repeat until aligned (feedback loop)
- **Capture Settings**: God mode enabled, enemies disabled, HUD messages suppressed
- **Result**: 4,356 WebP screenshots (1,089 positions × 4 angles)

### **3. Navigation Graph (Linker)**
The `linker.py` script generates the markdown navigation files.

- **Nodes**: Each state is `(x, y, angle)` 
- **Movement**: 8-directional with diagonal strafing
- **Rotation**: Left/Right arrows rotate 90° in place (no movement)
- **Result**: 4,356 interlinked markdown files

---

## **Technical Details**

| Aspect | Choice | Reason |
|--------|--------|--------|
| **Grid Size** | 64 units | Matches Doom's floor texture alignment |
| **Angles** | 4 (90° increments) | Balance between smoothness and file count |
| **Format** | WebP @ 85% | Small files, good quality |
| **Resolution** | 640×480 | Classic Doom resolution |

### **Controls**
- **⬆️ / ⬇️** — Move Forward / Backward  
- **⬅️ / ➡️** — Rotate Camera 90° (in place)  
- **↖️ / ↗️ / ↙️ / ↘️** — Strafe diagonally

---

## **The Journey**

1. **BFS Walker** — Failed. Couldn't find rooms behind doors.
2. **Omgifol Parser** — Success. Extracted geometry directly from WAD.
3. **Door Problem** — Gates blocked exploration. Edited WAD to remove them.
4. **Rotation Bug** — Console commands unreliable. Fixed with closed-loop turning.
5. **Final Result** — 1,089 positions, 4,356 images, full E1M1 coverage.

---

<p align="center">
<em>Click the image above to start exploring.</em>
</p>
</CodeContent>
<parameter name="EmptyFile">false
