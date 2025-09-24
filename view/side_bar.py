from PyQt5.QtWidgets import QDockWidget, QTabWidget, QWidget, QVBoxLayout, QLabel, QStyle, QPushButton
from PyQt5.QtGui import QIcon

class SideBar(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(" ", parent) # Title is removed as tabs have titles
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.setMovable(True)

        # Get standard icons
        style = self.style()
        self.settings_icon = QIcon(style.standardPixmap(QStyle.SP_FileDialogDetailedView))
        ai_icon = QIcon(style.standardPixmap(QStyle.SP_ComputerIcon))
        scheduler_icon = QIcon(style.standardPixmap(QStyle.SP_DialogYesButton))

        # Settings Tab
        self.init_settings_tab()

        # AI Tab
        self.ai_tab = QWidget()
        self.tabs.addTab(self.ai_tab, ai_icon, "AI")

        # Scheduler Tab
        self.scheduler_tab = QWidget()
        self.tabs.addTab(self.scheduler_tab, scheduler_icon, "Scheduler")

        self.setWidget(self.tabs)

    def init_settings_tab(self):
        self.settings_tab = QWidget()
        layout = QVBoxLayout()
        self.theme_button = QPushButton("Toggle Theme")
        layout.addWidget(self.theme_button)
        layout.addStretch() # Pushes the button to the top
        self.settings_tab.setLayout(layout)
        self.tabs.addTab(self.settings_tab, self.settings_icon, "Settings")
