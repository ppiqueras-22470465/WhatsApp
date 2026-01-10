import socket
import threading
import time
from datetime import datetime
import os
import glob

# Configuración
SERVER_IP = "127.0.0.1"
MI_USUARIO = ""
MI_PASSWORD = ""

# --- FUNCIONES AUXILIARES ---

def obtener_timestamp():
    """Devuelve fecha hora formato YYYYMMDDhhmmss [cite: 76]"""
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S")

def formatear_mensaje(origen, destino, estado, mensaje):
    """Crea el string separado por ;"""
    ts = obtener_timestamp()
    return f"{origen};{destino};{ts};{estado};{ts};\"{mensaje}\""

def guardar_localmente(mensaje_formateado, es_temporal=False):
    """
    Guarda el mensaje en el archivo correcto: MI_USUARIO_OTROUSUARIO.txt
    (Asume que la carpeta 'Historiales' ya existe)
    """
    # try:
    #     # 1. Separar el mensaje para saber quién es el "OTRO"
    # Guarda el mensaje en el archivo correcto: MIUSUARIO_OTROUSUARIO.txt

    try:
        # 1. Separamos el mensaje para saber quién es el "OTRO"
        partes = mensaje_formateado.split(";")
        origen = partes[0].replace("@", "")
        destino = partes[1].replace("@", "")

        # Determinar con quién es el historial
        if origen == MI_USUARIO:
            otro_usuario = destino
        else:
            otro_usuario = origen

        # 2. Construir nombre del archivo
        nombre_archivo = MI_USUARIO + "_" + otro_usuario
        if es_temporal:
            nombre_archivo += "_tmp.txt"
        else:
            nombre_archivo += ".txt"

        # 3. Construir ruta manualmente (sin os.path)
        ruta = "Historiales/" + nombre_archivo

        # 4. Guardar en modo append
        f = open(ruta, "a")
        f.write(mensaje_formateado + "\n")
        f.close()

    except Exception as e:
        print(f"Error guardando archivo: {e}")

        if origen == MI_USUARIO:
            otro_usuario = destino # Si yo soy el origen, el archivo es con el destino.
        else:
            otro_usuario = origen # Si yo soy el destino, el archivo es con el origen.

        # 2. Creamos el nombre del archivo
        nombre_archivo = f"{MI_USUARIO}_{otro_usuario}"

        if es_temporal:
            nombre_archivo += "_tmp.txt"  # [cite: 57]
        else:
            nombre_archivo += ".txt"

        # 3. Guardamos en la carpeta 'historiales' para ser ordenados
        if not os.path.exists("Historiales"):
            os.makedirs("Historiales")

        ruta = os.path.join("Historiales", nombre_archivo)

        # 'a' significa append (añadir al final sin borrar lo anterior)
        with open(ruta, "a") as f:
            f.write(mensaje_formateado + "\n")
    except Exception as e:
        print(f"Error guardando archivo: {e}")
# --- FUNCIONES DE RED ---

def enviar_al_666(mensaje_formateado):
    """Envía mensaje al puerto de envíos o guarda en local si falla."""
    enviado = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((SERVER_IP, 666))
        s.send(mensaje_formateado.encode())

        resp = s.recv(1024).decode()

        if resp == "OK":
            # Si el servidor dice OK, guardamos como enviado normal
            guardar_localmente(mensaje_formateado, False)
            enviado = True
        else:
            print("Error: El servidor respondió KO")

        s.close()

    except Exception as e:
        print(f"Fallo al conectar. Guardando en modo Offline. Error: {e}")

    # Si no se pudo enviar (por excepción o por KO), guardamos en temporal
    if not enviado:
        guardar_localmente(mensaje_formateado, True)

def obtener_ultimo_timestamp_local(usuario_contacto):
    try:
        ruta = "Historiales/" + MI_USUARIO + "_" + usuario_contacto + ".txt" # Construimos la ruta manualmente

        f = open(ruta, "r") # Intentamos abrir el archivo; si no existe, saltará al except
        lineas = f.readlines() # Leemos todas las líneas
        f.close() # Cerramos el archivo

        if len(lineas) == 0: # Si el archivo está vacío, no hay mensajes previos
            return "00000000000000"

        ultima_linea = lineas[-1] # Aquí cogemos la última línea del historial y extraemos el timestamp
        partes = ultima_linea.split(";")

        if len(partes) <= 2: # Sin esto petaba, así nos aseguramos de que haya las suficientes partes en el mensaje
            return "00000000000000"
        else:
            return partes[2] # Devolvemos el timestamp original del mensaje

    except Exception:
        return "00000000000000" # Si el archivo no existe o algo falla, devolvemos timestamp cero


