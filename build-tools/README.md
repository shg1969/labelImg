### Deploy to PyPI

```
cd [ROOT]
make pip_upload          # Linux / macOS
python setup.py upload   # Windows (no make)
```

This rebuilds the sdist/wheel, uploads it with `twine` and pushes the version
tag. See `UploadCommand` in `setup.py`. Requires `twine` (`pip install twine`).

### Build a Windows EXE natively (recommended)

Produces a single, double-clickable `dist/labelImg.exe`. Requires Python 3 with
PyQt5 and lxml; PyInstaller is installed automatically when missing.

```
python build-tools/build_windows_exe.py
```

Optional flags:

* `--console`  keep the console window (handy for troubleshooting startup errors)
* `--onedir`   build a folder instead of a single file (faster startup)
* `--no-clean` keep the previous `build/` and `dist/`

### Build for macOS High Sierra
```
cd build-tools
./build-for-macos.sh
```
