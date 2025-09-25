import fitz  # PyMuPDF
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QScrollArea, QSizePolicy, QSpinBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

class PdfViewer(QWidget):
    """
    A widget for displaying PDF files.
    It renders pages as images and provides navigation and zoom controls.
    """
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_pdf_viewer = True  # Flag to identify this widget type
        self.is_temporary_file = False # Flag for converted files
        self.zoom_factor = 1.0
        self.current_page = 0

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
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setWordWrap(True)
        layout.addWidget(error_label)

    def setup_ui(self):
        # --- Image Display ---
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.image_label)

        # --- Navigation Controls ---
        self.nav_bar = QWidget()
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(8, 5, 8, 5)

        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.page_input = QSpinBox()
        self.page_input.setRange(1, self.document.page_count)
        self.page_label = QLabel(f"/ {self.document.page_count}")
        
        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_reset_button = QPushButton("Reset Zoom")
        self.fit_width_button = QPushButton("Fit Width")
        self.zoom_label = QLabel()

        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(QLabel("Page:"))
        nav_layout.addWidget(self.page_input)
        nav_layout.addWidget(self.page_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self.zoom_label)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.zoom_out_button)
        nav_layout.addWidget(self.zoom_in_button)
        nav_layout.addWidget(self.zoom_reset_button)
        nav_layout.addWidget(self.fit_width_button)

        # --- Connect Signals ---
        self.page_input.valueChanged.connect(self.jump_to_page)
        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.next_button.clicked.connect(self.go_to_next_page)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_reset_button.clicked.connect(self.reset_zoom)
        self.fit_width_button.clicked.connect(self.fit_to_width)

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.nav_bar)
        main_layout.addWidget(self.scroll_area)

    def render_page(self):
        page = self.document.load_page(self.current_page)
        mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=mat)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.image_label.setPixmap(pixmap)

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

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.render_page()

    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.render_page()

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.render_page()

    def fit_to_width(self):
        page = self.document.load_page(self.current_page)
        page_width = page.rect.width
        scroll_area_width = self.scroll_area.width() - 2 * self.scroll_area.frameWidth()
        # Subtract scrollbar width if visible
        if self.scroll_area.verticalScrollBar().isVisible():
            scroll_area_width -= self.scroll_area.verticalScrollBar().width()
        self.zoom_factor = scroll_area_width / page_width
        self.render_page()

    def closeEvent(self, event):
        self.document.close()
        super().closeEvent(event)