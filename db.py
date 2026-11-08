import sqlite3
import os
from pathlib import Path

APP_DATA = Path(os.getenv("APPDATA", Path.home())) / "EmulatorHub"
APP_DATA.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DATA / "emulator_hub.db"

class Database:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS emulators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            system TEXT NOT NULL,
            exe_path TEXT DEFAULT '',
            rom_folder TEXT DEFAULT '',
            launch_args TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emulator_id INTEGER NOT NULL,
            system TEXT NOT NULL,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL UNIQUE,
            cover_path TEXT DEFAULT '',
            favorite INTEGER DEFAULT 0,
            FOREIGN KEY(emulator_id) REFERENCES emulators(id) ON DELETE CASCADE
        );
        """)
        self.conn.commit()

    def _dict(self, row):
        return dict(row) if row else None

    def emulators(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM emulators ORDER BY system, name")]

    def emulator(self, eid):
        return self._dict(self.conn.execute("SELECT * FROM emulators WHERE id=?", (eid,)).fetchone())

    def save_emulator(self, data, eid=None):
        vals = (data["name"], data["system"], data.get("exe_path",""), data.get("rom_folder",""), data.get("launch_args",""))
        if eid:
            self.conn.execute("UPDATE emulators SET name=?,system=?,exe_path=?,rom_folder=?,launch_args=? WHERE id=?", vals+(eid,))
        else:
            self.conn.execute("INSERT INTO emulators(name,system,exe_path,rom_folder,launch_args) VALUES(?,?,?,?,?)", vals)
        self.conn.commit()

    def delete_emulator(self, eid):
        self.conn.execute("DELETE FROM emulators WHERE id=?", (eid,)); self.conn.commit()

    def games(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM games ORDER BY title COLLATE NOCASE")]

    def upsert_game(self, g):
        self.conn.execute("""INSERT INTO games(emulator_id,system,title,file_path) VALUES(?,?,?,?)
        ON CONFLICT(file_path) DO UPDATE SET emulator_id=excluded.emulator_id, system=excluded.system, title=excluded.title""",
        (g["emulator_id"],g["system"],g["title"],g["file_path"]))
        self.conn.commit()

    def update_game(self, gid, **kwargs):
        allowed = {"cover_path","favorite"}
        fields = [(k,v) for k,v in kwargs.items() if k in allowed]
        if fields:
            sql = "UPDATE games SET " + ",".join(f"{k}=?" for k,_ in fields) + " WHERE id=?"
            self.conn.execute(sql, [v for _,v in fields]+[gid]); self.conn.commit()
