import os
import socket
import threading
from time import sleep
import re
from random import shuffle


searching_lock = threading.Lock()
client_init_lock = threading.Lock()
code_lock = threading.Lock()
wait_lock = threading.Lock()
game_lock = threading.Lock()

host = '127.0.0.1'
port = 5046

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = {}
free_players = []
session_info = {}


def handle(client):

    def opponent_valid(cl):
        op = session_info[cl]['opponent']
        if op.fileno == -1:
            clients[cl]['state'] = 4
            del session_info[cl]
            del session_info[op]
            del clients[op]
            free_players.append(cl)
            return False
        return op

    exception_connection = (ConnectionResetError, ConnectionAbortedError, ConnectionRefusedError)

    while True:
        if client.fileno() == -1:
            return

        if client not in clients:  # Клиент не аутентифицирован
            with client_init_lock:
                for c in clients:
                    if c.fileno == -1:
                        del clients[c]
                clients[client] = {'state': 4}
            try:
                client.send(f'valid_nickname'.encode('ascii'))
            except exception_connection:
                print('Connection torn apart')
                client.close()
                del clients[client]
                return

    #     if clients[client]['state'] == 0:  # Поиск игры
    #         while True:
    #             sleep(1)
    #             with searching_lock:
    #                 print(free_players)
    #
    #                 if client.fileno() == -1:
    #                     break
    #                 if client not in clients or clients[client]['state'] != 0:
    #                     break
    #
    #                 for opponent in free_players:  # Подбор свободного соперника
    #                     if opponent != client:
    #                         if opponent.fileno() == -1:
    #                             continue
    #                         free_players.remove(client)
    #                         free_players.remove(opponent)
    #
    #                         session_info[client] = {'opponent': opponent}
    #                         session_info[opponent] = {'opponent': client}
    #
    #                         clients[client]['state'] = 1
    #                         clients[opponent]['state'] = 1
    #
    #                         try:
    #                             client.send(f"game {clients[opponent]['nickname']}".encode('ascii'))
    #                         except conn_exceptions:
    #                             client.close()
    #                             print('Connection refused cln')
    #                             break
    #
    #                         try:
    #                             opponent.send(f"game {clients[client]['nickname']}".encode('ascii'))
    #                         except conn_exceptions:
    #                             opponent.close()
    #                             print('Connection refused opp')
    #                         break
    #
    # while True:
    #     if client.fileno == -1:  # Соединение разорвано
    #         print(f'Соединение закрыто с клиентом {client}')
    #         return

        # if client not in clients:  # Клиент не аутентифицирован
        #     client.send('nickname'.encode('ascii'))
        #
        #     nickname = client.recv(1024).decode('ascii')
        #     if not nickname:
        #         print(f'Connection closed with client {client}')
        #         return
        #
        #     if len(nickname) == 0:
        #         client.send('invalid'.encode('ascii'))
        #         continue
        #     client.send('valid'.encode('ascii'))
        #
        #     with client_init_lock:
        #         clients[client] = {'nickname': nickname, 'state': 0}
        #         free_players.append(client)
        #
        #     print("Nickname is {}".format(nickname))

        # if clients[client]['state'] == 0:  # Клиент еще не в сессии
        #     client.send('search'.encode('ascii'))
        #     while True:
        #         sleep(1)
        #         with searching_lock:
        #             if client.fileno == -1 or clients[client]['state'] != 0:
        #                 break
        #
        #             for opponent in free_players:  # Подбор свободного соперника
        #                 if opponent != client:
        #                     if opponent.fileno == -1:
        #                         free_players.remove(opponent)
        #                         del clients[opponent]
        #                         continue
        #                     free_players.remove(client)
        #                     free_players.remove(opponent)
        #
        #                     session_info[client] = {'opponent': opponent}
        #                     session_info[opponent] = {'opponent': client}
        #
        #                     clients[client]['state'] = 1
        #                     clients[opponent]['state'] = 1
        #                     break
        if clients[client]['state'] == 1:  # Загадывание числа
            while True:
                opponent = opponent_valid(client)
                if not isinstance(opponent, socket.socket):
                    try:
                        client.send('invalid_opponent'.encode('ascii'))
                    except exception_connection:
                        del clients[client]
                        print('Connection torn apart')
                        client.close()
                        return
                    clients[client]['state'] = 4
                    break

                if clients[client]['state'] != 1:
                    break

                try:
                    number = client.recv(1024)
                except exception_connection:
                    print('Connection torn apart')
                    del clients[client]
                    client.close()
                    break
                print(number)
                if number is False or number is None:
                    break
                try:
                    number = number.decode('ascii')
                except UnicodeDecodeError:
                    try:
                        client.send('invalid_characters'.encode('ascii'))
                    except exception_connection:
                        del clients[client]
                        print('Connection torn apart')
                        client.close()
                        return
                    continue

                if not number:
                    try:
                        client.send('invalid_length'.encode('ascii'))
                    except exception_connection:
                        del clients[client]
                        print('Connection torn apart')
                        client.close()
                        return
                    continue

                if not re.match(r'^(?!.*(.).*\1)\d{4}$', number):
                    try:
                        client.send('invalid_code'.encode('ascii'))
                    except exception_connection:
                        del clients[client]
                        print('Connection torn apart')
                        client.close()
                        return
                    continue

                try:
                    client.send(f'valid_wish {number}'.encode('ascii'))
                    print('ok')
                except exception_connection:
                    del clients[client]
                    print('Connection torn apart')
                    client.close()
                    return

                session_info[client]['code'] = number
                clients[client]['state'] = 2
                print(number)

        # if clients[client]['state'] == 1:  # Загадывание числа
        #     # client.send('guess'.encode('ascii'))
        #     while True:
        #         with code_lock:
        #             if client.fileno == -1 or clients[client]['state'] != 1:
        #                 break
        #
        #             number = client.recv(1024)
        #
        #             # opponent = opponent_valid(client)
        #             # if not isinstance(opponent, socket.socket):
        #             #     break
        #
        #             # if 'code' not in session_info[client]:
        #             #     number = client.recv(1024).decode('ascii')
        #             #     if not number:
        #             #         break
        #             #     if not re.match(r'^(?!.*(.).*\1)\d{4}$', number):
        #             #         client.send('invalid'.encode('ascii'))
        #             #         continue
        #             #     client.send('valid'.encode('ascii'))
        #             #
        #             #     session_info[client]['code'] = number
        #             if number is False or number is None:
        #                 break
        #             try:
        #                 number = number.decode('ascii')
        #             except UnicodeDecodeError:
        #                 client.send('invalid_characters'.encode('ascii'))
        #                 continue
        #
        #             if not number:
        #                 client.send('invalid_length'.encode('ascii'))
        #                 continue
        #
        #             if not re.match(r'^(?!.*(.).*\1)\d{4}$', number):
        #                 client.send('invalid_code'.encode('ascii'))
        #                 continue
        #
        #             client.send('valid_wish'.encode('ascii'))
        #
        #             session_info[client]['code'] = number
        #             clients[client]['state'] = 2

        # if clients[client]['state'] == 2:  # Ожидание загадывания числа от опонента и определение первого угадывающего
        #     client.send('wait'.encode('ascii'))
        #     while True:
        #         with wait_lock:
        #             if client.fileno == -1 or clients[client]['state'] != 2:
        #                 break
        #
        #             opponent = opponent_valid(client)
        #             if not isinstance(opponent, socket.socket):
        #                 break
        #
        #             opponent_info = session_info[opponent]
        #
        #             if 'code' in opponent_info:
        #                 if 'guessing' not in session_info.get(client):
        #                     order = [opponent, client]
        #                     shuffle(order)
        #
        #                     session_info[order[0]]['guessing'] = True
        #                     session_info[order[1]]['guessing'] = False
        #
        #                     clients[client]['state'] = 3
        #                     clients[opponent]['state'] = 3
        #                 break
        # elif clients[client]['state'] == 3:  # Игра началась
        #     client.send('start'.encode('ascii'))
        #     while True:
        #         with game_lock:
        #             if client.fileno == -1 or clients[client]['state'] != 3:
        #                 break
        #
        #             opponent = opponent_valid(client)
        #             if not isinstance(opponent, socket.socket):
        #                 break
        #
        #             opponent_info = session_info[opponent]
        #             client_info = session_info[client]
        #
        #             if not client_info['guessing']:
        #                 continue
        #
        #             client.send('guess'.encode('ascii'))
        #             number = client.recv(1024).decode('ascii')
        #
        #             if not number or not re.match(r'^(?!.*(.).*\1)\d{4}$', number):
        #                 client.send('invalid'.encode('ascii'))
        #                 continue
        #             client.send('valid'.encode('ascii'))
        #
        #             bull, cow = 0, 0
        #             opponent_number = opponent_info['code']
        #
        #             for i, digit in enumerate(number):
        #                 if digit in opponent_number and i == opponent_number.find(digit):
        #                     bull += 1
        #                 elif digit in opponent_number:
        #                     cow += 1
        #
        #             client.send(f"{number} | {bull} Bull | {cow} Cow".encode('ascii'))
        #             opponent.send(f"{number} | {bull} Bull | {cow} Cow".encode('ascii'))
        #
        #             if bull == 4:
        #                 clients[client]['state'] = 4
        #                 client.send('win'.encode('ascii'))
        #                 clients[opponent]['state'] = 4
        #                 opponent.send('lose'.encode('ascii'))
        #                 opponent.send(client_info['code'].encode('ascii'))
        #                 del session_info[opponent]
        #                 del session_info[client]
        #                 break
        #
        #             session_info[client]['guessing'] = False
        #             session_info[opponent]['guessing'] = True
        # elif clients[client]['state'] == 4:  # После итога матча
        #     msg = client.recv(1024).decode('ascii')
        #     if not msg:
        #         break
        #     if msg == 'search':
        #         clients[client]['state'] = 0
        #         free_players.append(client)


def receive():
    while True:
        client, address = server.accept()
        print("Connected with {}".format(str(address)))
        print(clients)
        # print(clients[client])
        print('ok')

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


os.system('clear')
receive()
