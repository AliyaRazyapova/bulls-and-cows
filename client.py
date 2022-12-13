import socket
import sys
import threading
import re

import python_files_from_ui

from PyQt6.QtGui import QIntValidator, QTextCursor
from python_files_from_ui import first, pravila, game
from PyQt6.QtWidgets import QMainWindow, QApplication

host = '127.0.0.1'
port = 5002

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection = (host, port)
stylesheet = "#MainWindow{border-image:url(static/background.jpg)}"


class Start(QMainWindow, first.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setStyleSheet(stylesheet)

        self.client = client
        self.client.connect(connection)
        self.start.clicked.connect(self.pravila)

    def pravila(self):
        self.pravila = PravilaWindow()
        self.close()
        self.pravila.show()


class PravilaWindow(QMainWindow, pravila.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setStyleSheet(stylesheet)

        self.pravila.clicked.connect(self.game)

    def game(self):
        self.game = Game()
        self.close()
        self.game.show()


class Game(QMainWindow, python_files_from_ui.game.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setStyleSheet(stylesheet)
        self.client = client

        self.receive = threading.Thread(target=self.receive)
        self.receive.start()

        self.chat.ensureCursorVisible()

        self.game_input_field.textChanged.connect(self.on_input_changed)
        self.game_input_ok.clicked.connect(self.send)

        self.game_input_button.clicked.connect(self.search)

        self.nickname = ''
        self.opponent_nick = ''

    def send(self):
        message = self.game_input_field.text()
        try:
            message.encode('ascii')
        except UnicodeEncodeError:
            self.last_response.setText('Используйте текст формата ASCII')
            self.game_input_field.setText('')
            return

        if self.nickname and not bool(re.match(r'^(?!.*(.).*\1)\d{4}$', message)):
            self.last_response.setText('Введите 4 уникальные цифры')
            self.game_input_field.setText('')
            return

        self.client.send(message.encode('ascii'))
        self.game_input_ok.setEnabled(False)
        self.game_input_button.setEnabled(True)

    def on_input_changed(self):
        self.game_input_ok.setEnabled(bool(self.game_input_field.text()))

    def search(self):
        self.chat.clear()
        self.client.send('search'.encode('ascii'))
        self.game_input_button.setEnabled(False)
        self.instructions.setText('Поиск...')
        self.last_response.setText('Поиск начался')

    def closeEvent(self, event):
        self.client.close()
        event.accept()

    def receive(self):
        conn_exceptions = (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError)
        while True:
            try:
                resp = self.client.recv(1024).decode('ascii')
            except conn_exceptions:
                return

            if resp == 'invalid_opponent':
                self.last_response.setText('Соперник покинул игру')
                self.chat.append(f"Вы технически победили!")
                self.game_input_field.clear()
                self.game_input_field.setEnabled(False)
                self.game_input_ok.setEnabled(False)
                self.game_input_button.setEnabled(True)
                self.instructions.setText("Начните поиск игры")
                continue

            if resp == 'invalid_characters':
                self.last_response.setText('Используйте латинские символы')
                self.game_input_field.clear()
                continue

            if resp == 'invalid_taken':
                self.last_response.setText('Такой никнейм уже существует')
                self.game_input_field.clear()
                continue

            if resp == 'invalid_empty':
                self.last_response.setText('Вы ввели пустое сообщение')
                continue

            if resp == 'invalid_code':
                self.last_response.setText('Введите 4 уникальные цифры')
                continue

            if resp.split()[0] == 'valid_nickname':
                self.nickname = resp.split()[1]
                self.label.setText(f'Окно игрока {self.code}')
                self.instructions.setText(f'Теперь можете искать игру')
                self.game_input_field.clear()
                self.game_input_field.setEnabled(False)
                self.game_input_ok.setEnabled(False)
                self.game_input_button.setEnabled(True)
                self.game_input_field.setMaxLength(4)
                self.game_input_field.setValidator(QIntValidator())
                continue

            if resp.split()[0] == 'valid_wish':
                code = resp.split()[1]
                self.last_response.setText(f"Вы ввели число {code}")
                self.chat.append(f"Вы ввели число {code}")
                self.game_input_field.clear()
                self.game_input_field.setEnabled(False)
                self.game_input_ok.setEnabled(False)
                continue

            if resp == 'first':
                self.last_response.setText("Вы вводите своё предположение первым")
                self.game_input_field.clear()
                self.game_input_field.setEnabled(True)
                self.game_input_ok.setEnabled(False)
                self.game_input_button.setEnabled(False)
                continue

            if resp == 'second':
                self.last_response.setText(f"{self.opponent_nick} угадывает первым")
                self.game_input_field.clear()
                self.game_input_field.setEnabled(False)
                self.game_input_ok.setEnabled(False)
                self.game_input_button.setEnabled(False)
                continue

            if resp.split()[0] == 'game':
                self.last_response.setText("Загадайте число")
                self.game_input_field.setEnabled(True)
                self.game_input_ok.setEnabled(False)
                self.opponent_nick = resp.split()[1]
                self.instructions.setText(f"{self.nickname} против {self.opponent_nick}")
                self.last_response.setProperty("color", "0")
                continue

            if resp.split()[0] == 'lose':
                code = resp.split()[1]
                self.last_response.setText(f'Было загадано: {code}')
                self.chat.append(f"{self.opponent_nick} победил")
                self.game_input_field.clear()
                self.game_input_field.setEnabled(False)
                self.game_input_ok.setEnabled(False)
                self.game_input_button.setEnabled(True)
                self.instructions.setText("Вы проиграли! Вы можете сыграть ещё раз")
                self.last_response.setProperty("color", "0")
                continue

            if resp == 'guess':
                self.last_response.setText("Ваша очередь угадывать")
                self.game_input_field.setEnabled(True)
                self.instructions.setText("Введите ваше предположение")
                self.last_response.setProperty("color", "1")
                continue

            if resp == 'win':
                self.last_response.setText('Вы выиграли эту игру!')
                self.chat.append(f"Вы выиграли!")
                self.game_input_field.clear()
                self.game_input_field.setEnabled(False)
                self.game_input_ok.setEnabled(False)
                self.game_input_button.setEnabled(True)
                self.instructions.setText("Вы выиграли! Вы можете сыграть ещё раз")
                self.last_response.setProperty("color", "0")
                continue

            if resp == 'wait':
                self.last_response.setText(f"Ждём предположение игрока {self.opponent_nick}")
                self.game_input_field.clear()
                self.game_input_field.setEnabled(False)
                self.game_input_ok.setEnabled(False)
                self.instructions.setText(f"Ждём предположение игрока {self.opponent_nick}")
                self.last_response.setProperty("color", "0")
                continue

            if resp == '?':
                continue

            self.chat.append(resp)


if __name__ == '__main__':
    app = QApplication([])
    window = Start()
    window.show()
    sys.exit(app.exec())
