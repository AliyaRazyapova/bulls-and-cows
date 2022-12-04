from PyQt6.QtWidgets import QMainWindow
from PyQt6 import uic


class StartWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui_files/first.ui', self)
        self.close()
