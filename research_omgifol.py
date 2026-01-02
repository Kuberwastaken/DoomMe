from omg import WAD, MapEditor

print("Loading WAD...")
w = WAD()
w.from_file("doom1.wad")
print(f"Loaded WAD: {w}")

print("\nSeeking E1M1...")
map_name = "E1M1"

if map_name in w.maps:
    print(f"Found {map_name}, initializing MapEditor...")
    # MapEditor takes the NameGroup usually
    editor = MapEditor(w.maps[map_name])
    
    print(f"Vertexes: {len(editor.vertexes)}")
    print(f"Linedefs: {len(editor.linedefs)}")
    print(f"Sectors: {len(editor.sectors)}")
    print(f"Things: {len(editor.things)}")
    
    if len(editor.sectors) > 0:
        s = editor.sectors[0]
        # Inspect sector object
        print(f"Sector 0 type: {type(s)}")
        print(f"Sector 0 dir: {dir(s)}")
        # Try attributes
        print(f"Floor/Ceil: {s.z_floor}/{s.z_ceil} Texture: {s.tx_floor}")
else:
    print(f"{map_name} not found.")
