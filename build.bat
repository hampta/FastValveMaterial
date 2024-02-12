@echo off
python -m nuitka --onefile --standalone --output-dir=build --enable-console ^
    --output-filename=FastValveMaterial --quiet --assume-yes-for-downloads --enable-plugin=upx ^
    --include-data-file=./VTFLibWrapper/bin/VTFLib.x64.dll=./VTFLibWrapper/bin/VTFLib.x64.dll ^
    --follow-imports --no-pyi-file ./FastValveMaterial.py
pause