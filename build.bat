@echo off
python -m nuitka --onefile --standalone --output-dir=build --enable-console --deployment ^
    --output-filename=FastValveMaterial --quiet --assume-yes-for-downloads --enable-plugin=upx ^
    --include-data-file=./VTFLibWrapper/bin/VTFLib.x64.dll=./VTFLibWrapper/bin/VTFLib.x64.dll ^
    --include-data-file=./phongwarp_steel.vtf=./phongwarp_steel.vtf ^
    --onefile-tempdir-spec={TEMP}/FastValveMaterial ^
    --follow-imports --no-pyi-file ./FastValveMaterial.py
pause