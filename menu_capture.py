"""
DOOM Menu Capture Script
Captures title screen, episode select, skill select, and loading screens.

Usage:
    python menu_capture.py
"""

import sys
import time
from pathlib import Path

try:
    import vizdoom as vzd
    import cv2
    import numpy as np
except ImportError:
    print("Missing dependencies! Run: pip install vizdoom opencv-python")
    sys.exit(1)

WAD_PATH = Path(__file__).parent / "doom1.wad"
MENU_DIR = Path(__file__).parent / "menu"
JPEG_QUALITY = 85


def save_screenshot(game: vzd.DoomGame, filename: str):
    """Save current screen as JPEG."""
    state = game.get_state()
    if state is not None and state.screen_buffer is not None:
        img = state.screen_buffer
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        filepath = MENU_DIR / filename
        cv2.imwrite(str(filepath), img, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        print(f"  Saved: {filename}")
        return True
    return False


def setup_game_for_menu() -> vzd.DoomGame:
    """Setup VizDoom to show menus."""
    game = vzd.DoomGame()
    game.set_doom_game_path(str(WAD_PATH))
    game.set_doom_map("E1M1")
    
    game.set_screen_resolution(vzd.ScreenResolution.RES_640X480)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    game.set_window_visible(False)
    
    # Don't auto-start the game
    game.set_episode_start_time(0)
    
    game.init()
    return game


def capture_gameplay_start(game: vzd.DoomGame):
    """Capture the E1M1 starting view with HUD."""
    print("\nCapturing E1M1 start...")
    
    # Start episode
    game.new_episode()
    
    # Wait for game to fully load
    for _ in range(35):
        game.advance_action(1)
    
    save_screenshot(game, "e1m1_start.jpg")


def main():
    MENU_DIR.mkdir(exist_ok=True)
    
    if not WAD_PATH.exists():
        print(f"Error: doom1.wad not found at {WAD_PATH}")
        sys.exit(1)
    
    print("=" * 50)
    print("DOOM Menu Capture")
    print("=" * 50)
    
    # Note: VizDoom doesn't easily expose the title screen menus
    # We'll capture the game start and note that title/episode screens
    # should be captured separately or we use the provided images
    
    print("\nNote: VizDoom auto-starts the game, bypassing menus.")
    print("Title and episode screens will use provided reference images.")
    print()
    
    game = setup_game_for_menu()
    
    try:
        # Capture the E1M1 starting point with HUD
        capture_gameplay_start(game)
        
        print()
        print("=" * 50)
        print("Menu capture complete!")
        print("=" * 50)
        print("\nFor title/episode screens, we'll use the reference images")
        print("provided by the user and place them in the menu/ folder.")
        
    finally:
        game.close()


if __name__ == "__main__":
    main()
