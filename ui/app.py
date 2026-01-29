# ui/app.py
import sys
from PyQt5.QtWidgets import QApplication
from .main_window import MainWindow


def run_desktop():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
