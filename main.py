import sys
from pathlib import Path
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QStackedWidget, QFileDialog,
    QMessageBox, QLineEdit, QComboBox, QDialog, QFormLayout, QDialogButtonBox,
    QFrame, QScrollArea, QGridLayout, QSplitter, QMenu, QInputDialog
)
from db import Database
from scanner import scan_games
from settings import Settings
from pathlib import Path

APP_NAME = "Emulator Hub"

STYLE = """
* { font-family: 'Segoe UI'; }
QMainWindow, QWidget#root { background: #10141d; color: #e9edf5; }
QLabel { color: #e9edf5; }
QPushButton {
  background: #202a3a; color: #edf3ff; border: 1px solid #34435a;
  border-radius: 8px; padding: 9px 13px;
}
QPushButton:hover { background: #2b3b53; border-color: #5b8bd9; }
QPushButton#primary { background: #2878d0; border: 0; font-weight: 600; }
QPushButton#primary:hover { background: #398be5; }
QListWidget { background: #151c28; border: 0; padding: 8px; }
QListWidget::item { padding: 12px; border-radius: 7px; }
QListWidget::item:selected { background: #263c59; color: white; }
QLineEdit, QComboBox {
  background: #182231; color: #edf3ff; border: 1px solid #34435a;
  border-radius: 7px; padding: 9px;
}
QFrame#topbar { background: #151c28; border-bottom: 1px solid #293548; }
QFrame#card { background: rgba(25, 34, 49, 235); border: 1px solid #34435a; border-radius: 12px; }
QLabel#muted { color: #9ba9bd; }
QLabel#heading { font-size: 23px; font-weight: 700; }
QLabel#gameTitle { font-size: 14px; font-weight: 600; }
QScrollArea { border: 0; background: transparent; }
"""

