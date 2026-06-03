import sys
import types
from unittest.mock import MagicMock

def _ensure_fake_qt():
    try:
        import PyQt5.QtCore  # noqa: F401
        import PyQt5.QtGui  # noqa: F401
        import PyQt5.QtWidgets  # noqa: F401
        return  # real Qt available
    except Exception:
        pass

    # Create top-level PyQt5 package if missing
    if "PyQt5" not in sys.modules:
        sys.modules["PyQt5"] = types.ModuleType("PyQt5")

    # --- QtCore ---
    if "PyQt5.QtCore" not in sys.modules:
        fake_core = types.ModuleType("PyQt5.QtCore")
        fake_core.QObject = object
        fake_core.QRunnable = object
        fake_core.QDir = MagicMock()
        class FakeQt:
            Checked = 2
            Unchecked = 0
            AlignCenter = 0
            Horizontal = 1
        fake_core.Qt = FakeQt()
        class FakeQStandardPaths:
            AppDataLocation = 0
            @staticmethod
            def writableLocation(_):
                return ""
        fake_core.QStandardPaths = FakeQStandardPaths
        fake_core.pyqtSignal = lambda *a, **kw: MagicMock()
        # also provide pyqtSignal as MagicMock class for isinstance checks
        fake_core.pyqtSignal = MagicMock  # will be called as pyqtSignal(str)
        # but need it to be callable returning a mock with emit
        def _signal(*a, **kw):
            m = MagicMock()
            m.emit = MagicMock()
            return m
        fake_core.pyqtSignal = _signal
        fake_core.QUrl = MagicMock
        sys.modules["PyQt5.QtCore"] = fake_core
        sys.modules["PyQt5"].QtCore = fake_core
    else:
        fake_core = sys.modules["PyQt5.QtCore"]
        # ensure needed attrs
        if not hasattr(fake_core, "QObject"):
            fake_core.QObject = object
        if not hasattr(fake_core, "QRunnable"):
            fake_core.QRunnable = object
        if not hasattr(fake_core, "pyqtSignal"):
            fake_core.pyqtSignal = lambda *a, **kw: MagicMock()

    # --- QtGui ---
    if "PyQt5.QtGui" not in sys.modules:
        fake_gui = types.ModuleType("PyQt5.QtGui")
        fake_gui.QPixmap = MagicMock
        fake_gui.QIcon = MagicMock
        fake_gui.QFont = MagicMock
        fake_gui.QTextOption = MagicMock()
        fake_gui.QTextOption.WordWrap = 1
        fake_gui.QTextOption.NoWrap = 0
        fake_gui.QDesktopServices = MagicMock()
        fake_gui.QTextDocument = MagicMock()
        fake_gui.QTextCursor = MagicMock()
        fake_gui.QKeySequence = MagicMock
        fake_gui.QImage = MagicMock
        sys.modules["PyQt5.QtGui"] = fake_gui
        sys.modules["PyQt5"].QtGui = fake_gui

    # --- QtWidgets ---
    if "PyQt5.QtWidgets" not in sys.modules:
        fake_widgets = types.ModuleType("PyQt5.QtWidgets")
        class FakeQWidget:
            def __init__(self, *a, **kw): pass
        class FakeQLineEdit(FakeQWidget): pass
        class FakeQPushButton(FakeQWidget): pass
        class FakeQListWidget(FakeQWidget): 
            def __init__(self, *a, **kw): super().__init__(*a, **kw); self.clear = MagicMock()
        class FakeQListWidgetItem:
            def __init__(self, *a, **kw): pass
        class FakeQVBoxLayout:
            def __init__(self, *a, **kw): pass
        class FakeQHBoxLayout:
            def __init__(self, *a, **kw): pass
        class FakeQMessageBox:
            Yes = 1; No = 2; Save=1; Discard=2; Cancel=3
            @staticmethod
            def question(*a, **kw): return FakeQMessageBox.No
            @staticmethod
            def warning(*a, **kw): return None
            @staticmethod
            def information(*a, **kw): return None
            @staticmethod
            def critical(*a, **kw): return None
            @staticmethod
            def about(*a, **kw): return None
        fake_widgets.QWidget = FakeQWidget
        fake_widgets.QMainWindow = FakeQWidget
        fake_widgets.QDockWidget = FakeQWidget
        fake_widgets.QTabWidget = FakeQWidget
        fake_widgets.QVBoxLayout = FakeQVBoxLayout
        fake_widgets.QHBoxLayout = FakeQHBoxLayout
        fake_widgets.QLineEdit = FakeQLineEdit
        fake_widgets.QPushButton = FakeQPushButton
        fake_widgets.QListWidget = FakeQListWidget
        fake_widgets.QListWidgetItem = FakeQListWidgetItem
        fake_widgets.QMessageBox = FakeQMessageBox
        fake_widgets.QApplication = MagicMock
        fake_widgets.QFileDialog = MagicMock
        fake_widgets.QLabel = MagicMock
        fake_widgets.QCheckBox = MagicMock
        fake_widgets.QComboBox = MagicMock
        fake_widgets.QTextEdit = MagicMock
        fake_widgets.QFormLayout = MagicMock
        fake_widgets.QFontComboBox = MagicMock
        fake_widgets.QSpinBox = MagicMock
        fake_widgets.QGroupBox = MagicMock
        fake_widgets.QTreeView = MagicMock
        fake_widgets.QFileSystemModel = MagicMock
        fake_widgets.QStackedWidget = MagicMock
        fake_widgets.QToolBar = MagicMock
        fake_widgets.QAction = MagicMock
        fake_widgets.QStyle = MagicMock
        fake_widgets.QScrollArea = MagicMock
        fake_widgets.QSpinBox = MagicMock
        sys.modules["PyQt5.QtWidgets"] = fake_widgets
        sys.modules["PyQt5"].QtWidgets = fake_widgets

    # --- QtPrintSupport ---
    if "PyQt5.QtPrintSupport" not in sys.modules:
        fake_print = types.ModuleType("PyQt5.QtPrintSupport")
        fake_print.QPrinter = MagicMock
        sys.modules["PyQt5.QtPrintSupport"] = fake_print

    # --- view.task_widget stub if needed ---
    if "view.task_widget" not in sys.modules:
        fake_task = types.ModuleType("view.task_widget")
        class FakeTaskWidget:
            def __init__(self, *a, **kw): pass
        fake_task.TaskWidget = FakeTaskWidget
        sys.modules["view.task_widget"] = fake_task

_ensure_fake_qt()
