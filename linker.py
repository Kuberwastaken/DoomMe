"""
DOOM README Explorer - Linker Script v2
Generates markdown files with simplified tank-style controls.

Control Layout:
        ⬆️           (Forward)
    ↰   💥   ↱       (Turn Left 45°, Shoot, Turn Right 45°)
        ⬇️           (Turn 180°)

Uses map_data.json as the source of truth.
"""

import os
import re
import json
from pathlib import Path
from typing import Set, Tuple, Optional

ASSETS_DIR = Path(__file__).parent / "assets"
GAME_DIR = Path(__file__).parent / "game"
MENU_DIR = Path(__file__).parent / "menu"
MAP_DATA = Path(__file__).parent / "map_data.json"

# Direction names
DIRECTION_NAMES = {
    0: "East", 45: "NE", 90: "North", 135: "NW",
    180: "West", 225: "SW", 270: "South", 315: "SE"
}

# Angle deltas for forward movement
ANGLE_DELTAS = {
    0:   (64, 0),
    45:  (64, 64),
    90:  (0, 64),
    135: (-64, 64),
    180: (-64, 0),
    225: (-64, -64),
    270: (0, -64),
    315: (64, -64),
}


def load_map_data() -> dict:
    """Load map data from JSON file."""
    if not MAP_DATA.exists():
        return None
    with open(MAP_DATA, "r") as f:
        return json.load(f)


def build_position_set(map_data: dict) -> Set[Tuple[int, int, int]]:
    """Build set of all (x, y, angle) positions from map data."""
    positions = set()
    for pos in map_data["positions"]:
        x, y = pos[0], pos[1]
        for angle in map_data["angles"]:
            positions.add((x, y, angle))
    return positions


def get_state_filename(x: int, y: int, angle: int) -> str:
    return f"{x}_{y}_{angle}.md"


def get_shoot_filename(x: int, y: int, angle: int) -> str:
    return f"shoot_{x}_{y}_{angle}.md"


def check_shoot_exists(x: int, y: int, angle: int) -> bool:
    """Check if shoot screenshot exists."""
    return (ASSETS_DIR / f"shoot_{x}_{y}_{angle}.jpg").exists()


def make_link(target: Tuple[int, int, int], emoji: str, 
              positions: Set[Tuple[int, int, int]]) -> str:
    """Create link if target exists, otherwise dim the emoji."""
    if target in positions:
        return f'<a href="{get_state_filename(*target)}">{emoji}</a>'
    return f'<span style="opacity:0.3">{emoji}</span>'


def generate_navigation_markdown(x: int, y: int, angle: int,
                                  positions: Set[Tuple[int, int, int]],
                                  is_shoot_state: bool = False) -> str:
    """
    Generate markdown with simplified tank controls.
    
    Controls:
    - ⬆️ Forward: Move in current direction
    - ↰/↱ Turn: Rotate 45° left/right (same position)
    - ⬇️ Back: Turn 180° (same position, opposite direction)
    - 💥 Shoot: Fire weapon
    """
    # Calculate relative movements based on current angle
    # ANGLE 90 (North) -> Left is West (-x), Right is East (+x)
    # This means:
    # Forward: Angle
    # Back: Angle + 180
    # Left (Strafe): Angle + 90
    # Right (Strafe): Angle - 90
    
    # FORWARD
    fwd_dx, fwd_dy = ANGLE_DELTAS[angle]
    forward_pos = (x + fwd_dx, y + fwd_dy, angle)
    
    # BACKWARD
    back_pos = (x - fwd_dx, y - fwd_dy, angle)
    
    # STRAFE LEFT (Angle + 90)
    # Need to be careful with angle indices. ANGLE_DELTAS has 8 keys.
    # strafe_left_angle = (angle + 90) % 360
    # But wait, strafing doesn't change facing angle! It changes POSITION.
    # So we use the DX/DY of the perpendicular angle, but keep current Angle.
    left_angle_vec = (angle + 90) % 360
    ldx, ldy = ANGLE_DELTAS[left_angle_vec]
    strafe_left_pos = (x + ldx, y + ldy, angle)
    
    # STRAFE RIGHT (Angle - 90)
    right_angle_vec = (angle - 90 + 360) % 360
    rdx, rdy = ANGLE_DELTAS[right_angle_vec]
    strafe_right_pos = (x + rdx, y + rdy, angle)
    
    # TURNS (Look)
    turn_left_45 = (x, y, (angle + 45) % 360)
    turn_right_45 = (x, y, (angle - 45 + 360) % 360)
    
    # Build links
    fwd_link = make_link(forward_pos, "⬆️", positions)
    back_link = make_link(back_pos, "⬇️", positions)
    str_left_link = make_link(strafe_left_pos, "⬅️", positions)
    str_right_link = make_link(strafe_right_pos, "➡️", positions)
    
    turn_left_link = make_link(turn_left_45, "↺", positions)
    turn_right_link = make_link(turn_right_45, "↻", positions)
    
    # Shoot button (Reload)
    shoot_link = f'<a href="{get_state_filename(x, y, angle)}">💥</a>'
    
    direction = DIRECTION_NAMES.get(angle, f"{angle}°")
    
    img_path = f"../assets/doom_{x}_{y}_{angle}.jpg"
    alt_text = f"E1M1 - {direction}"
    
    markdown = f"""<p align="center">
<img src="{img_path}" alt="{alt_text}" width="640">
</p>

<table align="center">
<tr>
<td align="center" width="80">{turn_left_link}</td>
<td align="center" width="80">{fwd_link}</td>
<td align="center" width="80">{turn_right_link}</td>
</tr>
<tr>
<td align="center" width="80">{str_left_link}</td>
<td align="center" width="80">{shoot_link}</td>
<td align="center" width="80">{str_right_link}</td>
</tr>
<tr>
<td colspan="3" align="center">{back_link}</td>
</tr>
</table>

<p align="center">
<sub>🧭 {direction} | <a href="../README.md">🏠 Menu</a></sub>
</p>
"""
    return markdown


