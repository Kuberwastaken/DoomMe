"""
DOOM Menu Linker (Static/Hardcoded)
links manually placed images in static/ so we don't need opencv
"""

from pathlib import Path

MENU_DIR = Path(__file__).parent / "menu"
MENU_DIR.mkdir(exist_ok=True)

def make_link(target_md, label):
    return f'<a href="{target_md}">{label}</a>'

def generate_menus():
    print("Generating hardcoded menu markdown...")

    # 1. Episode Selection (1, 2, 3)
    # 1 -> Knee-Deep (Go to Difficulty)
    # 2 -> Shores (Error)
    # 3 -> Inferno (Error)
    
    episodes = [1, 2, 3]
    
    for i in episodes:
        lines = []
        # Image: static/1.png, static/2.png, etc.
        lines.append(f'<p align="center"><img src="../static/{i}.png" width="640"></p>\n')
        
        # Navigation logic
        # Up: i-1 (clamped)
        # Down: i+1 (clamped)
        # Enter: Logic depends on episode
        
        up_link = f"episode_{max(1, i-1)}.md"
        down_link = f"episode_{min(3, i+1)}.md"
        
        if i == 1:
            # Episode 1 -> Difficulty Select 1
            enter_target = "difficulty_1.md"
            enter_label = "SELECT"
        else:
            # Episode 2/3 -> Error Page
            enter_target = f"episode_{i}_error.md"
            enter_label = "LOCKED"
            
        lines.append('<p align="center">')
        lines.append(f'{make_link(up_link, "⬆️")} | {make_link(enter_target, enter_label)} | {make_link(down_link, "⬇️")}')
        lines.append('</p>')
        
        with open(MENU_DIR / f"episode_{i}.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # 2. Error Pages for Ep 2 & 3
    for i in [2, 3]:
        lines = []
        # Image: static/2-error.png
        lines.append(f'<p align="center"><img src="../static/{i}-error.png" width="640"></p>\n')
        lines.append('<p align="center">')
        lines.append(f'{make_link(f"episode_{i}.md", "BACK")}')
        lines.append('</p>')
        
        with open(MENU_DIR / f"episode_{i}_error.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # 3. Difficulty Selection (1-5)
    # All lead to game start spawn
    spawn_node = "../game/1024_-3584_90.md"
    
    for i in range(1, 6):
        lines = []
        # Image: static/1-1.png ... static/1-5.png
        lines.append(f'<p align="center"><img src="../static/1-{i}.png" width="640"></p>\n')
        
        up_link = f"difficulty_{max(1, i-1)}.md"
        down_link = f"difficulty_{min(5, i+1)}.md"
        
        lines.append('<p align="center">')
        lines.append(f'{make_link(up_link, "⬆️")} | {make_link(spawn_node, "SHOOT TO START")} | {make_link(down_link, "⬇️")}')
        lines.append('</p>')
        
        with open(MENU_DIR / f"difficulty_{i}.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
            
    print("Done. Menu structure updated.")

if __name__ == "__main__":
    generate_menus()
