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

    # Movement vectors based on current facing direction
    # Forward = direction we're facing
    fwd = angle_deltas[angle]
    back = (-fwd[0], -fwd[1])
    
    # Strafe directions (perpendicular to facing)
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
    
    # Calculate Targets:
    # ROTATION: Left/Right rotate camera 90° IN PLACE (no movement!)
    # Turn Left = same position, rotate counter-clockwise
    turn_left_ang = (angle + 90) % 360
    turn_left_pos = (x, y, turn_left_ang)
    # Turn Right = same position, rotate clockwise  
    turn_right_ang = (angle - 90 + 360) % 360
    turn_right_pos = (x, y, turn_right_ang)
    
    # MOVEMENT: Up/Down move forward/backward, maintaining angle
    n_pos = (*add_pt(curr_pos, fwd), angle)   # Forward (Up arrow)
    s_pos = (*add_pt(curr_pos, back), angle)  # Backward (Down arrow)
    
    # DIAGONALS: Strafe diagonally while maintaining camera direction
    nw_pos = (*add_pt(add_pt(curr_pos, fwd), left), angle)   # Forward-Left
    ne_pos = (*add_pt(add_pt(curr_pos, fwd), right), angle)  # Forward-Right
    sw_pos = (*add_pt(add_pt(curr_pos, back), left), angle)  # Back-Left
    se_pos = (*add_pt(add_pt(curr_pos, back), right), angle) # Back-Right

    # shoot (reload) - stay put
    # PROXIMITY END GAME TRIGGER
    # Final room approx: x[2944, 3072], y[-4864, -4608]
    if x >= 2944 and y <= -4608:
        shoot_link = f'<a href="end_game.md">💥</a>'
    else:
        shoot_link = f'<a href="{get_state_filename(x, y, angle)}">💥</a>'

    # Link Helper
    def get_link(target, label):
        if target in positions:
            return f'<a href="{get_state_filename(*target)}">{label}</a>'
        return f'<span style="opacity:0.3">{label}</span>'

    # Generate Grid Links
    # W/E are now ROTATION (in place), not strafe+turn
    links = {
        "nw": get_link(nw_pos, "↖️"),
        "n":  get_link(n_pos, "⬆️"),
        "ne": get_link(ne_pos, "↗️"),
        "w":  get_link(turn_left_pos, "⬅️"),   # Just rotate left
        "e":  get_link(turn_right_pos, "➡️"),  # Just rotate right
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
    readme = """<h1 align="center">DoomMe: Running DOOM from a GitHub Readme</h1>

<p align="center">
<a href="menu/episode_1.md">
<img src="static/start-visual.gif" alt="Click to Play DOOM" width="640">
</a>
<br>
<sub><strong>Yes, this is literally the game. You can click it to start playing.</strong></sub>
</p>

<p align="center">
<img src="https://img.shields.io/static/v1?label=Kuberwastaken&message=DoomMe&color=black&logo=github" alt="Kuberwastaken - DoomMe">
<img src="https://img.shields.io/badge/version-5-black" alt="Version 5">
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-black" alt="License MIT"></a>
</p>

---

## What Is This?

**DoomMe** is Doom's E1M1 level running entirely inside GitHub's markdown viewer. Without using any javascript or a backend server, it's just **4,340 pre-rendered screenshots** linked together with hyperlinks.

Every position × every angle = a unique markdown file. Click a direction, load a new file. That's the whole "engine."

📖 **Full story**: [How I Made DOOM Run Inside a GitHub Readme](https://kuber.studio/blog/Projects/How-I-Made-DOOM-Run-Inside-a-GitHub-Readme)

---

## Gameplay

Here's some gameplay I captured locally

<p align="center">
<img src="static/gameplay-local.gif">
</p>


## Repo Structure

```
DoomMe/
├── assets/              # 4,340 WebP screenshots (doom_x_y_angle.webp)
├── game/                # 4,340 navigation markdown files
├── menu/                # Episode & difficulty selection screens
├── static/              # Banner GIF, map image, menu assets
├── linker.py            # Generates the markdown graph from map_data
├── gridmapper.py        # VizDoom capture script
├── omgi_mapper.py       # WAD parser using Omgifol
├── map_data.json        # Valid (x, y) coordinates for E1M1
└── README.md            # You are here
```

---

## How It Works (TL;DR)

1. **Parse the WAD** — `omgi_mapper.py` uses [Omgifol](https://github.com/devinacker/omgifol) to extract E1M1 geometry
2. **Generate the grid** — Point-in-Polygon filtering on a 64-unit grid → 1,085 valid spots  
3. **Capture screenshots** — `gridmapper.py` teleports a VizDoom agent to each spot, 4 angles each
4. **Link it all** — `linker.py` builds the navigation graph as interlinked `.md` files

## License

[MIT](LICENSE) - feel free to tweak around and play with the code
Feel free to raise issues and PRs too

## Credits

- ID Software for DOOM 1993 and the WAD file
- [Omgifol](https://github.com/devinacker/omgifol) - WAD parser
- [VizDoom](https://github.com/mwydmuch/VizDoom) - Doom AI
- [Ultimate DOOM Builder](https://github.com/UltimateDOOMBuilder/UltimateDOOMBuilder) - WAD editor

---

<p align="center">
  Made with &lt;3 by <a href="https://kuber.studio">Kuber Mehta</a>
</p>
"""
    with open(Path(__file__).parent / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    print("README.md saved")

def generate_end_screen():
    print("Generating end_game.md...")
    content = """<p align="center">
<img src="../static/end-screen.png" alt="THE END" width="640">
</p>

<h2 align="center">YOU SURVIVED E1M1</h2>

<p align="center">
<a href="../menu/episode_1.md"><strong>🔄 RESTART MISSION</strong></a>
&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
<a href="https://github.com/Kuberwastaken/DoomMe"><strong>⭐ STAR PROJECT</strong></a>
</p>
"""
    with open(GAME_DIR / "end_game.md", "w", encoding="utf-8") as f:
        f.write(content)

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
    generate_end_screen()
    print("Done.")

if __name__ == "__main__":
    main()
