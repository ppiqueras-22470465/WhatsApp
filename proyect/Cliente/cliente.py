import socket
# Dirección IP y puerto

ip = socket.gethostbyname(socket.gethostname()) # Esto lo hago de forma dinámica
socket_send = 666
socket_receive = 999
addr = (ip, socket_receive)
client_list = []
disconnect_msg = "!DISCONNECT"

def client_connection():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(addr)
    print(f"[CONNECTED TO] CLIENT CONNECTED TO SERVER AT {ip}:{socket_receive}")
    connection = True
    while connection:
        message = input("> ")
        client.send(message.encode())
        if message == disconnect_msg:
            connection = False
        else:
            message = client.recv(1024).decode()
            print(f"[SERVER] {message}")
client_connection()