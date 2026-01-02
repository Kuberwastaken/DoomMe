"""
Debug script to understand floor heights and void detection
"""
import vizdoom as vzd
from pathlib import Path

WAD_PATH = Path(__file__).parent / "doom1.wad"

def main():
    game = vzd.DoomGame()
    game.set_doom_game_path(str(WAD_PATH))
    game.set_doom_map("E1M1")
    game.set_screen_resolution(vzd.ScreenResolution.RES_320X240)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    game.set_window_visible(False)
    
    game.add_available_game_variable(vzd.GameVariable.POSITION_X)
    game.add_available_game_variable(vzd.GameVariable.POSITION_Y)
    game.add_available_game_variable(vzd.GameVariable.POSITION_Z)
    
    game.add_game_args("+sv_cheats 1")
    game.init()
    
    # Test warping to valid and void positions
    test_positions = [
        (1056, -3616, "Spawn (valid)"),
        (1024, -3584, "Near spawn (should be valid)"),
        (1024, -3200, "Further north (should be valid)"),
        (500, -3500, "Far west (likely void)"),
        (2000, -3500, "Far east (likely void)"),
        (1024, -2500, "Far north (may be void)"),
    ]
    
    print("Testing positions (Z height = floor/void indicator):\n")
    
    for x, y, desc in test_positions:
        game.new_episode()
        for _ in range(10):
            game.advance_action(1)
        
        game.send_game_command(f"warp {x} {y}")
        for _ in range(10):
            game.advance_action(1)
        
        actual_x = game.get_game_variable(vzd.GameVariable.POSITION_X)
        actual_y = game.get_game_variable(vzd.GameVariable.POSITION_Y)
        actual_z = game.get_game_variable(vzd.GameVariable.POSITION_Z)
        
        # Check if position matches (could indicate blocked/void)
        dist = ((actual_x - x)**2 + (actual_y - y)**2)**0.5
        
        print(f"{desc}")
        print(f"  Target:  ({x}, {y})")
        print(f"  Actual:  ({actual_x:.0f}, {actual_y:.0f}, Z={actual_z:.0f})")
        print(f"  Dist:    {dist:.1f}")
        print()
    
    game.close()

if __name__ == "__main__":
    main()
