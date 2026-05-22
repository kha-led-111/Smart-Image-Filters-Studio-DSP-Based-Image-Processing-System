"""
Filter control sidebar: group tabs, filter list, dynamic parameter sliders.
Redesigned for clarity — larger fonts, taller buttons, full-width layout.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QScrollArea, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from processing.filter_registry import FILTER_REGISTRY, GROUPS

# Full names for group tab buttons
GROUP_ABBR = {
    "Basic":     "⬡  Basic",
    "Blur":      "〜  Blur",
    "Sharpen":   "◈  Sharpen",
    "Edge":      "◇  Edge",
    "Noise":     "∿  Noise",
    "Histogram": "▨  Histogram",
    "Frequency": "∿  Frequency",
}


class FilterSidebar(QWidget):
    filter_selected = pyqtSignal(str)
    params_changed  = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #0b0b18; border-right: 2px solid #1a1a30;")
        self._active_filter = "none"
        self._param_widgets = {}
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_params)
        self._build()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet("background: #0d0d1e; border-bottom: 2px solid #1a1a30;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 0, 18, 0)
        icon = QLabel("⚙")
        icon.setStyleSheet("font-size: 26px; color: #00e5c8;")
        title = QLabel("FILTER PANEL")
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; letter-spacing: 3px; color: #c8d8e8;"
        )
        hl.addWidget(icon)
        hl.addSpacing(10)
        hl.addWidget(title)
        hl.addStretch()
        layout.addWidget(header)

        # ── Group tab bar — vertical stack of full-width tabs ──
        self._tab_btns = {}
        tab_bar = QWidget()
        tab_bar.setStyleSheet("background: #0b0b18;")
        tb_layout = QVBoxLayout(tab_bar)
        tb_layout.setContentsMargins(10, 12, 10, 8)
        tb_layout.setSpacing(5)

        grp_label = QLabel("  CATEGORY")
        grp_label.setStyleSheet(
            "font-size: 11px; color: #3a4858; letter-spacing: 2px; padding-left: 4px;"
        )
        tb_layout.addWidget(grp_label)

        for g in GROUPS:
            btn = QPushButton(GROUP_ABBR.get(g, g))
            btn.setFixedHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(self._tab_style(False))
            btn.clicked.connect(lambda _, grp=g: self._select_group(grp))
            tb_layout.addWidget(btn)
            self._tab_btns[g] = btn

        layout.addWidget(tab_bar)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("border: none; border-top: 1px solid #1a1a30; margin: 0 8px;")
        layout.addWidget(div)

        # ── Filter list (scrollable) ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea          { border: none; background: #0b0b18; }
            QScrollBar:vertical  { background: #0d0d1a; width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #2a2a48; border-radius: 3px; min-height: 24px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self.filter_container = QWidget()
        self.filter_container.setStyleSheet("background: #0b0b18;")
        self.filter_layout = QVBoxLayout(self.filter_container)
        self.filter_layout.setContentsMargins(8, 8, 8, 8)
        self.filter_layout.setSpacing(3)
        self.filter_layout.addStretch()
        scroll.setWidget(self.filter_container)
        layout.addWidget(scroll, stretch=1)

        # ── Parameter panel ──
        self.param_panel = QWidget()
        self.param_panel.setStyleSheet(
            "background: #0e0e20; border-top: 2px solid #1a1a30;"
        )
        self.param_layout = QVBoxLayout(self.param_panel)
        self.param_layout.setContentsMargins(14, 12, 14, 14)
        self.param_layout.setSpacing(10)
        layout.addWidget(self.param_panel)

        self._filter_buttons = {}
        self._select_group(GROUPS[0])

    # ── Styles ─────────────────────────────────────────────────────────────────

    def _tab_style(self, active):
        base = (
            "font-size: 14px; font-family: 'Consolas', monospace; "
            "font-weight: bold; letter-spacing: 1px; border-radius: 5px;"
        )
        if active:
            return (f"QPushButton {{ {base} background: #00e5c818; color: #00e5c8; "
                    "border: 1px solid #00e5c855; text-align: left; padding-left: 16px; }"
                    "QPushButton:hover { background: #00e5c825; }")
        return (f"QPushButton {{ {base} background: #111124; color: #6a7888; "
                "border: 1px solid #1e2038; text-align: left; padding-left: 16px; }"
                "QPushButton:hover { color: #a0b8c8; border-color: #2a3a50; }")

    def _filter_btn_style(self, active):
        base = (
            "font-size: 14px; font-family: 'Consolas', monospace; "
            "text-align: left; padding-left: 18px; border-radius: 5px;"
        )
        if active:
            return (f"QPushButton {{ {base} background: #00e5c812; color: #00e5c8; "
                    "border-left: 4px solid #00e5c8; border-top: none; "
                    "border-right: none; border-bottom: none; }"
                    "QPushButton:hover { background: #00e5c81c; }")
        return (f"QPushButton {{ {base} background: transparent; color: #8898a8; "
                "border: none; border-left: 4px solid transparent; }"
                "QPushButton:hover { color: #c0d0e0; "
                "background: #ffffff08; border-left: 4px solid #2a3a52; }")

    # ── Group selection ────────────────────────────────────────────────────────

    def _select_group(self, group):
        self._active_group = group
        for g, btn in self._tab_btns.items():
            btn.setStyleSheet(self._tab_style(g == group))

        # Clear existing filter buttons
        while self.filter_layout.count() > 1:
            item = self.filter_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._filter_buttons.clear()

        # Count for this group
        filters_in_group = [(fid, e) for fid, e in FILTER_REGISTRY.items()
                            if e["group"] == group]

        # Group label inside list
        grp_lbl = QLabel(f"  {group.upper()} FILTERS")
        grp_lbl.setStyleSheet(
            "font-size: 12px; color: #e56b00; letter-spacing: 2px; "
            "padding: 6px 0 8px 4px;"
        )
        self.filter_layout.insertWidget(0, grp_lbl)

        for idx, (fid, entry) in enumerate(filters_in_group):
            btn = QPushButton(entry["label"])
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setFixedHeight(50)          # taller — easier to click & read
            has_params = bool(entry["params"])
            label_text = entry["label"]
            if has_params:
                label_text += "  ⚙"
            btn.setText(label_text)
            btn.setStyleSheet(self._filter_btn_style(fid == self._active_filter))
            btn.clicked.connect(lambda _, f=fid: self.select_filter(f))
            self.filter_layout.insertWidget(idx + 1, btn)
            self._filter_buttons[fid] = btn

    # ── Filter selection ───────────────────────────────────────────────────────

    def select_filter(self, filter_id: str):
        self._active_filter = filter_id
        for fid, btn in self._filter_buttons.items():
            btn.setStyleSheet(self._filter_btn_style(fid == filter_id))
        self._build_param_panel(filter_id)
        self.filter_selected.emit(filter_id)

    # ── Parameter panel ────────────────────────────────────────────────────────

    def _build_param_panel(self, filter_id: str):
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._param_widgets.clear()

        entry  = FILTER_REGISTRY.get(filter_id, {})
        params = entry.get("params", [])

        if not params:
            self.param_panel.hide()
            return

        self.param_panel.show()

        # Panel title
        p_title = QLabel("⚙  PARAMETERS")
        p_title.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #e56b00; letter-spacing: 2px;"
        )
        self.param_layout.addWidget(p_title)

        for (name, mn, mx, default, step, label) in params:
            wrapper = QWidget()
            wrapper.setStyleSheet(
                "background: #111126; border-radius: 6px; border: 1px solid #1e2038;"
            )
            wl = QVBoxLayout(wrapper)
            wl.setContentsMargins(14, 12, 14, 12)
            wl.setSpacing(8)

            # Label row
            hdr = QWidget()
            hdr.setStyleSheet("background: transparent; border: none;")
            hl = QHBoxLayout(hdr)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(0)

            lbl = QLabel(label)
            lbl.setStyleSheet(
                "font-size: 13px; color: #90a8b8; font-family: 'Consolas', monospace;"
                "background: transparent; border: none;"
            )
            val_lbl = QLabel(f"{default:.2f}")
            val_lbl.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #00e5c8; "
                "font-family: 'Consolas', monospace; background: transparent; border: none;"
            )
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            hl.addWidget(lbl)
            hl.addStretch()
            hl.addWidget(val_lbl)
            wl.addWidget(hdr)

            # Slider
            scale  = int(1 / step) if step < 1 else 1
            slider = QSlider(Qt.Horizontal)
            slider.setRange(int(mn * scale), int(mx * scale))
            slider.setValue(int(default * scale))
            slider.setFixedHeight(32)
            slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    background: #1e2038; height: 6px; border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #00e5c8; width: 22px; height: 22px;
                    margin: -8px 0; border-radius: 11px;
                    border: 2px solid #007a6a;
                }
                QSlider::sub-page:horizontal {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #007a6a, stop:1 #00e5c8);
                    border-radius: 3px;
                }
            """)

            def on_change(v, s=scale, vl=val_lbl):
                vl.setText(f"{v / s:.2f}")
                self._debounce_timer.start(80)

            slider.valueChanged.connect(on_change)
            wl.addWidget(slider)

            # Min / Max row
            rng = QWidget()
            rng.setStyleSheet("background: transparent; border: none;")
            rrl = QHBoxLayout(rng)
            rrl.setContentsMargins(0, 0, 0, 0)
            mn_lbl = QLabel(str(mn))
            mx_lbl = QLabel(str(mx))
            for l in (mn_lbl, mx_lbl):
                l.setStyleSheet(
                    "font-size: 11px; color: #3a4858; "
                    "font-family: 'Consolas', monospace; background: transparent; border: none;"
                )
            rrl.addWidget(mn_lbl)
            rrl.addStretch()
            rrl.addWidget(mx_lbl)
            wl.addWidget(rng)

            self.param_layout.addWidget(wrapper)
            self._param_widgets[name] = (slider, scale)

    def _emit_params(self):
        params = {name: slider.value() / scale
                  for name, (slider, scale) in self._param_widgets.items()}
        self.params_changed.emit(params)
