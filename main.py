import sys
from PyQt5.QtWidgets import QApplication
from UInew import AudioApp
#from ui2 import AudioApp

app = QApplication(sys.argv)
window = AudioApp()
window.show()
sys.exit(app.exec_())