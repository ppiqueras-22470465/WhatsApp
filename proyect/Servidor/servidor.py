import socket
import threading

# Dirección IP y puerto

ip = socket.gethostbyname(socket.gethostname()) # Esto lo hago de forma dinámica
socket_send = 666
socket_receive = 999
addr = (ip, socket_receive)
connection = True
connection_client = True
client_list = []
disconnect_msg = "!DISCONNECT"

def handle_client(client_socket, addr):
    global connection_client
    print(f"[NEW CONNECTION] {addr} CONNECTED.")
    while connection_client:
        message = client_socket.recv(1024).decode()
        if message == disconnect_msg:
            connection_client = False
            client_socket.close()
        else:
            client_list.append(client_socket)
            print(f"[{addr}] {message}")
            message = f"[MESSAGE RECEIVED] {message}]"
            client_socket.send(message.encode())
        client_socket.close()



def server():
    global addr
    print("[STARTING] I AM GETTING UP")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(addr)
    server.listen()
    print(f"[LISTENING] I AM LISTENING IN {ip}:{socket_receive}")

    while connection:
        num_clients = 0
        connection_client, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(connection_client, addr))
        thread.start()
        client_list.append(connection_client)
        num_clients += 1
        print(f"[ACTIVE CONNECTIONS] {num_clients}")

server()

