# Emulator Hub — Windows 11

A starter desktop launcher built with Python, PySide6 and SQLite.

## Features in this starter
- Steam-inspired dark interface
- Windowed and fullscreen modes (F11 toggles; Esc exits fullscreen)
- Global wallpaper selection
- Per-console wallpaper preferences stored in settings
- Emulator profiles (name, console, executable, games folder, optional launch arguments)
- Recursive scan of common ROM/game file extensions
- Manual game cover assignment
- Favorites, search and system filtering
- One-click launch through the configured emulator

## Requirements
- Windows 10/11
- Python 3.10+ (Python 3.11 or 3.12 recommended)
- Internet connection for first-time PySide6 installation

## Run
1. Extract this ZIP to a normal folder, e.g. `C:\\EmulatorHub`.
2. Install Python and make sure the Python launcher `py` is available.
3. Double-click `run_windows.bat`.
4. Open **Emulators → Add emulator**.
5. Enter an emulator name, choose its console, browse to its `.exe`, and choose the folder containing games.
6. Press **Scan games**.
7. Use **My Library** and click **Play**.

## Launch arguments
Leave arguments empty for the common case where the emulator accepts the ROM path as its first argument.
If your emulator needs custom arguments, use `{rom}` as the placeholder for the game path.
Example:
`--fullscreen "{rom}"`

The argument parser uses Windows-friendly splitting, but emulator-specific command-line syntax can differ. Test with one game first.

## Wallpaper notes
- Global wallpaper is applied to the app background.
- Console wallpaper paths are saved separately by system for the next personalization iteration. The current starter saves these per-console choices; the console-specific visual switching is not yet wired into each page.
- Keep selected wallpaper files in their original locations.

## Data files
- `emulator_hub.db`: emulator profiles and game library
- `settings.json`: wallpaper paths and startup display preference

Back up these two files to preserve your setup.

## Important limitations of version 1.0 starter
- Game scanning is extension-based. It does not yet fetch artwork automatically from online databases.
- Manual cover import is supported from each game card's `⋯` menu.
- Console-specific wallpapers are saved, but automatic page-level application is a planned next step.
- Some emulators require special command-line arguments or a specific ROM format. Configure and test each emulator individually.
- This is a starter project, not a signed installer. Windows SmartScreen may show a warning for a locally built unsigned EXE.


## Portable EXE without Python on your PC
See `README_PORTABLE_BUILD.md` for the GitHub Actions Windows build route. Python is used on the hosted build runner only; your PC only receives the portable EXE.
