"""
DOOM README Explorer - Photographer Script
Captures screenshots from E1M1 at grid positions for all 4 cardinal directions.

Usage:
    python photographer.py [--explore] [--small]
    
    --explore   Explore mode: prints current position without saving (use to find boundaries)
    --small     Small grid mode: 3x3 positions for testing (36 screenshots)
"""

import os
import sys
import argparse
from pathlib import Path

try:
    import vizdoom as vzd
    import cv2
    import numpy as np
except ImportError:
    print("Missing dependencies! Run: pip install vizdoom opencv-python")
    sys.exit(1)

# =============================================================================
# CONFIGURATION - Adjust these values based on E1M1 exploration
# =============================================================================

# E1M1 Starting Room Approximate Boundaries (needs calibration!)
# These are estimates - use --explore mode to find actual boundaries
X_MIN = 1056
X_MAX = 1500
Y_MIN = -3600
Y_MAX = -3200

# Grid step size (Doom units, typical wall thickness is 64)
STEP_SIZE = 64

# Cardinal directions in Doom angles (0=East, 90=North, 180=West, 270=South)
ANGLES = [0, 90, 180, 270]

# Output settings
ASSETS_DIR = Path(__file__).parent / "assets"
WAD_PATH = Path(__file__).parent / "doom1.wad"

# Screen resolution for captures
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480


def setup_game(wad_path: Path, visible: bool = False) -> vzd.DoomGame:
    """Initialize VizDoom with E1M1 configuration."""
    game = vzd.DoomGame()
    
    # Set the path to doom1.wad
    game.set_doom_game_path(str(wad_path))
    
    # Load E1M1 (Episode 1, Map 1)
    game.set_doom_map("E1M1")
    
    # Screen settings
    game.set_screen_resolution(vzd.ScreenResolution.RES_640X480)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    
    # Window visibility (False for headless capture)
    game.set_window_visible(visible)
    
    # Disable HUD for cleaner screenshots
    game.set_render_hud(False)
    game.set_render_crosshair(False)
    game.set_render_weapon(True)  # Keep the weapon visible for authenticity
    game.set_render_messages(False)
    
    # Enable cheats (needed for warp command)
    game.add_game_args("+sv_cheats 1")
    
    # Set skill level (1=easiest, 5=nightmare)
    game.set_doom_skill(1)
    
    # We need to be able to read position for exploration mode
    game.add_available_game_variable(vzd.GameVariable.POSITION_X)
    game.add_available_game_variable(vzd.GameVariable.POSITION_Y)
    game.add_available_game_variable(vzd.GameVariable.POSITION_Z)
    game.add_available_game_variable(vzd.GameVariable.ANGLE)
    
    game.init()
    return game


def teleport_player(game: vzd.DoomGame, x: int, y: int, angle: int):
    """Teleport player to specified coordinates and angle."""
    # Warp to position
    game.send_game_command(f"warp {x} {y}")
    
    # Set angle (Doom uses 0-255 for angles internally, but console uses degrees)
    game.send_game_command(f"angle {angle}")
    
    # Wait a few tics for renderer to catch up
    for _ in range(5):
        game.advance_action(1)


def capture_screenshot(game: vzd.DoomGame, filename: Path):
    """Capture current screen and save as PNG."""
    state = game.get_state()
    if state is not None and state.screen_buffer is not None:
        # VizDoom returns (channels, height, width), OpenCV needs (height, width, channels)
        img = np.transpose(state.screen_buffer, (1, 2, 0))
        # Convert RGB to BGR for OpenCV
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(filename), img)
        return True
    return False


def get_player_position(game: vzd.DoomGame) -> tuple:
    """Get current player position and angle."""
    state = game.get_state()
    if state is not None:
        x = game.get_game_variable(vzd.GameVariable.POSITION_X)
        y = game.get_game_variable(vzd.GameVariable.POSITION_Y)
        z = game.get_game_variable(vzd.GameVariable.POSITION_Z)
        angle = game.get_game_variable(vzd.GameVariable.ANGLE)
        return (x, y, z, angle)
    return (0, 0, 0, 0)