def procesar_mensajes_offline():
    """Revisa archivos _tmp y trata de reenviarlos."""
    if os.path.exists("Historiales"):
        # Buscar archivos temporales manualmente
        patron = os.path.join("Historiales", "*_tmp.txt")
        lista_archivos = glob.glob(patron)

        i = 0
        while i < len(lista_archivos):
            ruta_archivo = lista_archivos[i]

            # Leer las líneas del archivo temporal
            try:
                f = open(ruta_archivo, "r")
                lineas = f.readlines()
                f.close()

                archivo_procesado_correctamente = True
                j = 0

                # Intentar enviar línea por línea
                while j < len(lineas) and archivo_procesado_correctamente:
                    linea = lineas[j].strip()
                    if len(linea) > 0:
                        try:
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.settimeout(5)
                            s.connect((SERVER_IP, 666))
                            s.send(linea.encode())
                            resp = s.recv(1024).decode()
                            s.close()

                            if resp == "OK":
                                # Si se envió bien, guardar en el historial limpio
                                guardar_localmente(linea, False)
                                print(f"Mensaje recuperado y enviado: {linea}")
                            else:
                                # Si falla uno, paramos este archivo para no perder orden
                                archivo_procesado_correctamente = False
                        except:
                            archivo_procesado_correctamente = False
                    j = j + 1

                # Si todas las líneas se enviaron bien, borramos el temporal
                if archivo_procesado_correctamente:
                    os.remove(ruta_archivo)
                    print(f"Archivo temporal procesado y borrado: {ruta_archivo}")

            except Exception as e:
                print(f"Error leyendo archivo temporal {ruta_archivo}: {e}")

            i = i + 1


