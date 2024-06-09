import socket
import traceback
from threading import Thread
import mysql.connector
from tcpbysize import recv_by_size, send_with_size
from diffie_hellman import DIFFIEHELLMAN
from AES import ENCRYPTION
import hashlib

db = mysql.connector.connect(host="localhost", user="root", passwd="jonatan65", database="dueldb")
cursor = db.cursor(buffered=True)
insert_user_formula = "INSERT INTO users (username, password) VALUES (%s, %s)"
check_username_formula = "SELECT * FROM users WHERE username = %s"
check_connection = "SELECT connection FROM users WHERE username = %s"
update_connection = "UPDATE users SET connection = %s, address = %s WHERE username = %s;"
check_connected_users = "SELECT * FROM users WHERE connection = \"connected\""
get_user_by_address = "SELECT * FROM users WHERE address = %s"
update_connection_by_address = "UPDATE users SET connection = %s WHERE address = %s;"


connection_stat = ["connected", "disconnected"]
clients_socks = {}
rooms = {}


def check_length(data):
    if len(data) < 4:
        return "ERRR~001~Communication error"
    return ''


def encrypt_db(data, aes: ENCRYPTION):
    encryption = aes.encrypt(data)
    encryption = [str(element) for element in encryption]
    print(encryption)
    return "|||".join(encryption)


def decrypt_db(nonce, text, tag, aes: ENCRYPTION):
    return aes.decrypt((nonce, text, tag))


def handle_protocol(data, addr, aes: ENCRYPTION):
    data_split = data.split('~')
    if data == 'LOST':
        return "", "WINN"

    elif data_split[0] == 'USRN':
        cursor.execute(check_username_formula, (data_split[1], ))
        user = cursor.fetchone()
        if user is None:
            return "", "ERRR~002~No such user"
        return "", "SUCC"

    elif data_split[0] == 'PSSW':
        cursor.execute(check_username_formula, (data_split[1], ))
        user = cursor.fetchone()
        if hashlib.sha256(data_split[2].encode()).hexdigest() != user[1]:
            return "", "ERRR~003~Password is not correct"
        if addr[0] == "127.0.0.1":
            cursor.execute(update_connection, (connection_stat[0], socket.gethostbyname(socket.gethostname()), data_split[1]))
        else:
            cursor.execute(update_connection, (connection_stat[0], addr[0], data_split[1]))
        return "", "SUCC"

    elif data_split[0] == 'DCON':
        cursor.execute(update_connection, (connection_stat[1], "", data_split[1]))
        return "", "SUCC"

    elif data_split[0] == 'NEWU':
        cursor.execute(check_username_formula, (data_split[1], ))
        user = cursor.fetchone()
        if user is not None:
            return "", "ERRR~004~Already such user"
        cursor.execute(insert_user_formula, (data_split[1], hashlib.sha256(data_split[2].encode()).hexdigest()))
        return "", "SUCC"

    elif data == 'USR2':
        cursor.execute(check_connected_users)
        users = cursor.fetchall()
        if len(users) < 2:
            return "", "ERRR~005~no connected users"
        users_str = "CONU~"
        for user in users:
            users_str += user[0] + "~"
        return "", users_str[:-1]

    elif data_split[0] == "RQST":
        cursor.execute(check_username_formula, (data_split[1],))
        user = cursor.fetchone()
        if user[3] == "connected":
            if addr[0] == "127.0.0.1":
                return f"both|{user[2]}", f"CONC~{data_split[2]}~{socket.gethostbyname(socket.gethostname())}"
            return f"both|{user[2]}", f"CONC~{data_split[2]}~{addr[0]}"
        else:
            return '', "ERRR~006~client is not connected"

    elif data_split[0] == "PLAY":
        cursor.execute(get_user_by_address, (data_split[1],))
        user = cursor.fetchone()
        if user[3] == "connected":
            if addr[0] == "127.0.0.1":
                return f"both|{data_split[1]}", f"ACPT~{data_split[1]}~{socket.gethostbyname(socket.gethostname())}"
            return f"both|{data_split[1]}", f"ACPT~{data_split[1]}~{addr[0]}"
        else:
            return '', "ERRR~007~player had disconnected"

    else:
        return "", data


def handle_client(sock, tid, addr, aes):
    print(f'New Client from {addr}')
    while True:
        second_addr = ''
        try:
            byte_data = recv_by_size(sock, aes, True)
            if byte_data == '':
                print('Seems client disconnected')
                if addr[0] == "127.0.0.1":
                    cursor.execute(update_connection_by_address, (connection_stat[1],
                                                                  socket.gethostbyname(socket.gethostname())))
                else:
                    cursor.execute(update_connection_by_address, (connection_stat[1], addr[0]))
                db.commit()
                break
            err_size = check_length(byte_data)
            if err_size != '':
                to_send = err_size
            else:
                second_addr, to_send = handle_protocol(byte_data, addr, aes)
                db.commit()
            if to_send != '':
                if second_addr == '':
                    send_with_size(sock, to_send, aes, True)
                elif second_addr[:4] == "both":
                    send_with_size(sock, to_send, aes)
                    send_with_size(clients_socks[second_addr[5:]], to_send, aes)
                else:
                    send_with_size(clients_socks[second_addr], to_send, aes)
        except socket.error as err:
            print(f'Socket Error exit client loop: err:  {err}')
            break
        except Exception as err:
            print(f'General Error %s exit client loop: {err}')
            print(traceback.format_exc())
            break

    print(f'Client {tid} Exit')
    sock.close()


def main():
    threads = []
    dp_hellman = DIFFIEHELLMAN()

    srv_sock = socket.socket()
    srv_sock.setblocking(True)
    srv_sock.bind(('0.0.0.0', 42069))
    srv_sock.listen()
    # next line release the port
    srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    private_a = dp_hellman.get_private_number()
    public_num = dp_hellman.get_public_number(private_a)

    i = 1
    while True:
        print('\nMain thread: before accepting ...')
        cli_sock, addr = srv_sock.accept()

        if addr[0] == "127.0.0.1":
            clients_socks[socket.gethostbyname(socket.gethostname())] = cli_sock
        else:
            clients_socks[addr[0]] = cli_sock

        # encryption initiation
        send_with_size(cli_sock, str(public_num), None)
        public_num_b = int(recv_by_size(cli_sock, None))
        private_key = dp_hellman.get_private_key(public_num_b, private_a)
        aes = ENCRYPTION(private_key)

        t = Thread(target=handle_client, args=(cli_sock, i, addr, aes))
        t.start()
        i += 1
        threads.append(t)
        if i > 100:  # for tests change to 4
            print('\nMain thread: going down for maintenance')
            break

    print('Main thread: waiting to all clients to die')
    for t in threads:
        t.join()
    srv_sock.close()
    print('Bye ..')


if __name__ == "__main__":
    main()
