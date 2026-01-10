import socket
import threading
import time
from datetime import datetime

# --- CONFIGURACIÓN ---
SERVER_IP = "127.0.0.1"
PUERTO_ENVIOS = 666
PUERTO_RECEPCION = 999

# Variables Globales
MI_USUARIO = ""
MI_PASSWORD = ""
CONECTADO = False


# --- 1. FUNCIONES LOCALES ---

def obtener_timestamp():
    """Genera fecha/hora para el protocolo."""
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S")


def guardar_localmente(mensaje_formateado):
    """Guarda en fichero sin usar OS ni pass."""
    exito = False
    try:
        partes = mensaje_formateado.split(";")
        if len(partes) >= 6:
            origen = partes[0].replace("@", "")
            destino = partes[1].replace("@", "")

            # Determinar el nombre del otro usuario
            if origen == MI_USUARIO:
                otro = destino
            else:
                otro = origen

            nombre_archivo = f"{MI_USUARIO}_{otro}.txt"

            # Escribir en modo append
            archivo = open(nombre_archivo, "a")
            archivo.write(mensaje_formateado + "\n")
            archivo.close()
            exito = True
    except Exception as e:
        print(f"[ERROR LOCAL] {e}")

    return exito


def obtener_ultimo_timestamp_local(amigo):
    """Busca el timestamp más alto sin usar break."""
    ts_max = "00000000000000"
    nombre_archivo = f"{MI_USUARIO}_{amigo}.txt"

    try:
        archivo = open(nombre_archivo, "r")
        lineas = archivo.readlines()
        archivo.close()

        # Recorremos todas las líneas con un while para no usar break
        i = 0
        while i < len(lineas):
            linea = lineas[i]
            partes = linea.split(";")
            if len(partes) >= 6:
                ts = partes[2]
                if ts > ts_max:
                    ts_max = ts
            i = i + 1

    except FileNotFoundError:
        # No usamos pass, simplemente asignamos un valor dummy o imprimimos
        ts_max = "00000000000000"
    except Exception:
        ts_max = "00000000000000"

    return ts_max


# --- 2. FUNCIONES DE RED ---

def enviar_mensaje(destinatario, texto):
    """Envía mensaje al 666."""
    ts = obtener_timestamp()
    mensaje_final = f"{MI_USUARIO};{destinatario};{ts};ENVIADO;{ts};{texto}"

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, PUERTO_ENVIOS))

        s.send(mensaje_final.encode())
        respuesta = s.recv(1024).decode()
        s.close()

        if respuesta == "OK":
            guardar_localmente(mensaje_final)
            print(f"[OK] Enviado a {destinatario}")
        else:
            print(f"[ERROR] Servidor rechazó el mensaje")

    except Exception as e:
        print(f"[OFFLINE] Error de conexión: {e}")


def hilo_actualizador():
    """Bucle en segundo plano. Controlado por variable booleana."""
    while CONECTADO:
        try:
            # Pausa para no saturar
            time.sleep(5)

            # Conexión
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_IP, PUERTO_RECEPCION))

            # Login
            s.send(f"LOGIN;{MI_USUARIO};{MI_PASSWORD}".encode())
            resp_login = s.recv(1024).decode()

            if resp_login == "OK":
                # Pedir LISTA
                s.send("LIST".encode())
                lista_raw = s.recv(4096).decode()

                if lista_raw != "VACIO":
                    lista_archivos = lista_raw.split("#")

                    # Iteramos la lista de chats
                    i = 0
                    while i < len(lista_archivos):
                        archivo = lista_archivos[i]

                        # Solo procesamos si tiene contenido (evitamos continue)
                        if len(archivo) > 0:
                            amigo = archivo.replace(".txt", "").replace(MI_USUARIO, "").replace("_", "")

                            if len(amigo) > 0:
                                # Pedir UPDATE
                                ts_ultimo = obtener_ultimo_timestamp_local(amigo)
                                s.send(f"UPDATE;{amigo};{ts_ultimo}".encode())

                                datos_nuevos = s.recv(4096).decode()

                                if datos_nuevos != "VACIO" and datos_nuevos != "ERROR FORMATO":
                                    mensajes = datos_nuevos.split("#")

                                    # Procesar mensajes recibidos
                                    j = 0
                                    while j < len(mensajes):
                                        m = mensajes[j]
                                        if len(m) > 5:
                                            guardar_localmente(m)
                                            p = m.split(";")
                                            if len(p) >= 6:
                                                print(f"\n[NUEVO] @{p[0]}: {p[5]}")
                                                print(">> ", end="")
                                        j = j + 1

                        # Avanzamos índice
                        i = i + 1

            s.close()

        except Exception as e:
            # En lugar de pass, imprimimos error (opcional)
            # print(f"Error background: {e}")
            error_detectado = True

        # --- 3. EJECUCIÓN PRINCIPAL ---


print("--- CLIENTE WHATSAPP ---")

MI_USUARIO = input("Usuario: ")
MI_PASSWORD = input("Contraseña: ")

login_exitoso = False

# Intentamos login inicial
try:
    sock_test = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_test.connect((SERVER_IP, PUERTO_RECEPCION))
    sock_test.send(f"LOGIN;{MI_USUARIO};{MI_PASSWORD}".encode())
    resp = sock_test.recv(1024).decode()
    sock_test.close()

    if resp == "OK":
        login_exitoso = True
except Exception as e:
    print(f"Error conectando al servidor: {e}")
    login_exitoso = False

if login_exitoso:
    print(f"Bienvenido {MI_USUARIO}.")
    CONECTADO = True

    # Arrancar hilo
    hilo = threading.Thread(target=hilo_actualizador)
    hilo.start()

    print("Escribe '@Usuario: Mensaje' o 'SALIR'")

    # Bucle Principal controlado por bandera
    while CONECTADO:
        try:
            texto = input(">> ")

            if texto == "SALIR":
                CONECTADO = False
                print("Cerrando...")
            else:
                if texto.startswith("@") and ":" in texto:
                    partes = texto.split(":", 1)
                    destinatario = partes[0].replace("@", "").strip()
                    contenido = partes[1].strip()
                    enviar_mensaje(destinatario, contenido)
                else:
                    print("Formato incorrecto.")

        except Exception:
            print("Error en entrada de datos.")
            CONECTADO = False

else:
    print("Login fallido o servidor apagado.")

# Espera final para cerrar limpio sin usar join a lo bruto
if login_exitoso:
    try:
        # Esperamos un poco a que el hilo lea la variable CONECTADO = False
        time.sleep(2)
    except Exception:
        error_cierre = True