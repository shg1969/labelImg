### Deploy to PyPI

```
cd [ROOT]
sh build-tools/build-for-pypi.sh
```

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
