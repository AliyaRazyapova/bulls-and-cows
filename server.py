import socket
import threading
from time import sleep
import re
from random import shuffle


searching_lock = threading.Lock()
client_init_lock = threading.Lock()
wait_lock = threading.Lock()
game_lock = threading.Lock()

host = '127.0.0.1'
port = 6090

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = {}
free_players = []
session_info = {}


def handle(client):
    def opponent_valid(client_1):
        opponent_1 = session_info[client_1]['opponent']
        if opponent_1.fileno() == -1:
            clients[client_1]['state'] = 4
            del session_info[client_1]
            del session_info[opponent_1]
            return False
        return opponent_1

    exception_connection = (ConnectionResetError, ConnectionAbortedError, ConnectionRefusedError)

    while True:
        if client.fileno() == -1:
            return

        if client not in clients:
            try:
                nickname = client.recv(1024)
            except exception_connection:
                print('Connection torn apart')
                client.close()
                del clients[client]
                return

            try:
                nickname = nickname.decode('ascii')
            except UnicodeDecodeError:
                try:
                    client.send('latin_characters'.encode('ascii'))
                except exception_connection:
                    print('Connection torn apart')
                    client.close()
                    del clients[client]
                    return
                continue

            with client_init_lock:
                for c in clients:
                    if c.fileno == -1:
                        del clients[c]
                        if clients[c]['nickname'] == nickname:
                            break
                    if clients[c]['nickname'] == nickname:
                        try:
                            client.send('repeat_nickname'.encode('ascii'))
                        except exception_connection:
                            print('Connection torn apart')
                            client.close()
                            del clients[client]
                            return
                        continue
                clients[client] = {'nickname': nickname, 'state': 4}
            try:
                client.send(f'authorized_nickname {nickname}'.encode('ascii'))
            except exception_connection:
                print('Connection torn apart')
                client.close()
                del clients[client]
                return

        if clients[client]['state'] == 0:
            while True:
                with searching_lock:
                    print('tes', free_players)
                    print('gsfkj', session_info)
                    print('fkj', clients)

                    if client.fileno() == -1:
                        break
                    if client not in clients or clients[client]['state'] != 0:
                        break

                    for opponent in free_players:
                        if opponent != client:
                            if opponent.fileno() == -1:
                                continue

                            free_players.remove(client)
                            free_players.remove(opponent)

                            session_info[client] = {'opponent': opponent}
                            session_info[opponent] = {'opponent': client}

                            clients[client]['state'] = 1
                            clients[opponent]['state'] = 1

                            try:
                                client.send(f"game {clients[opponent]['nickname']}".encode('ascii'))
                            except exception_connection:
                                client.close()
                                print('Connection refused cln')
                                break

                            try:
                                opponent.send(f"game {clients[client]['nickname']}".encode('ascii'))
                            except exception_connection:
                                opponent.close()
                                print('Connection refused opp')
                            break

        elif clients[client]['state'] == 1:
            while True:
                opponent = opponent_valid(client)
                if not isinstance(opponent, socket.socket):
                    try:
                        client.send('opponent_leave'.encode('ascii'))
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

                if number is False or number is None:
                    break
                try:
                    number = number.decode('ascii')
                except UnicodeDecodeError:
                    try:
                        client.send('latin_characters'.encode('ascii'))
                    except exception_connection:
                        del clients[client]
                        print('Connection torn apart')
                        client.close()
                        return
                    continue

                if not number:
                    try:
                        client.send('length'.encode('ascii'))
                    except exception_connection:
                        del clients[client]
                        print('Connection torn apart')
                        client.close()
                        return
                    continue

                if not re.match(r'^(?!.*(.).*\1)\d{4}$', number):
                    try:
                        client.send('four_unique_digits'.encode('ascii'))
                    except exception_connection:
                        del clients[client]
                        print('Connection torn apart')
                        client.close()
                        return
                    continue

                try:
                    client.send(f'authorized_opponennt {number}'.encode('ascii'))
                except exception_connection:
                    del clients[client]
                    print('Connection torn apart')
                    client.close()
                    return

                session_info[client]['code'] = number
                clients[client]['state'] = 2

        elif clients[client]['state'] == 2:
            while True:
                with wait_lock:
                    if client.fileno() == -1 or clients[client]['state'] != 2:
                        break

                    opponent = opponent_valid(client)
                    if not isinstance(opponent, socket.socket):
                        try:
                            client.send('opponent_leave'.encode('ascii'))
                        except exception_connection:
                            del clients[client]
                        clients[client]['state'] = 4
                        break

                    opponent_info = session_info[opponent]

                    if 'code' in opponent_info:
                        if 'guessing' not in session_info.get(client):
                            order = [opponent, client]
                            shuffle(order)

                            session_info[order[0]]['guessing'] = True
                            session_info[order[1]]['guessing'] = False

                            clients[client]['state'] = 3
                            clients[opponent]['state'] = 3

                            try:
                                order[0].send('first_move'.encode('ascii'))
                            except exception_connection:
                                del clients[order[0]]
                                order[0].close()
                                try:
                                    order[1].send('opponent_leave'.encode('ascii'))
                                except exception_connection:
                                    del clients[order[1]]
                                    order[1].close()
                                    print('both conn torn apart')
                                    return
                                print('first conn torn apart')
                                continue
                            try:
                                order[1].send('second_move'.encode('ascii'))
                            except exception_connection:
                                del clients[order[1]]
                                order[1].close()
                                try:
                                    order[0].recv(1024)
                                    order[0].send('opponent_leave'.encode('ascii'))
                                except exception_connection:
                                    del clients[order[0]]
                                    order[0].close()
                                    print('both conn torn apart')
                                    return
                                print('second conn torn apart')
                        break

        elif clients[client]['state'] == 3:
            while True:
                opponent = opponent_valid(client)
                try:
                    number = client.recv(1024)
                except exception_connection:
                    print('Connection torn apart')
                    client.close()
                    opponent.send('opponent_leave'.encode('ascii'))
                    return
                print(number.decode('ascii'), 3)
                if number.decode('ascii') == 'search':
                    clients[client]['state'] = 0
                    with searching_lock:
                        free_players.append(client)
                    break
                if client.fileno() == -1:
                    break
                if clients[client]['state'] != 3:
                    break

                client_info = session_info[client]
                if not client_info['guessing']:
                    continue

                opponent = opponent_valid(client)
                if not isinstance(opponent, socket.socket):
                    clients[client]['state'] = 4
                    break

                with game_lock:
                    opponent_info = session_info[opponent]

                    try:
                        number = number.decode('ascii')
                    except UnicodeDecodeError:
                        try:
                            client.send('latin_characters'.encode('ascii'))
                        except exception_connection:
                            del clients[client]
                            client.close()
                            print('Connection torn apart')
                        continue

                    if not number or not re.match(r'^(?!.*(.).*\1)\d{4}$', number):
                        try:
                            client.send('four_unique_digits'.encode('ascii'))
                        except exception_connection:
                            del clients[client]
                            client.close()
                            print('Connection torn apart')
                        continue

                    bull = 0
                    cow = 0
                    opponent_number = opponent_info['code']

                    for i, digit in enumerate(number):
                        if digit in opponent_number and i == opponent_number.find(digit):
                            bull += 1
                        elif digit in opponent_number:
                            cow += 1

                    try:
                        client.send(f"{number} | {bull} Bull | {cow} Cow".encode('ascii'))
                    except exception_connection:
                        del clients[client]
                        client.close()
                        try:
                            opponent.send('opponent_leave'.encode('ascii'))
                            clients[opponent]['state'] = 4
                        except exception_connection:
                            del clients[opponent]
                            print('Both conn torn apart')
                            opponent.close()
                            return
                        print('client conn torn apart')
                        continue

                    if bull == 4:
                        clients[client]['state'] = 4
                        clients[opponent]['state'] = 4
                        del session_info[opponent]
                        del session_info[client]
                        try:
                            opponent.send(f"loser {client_info['code']}".encode('ascii'))
                        except exception_connection:
                            opponent.close()
                        try:
                            client.send('winner'.encode('ascii'))
                        except exception_connection:
                            del clients[client]
                            client.close()
                        break
                    else:
                        try:
                            client.send('expectation'.encode('ascii'))
                        except exception_connection:
                            del clients[client]
                            client.close()
                            try:
                                opponent.send('opponent_leave'.encode('ascii'))
                            except exception_connection:
                                del clients[opponent]
                                opponent.close()
                            break
                        try:
                            opponent.send('queue'.encode('ascii'))
                        except exception_connection:
                            del clients[opponent]
                            opponent.close()
                            try:
                                client.send('opponent_leave'.encode('ascii'))
                            except exception_connection:
                                del clients[client]
                                client.close()
                            break

                    session_info[client]['guessing'] = False
                    session_info[opponent]['guessing'] = True

        elif clients[client]['state'] == 4:
            try:
                message = client.recv(1024).decode('ascii')
            except exception_connection:
                client.close()
                print('Connection torn apart')
                del clients[client]
                return
            print(message, 4)
            if not message:
                break
            if message == 'search':
                clients[client]['state'] = 0
                with searching_lock:
                    free_players.append(client)


def receive():
    while True:
        client, address = server.accept()
        print("Connected with {}".format(str(address)))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


receive()
