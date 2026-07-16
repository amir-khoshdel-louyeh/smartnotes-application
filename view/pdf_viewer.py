from contextlib import suppress

import fitz  # PyMuPDF
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class PdfViewer(QWidget):
    """Displays PDF pages as images with navigation and zoom controls."""

    MIN_ZOOM = 0.25
    MAX_ZOOM = 5.0

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_pdf_viewer = True  # Flag to identify this widget type
        self.is_temporary_file = False  # Flag for converted files
        self.zoom_factor = 1.0
        self.current_page = 0
        self._auto_fitted = False

        self.document = None
        try:
            self.document = fitz.open(self.file_path)
        except Exception as e:
            self.setup_error_ui(f"Failed to load PDF: {e}")
            return

        self.setup_ui()
        self.render_page()

    def setup_error_ui(self, message):
        layout = QVBoxLayout(self)
        error_label = QLabel(message)
        error_label.setWordWrap(True)
        error_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(error_label)

    def setup_ui(self):
        # --- Image display ---
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        # --- Navigation controls ---
        self.nav_bar = QFrame()
        self.nav_bar.setObjectName("PdfNavBar")
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(10, 6, 10, 6)
        nav_layout.setSpacing(6)

        self.prev_button = QPushButton("Previous")
        self.prev_button.setObjectName("Ghost")
        self.prev_button.setToolTip("Previous page (Page Up)")
        self.next_button = QPushButton("Next")
        self.next_button.setObjectName("Ghost")
        self.next_button.setToolTip("Next page (Page Down)")

        self.page_input = QSpinBox()
        self.page_input.setRange(1, self.document.page_count)
        self.page_input.setFixedWidth(64)
        self.page_input.setToolTip("Jump to page")
        self.page_label = QLabel(f"/ {self.document.page_count}")
        self.page_label.setObjectName("Hint")

        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setObjectName("IconButton")
        self.zoom_in_button.setFixedSize(26, 26)
        self.zoom_in_button.setToolTip("Zoom in (Ctrl + wheel)")
        self.zoom_out_button = QPushButton("−")
        self.zoom_out_button.setObjectName("IconButton")
        self.zoom_out_button.setFixedSize(26, 26)
        self.zoom_out_button.setToolTip("Zoom out (Ctrl + wheel)")
        self.zoom_reset_button = QPushButton("Reset")
        self.zoom_reset_button.setObjectName("Ghost")
        self.zoom_reset_button.setToolTip("Reset zoom (Ctrl+0)")
        self.fit_width_button = QPushButton("Fit width")
        self.fit_width_button.setObjectName("Ghost")
        self.zoom_label = QLabel()
        self.zoom_label.setObjectName("Hint")
        self.zoom_label.setMinimumWidth(74)

        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addSpacing(8)
        nav_layout.addWidget(QLabel("Page"))
        nav_layout.addWidget(self.page_input)
        nav_layout.addWidget(self.page_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self.zoom_label)
        nav_layout.addWidget(self.zoom_out_button)
        nav_layout.addWidget(self.zoom_in_button)
        nav_layout.addWidget(self.zoom_reset_button)
        nav_layout.addWidget(self.fit_width_button)

        # --- Connect signals ---
        self.page_input.valueChanged.connect(self.jump_to_page)
        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.next_button.clicked.connect(self.go_to_next_page)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_reset_button.clicked.connect(self.reset_zoom)
        self.fit_width_button.clicked.connect(self.fit_to_width)

        # --- Main layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.nav_bar)
        main_layout.addWidget(self.scroll_area)

        self.setFocusPolicy(Qt.StrongFocus)

    def render_page(self):
        if self.document is None:
            return
        if self.current_page < 0:
            self.current_page = 0
        self.current_page = min(self.current_page, self.document.page_count - 1)

        page = self.document.load_page(self.current_page)
        matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        image = QImage(
            pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888
        ).copy()
        self.image_label.setPixmap(QPixmap.fromImage(image))

        # Update UI elements
        self.page_input.blockSignals(True)
        self.page_input.setValue(self.current_page + 1)
        self.page_input.blockSignals(False)

        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.document.page_count - 1)
        self.zoom_label.setText(f"Zoom: {self.zoom_factor:.0%}")

    def jump_to_page(self, page_num):
        self.current_page = page_num - 1
        self.render_page()

    def go_to_previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def go_to_next_page(self):
        if self.current_page < self.document.page_count - 1:
            self.current_page += 1
            self.render_page()

    def _set_zoom(self, factor):
        self.zoom_factor = max(self.MIN_ZOOM, min(self.MAX_ZOOM, factor))
        self.render_page()

    def zoom_in(self):
        self._set_zoom(self.zoom_factor * 1.2)

    def zoom_out(self):
        self._set_zoom(self.zoom_factor / 1.2)

    def reset_zoom(self):
        self._set_zoom(1.0)

    def fit_to_width(self):
        if self.document is None:
            return
        page = self.document.load_page(self.current_page)
        page_width = page.rect.width
        scroll_area_width = self.scroll_area.viewport().width()
        if scroll_area_width <= 1:
            return
        self.zoom_factor = max(
            self.MIN_ZOOM, min(self.MAX_ZOOM, scroll_area_width / page_width)
        )
        self.render_page()
        self._auto_fitted = True

    def showEvent(self, event):
        super().showEvent(event)
        if not self._auto_fitted:
            QTimer.singleShot(60, self.fit_to_width)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_PageDown, Qt.Key_Right, Qt.Key_Space):
            self.go_to_next_page()
            return
        if event.key() in (Qt.Key_PageUp, Qt.Key_Left):
            self.go_to_previous_page()
            return
        if event.key() == Qt.Key_Home:
            self.current_page = 0
            self.render_page()
            return
        if event.key() == Qt.Key_End:
            self.current_page = self.document.page_count - 1
            self.render_page()
            return
        if event.modifiers() & Qt.ControlModifier:
            if event.key() in (Qt.Key_Plus, Qt.Key_Equal):
                self.zoom_in()
                return
            if event.key() == Qt.Key_Minus:
                self.zoom_out()
                return
            if event.key() == Qt.Key_0:
                self.reset_zoom()
                return
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)

    def cleanup(self):
        """Explicit cleanup for FileHandler.removeTab path where closeEvent isn't sent."""
        if getattr(self, "document", None) is not None:
            with suppress(Exception):
                self.document.close()
            self.document = None
