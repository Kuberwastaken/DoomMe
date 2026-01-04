<h1 align="center">DoomMe: Running DOOM from a GitHub Readme</h1>

<p align="center">
<a href="menu/episode_1.md">
<img src="static/start-visual.gif" alt="Click to Play DOOM" width="640">
</a>
<br>
<sub><strong>Yes, this is literally the game. You can click it to start playing.</strong></sub>
</p>

<p align="center">
<img src="https://img.shields.io/static/v1?label=Kuberwastaken&message=DoomMe&color=black&logo=github" alt="Kuberwastaken - DoomMe">
<img src="https://img.shields.io/badge/version-5-black" alt="Version 5">
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-black" alt="License MIT"></a>
</p>

---

## What Is This?

**DoomMe** is Doom's E1M1 level running entirely inside GitHub's markdown viewer. Without using any javascript or a backend server, it's just **4,340 pre-rendered screenshots** linked together with hyperlinks.

Every position × every angle = a unique markdown file. Click a direction, load a new file. That's the whole "engine."

📖 **Full story**: [How I Made DOOM Run Inside a GitHub Readme](https://kuber.studio/blog/Projects/How-I-Made-DOOM-Run-Inside-a-GitHub-Readme)

---

## Gameplay

Here's some gameplay I captured locally

<p align="center">
<img src="static/gameplay-local.gif">
</p>


## Repo Structure

```
DoomMe/
├── assets/              # 4,340 WebP screenshots (doom_x_y_angle.webp)
├── game/                # 4,340 navigation markdown files
├── menu/                # Episode & difficulty selection screens
├── static/              # Banner GIF, map image, menu assets
├── linker.py            # Generates the markdown graph from map_data
├── gridmapper.py        # VizDoom capture script
├── omgi_mapper.py       # WAD parser using Omgifol
├── map_data.json        # Valid (x, y) coordinates for E1M1
└── README.md            # You are here
```

---

## How It Works (TL;DR)

1. **Parse the WAD** — `omgi_mapper.py` uses [Omgifol](https://github.com/devinacker/omgifol) to extract E1M1 geometry
2. **Generate the grid** — Point-in-Polygon filtering on a 64-unit grid → 1,085 valid spots  
3. **Capture screenshots** — `gridmapper.py` teleports a VizDoom agent to each spot, 4 angles each
4. **Link it all** — `linker.py` builds the navigation graph as interlinked `.md` files

## License

MIT - feel free to tweak around and play with the code
Feel free to raise issues and PRs too

## Credits

- ID Software for DOOM 1993 and the WAD file
- [Omgifol](https://github.com/devinacker/omgifol) - WAD parser
- [VizDoom](https://github.com/mwydmuch/VizDoom) - Doom AI
- [Ultimate DOOM Builder](https://github.com/UltimateDOOMBuilder/UltimateDOOMBuilder) - WAD editor

---

<p align="center">
  Made with &lt;3 by <a href="https://kuber.studio">Kuber Mehta</a>
</p>

