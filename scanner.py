from pathlib import Path

# Add/remove extensions to match the formats supported by your emulators.
SUPPORTED_EXTENSIONS = {
    ".iso", ".cso", ".chd", ".cue", ".bin", ".img", ".pbp", ".elf",
    ".gcm", ".gcz", ".wbfs", ".wud", ".wux", ".nsp", ".xci",
    ".nes", ".sfc", ".smc", ".gba", ".gbc", ".gb", ".nds", ".3ds",
    ".zip", ".7z", ".wad"
}

def scan_games(folder, system, emulator_id):
    base = Path(folder)
    results = []
    try:
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                results.append({
                    "emulator_id": emulator_id,
                    "system": system,
                    "title": p.stem.replace("_", " ").replace(".", " "),
                    "file_path": str(p.resolve())
                })
    except (PermissionError, OSError):
        pass
    return results
