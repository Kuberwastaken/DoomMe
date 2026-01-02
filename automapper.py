"""
DOOM README Explorer - Auto-Mapper Script
Automatically discovers all valid walkable positions in E1M1 using flood-fill exploration.

Usage:
    python automapper.py
    
This script will:
1. Start at the player spawn
2. Try moving in all directions
3. Record positions where movement succeeds
4. Recursively explore until all reachable positions are found
5. Save coordinates to a JSON file
6. Optionally capture screenshots at each position
"""

import os
import sys
import json
import time
from pathlib import Path
from collections import deque
from typing import Set, Tuple, Dict, List

try:
    import vizdoom as vzd
    import cv2
    import numpy as np
except ImportError:
    print("Missing dependencies! Run: pip install vizdoom opencv-python")
    sys.exit(1)

# =============================================================================
# CONFIGURATION
# =============================================================================

WAD_PATH = Path(__file__).parent / "doom1.wad"
ASSETS_DIR = Path(__file__).parent / "assets"
OUTPUT_JSON = Path(__file__).parent / "map_data.json"

# Grid step size (Doom units)
STEP_SIZE = 64

# Angles to capture (cardinal directions)
ANGLES = [0, 90, 180, 270]

# Movement tolerance - positions within this range are considered "same"
POSITION_TOLERANCE = 32

# Screen resolution
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Movement actions for VizDoom
MOVE_SPEED = 50  # How many tics to move


def setup_game(wad_path: Path) -> vzd.DoomGame:
    """Initialize VizDoom for E1M1."""
    game = vzd.DoomGame()
    
    game.set_doom_game_path(str(wad_path))
    game.set_doom_map("E1M1")
    
    game.set_screen_resolution(vzd.ScreenResolution.RES_640X480)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    game.set_window_visible(False)
    
    game.set_render_hud(False)
    game.set_render_crosshair(False)
    game.set_render_weapon(True)
    game.set_render_messages(False)
    
    # Enable position tracking
    game.add_available_game_variable(vzd.GameVariable.POSITION_X)
    game.add_available_game_variable(vzd.GameVariable.POSITION_Y)
    game.add_available_game_variable(vzd.GameVariable.POSITION_Z)
    game.add_available_game_variable(vzd.GameVariable.ANGLE)
    
    # Add movement buttons
    game.add_available_button(vzd.Button.MOVE_FORWARD)
    game.add_available_button(vzd.Button.MOVE_BACKWARD)
    game.add_available_button(vzd.Button.MOVE_LEFT)
    game.add_available_button(vzd.Button.MOVE_RIGHT)
    game.add_available_button(vzd.Button.TURN_LEFT)
    game.add_available_button(vzd.Button.TURN_RIGHT)
    
    # Cheats for warping
    game.add_game_args("+sv_cheats 1")
    game.set_doom_skill(1)
    
    game.init()
    return game


def get_position(game: vzd.DoomGame) -> Tuple[float, float]:
    """Get current player position."""
    x = game.get_game_variable(vzd.GameVariable.POSITION_X)
    y = game.get_game_variable(vzd.GameVariable.POSITION_Y)
    return (x, y)


def snap_to_grid(x: float, y: float) -> Tuple[int, int]:
    """Snap coordinates to nearest grid position."""
    grid_x = round(x / STEP_SIZE) * STEP_SIZE
    grid_y = round(y / STEP_SIZE) * STEP_SIZE
    return (int(grid_x), int(grid_y))


def warp_to(game: vzd.DoomGame, x: int, y: int):
    """Warp player to specific coordinates."""
    game.send_game_command(f"warp {x} {y}")
    # Wait for movement to complete
    for _ in range(10):
        game.advance_action(1)