class EmulatorDialog(QDialog):
    def __init__(self, parent=None, existing=None):
        super().__init__(parent)
        self.setWindowTitle("Add / Edit Emulator")
        self.setMinimumWidth(430)
        form = QFormLayout(self)
        self.name = QLineEdit()
        self.system = QComboBox()
        self.system.setEditable(True)
        self.system.addItems(["PS1", "PS2", "PSP", "PS3", "PS4", "PS5", "Nintendo DS",
                              "3DS", "GameCube / Wii", "Wii U", "Switch", "Arcade", "Other"])
        self.exe = QLineEdit()
        self.rom = QLineEdit()
        self.args = QLineEdit()
        self.args.setPlaceholderText('Optional, e.g. --fullscreen "{rom}"')
        browse_exe = QPushButton("Browse…")
        browse_rom = QPushButton("Browse…")
        row1 = QHBoxLayout(); row1.addWidget(self.exe); row1.addWidget(browse_exe)
        row2 = QHBoxLayout(); row2.addWidget(self.rom); row2.addWidget(browse_rom)
        browse_exe.clicked.connect(self.pick_exe)
        browse_rom.clicked.connect(self.pick_rom)
        form.addRow("Emulator name", self.name)
        form.addRow("Console / system", self.system)
        form.addRow("Emulator executable", row1)
        form.addRow("Games folder", row2)
        form.addRow("Launch arguments", self.args)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        if existing:
            self.name.setText(existing["name"])
            self.system.setCurrentText(existing["system"])
            self.exe.setText(existing["exe_path"])
            self.rom.setText(existing["rom_folder"])
            self.args.setText(existing.get("launch_args", ""))

    def pick_exe(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select emulator executable", "", "Programs (*.exe);;All files (*)")
        if p: self.exe.setText(p)

    def pick_rom(self):
        p = QFileDialog.getExistingDirectory(self, "Select games folder")
        if p: self.rom.setText(p)

    def data(self):
        return {"name": self.name.text().strip(), "system": self.system.currentText().strip(),
                "exe_path": self.exe.text().strip(), "rom_folder": self.rom.text().strip(),
                "launch_args": self.args.text().strip()}

class GameCard(QFrame):
    def __init__(self, game, launch_callback, cover_callback, favorite_callback):
        super().__init__()
        self.setObjectName("card")
        self.game = game
        self.setFixedSize(174, 250)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 9, 9, 9)
        layout.setSpacing(6)
        cover = QLabel()
        cover.setAlignment(Qt.AlignCenter)
        cover.setFixedSize(154, 174)
        cover.setStyleSheet("background:#202b3b;border-radius:7px;color:#8493a8;")
        path = game.get("cover_path") or ""
        pix = QPixmap(path) if path and Path(path).exists() else QPixmap()
        if not pix.isNull():
            cover.setPixmap(pix.scaled(154, 174, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            cover.setText("NO COVER")
        layout.addWidget(cover)
        title = QLabel(game["title"]); title.setObjectName("gameTitle")
        title.setWordWrap(True); title.setMaximumHeight(36)
        layout.addWidget(title)
        row = QHBoxLayout()
        play = QPushButton("▶ Play"); play.setObjectName("primary")
        play.clicked.connect(lambda: launch_callback(game))
        more = QPushButton("⋯"); more.setFixedWidth(38)
        menu = QMenu(more)
        a_cover = menu.addAction("Set cover…")
        a_fav = menu.addAction("Toggle favorite")
        a_cover.triggered.connect(lambda: cover_callback(game))
        a_fav.triggered.connect(lambda: favorite_callback(game))
        more.setMenu(menu)
        row.addWidget(play); row.addWidget(more)
        layout.addLayout(row)

class EmulatorHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.settings = Settings()
        self.setWindowTitle(APP_NAME)
        self.resize(1380, 850)
        self.setMinimumSize(1000, 650)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self.apply_wallpaper()
        self.refresh_all()

    def _build_ui(self):
        root = QWidget(); root.setObjectName("root")
        self.setCentralWidget(root)
        main = QHBoxLayout(root); main.setContentsMargins(0,0,0,0); main.setSpacing(0)

        sidebar = QWidget(); sidebar.setFixedWidth(218)
        side = QVBoxLayout(sidebar); side.setContentsMargins(16,22,16,16)
        logo = QLabel("EMULATOR HUB"); logo.setStyleSheet("font-size:18px;font-weight:800;letter-spacing:1px;color:#72a9f5;")
        side.addWidget(logo); side.addSpacing(22)
        self.nav = QListWidget()
        for name in ["Home", "My Library", "Emulators", "Favorites", "Personalization"]:
            self.nav.addItem(name)
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(self.change_page)
        side.addWidget(self.nav, 1)
        note = QLabel("WINDOWS 11 EDITION\\nVersion 1.0"); note.setObjectName("muted")
        side.addWidget(note)
        main.addWidget(sidebar)

        content = QWidget()
        c = QVBoxLayout(content); c.setContentsMargins(0,0,0,0); c.setSpacing(0)
        top = QFrame(); top.setObjectName("topbar")
        top_l = QHBoxLayout(top); top_l.setContentsMargins(22,12,22,12)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search your games…")
        self.search.textChanged.connect(self.refresh_library)
        top_l.addWidget(self.search, 1)
        self.window_btn = QPushButton("⛶ Fullscreen")
        self.window_btn.clicked.connect(self.toggle_fullscreen)
        top_l.addWidget(self.window_btn)
        c.addWidget(top)
        self.pages = QStackedWidget()
        self.home_page = self.make_home()
        self.library_page = self.make_library()
        self.emu_page = self.make_emulators()
        self.fav_page = self.make_favorites()
        self.personal_page = self.make_personalization()
        for p in [self.home_page,self.library_page,self.emu_page,self.fav_page,self.personal_page]:
            self.pages.addWidget(p)
        c.addWidget(self.pages, 1)
        main.addWidget(content, 1)

        fs = QAction("Toggle fullscreen", self)
        fs.setShortcut(QKeySequence("F11")); fs.triggered.connect(self.toggle_fullscreen)
        self.addAction(fs)
        esc = QAction("Exit fullscreen", self); esc.setShortcut(QKeySequence("Escape"))
        esc.triggered.connect(self.showNormal); self.addAction(esc)

    def make_home(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(28,26,28,26)
        title = QLabel("Welcome back"); title.setObjectName("heading")
        subtitle = QLabel("Your games, all in one place."); subtitle.setObjectName("muted")
        l.addWidget(title); l.addWidget(subtitle); l.addSpacing(18)
        row = QHBoxLayout()
        self.stat_games = QLabel("0\\nGAMES"); self.stat_emus = QLabel("0\\nEMULATORS")
        for w in [self.stat_games,self.stat_emus]:
            w.setObjectName("card"); w.setAlignment(Qt.AlignCenter); w.setMinimumHeight(95)
            w.setStyleSheet("background:#192231;border:1px solid #34435a;border-radius:10px;font-size:18px;font-weight:700;")
            row.addWidget(w)
        l.addLayout(row); l.addSpacing(22)
        l.addWidget(QLabel("Recently added"))
        self.recent_area = QScrollArea(); self.recent_area.setWidgetResizable(True)
        self.recent_widget = QWidget(); self.recent_grid = QGridLayout(self.recent_widget)
        self.recent_area.setWidget(self.recent_widget); l.addWidget(self.recent_area,1)
        return page

    def make_library(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(28,24,28,24)
        head = QHBoxLayout()
        title = QLabel("My Library"); title.setObjectName("heading")
        self.filter_system = QComboBox(); self.filter_system.addItem("All systems")
        self.filter_system.currentTextChanged.connect(self.on_library_filter_changed)
        head.addWidget(title); head.addStretch(); head.addWidget(QLabel("Filter:")); head.addWidget(self.filter_system)
        l.addLayout(head)
        self.library_scroll = QScrollArea(); self.library_scroll.setWidgetResizable(True)
        self.library_widget = QWidget(); self.library_grid = QGridLayout(self.library_widget)
        self.library_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft); self.library_grid.setSpacing(15)
        self.library_scroll.setWidget(self.library_widget); l.addWidget(self.library_scroll,1)
        return page

    def make_emulators(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(28,24,28,24)
        head = QHBoxLayout(); title = QLabel("Emulators"); title.setObjectName("heading")
        add = QPushButton("+ Add emulator"); add.setObjectName("primary"); add.clicked.connect(self.add_emulator)
        scan = QPushButton("↻ Scan games"); scan.clicked.connect(self.scan_all)
        head.addWidget(title); head.addStretch(); head.addWidget(scan); head.addWidget(add)
        l.addLayout(head)
        self.emu_list = QListWidget(); l.addWidget(self.emu_list,1)
        row = QHBoxLayout()
        edit = QPushButton("Edit selected"); edit.clicked.connect(self.edit_emulator)
        delete = QPushButton("Remove selected"); delete.clicked.connect(self.delete_emulator)
        row.addWidget(edit); row.addWidget(delete); row.addStretch(); l.addLayout(row)
        return page

    def make_favorites(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(28,24,28,24)
        title = QLabel("Favorites"); title.setObjectName("heading"); l.addWidget(title)
        self.fav_scroll = QScrollArea(); self.fav_scroll.setWidgetResizable(True)
        self.fav_widget = QWidget(); self.fav_grid = QGridLayout(self.fav_widget)
        self.fav_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.fav_scroll.setWidget(self.fav_widget); l.addWidget(self.fav_scroll,1)
        return page

    def make_personalization(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(28,24,28,24)
        title = QLabel("Personalization"); title.setObjectName("heading"); l.addWidget(title)
        desc = QLabel("Set one wallpaper for the whole launcher, or a different wallpaper for each console.")
        desc.setObjectName("muted"); desc.setWordWrap(True); l.addWidget(desc)
        global_row = QHBoxLayout()
        global_row.addWidget(QLabel("Global wallpaper"))
        b = QPushButton("Choose image…"); b.clicked.connect(self.choose_global_wallpaper)
        clear = QPushButton("Clear"); clear.clicked.connect(self.clear_global_wallpaper)
        global_row.addStretch(); global_row.addWidget(b); global_row.addWidget(clear)
        l.addLayout(global_row)
        console_row = QHBoxLayout()
        self.wall_system = QComboBox()
        self.wall_system.addItem("Choose console…")
        console_row.addWidget(QLabel("Console wallpaper")); console_row.addWidget(self.wall_system,1)
        choose = QPushButton("Choose image…"); choose.clicked.connect(self.choose_console_wallpaper)
        clear2 = QPushButton("Clear"); clear2.clicked.connect(self.clear_console_wallpaper)
        console_row.addWidget(choose); console_row.addWidget(clear2); l.addLayout(console_row)
        info = QLabel("Supported: JPG, PNG, WEBP. Wallpaper files are referenced from their original location. Keep them in place.")
        info.setObjectName("muted"); info.setWordWrap(True); l.addWidget(info)
        l.addSpacing(20)
        l.addWidget(QLabel("Display mode"))
        mode_row = QHBoxLayout()
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["Windowed", "Fullscreen"])
        self.mode_combo.setCurrentText("Fullscreen" if self.settings.get("start_fullscreen", False) else "Windowed")
        save_mode = QPushButton("Save startup mode")
        save_mode.clicked.connect(self.save_startup_mode)
        mode_row.addWidget(self.mode_combo); mode_row.addWidget(save_mode); mode_row.addStretch()
        l.addLayout(mode_row); l.addStretch()
        return page

    def change_page(self, index):
        self.pages.setCurrentIndex(index)
        self.apply_wallpaper()
        if index == 1: self.refresh_library()
        if index == 2: self.refresh_emulators()
        if index == 3: self.refresh_favorites()
        if index == 4: self.refresh_wallpaper_lists()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

    def refresh_all(self):
        self.refresh_emulators()
        self.refresh_library()
        self.refresh_favorites()
        self.refresh_home()
        self.refresh_wallpaper_lists()

    def refresh_home(self):
        games = self.db.games()
        emus = self.db.emulators()
        self.stat_games.setText(f"{len(games)}\\nGAMES")
        self.stat_emus.setText(f"{len(emus)}\\nEMULATORS")
        self.clear_layout(self.recent_grid)
        for i, game in enumerate(games[:8]):
            card = GameCard(game, self.launch_game, self.set_cover, self.toggle_favorite)
            self.recent_grid.addWidget(card, i//4, i%4)

    def add_cards(self, layout, games):
        self.clear_layout(layout)
        for i, game in enumerate(games):
            card = GameCard(game, self.launch_game, self.set_cover, self.toggle_favorite)
            layout.addWidget(card, i//5, i%5)

    def on_library_filter_changed(self, *_):
        self.refresh_library()
        self.apply_wallpaper()

    def refresh_library(self, *_):
        if not hasattr(self, "library_grid"): return
        systems = ["All systems"] + sorted({e["system"] for e in self.db.emulators()})
        current = self.filter_system.currentText() if self.filter_system.count() else "All systems"
        self.filter_system.blockSignals(True); self.filter_system.clear(); self.filter_system.addItems(systems)
        self.filter_system.setCurrentText(current if current in systems else "All systems")
        self.filter_system.blockSignals(False)
        query = self.search.text().lower().strip()
        system = self.filter_system.currentText()
        games = [g for g in self.db.games() if query in g["title"].lower() and (system == "All systems" or g["system"] == system)]
        self.add_cards(self.library_grid, games)

    def refresh_favorites(self):
        if hasattr(self, "fav_grid"):
            self.add_cards(self.fav_grid, [g for g in self.db.games() if g["favorite"]])

    def refresh_emulators(self):
        if not hasattr(self, "emu_list"): return
        self.emu_list.clear()
        for e in self.db.emulators():
            item = QListWidgetItem(f'{e["name"]}   •   {e["system"]}\\n{e["rom_folder"] or "No games folder set"}')
            item.setData(Qt.UserRole, e["id"]); self.emu_list.addItem(item)

    def add_emulator(self):
        d = EmulatorDialog(self)
        if d.exec() == QDialog.Accepted:
            data = d.data()
            if not data["name"]:
                QMessageBox.warning(self, "Missing name", "Please enter an emulator name."); return
            self.db.save_emulator(data)
            self.refresh_all()

    def selected_emulator(self):
        item = self.emu_list.currentItem()
        return self.db.emulator(item.data(Qt.UserRole)) if item else None

    def edit_emulator(self):
        e = self.selected_emulator()
        if not e: return
        d = EmulatorDialog(self, e)
        if d.exec() == QDialog.Accepted:
            self.db.save_emulator(d.data(), e["id"]); self.refresh_all()

    def delete_emulator(self):
        e = self.selected_emulator()
        if not e: return
        if QMessageBox.question(self, "Remove emulator", f'Remove {e["name"]}? Games already scanned will remain in the library.') == QMessageBox.Yes:
            self.db.delete_emulator(e["id"]); self.refresh_all()

    def scan_all(self):
        emus = self.db.emulators()
        total = 0
        for e in emus:
            if e["rom_folder"] and Path(e["rom_folder"]).is_dir():
                found = scan_games(e["rom_folder"], e["system"], e["id"])
                for g in found:
                    self.db.upsert_game(g)
                total += len(found)
        self.refresh_all()
        QMessageBox.information(self, "Scan complete", f"Scan finished. {total} supported game files found.")

    def launch_game(self, game):
        emu = self.db.emulator(game["emulator_id"])
        if not emu:
            QMessageBox.warning(self, "Emulator missing", "Configure an emulator for this game first."); return
        exe = emu["exe_path"]
        if not exe or not Path(exe).exists():
            QMessageBox.warning(self, "Emulator not found", "Open Emulators and set a valid emulator .exe path."); return
        import subprocess, shlex
        args = [exe]
        custom = emu.get("launch_args", "")
        if custom:
            # {rom} is replaced by the selected game path; split args with Windows-friendly quoting.
            import os
            custom = custom.replace("{rom}", game["file_path"])
            args.extend(shlex.split(custom, posix=False))
        elif game["file_path"]:
            args.append(game["file_path"])
        try:
            subprocess.Popen(args, cwd=str(Path(exe).parent))
        except Exception as ex:
            QMessageBox.critical(self, "Launch failed", str(ex))

    def set_cover(self, game):
        p, _ = QFileDialog.getOpenFileName(self, "Choose game cover", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if p:
            self.db.update_game(game["id"], cover_path=p); self.refresh_all()

    def toggle_favorite(self, game):
        self.db.update_game(game["id"], favorite=0 if game["favorite"] else 1)
        self.refresh_all()

    def refresh_wallpaper_lists(self):
        if not hasattr(self, "wall_system"): return
        current = self.wall_system.currentText()
        systems = sorted({e["system"] for e in self.db.emulators()})
        self.wall_system.clear(); self.wall_system.addItem("Choose console…"); self.wall_system.addItems(systems)
        if current in systems: self.wall_system.setCurrentText(current)

    def choose_global_wallpaper(self):
        p, _ = QFileDialog.getOpenFileName(self, "Choose global wallpaper", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if p:
            self.settings.set("global_wallpaper", p); self.apply_wallpaper()

    def clear_global_wallpaper(self):
        self.settings.set("global_wallpaper", ""); self.apply_wallpaper()

    def choose_console_wallpaper(self):
        system = self.wall_system.currentText()
        if system == "Choose console…":
            QMessageBox.information(self, "Choose console", "Select a console first."); return
        p, _ = QFileDialog.getOpenFileName(self, "Choose console wallpaper", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if p:
            mapping = self.settings.get("console_wallpapers", {})
            mapping[system] = p; self.settings.set("console_wallpapers", mapping)
            QMessageBox.information(self, "Saved", f"Wallpaper saved for {system}.")
            self.apply_wallpaper()

    def clear_console_wallpaper(self):
        system = self.wall_system.currentText()
        mapping = self.settings.get("console_wallpapers", {})
        mapping.pop(system, None); self.settings.set("console_wallpapers", mapping)
        self.apply_wallpaper()

    def apply_wallpaper(self):
        p = self.settings.get("global_wallpaper", "")
        # In My Library, use the selected console's wallpaper when a specific
        # console filter is active; otherwise fall back to the global image.
        if hasattr(self, "pages") and self.pages.currentIndex() == 1 and hasattr(self, "filter_system"):
            system = self.filter_system.currentText()
            if system and system != "All systems":
                p = self.settings.get("console_wallpapers", {}).get(system, p)
        if p and Path(p).exists():
            safe_path = p.replace("\\", "/").replace("'", "\\'")
            self.centralWidget().setStyleSheet(f"QWidget#root {{ border-image: url('{safe_path}') 0 0 0 0 stretch stretch; }}")
        else:
            self.centralWidget().setStyleSheet("")

    def save_startup_mode(self):
        self.settings.set("start_fullscreen", self.mode_combo.currentText() == "Fullscreen")
        QMessageBox.information(self, "Saved", "Startup display preference saved.")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal(); self.window_btn.setText("⛶ Fullscreen")
        else:
            self.showFullScreen(); self.window_btn.setText("▣ Windowed")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    w = EmulatorHub()
    if w.settings.get("start_fullscreen", False): w.showFullScreen()
    else: w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
