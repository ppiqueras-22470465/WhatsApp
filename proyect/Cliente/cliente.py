import socket
import threading
import time
from datetime import datetime

# --- CONFIGURACIÓN ---
ip_servidor = "127.0.0.1"
puerto_envios = 666
puerto_recepcion = 999

# Variables de Estado
mi_usuario = ""
mi_password = ""
conectado = False


# --- 1. FUNCIONES AUXILIARES ---

def obtener_timestamp():
    """Genera fecha/hora formato YYYYMMDDhhmmss."""
    ahora = datetime.now()
    return ahora.strftime("%Y%m%d%H%M%S")


def registrar_contacto_local(amigo):
    """
    Actualiza mis_contactos.txt sin usar glob ni os.
    """
    ya_existe = False
    try:
        archivo = open("mis_contactos.txt", "r")
        contactos = archivo.readlines()
        archivo.close()

        i = 0
        while i < len(contactos) and not ya_existe:
            if contactos[i].strip() == amigo:
                ya_existe = True
            i = i + 1

    except FileNotFoundError:
        ya_existe = False
    except Exception:
        # Truco para no usar pass: Asignación inútil
        a = 0

        # Si no está, escribimos
    if not ya_existe:
        try:
            archivo_add = open("mis_contactos.txt", "a")
            archivo_add.write(amigo + "\n")
            archivo_add.close()
        except Exception:
            a = 0  # No hacemos nada


def guardar_localmente(mensaje_formateado):
    """Guarda en historial y actualiza lista de contactos."""
    exito = False
    try:
        partes = mensaje_formateado.split(";")
        if len(partes) >= 6:
            origen = partes[0].replace("@", "")
            destino = partes[1].replace("@", "")

            if origen == mi_usuario:
                otro = destino
            else:
                otro = origen

            nombre_archivo = f"Historiales/{mi_usuario}_{otro}.txt"
            archivo = open(nombre_archivo, "a")
            archivo.write(mensaje_formateado + "\n")
            archivo.close()

            # 2. Registrar contacto
            registrar_contacto_local(otro)

            exito = True
    except Exception as e:
        print(f"[ERROR DISCO] {e}")

    return exito


def obtener_ultimo_timestamp_local(amigo):
    """Obtiene el último timestamp del archivo local."""
    ts_max = "00000000000000"
    nombre_archivo = f"{mi_usuario}_{amigo}.txt"

    try:
        archivo = open(nombre_archivo, "r")
        lineas = archivo.readlines()
        archivo.close()

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
        ts_max = "00000000000000"
    except Exception:
        ts_max = "00000000000000"

    return ts_max


def mostrar_lista_contactos():
    """Muestra los contactos leyendo el archivo índice."""
    print("\n --- LISTA DE CONVERSACIONES ---")
    try:
        archivo = open("mis_contactos.txt", "r")
        lineas = archivo.readlines()
        archivo.close()

        if len(lineas) == 0:
            print(" (No tienes conversaciones iniciadas)")
        else:
            i = 0
            while i < len(lineas):
                nombre = lineas[i].strip()
                if len(nombre) > 0:
                    print(f" {i + 1}- @{nombre}")
                i = i + 1
    except FileNotFoundError:
        print(" (No tienes conversaciones iniciadas)")
    except Exception:
        print(" [Error leyendo contactos]")

    print(" -------------------------------\n")


# --- 2. FUNCIONES DE RED (PUERTO 666) ---

def enviar_mensaje(destinatario, texto):
    """Envía mensaje al servidor."""
    ts = obtener_timestamp()
    mensaje_final = f"{mi_usuario};{destinatario};{ts};ENVIADO;{ts};{texto}"

    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((ip_servidor, puerto_envios))

        cliente.send(mensaje_final.encode())
        respuesta = cliente.recv(1024).decode()
        cliente.close()

        if respuesta == "OK":
            guardar_localmente(mensaje_final)
            print(f" [✓] Enviado")
        else:
            print(f" [X] Error: Servidor rechazó el mensaje.")

    except Exception as e:
        print(f" [!] Error de conexión: {e}")


# --- 3. HILO AUTOMÁTICO (PUERTO 999) ---

