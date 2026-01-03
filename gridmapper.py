"""
DOOM E1M1 Static Capture Mapper (FIXED ROTATION)
"""

import os
import sys
import json
import math
import cv2
from pathlib import Path

try:
    import vizdoom as vzd
except ImportError:
    print("Missing vizdoom!")
    sys.exit(1)

WAD_PATH = Path(__file__).parent / "doom1.wad"
ASSETS_DIR = Path(__file__).parent / "assets"
OUTPUT_JSON = Path(__file__).parent / "map_data.json"

WEBP_QUALITY = 85
# Doom Coordinate System: 0=East, 90=North, 180=West, 270=South
ANGLES = [0, 90, 180, 270] 

def setup_game(wad_path: Path) -> vzd.DoomGame:
    game = vzd.DoomGame()
    game.set_doom_game_path(str(wad_path))
    game.set_doom_map("E1M1")
    game.set_screen_resolution(vzd.ScreenResolution.RES_640X480)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    game.set_window_visible(False)
    game.set_render_all_frames(True)
    
    # Render settings
    game.set_render_hud(True)
    game.set_render_crosshair(False)
    game.set_render_weapon(True)
    game.set_render_messages(False)
    game.set_render_particles(False)
    game.set_render_screen_flashes(False)
    
    # --- FIX 1: Add Turning Button ---
    # This allows us to apply rotation delta (turning) as a native engine action
    game.add_available_button(vzd.Button.TURN_LEFT_RIGHT_DELTA)
    
    # --- FIX 2: Add Angle Variable ---
    # This allows us to read exactly where we are looking to verify the turn
    game.add_available_game_variable(vzd.GameVariable.ANGLE)
    game.add_available_game_variable(vzd.GameVariable.POSITION_X)
    game.add_available_game_variable(vzd.GameVariable.POSITION_Y)
    
    game.add_game_args("+sv_cheats 1 -nomp -nosound -nomonsters +iddqd +notarget")
    
    game.init()
    return game

def get_angle_diff(target, current):
    """Calculates the shortest turn path (handling 0/360 wrap-around)."""
    diff = target - current
    while diff <= -180: diff += 360
    while diff > 180: diff -= 360
    return diff

def turn_to_angle(game, target_angle):
    """
    Robustly rotates the player to the target angle using a feedback loop.
    """
    # Try up to 10 ticks to align (usually takes 1-2)
    for _ in range(10):
        curr_angle = game.get_game_variable(vzd.GameVariable.ANGLE)
        diff = get_angle_diff(target_angle, curr_angle)
        
        # Tolerance check (Doom angles are floats, allow small error)
        if abs(diff) < 1.0:
            return

        # Apply turn. 
        # Note: In VizDoom, positive Delta usually turns Left (CCW).
        # Doom angles increase CCW (0->90). So Delta = diff works naturally.
        game.make_action([diff]) 
        
    # Final 'wait' to let the renderer catch up to the last input
    game.make_action([0])

def warp_silent(game, x, y):
    # We only warp position here. We handle angle separately.
    game.send_game_command(f"warp {x} {y}")
    # Wait for physics to settle (essential after warp)
    for _ in range(2): game.make_action([0])

def get_pos(game):
    return (game.get_game_variable(vzd.GameVariable.POSITION_X),
            game.get_game_variable(vzd.GameVariable.POSITION_Y))

def dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def capture_at_node(game, x, y):
    """Capture 4 angles at valid node."""
    # 1. Warp
    game.new_episode()
    warp_silent(game, x, y)
    
    # 2. Verify position
    curr_x, curr_y = get_pos(game)
    if dist((curr_x, curr_y), (x, y)) > 16.0:
        return False 

    count = 0
    for angle in ANGLES:
        # --- FIX 3: Use the new turning logic ---
        turn_to_angle(game, angle)
        
        # Wait 1 tic for the render buffer to update with the new angle
        game.make_action([0]) 
        
        state = game.get_state()
        if state and state.screen_buffer is not None:
            img = state.screen_buffer
            
            # CHW -> HWC
            if img.ndim == 3 and img.shape[0] == 3:
                img = img.transpose(1, 2, 0)
            
            # RGB -> BGR
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            p = ASSETS_DIR / f"doom_{x}_{y}_{angle}.webp"
            cv2.imwrite(str(p), img, [cv2.IMWRITE_WEBP_QUALITY, WEBP_QUALITY])
            count += 1
            
    return count > 0

def load_map_data():
    if not OUTPUT_JSON.exists(): return None
    with open(OUTPUT_JSON, "r") as f: return json.load(f)

def run_static_capture(game):
    ASSETS_DIR.mkdir(exist_ok=True)
    
    data = load_map_data()
    if not data:
        print("map_data.json missing!")
        return
        
    positions = data["positions"]
    total = len(positions)
    print(f"Starting Static Capture for {total} nodes...")
    
    captured = 0
    skipped = 0
    
    for i, (x, y) in enumerate(positions):
        # Optimization: Check if all 4 angles exist
        all_exist = True
        for ang in ANGLES:
            if not (ASSETS_DIR / f"doom_{x}_{y}_{ang}.webp").exists():
                all_exist = False
                break
        
        if all_exist:
            skipped += 1
            if i % 50 == 0: print(f"\rSkipping {i}/{total}...", end="")
            continue
            
        success = capture_at_node(game, x, y)
        if success:
            captured += 1
            
        if i % 10 == 0:
            print(f"\rCaptured: {captured} | Skipped: {skipped} | Progress: {i}/{total}", end="")
            
    print(f"\nCapture Complete. New: {captured}, Total Checked: {total}")

def main():
    if not WAD_PATH.exists():
        print("doom1.wad not found!")
        sys.exit(1)
        
    game = setup_game(WAD_PATH)
    try:
        run_static_capture(game)
        print("\nStatic Capture Complete.")
    finally:
        game.close()

if __name__ == "__main__":
    main()