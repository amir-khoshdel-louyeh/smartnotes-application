from PyQt5.QtWidgets import QMenuBar, QAction
from PyQt5.QtGui import QKeySequence

class MenuBar(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_menus()

    def init_menus(self):
        # File Menu
        file_menu = self.addMenu("&File")
        open_action = QAction("Open File", self)
        open_action.setShortcut(QKeySequence.Open)
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_as_action = QAction("Save As", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        export_pdf_action = QAction("Export PDF", self)
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(export_pdf_action)
        file_menu.addSeparator()

        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = self.addMenu("&Edit")
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        cut_action = QAction("Cut", self)
        cut_action.setShortcut(QKeySequence.Cut)
        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(cut_action)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)
        # View Menu
        view_menu = self.addMenu("&View")
        toggle_sidebar = QAction("Toggle Sidebar", self)
        toggle_sidebar.setShortcut("Ctrl+M")
        view_menu.addAction(toggle_sidebar)

        # Help Menu
        help_menu = self.addMenu("Help")
        about_action = QAction("About", self)
        help_menu.addAction(about_action)

        # Store actions for connecting signals in MainWindow
        self.open_action = open_action
        self.save_action = save_action
        self.save_as_action = save_as_action
        self.exit_action = exit_action
        self.undo_action = undo_action
        self.redo_action = redo_action
        self.cut_action = cut_action
        self.copy_action = copy_action
        self.paste_action = paste_action
        self.toggle_sidebar_action = toggle_sidebar

    def get_action(self, action_name):
        if action_name == "Open File":
            return self.open_action
        elif action_name == "Save":
            return self.save_action
        elif action_name == "Save As":
            return self.save_as_action
        elif action_name == "Copy":
            return self.copy_action
        elif action_name == "Cut":
            return self.cut_action
        else:
            return None


    def create_action(self, text, shortcut, triggered):
        action = QAction(text, self)
        action.setShortcut(shortcut)
        action.triggered.connect(triggered)
        return action
