from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QFileDialog)
from processing2 import clean_audio_signal, speech_to_text
from read_save import load_audio, save_audio
from playsound import AudioPlayer

class AudioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSP: Noise Reduction & STT")
        self.resize(500, 400)

        self.audio = None
        self.sr = None
        self.player = AudioPlayer() 

        layout = QVBoxLayout()

        self.status_label = QLabel("برجاء اختيار ملف صوتي (WAV)")
        layout.addWidget(self.status_label)

        self.load_btn = QPushButton("تحميل ملف الصوت")
        self.load_btn.clicked.connect(self.load_audio)
        layout.addWidget(self.load_btn)

        self.process_btn = QPushButton("تنظيف الصوت واستخراج النص")
        self.process_btn.clicked.connect(self.process_audio)
        layout.addWidget(self.process_btn)

        self.text_display = QTextEdit()
        self.text_display.setPlaceholderText("النص المستخرج سيظهر هنا...")
        layout.addWidget(self.text_display)

        self.play_btn = QPushButton("تشغيل الصوت المنقى")
        self.play_btn.clicked.connect(self.play_audio)
        layout.addWidget(self.play_btn)

        self.setLayout(layout)

    def load_audio(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open", "", "WAV (*.wav)")
        if file:
            self.audio, self.sr = load_audio(file)
            self.status_label.setText(f"تم تحميل: {file.split('/')[-1]}")
            self.current_file = file

    def process_audio(self):
        if self.audio is None: return
        
        self.status_label.setText("جاري معالجة الإشارة وتنظيف الضوضاء...")

        cleaned = clean_audio_signal(self.audio, self.sr)

        save_audio("cleaned_temp.wav", cleaned, self.sr) #[cite: 3]
        
        result_text = speech_to_text("cleaned_temp.wav")
        self.text_display.setText(result_text)
        self.status_label.setText("تمت المعالجة بنجاح!")

    def play_audio(self):
        self.player.play("cleaned_temp.wav") #[cite: 1]