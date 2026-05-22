from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

class AudioPlayer:
    def __init__(self):
        self.player = QMediaPlayer()
        self.current_file = None

    def play(self, file):
        self.current_file = file
        url = QUrl.fromLocalFile(file)
        self.player.setMedia(QMediaContent(url))
        self.player.play()

    def toggle(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            return "Play ⏯️"
        else:
            self.player.play()
            return "Pause ⏸️"

    def stop(self):
        self.player.stop()