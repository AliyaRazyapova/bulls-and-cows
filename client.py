import socket
import sys
import threading
import re

from PyQt6 import uic

from PyQt6.QtGui import QIntValidator, QTextCursor

from python_files_from_ui import first, pravila, game_input

from PyQt6.QtWidgets import QMainWindow, QApplication


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection = ('127.0.0.1', 5046)


class Start(QMainWindow, first.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui_files/first.ui', self)
        self.setStyleSheet("#MainWindow{border-image:url(static/game_1.jpg)}")

        self.client = client
        self.client.connect(connection)
        self.start.clicked.connect(self.pravila)

    def pravila(self):
        self.pravila = PravilaWindow()
        self.close()
        self.pravila.show()


class PravilaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui_files/pravila.ui', self)
        self.setStyleSheet("#MainWindow{border-image:url(static/game_1.jpg)}")
        # self.client = client
        # self.client.connect(connection)
        self.pravila.clicked.connect(self.game_input)

    def game_input(self):
        self.game_input = Game_Input()
        self.close()
        self.game_input.show()


class Game_Input(QMainWindow, game_input.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # uic.loadUi('ui_files/game_input.ui', self)
        self.setStyleSheet("#MainWindow{border-image:url(static/game_1.jpg)}")
        self.client = client
        # self.client.connect(connection)

        # self.game_input.clicked.connect(self.game)
        self.receive = threading.Thread(target=self.receive)
        self.receive.start()

        # self.game_input_button.clicked(self.game)

        self.game_input_field.textChanged.connect(self.on_input_changed)
        self.game_input_ok.clicked.connect(self.send)
        self.game_input_button.clicked.connect(self.game)

    def send(self):
        message = self.game_input_field.text()
        try:
            message.encode('ascii')
        except UnicodeEncodeError:
            self.game_input_field.setText('')
            return

        if not bool(re.match(r'^(?!.*(.).*\1)\d{4}$', message)):
            self.game_input_field.setText('')
            return

        self.client.send(message.encode('ascii'))
        self.game_input_ok.setEnabled(False)
        self.game_input_button.setEnabled(True)

    def on_input_changed(self):
        self.game_input_ok.setEnabled(bool(self.game_input_field.text()))

    # def search(self):
        # self.curc.clear()
        # self.client.send('search'.encode('ascii'))
        # self.search_button.setEnabled(False)

    def receive(self):
        #TODO
        exceptions_connection = (ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError)
        while True:
            try:
                resp = self.client.recv(1024).decode('ascii')
            except exceptions_connection:
                return

            if resp == "kek":
                self.input_button.setEnabled(False)
                continue

            if resp == '?':
                continue

    #     # self.close()

    def game(self):
        # self.client.send(self.)
        self.game = Game()
        self.close()
        self.game.show()
#
#
class Game(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui_files/game.ui', self)
        self.setStyleSheet("#MainWindow{border-image:url(static/game_1.jpg)}")
        self.close()


if __name__ == '__main__':
    app = QApplication([])
    window = Start()
    window.show()
    sys.exit(app.exec())
