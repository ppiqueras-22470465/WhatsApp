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
    """Guarda o ACTUALIZA un mensaje en el historial."""
    try:
        partes = mensaje_formateado.split(";")
        if len(partes) >= 6:
            origen = partes[0].replace("@", "")
            destino = partes[1].replace("@", "")
            ts_msg = partes[2]

            if origen == MI_USUARIO:
                otro = destino
            else:
                otro = origen

            nombre = MI_USUARIO + "_" + otro
            if es_temporal:
                nombre += "_tmp.txt"
            else:
                nombre += ".txt"

            if not os.path.exists("Historiales"):
                os.makedirs("Historiales")

            ruta = "Historiales/" + nombre

            lineas_finales = []
            ya_existe = False

            if os.path.exists(ruta):
                f = open(ruta, "r")
                lineas = f.readlines()
                f.close()

                i = 0
                while i < len(lineas):
                    linea = lineas[i].strip()
                    p_lin = linea.split(";")
                    # Si coincide timestamp y contenido, actualizamos estado
                    if len(p_lin) >= 6 and p_lin[2] == ts_msg and p_lin[5] == partes[5]:
                        lineas_finales.append(mensaje_formateado)
                        ya_existe = True
                    else:
                        lineas_finales.append(linea)
                    i = i + 1

            if not ya_existe:
                lineas_finales.append(mensaje_formateado)

            f = open(ruta, "w")
            for l in lineas_finales:
                f.write(l + "\n")
            f.close()

    except Exception as e:
        print(f"Error guardando: {e}")

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

    # Inicializamos el timestamp a 0 solo al arrancar el programa
    ts_ultimo = "00000000000000"

    while True:  # Bucle de reconexión
        if MI_USUARIO != "":
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((SERVER_IP, 999))

                cadena_login = f"LOGIN:{MI_USUARIO}:{MI_PASSWORD}"
                s.send(cadena_login.encode())
                resp_login = s.recv(1024).decode()

                if resp_login == "OK":
                    conectado = True
                    # Bucle interno: Pedir actualizaciones constantemente
                    while conectado:
                        try:
                            # Pedimos SOLO lo posterior a lo último que recibimos
                            msg_update = f"{MI_USUARIO};@;{ts_ultimo};UPDATE;{ts_ultimo};\"\""
                            s.send(msg_update.encode())

                            # Recibir cabecera
                            cabecera = s.recv(1024).decode()

                            if cabecera == "":
                                conectado = False
                            else:
                                partes = cabecera.split(";")
                                if len(partes) >= 6:
                                    cantidad_str = partes[5].replace('"', '')
                                    try:
                                        cantidad = int(cantidad_str)
                                    except:
                                        cantidad = 0

                                    s.send("OK".encode())

                                    # Recibir mensajes
                                    k = 0
                                    # Variable temporal para guardar el timestamp más reciente de este lote
                                    max_ts_lote = ts_ultimo

                                    while k < cantidad:
                                        msg_recibido = s.recv(1024).decode()
                                        if msg_recibido:
                                            guardar_localmente(msg_recibido, False)

                                            # Analizar mensaje
                                            p_msg = msg_recibido.split(";")
                                            if len(p_msg) >= 6:
                                                remitente = p_msg[0].replace("@", "")
                                                # El timestamp de estado es el campo 4 (índice 4)
                                                ts_msg = p_msg[4]

                                                # Actualizamos el control de tiempo si este mensaje es más nuevo
                                                if ts_msg > max_ts_lote:
                                                    max_ts_lote = ts_msg

                                                # VISUALIZACIÓN:
                                                # Solo imprimimos si NO soy yo el remitente (evita el eco)
                                                if remitente != MI_USUARIO:
                                                    texto_msg = p_msg[5].replace('"', '')
                                                    print(f"\n[NUEVO MENSAJE] @{remitente}: {texto_msg}")

                                            s.send("OK".encode())
                                        else:
                                            k = cantidad
                                            conectado = False
                                        k = k + 1

                                    # Actualizamos el timestamp global para la siguiente petición
                                    ts_ultimo = max_ts_lote
                                else:
                                    conectado = False

                            # Esperamos un poco
                            time.sleep(0.5)

                        except Exception as e:
                            # Si da timeout o error, salimos del bucle interno para reconectar
                            # print(f"Reconectando... {e}") # Descomenta para depurar
                            conectado = False

                s.close()

            except Exception as e:
                print(f"Error al intentar conectar: {e}")

        # Espera de seguridad antes de intentar reconectar
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

def enviar_confirmacion_leido(usuario_destino):
    """Avisa al servidor de que hemos abierto el chat con usuario_destino[cite: 90]."""
    try:
        # Enviamos un mensaje especial con estado LEIDO
        # Formato: YO;@OTRO;ts;LEIDO;ts;"CONFIRMACION"
        msg = formatear_mensaje(MI_USUARIO, "@" + usuario_destino, "LEIDO", "CONFIRMACION")

        # Usamos el puerto 666 que es para enviar cambios/mensajes
        enviar_al_666(msg)
    except Exception as e:
        print(f"No se pudo confirmar lectura: {e}")


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

            enviar_confirmacion_leido(destinatario)

            msg_final = formatear_mensaje(MI_USUARIO, destinatario, "ENVIADO", contenido)
            enviar_al_666(msg_final)
        else:
            print("Formato incorrecto. Usa: @Nombre: Mensaje")