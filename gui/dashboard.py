"""
Main application window — Smart Image Filters Studio.
Layout: Left sidebar (filters) | Center (image viewer) | Right (info + histogram)
"""
import cv2
import numpy as np
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QPushButton, QFileDialog, QStatusBar, QFrame,
    QSizePolicy, QScrollArea, QAction, QToolBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QSize
from PyQt5.QtGui import QPixmap, QFont, QDragEnterEvent, QDropEvent, QPalette, QColor

from gui.controls import FilterSidebar
from gui.viewer import ImageViewer, HistogramWidget, CompareWidget
from processing.filter_registry import FILTER_REGISTRY
from utils.image_loader import load_image, save_image, resize_for_display, bgr_to_qimage


# ─── WORKER THREAD ───────────────────────────────────────────────────────────

class FilterWorker(QThread):
    result_ready = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)

    def __init__(self, img, filter_id, params):
        super().__init__()
        self.img = img
        self.filter_id = filter_id
        self.params = params

    def run(self):
        try:
            entry = FILTER_REGISTRY[self.filter_id]
            result = entry["fn"](self.img, **self.params)
            self.result_ready.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ─── MAIN WINDOW ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Image Filters Studio — DSP Engine")
        self.setMinimumSize(1400, 820)
        self.resize(1600, 920)
        self.original_image = None
        self.processed_image = None
        self.current_filter = "none"
        self.current_params = {}
        self._worker = None
        self.compare_mode = False

        self._apply_theme()
        self._build_ui()
        self._connect_signals()

    # ── Theme ──────────────────────────────────────────────────────────────

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background: #080810; }
            QWidget { background: #080810; color: #c0ccd8; font-family: 'Consolas', 'Courier New', monospace; }
            QSplitter::handle { background: #1a1a2e; width: 2px; height: 2px; }
            QStatusBar { background: #0d0d1a; color: #5a7080; font-size: 12px;
                         border-top: 1px solid #1a1a2e; padding: 2px 10px; }
            QScrollBar:vertical { background: #0d0d1a; width: 8px; }
            QScrollBar::handle:vertical { background: #2a2a40; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QToolBar { background: #0d0d1e; border-bottom: 2px solid #1a1a30;
                       spacing: 6px; padding: 6px 12px; min-height: 52px; }
            QPushButton {
                background: transparent; color: #7090a0; border: 1px solid #1e2030;
                padding: 7px 16px; font-family: 'Consolas', monospace; font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover { color: #00e5c8; border-color: #00e5c840; background: #00e5c808; }
            QPushButton:disabled { color: #303840; border-color: #161820; }
            QPushButton#primary {
                background: #00e5c8; color: #000; font-weight: bold; border: none;
                font-size: 13px; padding: 7px 18px;
            }
            QPushButton#primary:hover { background: #00ffdf; }
            QPushButton#primary:disabled { background: #1a3030; color: #2a5050; }
            QLabel { background: transparent; }
        """)

    # ── UI Build ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Toolbar
        self._build_toolbar()

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)

        # Left: filter sidebar — wider so text is fully visible
        self.sidebar = FilterSidebar()
        self.sidebar.setMinimumWidth(300)
        self.sidebar.setMaximumWidth(360)
        splitter.addWidget(self.sidebar)

        # Center: image viewer
        center_widget = QWidget()
        center_widget.setStyleSheet("background: #0a0a14;")
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # Drop zone / image label
        self.drop_zone = DropZoneWidget()
        self.drop_zone.file_dropped.connect(self._load_image_from_path)
        center_layout.addWidget(self.drop_zone)

        # Image viewer (hidden initially)
        self.viewer = ImageViewer()
        self.viewer.hide()
        center_layout.addWidget(self.viewer)

        splitter.addWidget(center_widget)

        # Right: info + histogram — wider for readable text
        self.right_panel = RightPanel()
        self.right_panel.setMinimumWidth(340)
        self.right_panel.setMaximumWidth(420)
        splitter.addWidget(self.right_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        layout.addWidget(splitter)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready — drag & drop an image or use File > Open")

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        logo = QLabel("  ◈ SFILT<span style='color:#00e5c8'>STUDIO</span>  ")
        logo.setStyleSheet("color: #e8eaf6; font-weight: bold; font-size: 14px; letter-spacing: 2px;")
        logo.setTextFormat(Qt.RichText)
        tb.addWidget(logo)

        sep = QLabel("  |  ")
        sep.setStyleSheet("color: #2a3040;")
        tb.addWidget(sep)

        btn_open = QPushButton("📂 Open Image")
        btn_open.clicked.connect(self._open_file_dialog)
        tb.addWidget(btn_open)

        self.btn_compare = QPushButton("⊞ Compare")
        self.btn_compare.clicked.connect(self._toggle_compare)
        self.btn_compare.setEnabled(False)
        tb.addWidget(self.btn_compare)

        self.btn_reset = QPushButton("↺ Reset")
        self.btn_reset.clicked.connect(self._reset_filter)
        self.btn_reset.setEnabled(False)
        tb.addWidget(self.btn_reset)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        self.btn_export = QPushButton("↓ Export PNG")
        self.btn_export.setObjectName("primary")
        self.btn_export.clicked.connect(self._export_image)
        self.btn_export.setEnabled(False)
        tb.addWidget(btn_open)
        tb.addWidget(self.btn_compare)
        tb.addWidget(self.btn_reset)
        tb.addWidget(spacer)
        tb.addWidget(self.btn_export)

    def _connect_signals(self):
        self.sidebar.filter_selected.connect(self._on_filter_selected)
        self.sidebar.params_changed.connect(self._on_params_changed)

    # ── Image Loading ───────────────────────────────────────────────────────

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.jpg *.jpeg *.png *.bmp *.webp *.tiff)")
        if path:
            self._load_image_from_path(path)

    def _load_image_from_path(self, path: str):
        try:
            img = load_image(path)
            self.original_image = img
            self.processed_image = img.copy()
            self._show_image(img)
            self.drop_zone.hide()
            self.viewer.show()
            h, w = img.shape[:2]
            self.status.showMessage(f"Loaded: {Path(path).name}  |  {w}×{h} px  |  {img.nbytes // 1024} KB")
            self.btn_compare.setEnabled(True)
            self.btn_reset.setEnabled(True)
            self.btn_export.setEnabled(True)
            # update right panel info
            self.right_panel.update_image_info(Path(path).name, w, h, img.nbytes)
            # apply current filter
            self._run_filter()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image:\n{e}")

    def _show_image(self, img: np.ndarray):
        display = resize_for_display(img)
        qimg = bgr_to_qimage(display)
        self.viewer.set_processed(QPixmap.fromImage(qimg))

    # ── Filter Execution ────────────────────────────────────────────────────

    def _on_filter_selected(self, filter_id: str):
        self.current_filter = filter_id
        entry = FILTER_REGISTRY.get(filter_id, {})
        self.right_panel.update_filter_info(
            entry.get("label", filter_id),
            entry.get("formula", "—"),
            entry.get("desc", ""),
            entry.get("group", ""),
        )
        if self.original_image is not None:
            self._run_filter()

    def _on_params_changed(self, params: dict):
        self.current_params = params
        if self.original_image is not None:
            self._run_filter()

    def _run_filter(self):
        if self.original_image is None:
            return
        self.status.showMessage("⚙ Processing…")
        if self._worker and self._worker.isRunning():
            self._worker.quit()
        self._worker = FilterWorker(self.original_image, self.current_filter, self.current_params)
        self._worker.result_ready.connect(self._on_filter_done)
        self._worker.error.connect(lambda e: self.status.showMessage(f"Error: {e}"))
        self._worker.start()

    def _on_filter_done(self, result: np.ndarray):
        self.processed_image = result
        display = resize_for_display(result)
        qimg = bgr_to_qimage(display)
        if self.compare_mode:
            orig_display = resize_for_display(self.original_image)
            orig_qimg = bgr_to_qimage(orig_display)
            self.viewer.set_original(QPixmap.fromImage(orig_qimg))
        self.viewer.set_processed(QPixmap.fromImage(qimg))
        # Update histogram
        from processing.histogram import compute_histogram
        hist = compute_histogram(result)
        self.right_panel.histogram_widget.update_histogram(hist)
        h, w = result.shape[:2]
        self.status.showMessage(f"✔ Filter: {FILTER_REGISTRY[self.current_filter]['label']}  |  {w}×{h} px")

    def _reset_filter(self):
        self.sidebar.select_filter("none")

    def _toggle_compare(self):
        self.compare_mode = not self.compare_mode
        self.viewer.set_compare_mode(self.compare_mode)
        self.btn_compare.setText("⊟ Single View" if self.compare_mode else "⊞ Compare")
        if self.original_image is not None:
            self._on_filter_done(self.processed_image)

    def _export_image(self):
        if self.processed_image is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Image", f"filtered_{self.current_filter}.png",
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)")
        if path:
            if save_image(self.processed_image, path):
                self.status.showMessage(f"✔ Exported: {path}")
            else:
                QMessageBox.warning(self, "Export Failed", "Could not save image.")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            self._load_image_from_path(urls[0].toLocalFile())


# ─── DROP ZONE ────────────────────────────────────────────────────────────────

class DropZoneWidget(QWidget):
    file_dropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        icon = QLabel("⬡")
        icon.setStyleSheet("font-size: 56px; color: #00e5c840;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        title = QLabel("Drop an Image Here")
        title.setStyleSheet("font-size: 20px; color: #a0b0c0; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("JPG · PNG · BMP · WebP · TIFF")
        sub.setStyleSheet("font-size: 11px; color: #405060; letter-spacing: 1px;")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)

        btn = QPushButton("Browse Files")
        btn.setObjectName("primary")
        btn.setFixedWidth(140)
        btn.clicked.connect(self._browse)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

        self.setStyleSheet("""
            DropZoneWidget {
                border: 1px dashed #2a3048;
                background: #0a0a14;
            }
        """)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.jpg *.jpeg *.png *.bmp *.webp *.tiff)")
        if path:
            self.file_dropped.emit(path)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setStyleSheet("DropZoneWidget { border: 1px dashed #00e5c8; background: #00e5c808; }")

    def dragLeaveEvent(self, e):
        self.setStyleSheet("DropZoneWidget { border: 1px dashed #2a3048; background: #0a0a14; }")

    def dropEvent(self, e):
        self.setStyleSheet("DropZoneWidget { border: 1px dashed #2a3048; background: #0a0a14; }")
        urls = e.mimeData().urls()
        if urls:
            self.file_dropped.emit(urls[0].toLocalFile())


# ─── RIGHT PANEL ─────────────────────────────────────────────────────────────

class RightPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #0b0b18; border-left: 2px solid #1a1a30;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header ──
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet("background: #0d0d1e; border-bottom: 2px solid #1a1a30;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 0, 18, 0)
        icon = QLabel("📊")
        icon.setStyleSheet("font-size: 26px;")
        title = QLabel("INFO PANEL")
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; letter-spacing: 3px; color: #c8d8e8;"
        )
        hl.addWidget(icon)
        hl.addSpacing(10)
        hl.addWidget(title)
        hl.addStretch()
        outer.addWidget(header)

        # ── Scrollable body ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea          { border: none; background: #0b0b18; }
            QScrollBar:vertical  { background: #0d0d1a; width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #2a2a48; border-radius: 3px; min-height: 24px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        body = QWidget()
        body.setStyleSheet("background: #0b0b18;")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)

        # ── Image info card ──
        layout.addWidget(self._section_label("📁  IMAGE INFO"))
        info_card = QWidget()
        info_card.setStyleSheet(
            "background: #0e0e22; border: 1px solid #1e2038; border-radius: 8px;"
        )
        ic_layout = QVBoxLayout(info_card)
        ic_layout.setContentsMargins(16, 14, 16, 14)
        ic_layout.setSpacing(10)
        self.info_name  = self._info_row("File",    "—")
        self.info_size  = self._info_row("Size",    "—")
        self.info_bytes = self._info_row("Memory",  "—")
        ic_layout.addWidget(self.info_name)
        ic_layout.addWidget(self._divider())
        ic_layout.addWidget(self.info_size)
        ic_layout.addWidget(self._divider())
        ic_layout.addWidget(self.info_bytes)
        layout.addWidget(info_card)
        layout.addSpacing(20)

        # ── Active filter card ──
        layout.addWidget(self._section_label("🎚  ACTIVE FILTER"))
        filter_card = QWidget()
        filter_card.setStyleSheet(
            "background: #0e0e22; border: 1px solid #1e2038; border-radius: 8px;"
        )
        fc_layout = QVBoxLayout(filter_card)
        fc_layout.setContentsMargins(16, 16, 16, 16)
        fc_layout.setSpacing(8)

        self.filter_label = QLabel("Original")
        self.filter_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #00e5c8; "
            "font-family: 'Consolas', monospace; background: transparent;"
        )
        fc_layout.addWidget(self.filter_label)

        self.filter_group = QLabel("Basic")
        self.filter_group.setStyleSheet(
            "font-size: 14px; color: #e56b00; letter-spacing: 1px; "
            "font-family: 'Consolas', monospace; background: transparent;"
        )
        fc_layout.addWidget(self.filter_group)

        layout.addWidget(filter_card)
        layout.addSpacing(20)

        # ── DSP Formula card ──
        layout.addWidget(self._section_label("∑  DSP FORMULA"))
        formula_card = QWidget()
        formula_card.setStyleSheet(
            "background: #080818; border: 1px solid #00e5c830; border-radius: 8px;"
        )
        fml_layout = QVBoxLayout(formula_card)
        fml_layout.setContentsMargins(16, 16, 16, 16)
        fml_layout.setSpacing(12)

        self.formula_label = QLabel("g(x,y) = f(x,y)")
        self.formula_label.setStyleSheet(
            "font-size: 16px; color: #00e5c8; font-family: 'Consolas', monospace; "
            "font-weight: bold; background: transparent;"
        )
        self.formula_label.setWordWrap(True)
        fml_layout.addWidget(self.formula_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border: none; border-top: 1px solid #1a2a1a;")
        fml_layout.addWidget(sep)

        self.desc_label = QLabel("Identity — no transformation.")
        self.desc_label.setStyleSheet(
            "font-size: 13px; color: #6a8898; line-height: 1.6; "
            "font-family: 'Consolas', monospace; background: transparent;"
        )
        self.desc_label.setWordWrap(True)
        fml_layout.addWidget(self.desc_label)

        layout.addWidget(formula_card)
        layout.addSpacing(20)

        # ── Histogram card ──
        layout.addWidget(self._section_label("📈  HISTOGRAM — RGB"))
        hist_card = QWidget()
        hist_card.setStyleSheet(
            "background: #0e0e22; border: 1px solid #1e2038; border-radius: 8px;"
        )
        hc_layout = QVBoxLayout(hist_card)
        hc_layout.setContentsMargins(12, 12, 12, 12)
        hc_layout.setSpacing(10)

        self.histogram_widget = HistogramWidget()
        self.histogram_widget.setMinimumHeight(180)
        hc_layout.addWidget(self.histogram_widget)

        legend = QLabel(
            "<span style='color:#ff5a5a; font-size:14px;'>■ Red</span>  "
            "<span style='color:#50dc78; font-size:14px;'>■ Green</span>  "
            "<span style='color:#5090ff; font-size:14px;'>■ Blue</span>"
        )
        legend.setTextFormat(Qt.RichText)
        legend.setAlignment(Qt.AlignCenter)
        hc_layout.addWidget(legend)

        layout.addWidget(hist_card)
        layout.addStretch()

        scroll.setWidget(body)
        outer.addWidget(scroll)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #4a6070; "
            "letter-spacing: 2px; padding-bottom: 8px; background: transparent;"
        )
        return lbl

    def _divider(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setStyleSheet("border: none; border-top: 1px solid #1a1a30;")
        f.setFixedHeight(1)
        return f

    def _info_row(self, key: str, val: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 2, 0, 2)
        h.setSpacing(0)

        lbl_k = QLabel(key)
        lbl_k.setStyleSheet(
            "font-size: 13px; color: #4a6070; font-family: 'Consolas', monospace; "
            "background: transparent;"
        )
        lbl_v = QLabel(val)
        lbl_v.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #a8c8d8; "
            "font-family: 'Consolas', monospace; background: transparent;"
        )
        lbl_v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h.addWidget(lbl_k)
        h.addStretch()
        h.addWidget(lbl_v)
        w._val = lbl_v
        return w

    # ── Update methods ─────────────────────────────────────────────────────────

    def update_image_info(self, name, w, h, nbytes):
        self.info_name._val.setText(name[:22] + ("…" if len(name) > 22 else ""))
        self.info_size._val.setText(f"{w} × {h} px")
        self.info_bytes._val.setText(f"{nbytes // 1024} KB")

    def update_filter_info(self, label, formula, desc, group):
        self.filter_label.setText(label)
        self.filter_group.setText(f"▸  {group}")
        self.formula_label.setText(formula)
        self.desc_label.setText(desc)
