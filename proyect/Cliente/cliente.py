import socket
import threading
import time
from datetime import datetime
import os
import glob

# Configuración inicial del cliente
SERVER_IP = "127.0.0.1"
MI_USUARIO = ""
MI_PASSWORD = ""


# --- FUNCIONES AUXILIARES ---

def obtener_timestamp():
    """Generamos la marca de tiempo actual."""
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S")


def formatear_mensaje(origen, destino, estado, mensaje):
    """Creamos la cadena de texto con el formato CSV requerido."""
    ts = obtener_timestamp()
    return f"{origen};{destino};{ts};{estado};{ts};\"{mensaje}\""


def guardar_localmente(mensaje_formateado, es_temporal=False):
    """Guardamos el mensaje en nuestro historial local o lo actualizamos."""
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
                    # Si coincide timestamp y contenido, actualizamos el estado
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
    """Enviamos el mensaje al servidor o lo guardamos localmente si falla."""
    enviado = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((SERVER_IP, 666))
        s.send(mensaje_formateado.encode())

        resp = s.recv(1024).decode()

        if resp == "OK":
            guardar_localmente(mensaje_formateado, False)
            enviado = True
        else:
            print("Error: El servidor respondió KO")

        s.close()

    except Exception as e:
        print(f"Fallo al conectar. Guardando en modo Offline. Error: {e}")

    if not enviado:
        guardar_localmente(mensaje_formateado, True)


def obtener_ultimo_timestamp_local(usuario_contacto):
    """Consultamos cuándo fue el último mensaje registrado en local."""
    try:
        ruta = "Historiales/" + MI_USUARIO + "_" + usuario_contacto + ".txt"

        f = open(ruta, "r")
        lineas = f.readlines()
        f.close()

        if len(lineas) == 0:
            return "00000000000000"

        ultima_linea = lineas[-1]
        partes = ultima_linea.split(";")

        if len(partes) <= 2:
            return "00000000000000"
        else:
            return partes[2]

    except Exception:
        return "00000000000000"


def procesar_mensajes_offline():
    """Revisamos los archivos temporales para reintentar el envío."""
    if os.path.exists("Historiales"):
        patron = os.path.join("Historiales", "*_tmp.txt")
        lista_archivos = glob.glob(patron)

        i = 0
        while i < len(lista_archivos):
            ruta_archivo = lista_archivos[i]

            try:
                f = open(ruta_archivo, "r")
                lineas = f.readlines()
                f.close()

                archivo_procesado_correctamente = True
                j = 0

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
                                guardar_localmente(linea, False)
                                print(f"Mensaje recuperado y enviado: {linea}")
                            else:
                                archivo_procesado_correctamente = False
                        except:
                            archivo_procesado_correctamente = False
                    j = j + 1

                if archivo_procesado_correctamente:
                    os.remove(ruta_archivo)
                    print(f"Archivo temporal procesado y borrado: {ruta_archivo}")

            except Exception as e:
                print(f"Error leyendo archivo temporal {ruta_archivo}: {e}")

            i = i + 1


