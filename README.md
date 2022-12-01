[![Releases](https://img.shields.io/github/downloads/marv7000/FastValveMaterial/total.svg)](https://github.com/marv7000/FastValveMaterial/releases) [![License](https://img.shields.io/github/license/marv7000/FastValveMaterial.svg)](https://github.com/marv7000/Tyrant/blob/master/LICENSE)
# FastValveMaterial
Convert PBR materials to VMT and VTF files that imitate PBR properties in Source engine games like Garry's Mod.
# Warning
The releases might be outdated, they are simply the latest commit at that time, packed together with VTFLibWrapper.
# Dependencies:
- pillow (PIL)
- numpy
- VTFLibWrapper (https://github.com/Ganonmaster/VTFLibWrapper)
# Setup:
- If you're using the release version, you don't need to do anything else
- On the other hand, when cloning the source, make sure to also pull and initialize VTFLibWrapper ("`git submodules init`" + "`git submodules update`")
- `pip install -r requirements.txt`
- You will need the following textures:
    - Diffuse/Color map
    - Normal map
    - Metalness map
    - Glossiness map (If you have a roughness map, set "Material Type" in config.md to "rough")
    - Optional: Ambient Occlusion map (If no image is given, the script defaults to a white image as the AO map)

1. Adjust config.md
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
- binary (.exe) build for windows
- rewrite textures finder
- move .vmt templates to separate files
- rewrite main function
- multithreading support
