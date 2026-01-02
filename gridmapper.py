"""
DOOM E1M1 Grid Scanner v8 (Clean & Fast)
- Wipes DISABLED via engine args (no tearing)
- HUD DISABLED
- Simple wait-and-capture (no complex stability loops)
- Fresh episodes for every capture to ensure clean state
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Set, Tuple
import numpy as np

try:
    import vizdoom as vzd
    import cv2
except ImportError:
    print("Missing dependencies!")
    sys.exit(1)

WAD_PATH = Path(__file__).parent / "doom1.wad"
ASSETS_DIR = Path(__file__).parent / "assets"
OUTPUT_JSON = Path(__file__).parent / "map_data.json"

# Conservative E1M1 bounds
X_MIN = 640
X_MAX = 1536
Y_MIN = -3712
Y_MAX = -2560

STEP_SIZE = 64
ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
JPEG_QUALITY = 85


def setup_game(wad_path: Path) -> vzd.DoomGame:
    game = vzd.DoomGame()
    game.set_doom_game_path(str(wad_path))
    game.set_doom_map("E1M1")
    game.set_screen_resolution(vzd.ScreenResolution.RES_640X480)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    
    # Hidden window, render all frames
    game.set_window_visible(False)
    game.set_render_all_frames(True)
    
    # NO HUD
    game.set_render_hud(False)
    game.set_render_minimal_hud(False)
    game.set_render_weapon(True)
    game.set_render_crosshair(False)
    game.set_render_messages(False)
    
    game.add_available_game_variable(vzd.GameVariable.POSITION_X)
    game.add_available_game_variable(vzd.GameVariable.POSITION_Y)
    game.add_available_button(vzd.Button.ATTACK)
    
    # CRITICAL: Disable wipes to prevent tearing/fading artifacts
    game.add_game_args("+sv_cheats 1 -nomp -nosound +wipescreen_start None +wipescreen_end None")
    
    game.set_doom_skill(3)
    game.init()
    return game


def get_position(game: vzd.DoomGame) -> Tuple[float, float]:
    return (game.get_game_variable(vzd.GameVariable.POSITION_X),
            game.get_game_variable(vzd.GameVariable.POSITION_Y))


def wait_frames(game: vzd.DoomGame, n: int):
    """Wait n frames."""
    for _ in range(n):
        if not game.is_episode_finished():
            game.make_action([0])


def warp_and_ready(game: vzd.DoomGame, x: int, y: int, angle: int, wait_time: int = 10):
    """Warp, rotate, and wait for render."""
    game.send_game_command(f"warp {x} {y}")
    # Short wait after warp
    wait_frames(game, 5)
    
    game.send_game_command(f"angle {angle}")
    # Wait for render to finish
    wait_frames(game, wait_time)


def capture_frame(game: vzd.DoomGame, filepath: Path) -> bool:
    state = game.get_state()
    if state and state.screen_buffer is not None:
        # Direct capture - no stability check needed if wipes are off
        img = cv2.cvtColor(state.screen_buffer, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(filepath), img, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        return True
    return False


def is_valid_view(game: vzd.DoomGame) -> bool:
    """Check if current view is valid (not void)."""
    state = game.get_state()
    if not state or state.screen_buffer is None:
        return False
        
    img = state.screen_buffer
    # Simple check: if image is too dark or uniform, it's likely void/bad
    if img.mean() < 10 or img.std() < 10:
        return False
    return True


def scan_and_capture(game: vzd.DoomGame) -> Set[Tuple[int, int]]:
    ASSETS_DIR.mkdir(exist_ok=True)
    
    x_range = list(range(X_MIN, X_MAX + 1, STEP_SIZE))
    y_range = list(range(Y_MIN, Y_MAX + 1, STEP_SIZE))
    total = len(x_range) * len(y_range)
    
    print(f"Scanning {total} positions...")
    
    valid = set()
    checked = 0
    screenshots = 0
    
    for x in x_range:
        for y in y_range:
            checked += 1
            
            # 1. Validation Check
            game.new_episode()
            wait_frames(game, 2) # Minimal wait since no wipe
            warp_and_ready(game, x, y, 90, wait_time=5)
            
            if is_valid_view(game):
                valid.add((x, y))
                
                # 2. Capture Angles
                for angle in ANGLES:
                    # -- Normal View --
                    game.new_episode()
                    wait_frames(game, 2)
                    warp_and_ready(game, x, y, angle, wait_time=15) # 15 frames to settle
                    
                    if capture_frame(game, ASSETS_DIR / f"doom_{x}_{y}_{angle}.jpg"):
                        screenshots += 1

            
            pct = checked / total * 100
            print(f"\r[{pct:5.1f}%] Valid: {len(valid)} | Captures: {screenshots}   ", end="")
    
    print()
    return valid


def main():
    if not WAD_PATH.exists():
        print("doom1.wad not found!")
        sys.exit(1)
    
    print("=" * 50)
    print("DOOM Grid Scanner v8 (No HUD, No Wipes)")
    print("=" * 50)
    
    game = setup_game(WAD_PATH)
    
    try:
        # Get actual spawn just for reference
        game.new_episode()
        wait_frames(game, 5)
        spawn = get_position(game)
        spawn_grid = (round(spawn[0]/STEP_SIZE)*STEP_SIZE, round(spawn[1]/STEP_SIZE)*STEP_SIZE)
        
        positions = scan_and_capture(game)
        
        map_data = {
            "positions": [list(p) for p in sorted(positions)],
            "step_size": STEP_SIZE,
            "angles": ANGLES,
            "spawn": {"x": int(spawn_grid[0]), "y": int(spawn_grid[1]), "angle": 90},
            "bounds": {"x_min": X_MIN, "x_max": X_MAX, "y_min": Y_MIN, "y_max": Y_MAX}
        }
        with open(OUTPUT_JSON, "w") as f:
            json.dump(map_data, f, indent=2)
            
    finally:
        game.close()

if __name__ == "__main__":
    main()