def hilo_actualizador():
    """
    Gestiona LIST y UPDATE en segundo plano cada 5 segundos.
    """
    while conectado:
        try:
            # Espera fragmentada para cerrar rápido si salimos
            contador = 0
            while contador < 50 and conectado:
                time.sleep(0.1)
                contador = contador + 1

            if conectado:
                cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cliente.connect((ip_servidor, puerto_recepcion))

                # Login
                cliente.send(f"LOGIN:{mi_usuario}:{mi_password}".encode())
                resp_login = cliente.recv(1024).decode()

                if resp_login == "OK":

                    # --- A. COMANDO LIST ---
                    ts = obtener_timestamp()
                    cmd_list = f"{mi_usuario};@;{ts};LIST;{ts};\"\""
                    cliente.send(cmd_list.encode())

                    # 1. Cabecera Cantidad
                    cabecera_list = cliente.recv(1024).decode()
                    partes_cab = cabecera_list.split(";")

                    if len(partes_cab) >= 6:
                        cant_str = partes_cab[5].replace('"', '')
                        if cant_str.isdigit():
                            cantidad_chats = int(cant_str)
                        else:
                            cantidad_chats = 0

                        # 2. Confirmar Cantidad
                        cliente.send("OK".encode())

                        chats_para_actualizar = []

                        # 3. Recibir Items
                        k = 0
                        while k < cantidad_chats:
                            msg_chat = cliente.recv(1024).decode()
                            cliente.send("OK".encode())

                            p_chat = msg_chat.split(";")
                            if len(p_chat) >= 6:
                                # Limpiar nombre "Yo_Otro" -> "Otro"
                                nombre_archivo_chat = p_chat[1]
                                amigo_limpio = nombre_archivo_chat.replace(mi_usuario, "").replace("_", "")

                                if len(amigo_limpio) > 0:
                                    chats_para_actualizar.append(amigo_limpio)
                            k = k + 1

                        # --- B. COMANDO UPDATE ---
                        m = 0
                        while m < len(chats_para_actualizar):
                            amigo = chats_para_actualizar[m]

                            if len(amigo) > 0:
                                ts_ultimo = obtener_ultimo_timestamp_local(amigo)

                                cmd_upd = f"{mi_usuario};{amigo};{ts};UPDATE;{ts};\"{ts_ultimo}\""
                                cliente.send(cmd_upd.encode())

                                # 1. Cabecera Cantidad
                                cabecera_upd = cliente.recv(1024).decode()
                                p_cab_upd = cabecera_upd.split(";")

                                if len(p_cab_upd) >= 6:
                                    cant_msg_str = p_cab_upd[5].replace('"', '')
                                    if cant_msg_str.isdigit():
                                        cant_msgs = int(cant_msg_str)
                                    else:
                                        cant_msgs = 0

                                    # 2. Confirmar Cantidad
                                    cliente.send("OK".encode())

                                    # 3. Recibir Mensajes
                                    n = 0
                                    while n < cant_msgs:
                                        msg_nuevo = cliente.recv(1024).decode()
                                        cliente.send("OK".encode())

                                        if len(msg_nuevo) > 0:
                                            guardar_localmente(msg_nuevo)

                                            pm = msg_nuevo.split(";")
                                            if len(pm) >= 6:
                                                estado = pm[3]
                                                remitente = pm[0]
                                                texto = pm[5]

                                                # Mostrar solo si es RECIBIDO y no soy yo
                                                if estado == "RECIBIDO" and remitente != mi_usuario:
                                                    print(f"\n\n [NUEVO] @{remitente}: {texto}")
                                                    print(" >> ", end="")
                                        n = n + 1
                            m = m + 1

                cliente.close()

        except Exception:
            # Aquí usamos el truco. "a = 0" no hace nada pero evita el error de bloque vacío.
            a = 0


# --- 4. EJECUCIÓN PRINCIPAL ---

print("\n=======================================")
print("      TERMINAL WHATSAPP - CLIENTE      ")
print("=======================================\n")

mi_usuario = input(" Introduce tu Usuario: ")
mi_password = input(" Introduce tu Contraseña: ")

login_exitoso = False

print("\n Conectando con el servidor...")

# Login inicial
try:
    sock_test = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_test.connect((ip_servidor, puerto_recepcion))
    sock_test.send(f"LOGIN:{mi_usuario}:{mi_password}".encode())
    resp = sock_test.recv(1024).decode()
    sock_test.close()

    if resp == "OK":
        login_exitoso = True
except Exception as e:
    print(f" [ERROR] No se pudo conectar: {e}")
    login_exitoso = False

if login_exitoso:
    print(f" [OK] ¡Bienvenido/a {mi_usuario}!")
    print(" ---------------------------------------")
    print("  1. Escribir:    @Amigo: Hola")
    print("  2. Ver chats:   @lista")
    print("  3. Salir:       @salir")
    print(" ---------------------------------------")

    conectado = True

    # Hilo Background
    hilo = threading.Thread(target=hilo_actualizador)
    hilo.start()

    # Bucle Principal
    while conectado:
        try:
            texto = input(" >> ")

            if len(texto) > 0:
                if texto == "@salir":
                    print(" Cerrando sesión...")
                    try:
                        s_salida = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s_salida.connect((ip_servidor, puerto_envios))
                        s_salida.send("!DESCONECTAR".encode())
                        s_salida.close()
                    except Exception:
                        a = 0  #Lo he puesto para que no haga nada
                    conectado = False

                # --- COMANDO LISTA ---
                elif texto == "@lista":
                    mostrar_lista_contactos()

                # --- ENVIAR MENSAJE ---
                # Comprobamos índice 0 y existencia de dos puntos
                elif texto[0] == "@" and ":" in texto:

                    partes = texto.split(":", 1)

                    # Quitamos la '@' del inicio
                    destinatario_sucio = partes[0]
                    destinatario = destinatario_sucio[1:].strip()

                    contenido = partes[1].strip()

                    if len(destinatario) > 0 and len(contenido) > 0:
                        enviar_mensaje(destinatario, contenido)
                    else:
                        print(" [!] Mensaje vacío.")

                else:
                    if conectado:
                        print(" [!] Formato incorrecto.")

        except Exception:
            conectado = False

    time.sleep(1)
    print("\n [FIN] Programa cerrado.")

else:
    print(" [X] Login incorrecto o servidor apagado.")