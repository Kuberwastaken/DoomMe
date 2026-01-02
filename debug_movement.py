"""
Debug script to understand movement behavior
"""
import vizdoom as vzd
import math
from pathlib import Path

WAD_PATH = Path(__file__).parent / "doom1.wad"
STEP_SIZE = 64

def main():
    game = vzd.DoomGame()
    game.set_doom_game_path(str(WAD_PATH))
    game.set_doom_map("E1M1")
    game.set_screen_resolution(vzd.ScreenResolution.RES_640X480)
    game.set_screen_format(vzd.ScreenFormat.RGB24)
    game.set_window_visible(False)
    
    game.add_available_game_variable(vzd.GameVariable.POSITION_X)
    game.add_available_game_variable(vzd.GameVariable.POSITION_Y)
    game.add_available_game_variable(vzd.GameVariable.ANGLE)
    
    game.add_available_button(vzd.Button.MOVE_FORWARD)
    game.add_game_args("+sv_cheats 1")
    game.set_doom_skill(3)
    game.init()
    
    game.new_episode()
    for _ in range(35):
        game.advance_action(1)
    
    x = game.get_game_variable(vzd.GameVariable.POSITION_X)
    y = game.get_game_variable(vzd.GameVariable.POSITION_Y)
    print(f"Start: ({x:.1f}, {y:.1f})")
    
    # Try moving north (angle 90)
    game.send_game_command("angle 90")
    for _ in range(10):
        game.advance_action(1)
    
    print(f"\nAttempting to move NORTH from ({x:.1f}, {y:.1f})")
    print(f"Expected target: ({x:.1f}, {y + STEP_SIZE:.1f})")
    
    old_x = game.get_game_variable(vzd.GameVariable.POSITION_X)
    old_y = game.get_game_variable(vzd.GameVariable.POSITION_Y)
    
    # Move forward with different tic counts
    for tics in [20, 30, 40, 50, 60, 80]:
        game.new_episode()
        for _ in range(35):
            game.advance_action(1)
        
        game.send_game_command(f"warp {x} {y}")
        for _ in range(5):
            game.advance_action(1)
        game.send_game_command("angle 90")
        for _ in range(10):
            game.advance_action(1)
        
        for _ in range(tics):
            game.make_action([1])  # MOVE_FORWARD
        
        new_x = game.get_game_variable(vzd.GameVariable.POSITION_X)
        new_y = game.get_game_variable(vzd.GameVariable.POSITION_Y)
        
        dist = math.sqrt((new_x - x)**2 + (new_y - y)**2)
        target_y = y + STEP_SIZE
        dist_to_target = abs(new_y - target_y)
        
        print(f"  {tics} tics: moved to ({new_x:.1f}, {new_y:.1f}) | distance={dist:.1f} | to_target={dist_to_target:.1f}")
    
    game.close()

if __name__ == "__main__":
    main()
