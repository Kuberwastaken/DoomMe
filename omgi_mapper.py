import json
import math
from omg import WAD, MapEditor
from pathlib import Path

# Config
WAD_PATH = "doom1.wad"
MAP_NAME = "E1M1"
STEP_SIZE = 64
OUTPUT_FILE = "map_data.json"

def point_in_polygon(x, y, poly):
    """Ray casting algorithm or similar for PiP."""
    # poly is list of (x1, y1, x2, y2) segments or just vertices
    # Let's assume poly is a list of linedefs (v1, v2)
    inside = False
    for v1, v2 in poly:
        x1, y1 = v1
        x2, y2 = v2
        
        # Check intersection with horizontal ray to the right
        if ((y1 > y) != (y2 > y)):
            intersect_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < intersect_x:
                inside = not inside
    return inside

def main():
    print(f"Loading {WAD_PATH}...")
    w = WAD()
    w.from_file(WAD_PATH)
    
    print(f"Loading {MAP_NAME}...")
    editor = MapEditor(w.maps[MAP_NAME])
    
    # 1. Group Linedefs by Sector
    # Linedef has 'front_sidedef' and 'back_sidedef' (indices)
    # Sidedef has 'sector' (index)
    
    sector_lines = {} # sector_idx -> list of (v1, v2)
    
    print("Processing Linedefs...")
    for ld in editor.linedefs:
        v1 = (editor.vertexes[ld.vx_a].x, editor.vertexes[ld.vx_a].y)
        v2 = (editor.vertexes[ld.vx_b].x, editor.vertexes[ld.vx_b].y)
        
        # Front Side
        if ld.front != -1 and ld.front != 65535 and ld.front < len(editor.sidedefs):
            side = editor.sidedefs[ld.front]
            sec_idx = side.sector
            if sec_idx not in sector_lines: sector_lines[sec_idx] = []
            sector_lines[sec_idx].append((v1, v2))
            
        # Back Side
        if ld.back != -1 and ld.back != 65535 and ld.back < len(editor.sidedefs):
            side = editor.sidedefs[ld.back]
            sec_idx = side.sector
            if sec_idx not in sector_lines: sector_lines[sec_idx] = []
            sector_lines[sec_idx].append((v1, v2))

    # 2. Identify Walkable Sectors and Scan
    valid_positions = set()
    
    print(f"Scanning {len(editor.sectors)} sectors...")
    
    for i, sec in enumerate(editor.sectors):
        # Filter non-walkable
        # Height check
        height = sec.z_ceil - sec.z_floor
        if height < 56: continue # Too low
        
        # Texture check (Example: avoid NUKAGE if desired, but E1M1 nukage is walkable)
        # if 'NUKAGE' in sec.tx_floor: continue
        
        lines = sector_lines.get(i, [])
        if not lines: continue
        
        # Bounding Box
        min_x = min(min(v[0][0], v[1][0]) for v in lines)
        max_x = max(max(v[0][0], v[1][0]) for v in lines)
        min_y = min(min(v[0][1], v[1][1]) for v in lines)
        max_y = max(max(v[0][1], v[1][1]) for v in lines)
        
        # Align to Step Size
        start_x = math.ceil(min_x / STEP_SIZE) * STEP_SIZE
        start_y = math.ceil(min_y / STEP_SIZE) * STEP_SIZE
        
        # Scan Grid
        for x in range(start_x, int(max_x) + 1, STEP_SIZE):
            for y in range(start_y, int(max_y) + 1, STEP_SIZE):
                # 64-unit buffer from walls? 
                # PiP check returns true if EXACTLY inside.
                # But doom player has radius 16. 
                # Let's just check center point.
                
                if point_in_polygon(x, y, lines):
                    # Refinement: Is it TOO close to a wall?
                    # dist check
                    dist = float('inf')
                    for v1, v2 in lines:
                        # Distance to segment... slightly complex math
                        # Simply skip if very close to any wall
                        pass 
                    
                    # For now, accept it
                    valid_positions.add((x, y))

    print(f"Found {len(valid_positions)} valid grid points.")
    
    # 3. Export
    # Angles: 0, 90, 180, 270
    angles = [0, 90, 180, 270]
    
    output = {
        "positions": list(sorted(list(valid_positions))), # [ [x,y], ... ]
        "angles": angles,
        "step_size": STEP_SIZE,
        "map": MAP_NAME
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
