"""
DOOM README Explorer - Linker Script v3 (Final)
Generates markdown files with 4-way TURN-BASED controls.

Control Layout:
        ⬆️           (Forward)
    ⬅️  💥  ➡️       (Turn Left 90°, Reload, Turn Right 90°)
        ⬇️           (Backward)

Uses map_data.json and assets/*.webp.
"""

import os
import re
import json
from pathlib import Path
from typing import Set, Tuple, Optional

ASSETS_DIR = Path(__file__).parent / "assets"
GAME_DIR = Path(__file__).parent / "game"
MENU_DIR = Path(__file__).parent / "menu"
STATIC_DIR = Path(__file__).parent / "static"
MAP_DATA = Path(__file__).parent / "map_data.json"

# Direction names
DIRECTION_NAMES = {
    0: "East", 90: "North", 180: "West", 270: "South"
}

def get_angle_deltas(step: int) -> dict:
    """Generate angle deltas based on step size."""
    # 0=East, 90=North
    return {
        0:   (step, 0),
        90:  (0, step),
        180: (-step, 0),
        270: (0, -step),
    }

def load_map_data() -> dict:
    if not MAP_DATA.exists(): return None
    with open(MAP_DATA, "r") as f: return json.load(f)

def get_state_filename(x: int, y: int, angle: int) -> str:
    return f"{x}_{y}_{angle}.md"

def make_link(target: Tuple[int, int, int], emoji: str, 
              positions: Set[Tuple[int, int, int]]) -> str:
    """Create link if target exists."""
    if target in positions:
        return f'<a href="{get_state_filename(*target)}">{emoji}</a>'
    return f'<span style="opacity:0.3">{emoji}</span>'

def generate_navigation_markdown(x: int, y: int, angle: int,
                                  positions: Set[Tuple[int, int, int]],
                                  step_size: int) -> str:
    angle_deltas = get_angle_deltas(step_size)
    
    # Robustness: angle check
    if angle not in angle_deltas:
        return f"<!-- Unsupported angle {angle} -->"

    # Vectors
    fwd = angle_deltas[angle]
    # Right strafe is (angle - 90)
    right_ang = (angle - 90 + 360) % 360
    right = angle_deltas[right_ang]
    # Left strafe is (angle + 90)
    left_ang = (angle + 90) % 360
    left = angle_deltas[left_ang]
    
    # Helper to add tuples
    def add_pt(p, d): return (p[0]+d[0], p[1]+d[1])
    
    # Current Pos
    curr_pos = (x, y)
    
    # Calculate Targets
    # 1. Top Row (NW, N, NE) - Maintain Angle (Strafe)
    nw_pos = (*add_pt(add_pt(curr_pos, fwd), left), angle)
    n_pos  = (*add_pt(curr_pos, fwd), angle)
    ne_pos = (*add_pt(add_pt(curr_pos, fwd), right), angle)
    
    # 2. Middle Row (W, E) - Turn 90 + Move
    w_pos = (*add_pt(curr_pos, left), left_ang)   # Turn Left + Move Left
    e_pos = (*add_pt(curr_pos, right), right_ang) # Turn Right + Move Right
    
    # 3. Bottom Row (SW, S, SE) - Maintain Angle (Strafe)
    # Back vector is -fwd
    back = (-fwd[0], -fwd[1])
    sw_pos = (*add_pt(add_pt(curr_pos, back), left), angle)
    s_pos  = (*add_pt(curr_pos, back), angle)
    se_pos = (*add_pt(add_pt(curr_pos, back), right), angle)

    # shoot (reload) - stay put
    shoot_link = f'<a href="{get_state_filename(x, y, angle)}">💥</a>'

    # Link Helper
    def get_link(target, label):
        if target in positions:
            return f'<a href="{get_state_filename(*target)}">{label}</a>'
        return f'<span style="opacity:0.3">{label}</span>'

    # Generate Grid Links
    links = {
        "nw": get_link(nw_pos, "↖️"),
        "n":  get_link(n_pos, "⬆️"),
        "ne": get_link(ne_pos, "↗️"),
        "w":  get_link(w_pos, "⬅️"),
        "e":  get_link(e_pos, "➡️"),
        "sw": get_link(sw_pos, "↙️"),
        "s":  get_link(s_pos, "⬇️"),
        "se": get_link(se_pos, "↘️"),
    }
    
    direction = DIRECTION_NAMES.get(angle, f"{angle}°")
    img_path = f"../assets/doom_{x}_{y}_{angle}.webp"
    
    markdown = f"""<p align="center">
<img src="{img_path}" alt="E1M1 - {direction}" width="640">
</p>

<table align="center">
<tr>
<td align="center" width="80">{links['nw']}</td>
<td align="center" width="80">{links['n']}</td>
<td align="center" width="80">{links['ne']}</td>
</tr>
<tr>
<td align="center" width="80">{links['w']}</td>
<td align="center" width="80">{shoot_link}</td>
<td align="center" width="80">{links['e']}</td>
</tr>
<tr>
<td align="center" width="80">{links['sw']}</td>
<td align="center" width="80">{links['s']}</td>
<td align="center" width="80">{links['se']}</td>
</tr>
</table>

<p align="center">
<sub>🧭 {direction} | <a href="../README.md">🏠 Menu</a></sub>
</p>
"""
    return markdown

