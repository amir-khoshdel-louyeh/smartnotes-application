import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

from view.icons import app_icon
from view.main_window import MainWindow


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("StudyMate")
    app.setApplicationDisplayName("StudyMate")
    app.setOrganizationName("StudyMate")
    app.setWindowIcon(app_icon())
    # Fusion renders the stylesheet consistently across platforms.
    app.setStyle("Fusion")

    base_font = QFont(app.font())
    base_font.setPointSize(10)
    app.setFont(base_font)

    window = MainWindow()
    if window.maximized_on_close:
        window.showMaximized()
    else:
        window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
