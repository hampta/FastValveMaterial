[![Releases](https://img.shields.io/github/downloads/hampta/FastValveMaterial/total.svg)](https://github.com/hampta/FastValveMaterial/releases) 
[![wakatime](https://wakatime.com/badge/user/018ccf89-9b87-4916-8fba-bce250de562d/project/018d95d6-9e3b-45d9-a2b2-1ebed8471d4d.svg)](https://wakatime.com/badge/user/018ccf89-9b87-4916-8fba-bce250de562d/project/018d95d6-9e3b-45d9-a2b2-1ebed8471d4d)
[![License](https://img.shields.io/github/license/hampta/FastValveMaterial.svg)](https://github.com/hampta/Tyrant/blob/master/LICENSE)

# FastValveMaterial
Convert PBR materials to VMT and VTF files that imitate PBR properties in Source engine games like Garry's Mod.

# Dependencies:
- pillow (PIL)
- VTFLibWrapper (https://github.com/Ganonmaster/VTFLibWrapper)

# Usage:
- Download the latest release from the [Releases](https://github.com/hampta/FastValveMaterial/releases) tab
- Extract to a folder
- Change the settings in `config.ini`
- Run `FastValveMaterial.exe`

# Use arguments:
- `-c` or `--config` - Config file to use
- `-i` or `--input` - Input folder to use
- `-o` or `--output` - Output folder to use
- `-t` or `--threads` - Thread count to use
- `-d` or `--debug` - Enable debug messages
- `-f` or `--fast-export` - Enable fast export (no compression)
- `-e` or `--export` - Export images
- `-h` or `--help` - Show help message

# Usage from source (or linux):
- If you're using the release version, you don't need to do anything else
- On the other hand, when cloning the source, make sure to also pull and initialize VTFLibWrapper ("`git submodules init`" + "`git submodules update`")
- `pip install -r requirements.txt`
- You will need the following textures:
    - Diffuse/Color map
    - Normal map
    - Metalness map
    - Glossiness map (If you have a roughness map, set "Material Type" in `config.ini` to "rough")
    - Optional: Ambient Occlusion map (If no image is given, the script defaults to a white image as the AO map)

1. Adjust config.ini
2. Drop all texture files into your input folder
3. Run `FastValveMaterial.py`

## CMD
```
git clone https://github.com/hampta/FastValveMaterial
cd FastValveMaterial
git submodules init
git submodules update
pip install -r requirements.txt
python FastValveMaterial.py
```

# Notes and Troubleshooting:
- Make sure your images are in RGBA8888 format. While the script can understand many different color formats, if you're getting errors, check if this is the case.

# Examples:
- With FVM: ![1](https://user-images.githubusercontent.com/35012873/162594134-72cd6f11-e309-4090-a5e3-12a7582e2d9a.png)
- Witout FVM: ![2](https://user-images.githubusercontent.com/35012873/162594203-b2ca89f8-4806-4ac1-b5cd-b733b4d54ab6.png)

# TODO
- texture maps presets in `config.ini` (your metallic is in the alpha channel of the normal map, and roughness is in the alpha channel of the diffuse or any other “format”. So that you can make a preset for certain formats and use them without separating them in a photo editor)
- ~~binary (.exe) build for windows~~
- ~~rewrite textures finder~~
- ~~rewrite main function~~
- ~~multithreading support~~
