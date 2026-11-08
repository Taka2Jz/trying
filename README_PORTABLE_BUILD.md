# Build the portable Windows EXE without installing Python on your PC

This project includes a GitHub Actions workflow that builds `EmulatorHub.exe` on a hosted Windows build machine. Python is installed only on that build machine, not on your PC.

## Steps
1. Sign in to GitHub and create a new empty repository.
2. Upload the contents of this project folder to the repository (including `.github/workflows/build-windows.yml`).
3. Open the repository's **Actions** tab.
4. Select **Build Emulator Hub for Windows**.
5. Click **Run workflow** and confirm.
6. When the run completes successfully, open it and download the artifact named `EmulatorHub-Windows-Portable`.
7. Extract the downloaded artifact and double-click `EmulatorHub.exe`.

## Important
- This creates a Windows x64 portable executable. It has not yet been built or tested in this environment.
- The EXE is unsigned, so Windows SmartScreen may show an unrecognized-app warning.
- App data is stored in `%APPDATA%\\EmulatorHub`, so settings and the game database persist between launches and are not written into PyInstaller's temporary extraction folder.
- The launcher itself does not include emulator software or game ROMs. Add the emulator executable and your own game folders in the app.
- The app's current per-console wallpaper selection is saved, but per-console visual switching is still a planned improvement.