def gestionar_comando_lista():
    """Implementa el comando @lista con LOGIN previo."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((SERVER_IP, 999))

        # 1. HACER LOGIN
        cadena_login = f"LOGIN:{MI_USUARIO}:{MI_PASSWORD}"
        s.send(cadena_login.encode())
        resp_login = s.recv(1024).decode()

        if resp_login == "OK":
            # 2. ENVIAR PETICIÓN LIST
            msg = f"@{MI_USUARIO};@;{obtener_timestamp()};LIST;00000000000000;\"\""
            s.send(msg.encode())

            # 3. Recibir respuesta
            cabecera = s.recv(1024).decode()
            partes = cabecera.split(";")

            if len(partes) >= 6:
                cantidad_str = partes[5].replace('"', '')
                cantidad = int(cantidad_str)

                s.send("OK".encode())  # Confirmamos cabecera

                print(f"\n--- LISTA DE CONVERSACIONES ({cantidad}) ---")
                i = 0
                while i < cantidad:
                    datos_chat = s.recv(1024).decode()
                    p = datos_chat.split(";")
                    if len(p) >= 6:
                        usuario_remoto = p[0].replace("@", "")  # En LIST server manda Otro;Yo...
                        pendientes = p[5].replace('"', '')
                        print(f"{i + 1}. @{usuario_remoto} ({pendientes} mensajes nuevos)")
                    s.send("OK".encode())
                    i = i + 1
            else:
                print("Error formato lista servidor")
        else:
            print("Error: No se pudo verificar identidad para la lista.")

        s.close()
    except Exception as e:
        print(f"Error al pedir lista: {e}")


# EN cliente.py

def hilo_recepcion_actualizaciones():
    """Consulta periódicamente mensajes nuevos manteniendo la conexión abierta."""
    # Bucle principal para reconexiones
    while True:
        if MI_USUARIO != "":
            try:
                # 1. Conexión y Login (SE HACE SOLO UNA VEZ)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((SERVER_IP, 999))

                cadena_login = f"LOGIN:{MI_USUARIO}:{MI_PASSWORD}"
                s.send(cadena_login.encode())
                resp_login = s.recv(1024).decode()

                if resp_login == "OK":
                    conectado = True
                    # 2. Bucle interno: Pedir actualizaciones constantemente sin desconectarse
                    while conectado:
                        try:
                            # Pedir mensajes (Timestamp 0 para traer todo lo pendiente)
                            ts_ultimo = "00000000000000"
                            msg_update = f"{MI_USUARIO};@;{ts_ultimo};UPDATE;{ts_ultimo};\"\""
                            s.send(msg_update.encode())

                            # Recibir cabecera
                            cabecera = s.recv(1024).decode()

                            if cabecera == "":
                                conectado = False  # Servidor cerró
                            else:
                                partes = cabecera.split(";")
                                if len(partes) >= 6:
                                    cantidad_str = partes[5].replace('"', '')
                                    try:
                                        cantidad = int(cantidad_str)
                                    except:
                                        cantidad = 0

                                    s.send("OK".encode())

                                    # Recibir los mensajes individuales
                                    k = 0
                                    while k < cantidad:
                                        msg_recibido = s.recv(1024).decode()
                                        if msg_recibido:
                                            guardar_localmente(msg_recibido, False)
                                            p_msg = msg_recibido.split(";")
                                            if len(p_msg) >= 6:
                                                remitente = p_msg[0]
                                                # El mensaje es el campo 5, quitamos las comillas
                                                texto_msg = p_msg[5].replace('"', '')
                                                print(f"\n[NUEVO MENSAJE] @{remitente}: {texto_msg}")
                                            else:
                                                # Si el formato es raro, lo imprimimos tal cual
                                                print(f"\n[RAW] {msg_recibido}")
                                else:
                                    conectado = False  # Cabecera corrupta

                            # Esperamos solo 1 segundo (MENOS LATENCIA) y seguimos conectados
                            time.sleep(0.5)

                        except Exception as e:
                            print(f"Error en la conexión, reconectando... {e}")
                            conectado = False

                s.close()

            except Exception as e:
                # Si falla conectar al principio, esperamos un poco antes de reintentar
                print(f"Error al conectar al servidor: {e}")

        # Espera de seguridad antes de intentar reconectar si todo falló
        time.sleep(2)

def sistema_login():
    """Gestiona el inicio de sesión """
    global MI_USUARIO, MI_PASSWORD
    print("--- INICIO DE SESIÓN ---")
    user = input("Usuario: ")
    password = input("Contraseña: ")

    cadena_login = f"LOGIN:{user}:{password}"

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, 999))
        s.send(cadena_login.encode())

        respuesta = s.recv(1024).decode()
        s.close()

        if respuesta == "OK":
            print("Login Correcto.")
            MI_USUARIO = user
            MI_PASSWORD = password  # <--- GUARDAR LA CONTRASEÑA
            return True
        else:
            print("Login Incorrecto.")
            return False
    except:
        print("No se pudo conectar al servidor para Login.")
        return False


# --- ARRANQUE ---
if sistema_login():
    # Procesar mensajes que se quedaron colgados si se cayó la red antes
    procesar_mensajes_offline()

    # Lanzamos el hilo de recepción
    t = threading.Thread(target=hilo_recepcion_actualizaciones)
    t.daemon = True  # IMPORTANTE: Esto hace que el hilo muera al cerrar el programa principal
    t.start()

    print(f"Bienvenido {MI_USUARIO}. Escribe '@Usuario: mensaje' para chatear.")

    seguir_ejecutando = True

    while seguir_ejecutando:
        texto = input()

        if texto.strip() == "@salir":
            print("Cerrando sesión y saliendo...")
            seguir_ejecutando = False
            # Al ser t.daemon = True, el hilo se cerrará solo al salir de este bucle.

        elif texto.lower().startswith("@lista"):
            gestionar_comando_lista()

        elif texto.startswith("@") and ":" in texto:
            partes = texto.split(":", 1)
            destinatario = partes[0]
            contenido = partes[1].strip()

            msg_final = formatear_mensaje(MI_USUARIO, destinatario, "ENVIADO", contenido)
            enviar_al_666(msg_final)
        else:
            print("Formato incorrecto. Usa: @Nombre: Mensaje")