def try_move(game: vzd.DoomGame, direction: str) -> Tuple[float, float]:
    """
    Try to move in a direction and return new position.
    Direction: 'north', 'south', 'east', 'west'
    """
    # First, face the direction
    angle_map = {'east': 0, 'north': 90, 'west': 180, 'south': 270}
    target_angle = angle_map.get(direction, 0)
    
    game.send_game_command(f"angle {target_angle}")
    for _ in range(5):
        game.advance_action(1)
    
    # Now move forward
    action = [1, 0, 0, 0, 0, 0]  # MOVE_FORWARD
    game.make_action(action, MOVE_SPEED)
    
    return get_position(game)


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate distance between two points."""
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5


def explore_map(game: vzd.DoomGame) -> Set[Tuple[int, int]]:
    """
    Flood-fill exploration to find all reachable grid positions.
    Returns set of (x, y) grid coordinates.
    """
    game.new_episode()
    
    # Wait for game to start
    for _ in range(35):
        game.advance_action(1)
    
    # Get starting position
    start_pos = get_position(game)
    start_grid = snap_to_grid(*start_pos)
    
    print(f"Starting position: {start_pos}")
    print(f"Starting grid: {start_grid}")
    print()
    
    # BFS exploration
    visited: Set[Tuple[int, int]] = set()
    to_explore: deque = deque([start_grid])
    
    directions = ['north', 'south', 'east', 'west']
    direction_deltas = {
        'east': (STEP_SIZE, 0),
        'north': (0, STEP_SIZE),
        'west': (-STEP_SIZE, 0),
        'south': (0, -STEP_SIZE)
    }
    
    while to_explore:
        current = to_explore.popleft()
        
        if current in visited:
            continue
        
        visited.add(current)
        print(f"\rExploring: {current} | Found: {len(visited)} positions", end="")
        
        # Warp to current position
        game.new_episode()
        for _ in range(10):
            game.advance_action(1)
        
        warp_to(game, current[0], current[1])
        
        actual_pos = get_position(game)
        # Check if we actually got there (not blocked)
        if distance(actual_pos, current) > POSITION_TOLERANCE:
            # Couldn't reach this position, skip it
            visited.discard(current)
            continue
        
        # Try moving in each direction
        for direction in directions:
            dx, dy = direction_deltas[direction]
            target = (current[0] + dx, current[1] + dy)
            
            if target in visited:
                continue
            
            # Warp back to current position
            warp_to(game, current[0], current[1])
            for _ in range(5):
                game.advance_action(1)
            
            # Try to move
            old_pos = get_position(game)
            new_pos = try_move(game, direction)
            
            # Check if we actually moved
            move_distance = distance(old_pos, new_pos)
            
            if move_distance > STEP_SIZE * 0.3:  # Moved at least 30% of step
                # Snap new position to grid
                new_grid = snap_to_grid(*new_pos)
                
                if new_grid not in visited and new_grid not in to_explore:
                    to_explore.append(new_grid)
    
    print()
    return visited


def capture_all_positions(game: vzd.DoomGame, positions: Set[Tuple[int, int]]):
    """Capture screenshots at all positions and angles."""
    ASSETS_DIR.mkdir(exist_ok=True)
    
    total = len(positions) * len(ANGLES)
    captured = 0
    
    print(f"Capturing {total} screenshots...")
    
    for x, y in sorted(positions):
        for angle in ANGLES:
            game.new_episode()
            for _ in range(10):
                game.advance_action(1)
            
            # Warp to position
            warp_to(game, x, y)
            
            # Set angle
            game.send_game_command(f"angle {angle}")
            for _ in range(10):
                game.advance_action(1)
            
            # Capture
            state = game.get_state()
            if state is not None and state.screen_buffer is not None:
                # RGB24 format gives (height, width, channels) - no transpose needed
                img = state.screen_buffer
                # Convert RGB to BGR for OpenCV
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                filename = ASSETS_DIR / f"doom_{x}_{y}_{angle}.png"
                cv2.imwrite(str(filename), img)
                captured += 1
                
            print(f"\r[{captured}/{total}] Capturing...", end="")
    
    print(f"\nCapture complete! {captured} screenshots saved to {ASSETS_DIR}")


def main():
    if not WAD_PATH.exists():
        print(f"Error: doom1.wad not found at {WAD_PATH}")
        sys.exit(1)
    
    print("=" * 50)
    print("DOOM E1M1 Auto-Mapper")
    print("=" * 50)
    print(f"WAD: {WAD_PATH}")
    print(f"Grid step: {STEP_SIZE} units")
    print()
    
    game = setup_game(WAD_PATH)
    
    try:
        # Phase 1: Explore map
        print("Phase 1: Exploring map...")
        print("-" * 30)
        positions = explore_map(game)
        
        print()
        print(f"Found {len(positions)} valid grid positions!")
        
        # Calculate bounds
        if positions:
            x_vals = [p[0] for p in positions]
            y_vals = [p[1] for p in positions]
            print(f"X range: {min(x_vals)} to {max(x_vals)}")
            print(f"Y range: {min(y_vals)} to {max(y_vals)}")
        
        # Save map data
        map_data = {
            "positions": list(positions),
            "step_size": STEP_SIZE,
            "angles": ANGLES,
            "bounds": {
                "x_min": min(x_vals) if positions else 0,
                "x_max": max(x_vals) if positions else 0,
                "y_min": min(y_vals) if positions else 0,
                "y_max": max(y_vals) if positions else 0,
            }
        }
        
        with open(OUTPUT_JSON, "w") as f:
            json.dump(map_data, f, indent=2)
        print(f"Map data saved to: {OUTPUT_JSON}")
        
        # Phase 2: Capture screenshots
        print()
        print("Phase 2: Capturing screenshots...")
        print("-" * 30)
        capture_all_positions(game, positions)
        
        print()
        print("=" * 50)
        print("Auto-mapping complete!")
        print(f"Now run: python linker.py")
        print("=" * 50)
        
    finally:
        game.close()


if __name__ == "__main__":
    main()
