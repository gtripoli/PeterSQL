#!/bin/bash

rm -rf build/

python -m compileall -b ./

pyinstaller --onefile --windowed --name petersql --add-data "icons:." --distpath dist/nix --workpath build/nix --additional-hooks-dir=./hooks main.py

rm *.spec
