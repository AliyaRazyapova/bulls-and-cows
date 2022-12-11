import socket
import sys
import threading

from PyQt6 import uic

from python_files_from_ui import first, pravila

from PyQt6.QtWidgets import QMainWindow, QApplication


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection = ('127.0.0.1', 5060)


class Start(QMainWindow, first.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui_files/first.ui', self)
        self.setStyleSheet("#MainWindow{border-image:url(static/game_1.jpg)}")

        # self.client = client
        # self.client.connect(connection)
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


class Game_Input(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui_files/game_input.ui', self)
        self.setStyleSheet("#MainWindow{border-image:url(static/game_1.jpg)}")
        # self.client = client
        # self.client.connect(connection)

        self.curs.ensureCursorVisible()

        self.game_input.clicked.connect(self.game)
        self.receive = threading.Thread(target=self.receive)
        self.receive.start()

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

    def game(self):
        # self.client.send(self.)
        self.game = Game()
        self.close()
        self.game.show()


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
