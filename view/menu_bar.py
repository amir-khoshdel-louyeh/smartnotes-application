from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QMenuBar


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
        file_menu.addActions([print_action, export_pdf_action])
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

        find_action = QAction("Find / Replace...", self)
        find_action.setShortcut(QKeySequence.Find)

        edit_menu.addActions([self.undo_action, self.redo_action])
        edit_menu.addSeparator()
        edit_menu.addActions([self.cut_action, self.copy_action, self.paste_action, delete_action])
        edit_menu.addSeparator()
        edit_menu.addAction(select_all_action)
        edit_menu.addSeparator()
        edit_menu.addAction(find_action)

        # ---------------- AI Menu ----------------
        ai_menu = self.addMenu("&AI")
        summarize_action = QAction("Summarize Note", self)
        summarize_action.setShortcut("Ctrl+Alt+S")

        key_points_action = QAction("Extract Key Points", self)
        key_points_action.setShortcut("Ctrl+Alt+K")

        mind_map_action = QAction("Generate Mind Map", self)
        mind_map_action.setShortcut("Ctrl+Alt+M")

        export_mind_map_action = QAction("Export Mind Map PNG...", self)
        export_mind_map_action.setShortcut("Ctrl+Alt+E")

        study_plan_action = QAction("Create Study Plan...", self)
        study_plan_action.setShortcut("Ctrl+Alt+P")

        ai_menu.addActions([summarize_action, key_points_action, mind_map_action])
        ai_menu.addSeparator()
        ai_menu.addActions([export_mind_map_action, study_plan_action])

        # ---------------- View Menu ----------------
        view_menu = self.addMenu("&View")
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")

        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")

        fullscreen_action = QAction("Full Screen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.setCheckable(True)

        toggle_sidebar_action = QAction("Show Sidebar", self)
        toggle_sidebar_action.setShortcut("Ctrl+M")
        toggle_sidebar_action.setCheckable(True)
        toggle_sidebar_action.setChecked(True)

        toggle_statusbar_action = QAction("Show Status Bar", self)
        toggle_statusbar_action.setCheckable(True)
        toggle_statusbar_action.setChecked(True)

        preview_action = QAction("Markdown Preview", self)
        preview_action.setShortcut("Ctrl+Shift+M")
        preview_action.setCheckable(True)

        dark_mode_action = QAction("Dark Mode", self)
        dark_mode_action.setCheckable(True)

        view_menu.addActions([zoom_in_action, zoom_out_action, reset_zoom_action])
        view_menu.addSeparator()
        view_menu.addActions([fullscreen_action, toggle_sidebar_action, toggle_statusbar_action])
        view_menu.addAction(preview_action)
        view_menu.addSeparator()
        view_menu.addAction(dark_mode_action)

        # ---------------- Help Menu ----------------
        help_menu = self.addMenu("&Help")
        docs_action = QAction("Documentation", self)
        docs_action.setShortcut("F1")
        shortcuts_action = QAction("Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("Ctrl+/")
        check_updates_action = QAction("Check for Updates...", self)
        feedback_action = QAction("Send Feedback", self)
        about_action = QAction("About StudyMate", self)
        about_qt_action = QAction("About Qt", self)

        help_menu.addActions([docs_action, shortcuts_action, check_updates_action, feedback_action])
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
            "replace": find_action,
            "summarize": summarize_action,
            "key_points": key_points_action,
            "mind_map": mind_map_action,
            "export_mind_map": export_mind_map_action,
            "study_plan": study_plan_action,
            "zoom_in": zoom_in_action,
            "zoom_out": zoom_out_action,
            "reset_zoom": reset_zoom_action,
            "fullscreen": fullscreen_action,
            "toggle_sidebar": toggle_sidebar_action,
            "toggle_statusbar": toggle_statusbar_action,
            "preview": preview_action,
            "dark_mode": dark_mode_action,
            "docs": docs_action,
            "shortcuts": shortcuts_action,
            "check_updates": check_updates_action,
            "feedback": feedback_action,
            "about": about_action,
            "about_qt": about_qt_action,
        }