def generate_all_states(positions: Set[Tuple[int, int, int]], step_size: int = 64):
    GAME_DIR.mkdir(exist_ok=True)
    xy_positions = {(p[0], p[1]) for p in positions}
    angles = sorted({p[2] for p in positions})
    
    total = len(positions)
    print(f"Generating {total} navigation files...")
    
    count = 0
    for x, y in sorted(xy_positions):
        for angle in angles:
            if (x, y, angle) not in positions: continue
            
            content = generate_navigation_markdown(x, y, angle, positions, step_size)
            filepath = GAME_DIR / get_state_filename(x, y, angle)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            count += 1
            if count % 100 == 0: print(f"\r  Generated {count}/{total}...", end="")
    
    print(f"\nGenerated {count} navigation files")

def generate_readme(total_positions: int):
    # Root README points to menu/episode_1.md
    # We use static/start-visual.gif if available, else static/1.png
    
    img_src = "static/start-visual.gif"
    if not (STATIC_DIR / "start-visual.gif").exists():
        img_src = "static/1.png" # Fallback
        
    readme = f"""# DoomMe
<p align="center">
<a href="menu/episode_1.md">
<img src="{img_src}" alt="Click to Start" width="640">
</a>
</p>

---

## **Overview**
**DoomMe** is an experimental "spectator mode" exploration of the classic **Doom (1993)** E1M1 map, rendered entirely within GitHub's markdown viewer. 

It is **not** a playable version of Doom. Instead, it is a static traversal of the level's geometry, pre-rendered and interlinked to allow you to "walk" through the map by clicking directional buttons. Think of it as a museum tour of the E1M1 level design.

<p align="center">
<img src="static/e1m1_map.png" alt="E1M1 Map Layout via DoomWiki" width="600">
<br>
<sub><em>Map layout of E1M1 (Hangar) - The area covered by this project.</em></sub>
</p>

## **How It Works**
The "engine" you are interacting with is purely illusory. There is no JavaScript, no WASM, and no server-side logic. Every possible view and movement is pre-calculated.

### **1. The Map Extraction (Omgifol)**
The biggest challenge was accurately mapping the playable area. 
- **Initial Failure (BFS)**: My first attempt used a "Blind Walk" algorithm (Breadth-First Search) where an agent would bump into walls to find paths. This failed to discover disconnected rooms or areas behind doors.
- **The Solution**: I switched to **[Omgifol](https://github.com/devinacker/omgifol)**, a Python library that parses the original `doom1.wad` file.
    - We extract the **Linedefs** and **Sectors**.
    - We filter for sectors with a floor height > 50 (playable space).
    - We use a **Point-in-Polygon** ray-casting algorithm to generate a grid of valid coordinates every 64 units.

### **2. The Capture (VizDoom)**
Once the grid was established (resulting in ~1,085 valid nodes), I used **[VizDoom](http://vizdoom.cs.put.poznan.pl/)** to capture the visuals.
- The agent is "teleported" to each coordinate.
- It rotates to 4 cardinal directions (North, South, East, West).
- A screenshot is saved for every single state.
- **Result**: ~4,340 snapshots of the map.

### **3. The Graph (Linker)**
The `linker.py` script ties it all together into a massive graph.
- **Nodes**: `(x, y, angle)`
- **Edges**:
    - **Move**: `(x, y)` -> `(x ± 64, y ± 64)` details.
    - **Polishing**: I utilized 8-way movement logic, allowing for strafing (diagonal moves) which keeps the camera angle fixed but changes position.

## **Technical Roadblocks & Choices**
1.  **File Count vs. Git**: Storing 4,000+ files is heavy. I had to use `WebP` compression (85% quality) to keep the repo size manageable while maintaining visual fidelity.
2.  **Grid Quantization**: Doom is continuous, but this project is discrete. The **64-unit** step size was chosen because it matches Doom's floor texture alignment (64x64 pixels). This makes the movement feel "on the beat" of the level geometry.
3.  **Turning**: I limited turning to 90° increments. 45° turns would have doubled the file count to ~8,600 images, which was deemed too large for a single "fun" commit.

### **Controls**
- **⬆️ / ⬇️**: Move Forward / Backward
- **⬅️ / ➡️**: Turn 90° Left/Right AND Move
- **↖️ / ↗️ / ↙️ / ↘️**: Strafe (Move diagonally while facing same direction)

*(Click the top image to start your tour)*
"""
    with open(Path(__file__).parent / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    print("README.md saved")

def main():
    print("Linker v3 Starting...")
    map_data = load_map_data()
    if not map_data:
        print("Waiting for map_data.json...")
        return

    positions = set()
    for p in map_data["positions"]:
        # map_data positions is list of [x, y]
        # map_data angles is list of ints
        # We need to combinatorial them? 
        # Wait, previous re-builder made "positions": [[x,y],...] and "angles": [...]
        # BUT gridmapper might output DIFFERENT format.
        # Let's check map_data structure or just rely on rebuild_map_data.py to standardize it.
        pass
    
    # Actually, rebuild_map_data.py does the scanning. 
    # linker.py expects rebuild_map_data.py to have run.
    # rebuild_map_data.py produces: { "positions": [[x,y], ...], "angles": [0,90,180,270], "bounds": ... }
    # So we construct the set:
    
    for pos in map_data["positions"]:
        x, y = pos
        for ang in map_data["angles"]:
            positions.add((x, y, ang))
            
    generate_all_states(positions, map_data.get("step_size", 64))
    generate_readme(len(positions))
    print("Done.")

if __name__ == "__main__":
    main()