def generate_all_states(positions: Set[Tuple[int, int, int]]):
    """Generate all navigation markdown files."""
    GAME_DIR.mkdir(exist_ok=True)
    
    # Get unique (x, y) positions
    xy_positions = {(p[0], p[1]) for p in positions}
    angles = sorted({p[2] for p in positions})
    
    total = len(positions)
    print(f"Generating {total} navigation files...")
    
    count = 0
    
    for x, y in sorted(xy_positions):
        for angle in angles:
            state = (x, y, angle)
            if state not in positions:
                continue
            
            # Normal navigation state
            content = generate_navigation_markdown(x, y, angle, positions, False)
            filepath = GAME_DIR / get_state_filename(x, y, angle)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            count += 1
            
            if count % 50 == 0:
                print(f"  Generated {count}/{total}...")
    
    print(f"Generated {count} navigation files")


def generate_readme(spawn: dict, total_positions: int):
    """Generate README.md with title screen and start link."""
    x, y, angle = spawn["x"], spawn["y"], spawn["angle"]
    
    readme = f"""# 🎮 DOOM

<p align="center">
<img src="menu/title.jpg" alt="DOOM" width="640">
</p>

<h2 align="center">
<a href="menu/episode.md">🎮 NEW GAME</a>
</h2>

---

Navigate **E1M1: Hangar** through pre-rendered screenshots.

**Controls:**
```
        ⬆️           Forward
    ↰   💥   ↱       Turn / Shoot
        ⬇️           Turn Around
```

### Stats
- **Positions**: {total_positions}
- **Grid**: 64 Doom units
- **Angles**: 8 directions

---

*Built with [VizDoom](https://vizdoom.farama.org/)*
"""
    
    with open(Path(__file__).parent / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    print("README.md saved")


def generate_menu_pages(spawn: dict):
    """Generate menu markdown pages."""
    MENU_DIR.mkdir(exist_ok=True)
    x, y, angle = spawn["x"], spawn["y"], spawn["angle"]
    
    episode_md = f"""<p align="center">
<img src="episode.jpg" alt="Which Episode?" width="640">
</p>

<h2 align="center">
<a href="../game/{get_state_filename(x, y, angle)}">▶️ KNEE-DEEP IN THE DEAD</a>
</h2>

<p align="center">
<sub><a href="../README.md">← Back</a></sub>
</p>
"""
    
    with open(MENU_DIR / "episode.md", "w", encoding="utf-8") as f:
        f.write(episode_md)
    print("Menu pages generated")


def main():
    print("=" * 50)
    print("DOOM README Explorer - Linker v2")
    print("=" * 50)
    print()
    
    # Load from map_data.json
    map_data = load_map_data()
    if not map_data:
        print("No map_data.json found! Run gridmapper.py first.")
        return
    
    # Build position set
    positions = build_position_set(map_data)
    print(f"Loaded {len(positions)} positions from map_data.json")
    print(f"X range: {map_data['bounds']['x_min']} to {map_data['bounds']['x_max']}")
    print(f"Y range: {map_data['bounds']['y_min']} to {map_data['bounds']['y_max']}")
    print()
    
    # Generate all states
    generate_all_states(positions)
    
    # Get spawn (first position, facing North)
    first_pos = map_data["positions"][0]
    spawn = {"x": first_pos[0], "y": first_pos[1], "angle": 90}
    
    # If spawn was saved in map_data, use that
    if "spawn" in map_data:
        spawn = map_data["spawn"]
    
    print(f"\nStart position: ({spawn['x']}, {spawn['y']}) facing {spawn['angle']}°")
    
    # Generate README and menu
    generate_readme(spawn, len(map_data["positions"]))
    generate_menu_pages(spawn)
    
    print()
    print("=" * 50)
    print("Linking complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
