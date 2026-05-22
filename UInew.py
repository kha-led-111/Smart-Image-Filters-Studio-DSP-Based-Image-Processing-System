import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QFileDialog, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter, QBrush
from processing2 import clean_audio_signal, speech_to_text
from read_save import load_audio, save_audio
from playsound import AudioPlayer


# ─────────────────────────── Worker Thread ───────────────────────────
class ProcessingWorker(QThread):
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, audio, sr, lang):
        super().__init__()
        self.audio = audio
        self.sr    = sr
        self.lang  = lang

    def run(self):
        try:
            cleaned = clean_audio_signal(self.audio, self.sr)
            save_audio("cleaned_temp.wav", cleaned, self.sr)
            text = speech_to_text("cleaned_temp.wav", self.lang)
            self.finished.emit(text)
        except ExceptionW as e:
            self.error.emit(str(e))


# ─────────────────────────── Card Widget ─────────────────────────────
class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)


# ─────────────────────────── Main App ────────────────────────────────
class AudioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.audio        = None
        self.sr           = None
        self.current_file = None
        self.worker       = None
        self.player       = AudioPlayer()
        self.selected_lang = "ar-EG"

        self._build_ui()
        self._apply_styles()

    # ── Build UI ──────────────────────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle("DSP · Noise Reduction & Speech-to-Text")
        self.setMinimumSize(600, 680)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # ── Header ────────────────────────────────────────────────────
        header = QHBoxLayout()
        title  = QLabel("🎙 DSP Studio")
        title.setObjectName("title")
        subtitle = QLabel("Noise Reduction · Speech-to-Text")
        subtitle.setObjectName("subtitle")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(subtitle)
        root.addLayout(header)

        # ── Status bar ────────────────────────────────────────────────
        self.status_label = QLabel("اختر ملف صوتي للبدء")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.status_label)

        # ── Language toggle ───────────────────────────────────────────
        lang_row = QHBoxLayout()
        lang_lbl = QLabel("اللغة:")
        lang_lbl.setObjectName("sectionLabel")
        self.btn_ar = QPushButton("🇪🇬  عربي")
        self.btn_en = QPushButton("🇺🇸  English")
        self.btn_ar.setObjectName("langActive")
        self.btn_en.setObjectName("langInactive")
        self.btn_ar.clicked.connect(lambda: self._set_lang("ar-EG", self.btn_ar, self.btn_en))
        self.btn_en.clicked.connect(lambda: self._set_lang("en-US", self.btn_en, self.btn_ar))
        lang_row.addWidget(lang_lbl)
        lang_row.addWidget(self.btn_ar)
        lang_row.addWidget(self.btn_en)
        lang_row.addStretch()
        root.addLayout(lang_row)

        # ── Action buttons card ───────────────────────────────────────
        btn_card = Card()
        btn_layout = QHBoxLayout(btn_card)
        btn_layout.setContentsMargins(16, 16, 16, 16)
        btn_layout.setSpacing(12)

        self.load_btn    = self._make_btn("📂  تحميل ملف", "primary")
        self.process_btn = self._make_btn("⚙️  معالجة الصوت", "success")
        self.play_btn    = self._make_btn("▶️  تشغيل", "accent")
        self.save_btn    = self._make_btn("💾  حفظ", "save")

        self.process_btn.setEnabled(False)
        self.play_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

        self.load_btn.clicked.connect(self.load_audio)
        self.process_btn.clicked.connect(self.process_audio)
        self.play_btn.clicked.connect(self.play_audio)
        self.save_btn.clicked.connect(self.save_output)

        for b in (self.load_btn, self.process_btn, self.play_btn, self.save_btn):
            btn_layout.addWidget(b)

        root.addWidget(btn_card)

        # ── Waveform placeholder ──────────────────────────────────────
        self.wave_label = QLabel("〰 شكل الموجة سيظهر بعد التحميل")
        self.wave_label.setObjectName("wavePlaceholder")
        self.wave_label.setAlignment(Qt.AlignCenter)
        self.wave_label.setMinimumHeight(60)
        root.addWidget(self.wave_label)

        # ── Text output card ──────────────────────────────────────────
        text_card = Card()
        text_layout = QVBoxLayout(text_card)
        text_layout.setContentsMargins(16, 12, 16, 12)

        text_header = QLabel("📝  النص المستخرج")
        text_header.setObjectName("sectionLabel")
        self.text_display = QTextEdit()
        self.text_display.setPlaceholderText("النص المستخرج من الكلام سيظهر هنا …")
        self.text_display.setObjectName("textDisplay")
        self.text_display.setMinimumHeight(160)

        text_layout.addWidget(text_header)
        text_layout.addWidget(self.text_display)
        root.addWidget(text_card)

        # ── Footer ────────────────────────────────────────────────────
        footer = QLabel("DSP Studio · v2.0")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignCenter)
        root.addWidget(footer)

    # ── Helpers ───────────────────────────────────────────────────────
    def _make_btn(self, text, variant):
        btn = QPushButton(text)
        btn.setObjectName(f"btn_{variant}")
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    def _set_lang(self, code, active_btn, inactive_btn):
        self.selected_lang = code
        active_btn.setObjectName("langActive")
        inactive_btn.setObjectName("langInactive")
        active_btn.setStyle(active_btn.style())
        inactive_btn.setStyle(inactive_btn.style())
        self._apply_styles()

    def _set_status(self, msg, color="#94a3b8"):
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 13px;")

    # ── Slots ─────────────────────────────────────────────────────────
    def load_audio(self):
        file, _ = QFileDialog.getOpenFileName(self, "فتح ملف صوتي", "", "WAV Files (*.wav)")
        if not file:
            return
        self.audio, self.sr = load_audio(file)
        self.current_file   = file
        fname = os.path.basename(file)
        self._set_status(f"✅  تم التحميل: {fname}", "#4ade80")
        self.wave_label.setText(f"〰  {fname}  ·  {self.sr} Hz  ·  {len(self.audio)/self.sr:.1f}s")
        self.process_btn.setEnabled(True)
        self.play_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.text_display.clear()

    def process_audio(self):
        if self.audio is None:
            return
        self._set_status("⏳  جاري المعالجة …", "#facc15")
        self.process_btn.setEnabled(False)

        self.worker = ProcessingWorker(self.audio, self.sr, self.selected_lang)
        self.worker.finished.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_done(self, text):
        self.text_display.setText(text)
        self._set_status("✅  اكتملت المعالجة!", "#4ade80")
        self.process_btn.setEnabled(True)
        self.play_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

    def _on_error(self, msg):
        self._set_status(f"❌  خطأ: {msg}", "#f87171")
        self.process_btn.setEnabled(True)

    def play_audio(self):
        if os.path.exists("cleaned_temp.wav"):
            self.player.play("cleaned_temp.wav")

    def save_output(self):
        if not os.path.exists("cleaned_temp.wav"):
            return
        os.makedirs("output", exist_ok=True)
        base = os.path.splitext(os.path.basename(self.current_file))[0] if self.current_file else "audio"
        out_path = os.path.join("output", f"{base}_cleaned.wav")
        audio, sr = load_audio("cleaned_temp.wav")
        save_audio(out_path, audio, sr)
        self._set_status(f"💾  تم الحفظ في: {out_path}", "#818cf8")

    # ── Stylesheet ────────────────────────────────────────────────────
    def _apply_styles(self):
        self.setStyleSheet("""
            /* ── Window ── */
            QWidget {
                background-color: #0f172a;
                color: #e2e8f0;
                font-family: 'Segoe UI', 'Cairo', sans-serif;
                font-size: 14px;
            }

            /* ── Title / Subtitle ── */
            #title {
                font-size: 22px;
                font-weight: 700;
                color: #f1f5f9;
                letter-spacing: 0.5px;
            }
            #subtitle {
                font-size: 11px;
                color: #64748b;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }

            /* ── Status ── */
            #status {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 16px;
                color: #94a3b8;
                font-size: 13px;
            }

            /* ── Section label ── */
            #sectionLabel {
                color: #64748b;
                font-size: 11px;
                letter-spacing: 1px;
                text-transform: uppercase;
                font-weight: 600;
            }

            /* ── Card ── */
            #card {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 14px;
            }

            /* ── Wave placeholder ── */
            #wavePlaceholder {
                background: #1e293b;
                border: 1px dashed #334155;
                border-radius: 10px;
                color: #475569;
                font-size: 13px;
                padding: 12px;
            }

            /* ── Text display ── */
            #textDisplay {
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 15px;
                line-height: 1.7;
                padding: 10px;
            }
            #textDisplay:focus { border-color: #6366f1; }

            /* ── Buttons ── */
            QPushButton {
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 18px;
                border: none;
            }

            #btn_primary   { background: #3b82f6; color: #fff; }
            #btn_primary:hover  { background: #2563eb; }
            #btn_primary:disabled { background: #1e3a5f; color: #475569; }

            #btn_success   { background: #10b981; color: #fff; }
            #btn_success:hover  { background: #059669; }
            #btn_success:disabled { background: #064e3b; color: #475569; }

            #btn_accent    { background: #8b5cf6; color: #fff; }
            #btn_accent:hover   { background: #7c3aed; }
            #btn_accent:disabled { background: #2e1065; color: #475569; }

            #btn_save      { background: #f59e0b; color: #0f172a; }
            #btn_save:hover     { background: #d97706; }
            #btn_save:disabled  { background: #451a03; color: #475569; }

            /* ── Language buttons ── */
            #langActive   { background: #6366f1; color: #fff; border-radius: 6px;
                            padding: 4px 14px; font-size: 12px; font-weight: 700; }
            #langInactive { background: #1e293b; color: #64748b; border: 1px solid #334155;
                            border-radius: 6px; padding: 4px 14px; font-size: 12px; }
            #langInactive:hover { background: #334155; color: #e2e8f0; }

            /* ── Footer ── */
            #footer { color: #334155; font-size: 11px; padding-top: 4px; }
        """)