def gestionar_comando_lista():
    """Solicitamos la lista de usuarios y mensajes pendientes al servidor."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((SERVER_IP, 999))

        cadena_login = f"LOGIN:{MI_USUARIO}:{MI_PASSWORD}"
        s.send(cadena_login.encode())
        resp_login = s.recv(1024).decode()

        if resp_login == "OK":
            msg = f"@{MI_USUARIO};@;{obtener_timestamp()};LIST;00000000000000;\"\""
            s.send(msg.encode())

            cabecera = s.recv(1024).decode()
            partes = cabecera.split(";")

            if len(partes) >= 6:
                cantidad_str = partes[5].replace('"', '')
                cantidad = int(cantidad_str)

                s.send("OK".encode())

                print(f"\n--- LISTA DE CONVERSACIONES ({cantidad}) ---")
                i = 0
                while i < cantidad:
                    datos_chat = s.recv(1024).decode()
                    p = datos_chat.split(";")
                    if len(p) >= 6:
                        usuario_remoto = p[0].replace("@", "")
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


def hilo_recepcion_actualizaciones():
    """Consultamos periódicamente al servidor en segundo plano."""
    ts_ultimo = "00000000000000"
    servidor_era_inaccesible = False  # Bandera para controlar el aviso de reconexión

    while True:
        if MI_USUARIO != "":
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((SERVER_IP, 999))

                # Si llegamos aquí, la conexión ha tenido éxito
                if servidor_era_inaccesible:
                    print("\n[INFO] ¡Servidor online de nuevo!")
                    servidor_era_inaccesible = False

                cadena_login = f"LOGIN:{MI_USUARIO}:{MI_PASSWORD}"
                s.send(cadena_login.encode())
                resp_login = s.recv(1024).decode()

                if resp_login == "OK":
                    conectado = True
                    while conectado:
                        try:
                            msg_update = f"{MI_USUARIO};@;{ts_ultimo};UPDATE;{ts_ultimo};\"\""
                            s.send(msg_update.encode())

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

                                    k = 0
                                    max_ts_lote = ts_ultimo

                                    while k < cantidad:
                                        msg_recibido = s.recv(1024).decode()
                                        if msg_recibido:
                                            guardar_localmente(msg_recibido, False)

                                            p_msg = msg_recibido.split(";")
                                            if len(p_msg) >= 6:
                                                remitente = p_msg[0].replace("@", "")
                                                ts_msg = p_msg[4]

                                                if ts_msg > max_ts_lote:
                                                    max_ts_lote = ts_msg

                                                if remitente != MI_USUARIO:
                                                    texto_msg = p_msg[5].replace('"', '')
                                                    print(f"\n[NUEVO MENSAJE] @{remitente}: {texto_msg}")

                                            s.send("OK".encode())
                                        else:
                                            k = cantidad
                                            conectado = False
                                        k = k + 1

                                    ts_ultimo = max_ts_lote
                                else:
                                    conectado = False

                            time.sleep(0.5)

                        except Exception as e:
                            conectado = False

                s.close()

            except Exception as e:
                # Si fallamos al conectar, activamos la bandera
                servidor_era_inaccesible = True
                # print(f"Error al intentar conectar: {e}")

        time.sleep(2)


def sistema_login():
    """Gestionamos el inicio de sesión del usuario."""
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
            MI_PASSWORD = password
            return True
        else:
            print("Login Incorrecto.")
            return False
    except:
        print("No se pudo conectar al servidor para Login.")
        return False


def sistema_registro():
    """Gestionamos el registro de un nuevo usuario en el sistema."""
    print("--- REGISTRO DE USUARIO NUEVO ---")
    user = input("Nuevo Usuario: ")
    password = input("Nueva Contraseña: ")

    cadena_registro = f"REGISTER:{user}:{password}"

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, 999))
        s.send(cadena_registro.encode())

        respuesta = s.recv(1024).decode()
        s.close()

        if respuesta == "OK":
            print("Registro Correcto. Ahora puedes iniciar sesión.")
        else:
            print("Registro Fallido (El usuario quizá ya existe).")
    except:
        print("No se pudo conectar al servidor para Registro.")


def enviar_confirmacion_leido(usuario_destino):
    """Notificamos al servidor que hemos abierto una conversación."""
    try:
        msg = formatear_mensaje(MI_USUARIO, "@" + usuario_destino, "LEIDO", "CONFIRMACION")
        enviar_al_666(msg)
    except Exception as e:
        print(f"No se pudo confirmar lectura: {e}")


# --- ARRANQUE PRINCIPAL ---

acceso_concedido = False

# Bucle del menú inicial para elegir entre Login o Registro
while acceso_concedido == False:
    print("1. Login")
    print("2. Registro")
    opcion = input("Elige una opción: ")

    if opcion == "1":
        if sistema_login():
            acceso_concedido = True
    elif opcion == "2":
        sistema_registro()
    else:
        print("Opción no válida.")

if acceso_concedido:
    procesar_mensajes_offline()

    t = threading.Thread(target=hilo_recepcion_actualizaciones)
    t.daemon = True
    t.start()

    print(f"Bienvenido {MI_USUARIO}.")
    # Imprimimos la lista de comandos disponibles
    print("--- COMANDOS DISPONIBLES ---")
    print("1. @lista           -> Ver usuarios y mensajes pendientes")
    print("2. @salir           -> Cerrar programa")
    print("3. @Usuario: texto  -> Enviar mensaje")
    print("----------------------------")

    seguir_ejecutando = True

    while seguir_ejecutando:
        texto = input()

        if texto.strip() == "@salir":
            print("Cerrando sesión y saliendo...")
            seguir_ejecutando = False

        elif texto.lower().startswith("@lista"):
            gestionar_comando_lista()

        elif texto.startswith("@") and ":" in texto:
            partes = texto.split(":", 1)
            destinatario = partes[0].replace("@", "")
            contenido = partes[1].strip()

            enviar_confirmacion_leido(destinatario)
            msg_final = formatear_mensaje(MI_USUARIO, destinatario, "ENVIADO", contenido)
            enviar_al_666(msg_final)