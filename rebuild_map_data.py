import os
import re
import json
from pathlib import Path

ASSETS_DIR = Path("assets")
OUTPUT_JSON = Path("map_data.json")

def main():
    if not ASSETS_DIR.exists():
        print("No assets/ directory found!")
        return

    positions = set()
    x_vals = []
    y_vals = []
    angles = set()

    print("Scanning assets/...")
    files = list(ASSETS_DIR.glob("doom_*.webp"))
    print(f"Found {len(files)} screenshot files.")

    for f in files:
        # Parse doom_X_Y_ANGLE.webp
        match = re.match(r"doom_(-?\d+)_(-?\d+)_(\d+).webp", f.name)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            angle = int(match.group(3))
            
            positions.add((x, y))
            x_vals.append(x)
            y_vals.append(y)
            angles.add(angle)

    if not positions:
        print("No valid positions found.")
        return

    # Expand positions to include all angles for each x,y (since we know we have 8)
    # Actually, linker expects a list of [x, y] in "positions" and separate "angles".
    # But wait, linker.py's build_position_set iterates through map_data["positions"] (x,y)
    # and map_data["angles"].
    # It assumes every x,y has ALL angles.
    # If the capture is partial, some positions might not have all angles yet (though gridmapper does 8 at a time).
    # gridmapper does 8 angles per position loop. So it should be safe.

    sorted_positions = sorted(list(positions))
    sorted_angles = sorted(list(angles))

    map_data = {
        "positions": [list(p) for p in sorted_positions],
        "step_size": 64, 
        "angles": sorted_angles,
        "spawn": {"x": 1024, "y": -3584, "angle": 90}, # Default E1M1 spawn
        "bounds": {
            "x_min": min(x_vals),
            "x_max": max(x_vals),
            "y_min": min(y_vals),
            "y_max": max(y_vals)
        }
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(map_data, f, indent=2)
    
    print(f"Saved {len(sorted_positions)} positions to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