def explore_mode(game: vzd.DoomGame):
    """Interactive exploration mode to find map boundaries."""
    print("\n=== EXPLORATION MODE ===")
    print("Walk around E1M1 and note the coordinates of room boundaries.")
    print("Press Ctrl+C to exit.\n")
    
    game.new_episode()
    
    # Enable movement controls
    game.add_available_button(vzd.Button.MOVE_FORWARD)
    game.add_available_button(vzd.Button.MOVE_BACKWARD)
    game.add_available_button(vzd.Button.TURN_LEFT)
    game.add_available_button(vzd.Button.TURN_RIGHT)
    game.add_available_button(vzd.Button.MOVE_LEFT)
    game.add_available_button(vzd.Button.MOVE_RIGHT)
    
    try:
        while not game.is_episode_finished():
            game.advance_action()
            x, y, z, angle = get_player_position(game)
            print(f"\rPosition: X={x:8.1f}  Y={y:8.1f}  Z={z:8.1f}  Angle={angle:6.1f}°", end="")
    except KeyboardInterrupt:
        print("\n\nExploration ended.")


def capture_grid(game: vzd.DoomGame, small_mode: bool = False):
    """Capture screenshots at all grid positions."""
    ASSETS_DIR.mkdir(exist_ok=True)
    
    if small_mode:
        # Small test grid: 3x3 positions
        x_range = range(X_MIN, X_MIN + 3 * STEP_SIZE, STEP_SIZE)
        y_range = range(Y_MIN, Y_MIN + 3 * STEP_SIZE, STEP_SIZE)
        print(f"Small mode: {3*3*len(ANGLES)} screenshots")
    else:
        # Full grid
        x_range = range(X_MIN, X_MAX + 1, STEP_SIZE)
        y_range = range(Y_MIN, Y_MAX + 1, STEP_SIZE)
        total = len(list(x_range)) * len(list(y_range)) * len(ANGLES)
        print(f"Full mode: {total} screenshots")
        # Recalculate ranges since range() objects are consumed
        x_range = range(X_MIN, X_MAX + 1, STEP_SIZE)
        y_range = range(Y_MIN, Y_MAX + 1, STEP_SIZE)
    
    captured = 0
    failed = 0
    
    for x in x_range:
        for y in list(y_range):  # Copy y_range for inner loop
            for angle in ANGLES:
                # Start fresh episode
                game.new_episode()
                
                # Teleport to position
                teleport_player(game, x, y, angle)
                
                # Generate filename
                filename = ASSETS_DIR / f"doom_{x}_{y}_{angle}.png"
                
                # Capture
                if capture_screenshot(game, filename):
                    captured += 1
                    print(f"\r[{captured}] Captured: {filename.name}", end="")
                else:
                    failed += 1
                    print(f"\n[!] Failed: {filename.name}")
        
        # Reset y_range for next x iteration
        if small_mode:
            y_range = range(Y_MIN, Y_MIN + 3 * STEP_SIZE, STEP_SIZE)
        else:
            y_range = range(Y_MIN, Y_MAX + 1, STEP_SIZE)
    
    print(f"\n\nCapture complete!")
    print(f"  Captured: {captured}")
    print(f"  Failed:   {failed}")
    print(f"  Output:   {ASSETS_DIR}")


def main():
    parser = argparse.ArgumentParser(description="DOOM E1M1 Screenshot Photographer")
    parser.add_argument("--explore", action="store_true", 
                        help="Exploration mode - walk around and print coordinates")
    parser.add_argument("--small", action="store_true",
                        help="Small grid mode - 3x3 test grid (36 screenshots)")
    parser.add_argument("--visible", action="store_true",
                        help="Show game window (slower but useful for debugging)")
    args = parser.parse_args()
    
    # Check for WAD file
    if not WAD_PATH.exists():
        print(f"Error: doom1.wad not found at {WAD_PATH}")
        print("Please place doom1.wad in the same directory as this script.")
        sys.exit(1)
    
    print(f"Loading DOOM from: {WAD_PATH}")
    print(f"Output directory:  {ASSETS_DIR}")
    print()
    
    game = setup_game(WAD_PATH, visible=args.visible or args.explore)
    
    try:
        if args.explore:
            explore_mode(game)
        else:
            capture_grid(game, small_mode=args.small)
    finally:
        game.close()


if __name__ == "__main__":
    main()
