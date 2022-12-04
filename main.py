import sys

from PyQt6.QtWidgets import QApplication

from windows import StartWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StartWindow()
    ex.show()
    sys.exit(app.exec())
