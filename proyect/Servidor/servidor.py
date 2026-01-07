import socket
import threading
import datetime  # Para las fechas

HOST = "127.0.0.1"
ARCHIVO_USUARIOS = "usuarios.txt"
PORT_999=999
PORT_666=666


# --- FUNCIONES AUXILIARES (LÓGICA) ---

def validar_login(usuario_recibido, clave_recibida):
    try:
        archivo = open(ARCHIVO_USUARIOS, "r")
        lineas = archivo.readlines()
        archivo.close()

        for linea in lineas:
            linea = linea.strip()  # Quito los espacios vacío
            if linea:  # Sí sigue habiendo línea
                partes = linea.split(":")  # Como está separado por : los leemos así
                if len(partes) == 2:  # Si el formato es válido
                    if partes[0] == usuario_recibido and partes[
                        1] == clave_recibida:  # Sí coinciden usuario y contraseña
                        return True
            else:
                print(f"[ERROR] No se encuentra el archivo {ARCHIVO_USUARIOS}")

        return False
    except FileNotFoundError:
        print(f"[ERROR] No se encuentra el archivo {ARCHIVO_USUARIOS}")

# Con esta función me quito de usar la libreria os y la verifico yo
def validar_archivo(emisor, receptor):
    archivo = f"{emisor}_{receptor}.txt"
    archivo_invertido = f"{receptor}_{emisor}.txt"

    try:
        archivo_final = open(archivo, "r")
        archivo_final.close()
        archivo_final = archivo
    except FileNotFoundError:
        try:
            archivo_final = open(archivo_invertido, "r")
            archivo_final.close()
            archivo_final = archivo_invertido
        except FileNotFoundError:
            archivo_final = archivo

    return archivo_final
#
# def obtener_mensajes_pendientes(emisor, receptor ,ultimo_timestamp):
#     archivo_final = validar_archivo(emisor, receptor)
#     mensaje = []
#     try:
#         # Usamos el r para leer y seguimos la misma logica usada en validar_login
#         archivo_leer = open(archivo_final, "r")
#         lineas = archivo_leer.readlines()
#         archivo_leer.close()
#         for linea in lineas:
#             linea = linea.strip()
#             partes = linea.split(";")
#             if len(partes) >= 6:
#                 timestamp_mensaje = partes[2]
#                 # Comparó las cadenas
#                 if timestamp_mensaje > ultimo_timestamp:
#                     mensaje.append(linea)
#
#     except FileNotFoundError:
#         return []  # Si falla devuelvo vacía
#     except Exception as e:
#         print(f"[ERROR LECTURA] {e}")
#         return []
#
#     return mensaje

# def guardar_mensaje_en_archivo(mensaje_formateado):
#     mensaje = mensaje_formateado.decode()  # Cojo el mensaje del usuario
#     partes = mensaje.split(";")  # Separo el mensaje que me envia por ;
#     if len(partes) >= 6:  # El mensaje que se envia es [emisor;receptor;addrs;estado;mensaje]
#         emisor = partes[0].replace("@", "")
#         receptor = partes[1].replace("@", "")
#         print(f"Mensaje de {emisor} para {receptor}")
#         archivo_final = validar_archivo(emisor,receptor)
#
#         try:
#             archivo_final_escribir = open(archivo_final, "a")
#             archivo_final_escribir.write(mensaje + "\n")
#             archivo_final_escribir.close()
#             print(f"[SISTEMA] Guardado en: {archivo_final}")
#             chat_creado = False
#             try:
#                 indice = open("indice_chats.txt", "r")
#                 indice_chats = indice.readlines()
#                 indice.close()
#                 # Me lo recorro en busqueda de la conversación
#                 for i in range(len(indice_chats)):
#                     if indice_chats[i].strip() == archivo_final:
#                         chat_creado = True
#
#             except FileNotFoundError:
#                 chat_creado = False
#             # Si no he encontrado el chat lo tengo que crear
#             if chat_creado == False:
#                 chat_creado = False
#
#         except Exception as e:
#             print(f"[ERROR] {e}")
#     else:
#         print(f"[ERROR] El mensaje recibido no tiene el formato correcto")


# --- FUNCIONES NUEVAS NECESARIAS ---



# Envió de mensajes
def puerto_666():
    """Gestiona el ENVÍO de mensajes (Cliente -> Servidor)"""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, PORT_666))
    servidor.listen()
    print("Servidor [666]: Listo para recibir mensajes.")

    conexion_servidor = True

    while conexion_servidor:
        try:
            conn, addr = servidor.accept()
            mensaje = conn.recv(1024).decode()

            if mensaje != "":
                print(f"[666] Recibido: {mensaje}")
                partes = mensaje.split(";")
                if mensaje == "!DESCONECTAR":
                    print(f"[666] Apagando")
                    conn.send(f"[666] Apagando".encode())
                    conexion_servidor = False
                # Implementamos las logica como en los anteriores
                elif len(partes) >= 6:
                    emisor = partes[0]
                    receptor = partes[1]
                    timestamp_original = partes[2]  # Para poder actualizar la hora
                    contenido_mensaje = partes[5]
                    nuevo_estado = "RECIBIDO"
                    ahora = datetime.datetime.now()
                    nuevo_timestamp_estado = ahora.strftime("%Y%m%d%H%M%S")

                    mensaje_procesado = (
                            emisor + ";" +
                            receptor + ";" +
                            timestamp_original + ";" +
                            nuevo_estado + ";" +
                            nuevo_timestamp_estado + ";" +
                            contenido_mensaje
                    )

                    guardar_mensaje_en_archivo(mensaje_procesado.encode())
                    conn.send("OK".encode())
                else:
                    print("[ERROR-666] Faltan campos en el mensaje")
                    conn.send("KO".encode())
            conn.close()
            conexion_servidor = False
        except Exception as e:
            print(f"[ERROR-666] {e}")

# Login update y la lista
def puerto_999():
    """Gestiona RECEPCIÓN y LOGIN (Cliente <-> Servidor) [cite: 21]"""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, PORT_999))
    servidor.listen()
    print("Servidor [999]: Listo para Login y Updates.")
    while True:
        conn, addr = servidor.accept()
        print(f"[999] Conexión desde {addr}")

        login_ok = False
        conexion_cliente = True

        while conexion_cliente:
            datos = conn.recv(1024).decode().strip()

            if datos == "":
                conexion_cliente = False

            elif datos.startswith("LOGIN"):
                partes = datos.split(":")
                if len(partes) == 3:
                    usuario = partes[1]
                    password = partes[2]
                    if validar_login(usuario, password):
                        conn.send("OK".encode())
                        login_ok = True
                    else:
                        conn.send("KO".encode())

            elif datos.startswith("UPDATE") and login_ok:
                print(f"[999] UPDATE recibido de {usuario}")
                conn.send("OK".encode())

            elif datos.startswith("LIST") and login_ok:
                print(f"[999] LIST recibido de {usuario}")
                conn.send("OK".encode())


            else:
                print("[ERROR-999] Petición no válida o sin login")
                conn.send("KO".encode())

        conn.close()

# --- ARRANQUE ---
hilo_envios = threading.Thread(target=puerto_666)
hilo_recibos = threading.Thread(target=puerto_999)

hilo_envios.start()
hilo_recibos.start()
