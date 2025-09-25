from PyQt5.QtWidgets import QMenuBar, QAction
from PyQt5.QtGui import QKeySequence


class MenuBar(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_menus()

    def init_menus(self):
        # ---------------- File Menu ----------------
        file_menu = self.addMenu("&File")
        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.New)

        open_action = QAction("Open...", self)
        open_action.setShortcut(QKeySequence.Open)

        recent_files_menu = file_menu.addMenu("Open Recent")

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.Save)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)

        print_action = QAction("Print...", self)
        print_action.setShortcut(QKeySequence.Print)

        export_pdf_action = QAction("Export PDF...", self)

        close_action = QAction("Close", self)
        close_action.setShortcut(QKeySequence("Ctrl+W"))

        close_all_action = QAction("Close All", self)
        close_all_action.setShortcut("Ctrl+Shift+W")

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)

        file_menu.addActions([new_action, open_action])
        file_menu.addMenu(recent_files_menu)
        file_menu.addSeparator()
        file_menu.addActions([save_action, save_as_action])
        file_menu.addSeparator()
        file_menu.addAction(print_action)
        file_menu.addAction(export_pdf_action)
        file_menu.addSeparator()
        file_menu.addActions([close_action, close_all_action])
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # ---------------- Edit Menu ----------------
        edit_menu = self.addMenu("&Edit")
        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence.Undo)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")

        self.cut_action = QAction("Cut", self)
        self.cut_action.setShortcut(QKeySequence.Cut)

        self.copy_action = QAction("Copy", self)
        self.copy_action.setShortcut(QKeySequence.Copy)

        self.paste_action = QAction("Paste", self)
        self.paste_action.setShortcut(QKeySequence.Paste)

        delete_action = QAction("Delete", self)
        delete_action.setShortcut("Del")

        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)

        replace_action = QAction("Find...", self)
        replace_action.setShortcut(QKeySequence.Replace)

        edit_menu.addActions([self.undo_action, self.redo_action])
        edit_menu.addSeparator()
        edit_menu.addActions([self.cut_action, self.copy_action, self.paste_action, delete_action])
        edit_menu.addSeparator()
        edit_menu.addAction(select_all_action)
        edit_menu.addSeparator()
        edit_menu.addAction(replace_action)

        # ---------------- View Menu ----------------
        view_menu = self.addMenu("&View")
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")

        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")

        fullscreen_action = QAction("Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.setCheckable(True)

        toggle_sidebar_action = QAction("Toggle Sidebar", self)
        toggle_sidebar_action.setShortcut("Ctrl+M")
        toggle_sidebar_action.setCheckable(True)

        toggle_statusbar_action = QAction("Toggle Status Bar", self)
        toggle_statusbar_action.setCheckable(True)

        dark_mode_action = QAction("Dark Mode", self)
        dark_mode_action.setCheckable(True)

        view_menu.addActions([zoom_in_action, zoom_out_action, reset_zoom_action])
        view_menu.addSeparator()
        view_menu.addActions([fullscreen_action, toggle_sidebar_action, toggle_statusbar_action])
        view_menu.addSeparator()
        view_menu.addAction(dark_mode_action)

        # ---------------- Help Menu ----------------
        help_menu = self.addMenu("&Help")
        docs_action = QAction("Documentation", self)
        check_updates_action = QAction("Check for Updates...", self)
        feedback_action = QAction("Send Feedback", self)
        about_action = QAction("About", self)
        about_qt_action = QAction("About Qt", self)

        help_menu.addActions([docs_action, check_updates_action, feedback_action])
        help_menu.addSeparator()
        help_menu.addActions([about_action, about_qt_action])

        # ---------------- Store actions ----------------
        self.actions = {
            "new": new_action,
            "open": open_action,
            "recent_files_menu": recent_files_menu,
            "save": save_action,
            "save_as": save_as_action,
            "print": print_action,
            "export_pdf": export_pdf_action,
            "close": close_action,
            "close_all": close_all_action,
            "exit": exit_action,
            "undo": self.undo_action,
            "redo": self.redo_action,
            "cut": self.cut_action,
            "copy": self.copy_action,
            "paste": self.paste_action,
            "select_all": select_all_action,
            "replace": replace_action,
            "zoom_in": zoom_in_action,
            "zoom_out": zoom_out_action,
            "reset_zoom": reset_zoom_action,
            "fullscreen": fullscreen_action,
            "toggle_sidebar": toggle_sidebar_action,
            "toggle_statusbar": toggle_statusbar_action,
            "dark_mode": dark_mode_action,
            "docs": docs_action,
            "check_updates": check_updates_action,
            "feedback": feedback_action,
            "about": about_action,
            "about_qt": about_qt_action
        }
