import socket
import threading
import datetime
import time

# Hacer una lista de los mensajes en la que se comuncaran los hilos esta lista es un recurso compartido controlada por un semaforo
# cuando yo tengo un error de conexión se machaca,

ip_servidor = "127.0.0.1"
archivo_usuarios = "usuarios.txt"
port_999 = 999
port_666 = 666
lista_mensajes = []

sem_lista_mensajes = threading.Semaphore(1)


# --- FUNCIONES AUXILIARES (LÓGICA) ---

def validar_login(usuario, password):
    encontrado = False
    try:
        archivo = open(archivo_usuarios, "r")
        archivo_leido = archivo.readlines()
        archivo.close()
        i = 0
        while i < len(archivo_leido) and encontrado == False:
            archivo_leido_sin_espacios = archivo_leido[i].strip()
            if len(archivo_leido_sin_espacios) > 0:
                partes = archivo_leido_sin_espacios.split(":")  # Esta puesto por que es lo que uso para separar las cosas en usuarios.txt
                if len(partes) == 2:
                    usuario_archivo = partes[0]
                    password_archivo = partes[1]
                    if usuario_archivo == usuario and password_archivo == password:
                        encontrado = True
            i = i + 1
    except FileNotFoundError:
        print(f"[LOGIN] No he encontrado el archivo{archivo_usuarios}")
    return encontrado


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


def ordenar_mensajes(lista_mensajes):  # Lo ordeno como has pasado en el anuncio
    diccionario = {}
    for i in lista_mensajes:
        lista_mensajes_limpia = i.strip()
        if len(lista_mensajes_limpia) > 0:
            partes = lista_mensajes_limpia.split(";")
            if len(partes) == 6:  # Esto lo he hecho según los campos que pone en el PDF
                emisor = partes[0]
                receptor = partes[1]
                timestamp = partes[2]
                mensaje = partes[5].replace("\n", "")
                clave = timestamp + emisor + receptor + mensaje
                diccionario[clave] = lista_mensajes_limpia
    claves_ordenadas = sorted(diccionario)
    lista_mensajes_limpia_ordenada = []
    for i in claves_ordenadas:
        mensaje_original = diccionario[i]
        lista_mensajes_limpia_ordenada.append(mensaje_original)
    return lista_mensajes_limpia_ordenada

def obtener_mensajes_pendientes(emisor, receptor, ultimo_timestamp):
    archivo = validar_archivo(emisor, receptor)
    mensajes = []
    mensajes_finales = []
    leido = False
    while not leido:
        if sem_lista_mensajes.acquire(timeout=2):
            try:
                archivo_leer = open(archivo, "r")
                mensajes = archivo_leer.readlines()
                archivo_leer.close()
                sem_lista_mensajes.release()
                leido = True
            except FileNotFoundError:
                sem_lista_mensajes.release()
                leido = True

        else:
            time.sleep(1)
    lista_ordenada = ordenar_mensajes(mensajes)
    for i in lista_ordenada:
        partes = i.split(";")
        if len(partes)>=6:
            timestamp = partes[2]
            if timestamp > ultimo_timestamp:
                mensajes_finales.append(i)
        else:
            print(f"[ERROR-UPDATE] El formato de los mensajes es incorrecto")

    return mensajes_finales


def guardar_mensaje_en_archivo(mensaje_formateado):
    mensaje = mensaje_formateado.decode()
    partes = mensaje.split(";")
    if len(partes) >= 6:
        emisor = partes[0].replace("@", "")
        receptor = partes[1].replace("@", "")
        print(f"[SISTEMA] Mensaje de {emisor} para {receptor}")
        archivo_final = validar_archivo(emisor, receptor)
        guardado = False


        while not guardado:
            if sem_lista_mensajes.acquire(timeout=2):
                try:
                    # --- PARTE A: GUARDAR EL MENSAJE ---
                    archivo_final_escribir = open(archivo_final, "a")
                    archivo_final_escribir.write(mensaje + "\n")
                    archivo_final_escribir.close()
                    print(f"[SISTEMA] Guardado en: {archivo_final}")

                    # --- PARTE B: ACTUALIZAR EL ÍNDICE ---
                    chat_registrado = False
                    try:
                        indice = open("indice_chats.txt", "r")
                        indice_chats = indice.readlines()
                        indice.close()

                        # Buscamos si ya existe en la lista
                        for i in range(len(indice_chats)):
                            if indice_chats[i].strip() == archivo_final:
                                chat_registrado = True
                    except FileNotFoundError:
                        chat_ya_registrado = False

                    # --- ESCRIBIR EN EL ÍNDICE (Corrección de tu bug) ---
                    if chat_registrado == False:
                        nuevo_indice = open("indice_chats.txt", "a")
                        nuevo_indice.write(archivo_final + "\n")
                        nuevo_indice.close()
                        print(f"[SISTEMA] Nuevo chat registrado")

                    sem_lista_mensajes.release()
                    guardado = True

                except Exception as e:
                    print(f"[ERROR GUARDADO] {e}")
                    sem_lista_mensajes.release()
                    guardado = True
            else:
                time.sleep(1)
    else:
        print(f"[ERROR] El mensaje recibido no tiene el formato correcto")


# --- FUNCIONES NUEVAS NECESARIAS ---

# Envió de mensajes
def puerto_666():
    """Gestiona el ENVÍO de mensajes (Cliente -> Servidor)"""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((servidor, port_666))
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
    servidor.bind((servidor, port_999))
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
                    usuario = partes[1].replace("@", "")
                    password = partes[2].replace("@", "")
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

hilo_envios.join()
hilo_recibos.join()

print(f"[SERVIDOR - {port_666}] El servidor se encuentra escuchando por el {port_666}")
print(f"[SERVIDOR - {port_666}] El servidor se encuentra escuchando por el {port_999}")

