"""
Smart Image Filters Studio — DSP-Based Image Processing System
Entry point: python main.py
"""
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    from gui.dashboard import MainWindow
except ImportError as e:
    print(f"Error: Required module not found. Please install PyQt5:\n  pip install PyQt5\n\nDetails: {e}")
    sys.exit(1)


def main():
    # High-DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Smart Image Filters Studio")
    app.setApplicationVersion("1.0")

    # Base font
    font = QFont("Consolas", 10)
    app.setFont(font)

    window = MainWindow()
    window.setAcceptDrops(True)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
