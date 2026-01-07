import socket
import threading
import datetime  # Para las fechas
import os  # Para los archivos(leer, escribir etc..)

from proyect.Cliente.cliente import contenido

HOST = "127.0.0.1"
ARCHIVO_USUARIOS = "usuarios.txt"


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


def guardar_mensaje_en_archivo(mensaje_formateado):
    mensaje = mensaje_formateado.decode()  # Cojo el mensaje del usuario
    partes = mensaje.split(";")  # Separo el mensaje que me envia por ;
    if len(partes) >= 6:  # El mensaje que se envia es [emisor;receptor;addrs;estado;mensaje]
        emisor = partes[0]  # .replace("@","") Por si crea mal los archivos
        receptor = partes[1]
        print(f"Mensaje de {emisor} para {receptor}")

        archivo = f"{emisor}_{receptor}.txt"
        archivo_invertido = f"{receptor}_{emisor}.txt"

        if os.path.exists(archivo):  # - Comprobar con os.path.exists() si existe "remitente_destinatario.txt".
            archivo_final = archivo
        elif os.path.exists(archivo_invertido):  # - Si no, comprobar si existe "destinatario_remitente.txt".
            archivo_final = archivo_invertido
        else:
            archivo_final = archivo
        try:
            archivo_final_escribir = open(archivo_final, "a")
            archivo_final_escribir.write(mensaje + "\n")
            archivo_final_escribir.close()
            print(f"[SISTEMA] Guardado en: {archivo_final}")
        except Exception as e:
            print(f"[ERROR] {e}")
    else:
        print(f"[ERROR] El mensaje recibido no tiene el formato correcto")


# --- FUNCIONES NUEVAS NECESARIAS ---

def obtener_mensajes_pendientes(emisor, receptor, ultimo_timestamp):
    # TODO 4: Función para el UPDATE.
    # Usamos la misma logíca para abrir el archivo
    archivo = f"{emisor}_{receptor}.txt"
    archivo_invertido = f"{receptor}_{emisor}.txt"

    if os.path.exists(archivo):
        archivo_final = archivo
    elif os.path.exists(archivo_invertido):
        archivo_final = archivo_invertido
    else:
        # Si no encontramos el archivo devolvemos vacío
        return []
    mensaje = []
    try:
        # Usamos el r para leer y seguimos la misma logica usada en validar_login
        archivo_leer = open(archivo_final, "r")
        lineas = archivo_leer.readlines()
        archivo_leer.close()
        for linea in lineas:
            linea = linea.strip()
            partes = linea.split(";")
            if len(partes) >= 6:
                timestamp_mensaje = partes[2]
                # Comparó las cadenas
                if timestamp_mensaje > ultimo_timestamp:
                    mensaje.append(linea)
    except FileNotFoundError:
        return []  # Si falla devuelvo vacía
    except Exception as e:
        print(f"[ERROR LECTURA] {e}")
        return []

    return mensaje


# --- HILOS DE CONEXIÓN ---

def puerto_666():
    """Gestiona el ENVÍO de mensajes (Cliente -> Servidor)"""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, 666))
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
                    print("[ERROR] Faltan campos en el mensaje")
                    conn.send("KO".encode())
            conn.close()
            conexion_servidor = False
        except Exception as e:
            print(f"[ERROR] {e}")


def puerto_999():
    """Gestiona RECEPCIÓN y LOGIN (Cliente <-> Servidor) [cite: 21]"""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, 999))
    servidor.listen()
    print("Servidor [999]: Listo para Login y Updates.")

    while True:
        conn, addr = servidor.accept()
        datos = conn.recv(1024).decode()

        if datos.startswith("LOGIN"):
            # Gestión de Login 
            if validar_login(datos):
                conn.send("OK".encode())
            else:
                conn.send("KO".encode())

        elif "UPDATE" in datos:
            # Petición de actualización de mensajes [cite: 105]
            print(f"[999] Petición UPDATE recibida: {datos}")

            # TODO 6: Implementar protocolo de entrega de mensajes[cite: 123].
            # 1. Parsear 'datos' para sacar quién pide (Origen) y la fecha (Timestamp).
            # 2. Llamar a obtener_mensajes_pendientes().
            # 3. Enviar PRIMER mensaje: Cabecera con el número total de mensajes a enviar (en el campo texto).
            # 4. Esperar recibir "OK" del cliente.
            # 5. Bucle for mensaje in mensajes:
            #    - conn.send(mensaje)
            #    - conn.recv(1024) -> Esperar "OK" de cada mensaje.

            conn.send("OK".encode())  # Esto es temporal, borrar al hacer el TODO 6

        # TODO 7: Implementar LIST[cite: 108].
        # - Añadir un elif "LIST" in datos:
        # - Buscar todos los archivos donde aparezca el nombre del usuario.
        # - Enviar la lista siguiendo la misma lógica de bucle que el UPDATE.

        conn.close()


# --- ARRANQUE ---
hilo_envios = threading.Thread(target=puerto_666)
hilo_recibos = threading.Thread(target=puerto_999)

hilo_envios.start()
hilo_recibos.start()
