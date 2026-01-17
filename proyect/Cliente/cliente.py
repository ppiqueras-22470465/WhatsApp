import socket
import threading
import time
import datetime

# --- CONFIGURACION ---
SERVER_IP = "127.0.0.1"
PORT_999 = 999
PORT_666 = 666

MI_USUARIO = ""
MI_PASSWORD = ""
TIMEOUT_VAL = 15.0

# Variable global para controlar el hilo de fondo
SESION_ACTIVA = False


# --- FUNCIONES AUXILIARES ---

def obtener_timestamp():
    """Genera la marca de tiempo para el protocolo."""
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def es_entrada_segura(texto):
    """Valida que no haya caracteres que rompan el protocolo."""
    valido = True
    if ":" in texto or ";" in texto or texto.strip() == "":
        valido = False
    return valido


# --- FUNCIONES DE COMUNICACION ---

def enviar_mensaje(destinatario, contenido):
    """Envia un mensaje de texto al puerto 666."""
    try:
        ts = obtener_timestamp()
        # Protocolo: Origen;Destino;TS;Estado;TS;"Contenido"
        msg = MI_USUARIO + ";" + destinatario + ";" + ts + ";RECIBIDO;" + ts + ";\"" + contenido + "\""

        cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cli.settimeout(TIMEOUT_VAL)
        cli.connect((SERVER_IP, PORT_666))
        cli.send(msg.encode())

        respuesta = cli.recv(1024).decode()
        if respuesta == "OK":
            print("[INFO] Mensaje entregado al servidor para @" + destinatario)
        else:
            print("[ERROR] El servidor rechazo el mensaje.")
        cli.close()
    except Exception as e:
        print(f"Ha ocurrido un error en el archivo: {e}")


def gestionar_lista():
    """Solicita la lista de CONTACTOS DISPONIBLES (usuarios registrados)."""
    try:
        cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cli.settimeout(TIMEOUT_VAL)
        cli.connect((SERVER_IP, PORT_999))

        # Login silencioso para permiso
        cli.send(("LOGIN:" + MI_USUARIO + ":" + MI_PASSWORD).encode())
        if cli.recv(1024).decode() == "OK":
            ts = obtener_timestamp()
            # Pedimos LIST
            cli.send(("@" + MI_USUARIO + ";@;" + ts + ";LIST;" + ts + ";\"\"").encode())

            datos_cabecera = cli.recv(1024).decode()
            cabecera = datos_cabecera.split(";")

            if len(cabecera) >= 6:
                cantidad_str = cabecera[5].replace('"', '')
                try:
                    cantidad = int(cantidad_str)
                except Exception:
                    cantidad = 0

                cli.send("OK".encode())

                print("\n--- LISTA DE CONTACTOS DISPONIBLES (" + str(cantidad) + ") ---")
                i = 0
                while i < cantidad:
                    nombre_usuario = cli.recv(1024).decode()
                    print("[" + str(i + 1) + "] @" + nombre_usuario)
                    cli.send("OK".encode())
                    i = i + 1
                print("---------------------------------------------")
        cli.close()
    except Exception as e:
        print(f"Ha ocurrido un error en el archivo: {e}")


def hilo_actualizaciones():
    """Hilo en segundo plano que descarga mensajes nuevos automaticamente."""
    while SESION_ACTIVA == True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)  # Timeout corto para el hilo de fondo
            s.connect((SERVER_IP, PORT_999))

            # Login rapido
            s.send(("LOGIN:" + MI_USUARIO + ":" + MI_PASSWORD).encode())
            if s.recv(1024).decode() == "OK":

                # Pedir actualizaciones (UPDATE)
                ts = obtener_timestamp()
                s.send(("@" + MI_USUARIO + ";@;" + ts + ";UPDATE;" + ts + ";\"\"").encode())

                # Recibir cantidad
                cabecera = s.recv(1024).decode().split(";")
                if len(cabecera) >= 6:
                    cantidad = int(cabecera[5].replace('"', ''))
                    s.send("OK".encode())

                    # Si hay mensajes, recibirlos uno a uno
                    i = 0
                    while i < cantidad:
                        msg_raw = s.recv(1024).decode()
                        partes = msg_raw.split(";")
                        if len(partes) >= 6:
                            remitente = partes[0].replace("@", "")
                            texto = partes[5].replace('"', '')
                            print(f"\n[NUEVO MENSAJE] @{remitente}: {texto}")
                            print("> ", end="", flush=True)  # Restaurar prompt

                        s.send("OK".encode())
                        i = i + 1
            s.close()
        except Exception:
            # Silenciamos errores de red en el hilo secundario
            x = 0  # No hacemos nada (simula pass)

        # Esperar 2 segundos antes de volver a preguntar
        time.sleep(2)


# --- SISTEMA DE MENUS ---

def sistema_acceso():
    global MI_USUARIO, MI_PASSWORD
    acceso_concedido = False
    menu_activo = True

    while menu_activo == True:
        print("\n=== BIENVENIDO AL SISTEMA DE MENSAJERIA ===")
        print("1. Iniciar Sesion")
        print("2. Registrar una cuenta nueva")
        print("3. Salir")
        seleccion = input("Seleccione una opcion (1-3): ")

        if seleccion == "3":
            menu_activo = False

        elif seleccion == "1" or seleccion == "2":
            user = input("Usuario: ")
            pw = input("Contraseña: ")

            if es_entrada_segura(user) == True and es_entrada_segura(pw) == True:
                try:
                    cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    cli.settimeout(TIMEOUT_VAL)
                    cli.connect((SERVER_IP, PORT_999))

                    comando = "LOGIN"
                    if seleccion == "2":
                        comando = "REGISTER"

                    msg_auth = comando + ":" + user + ":" + pw
                    cli.send(msg_auth.encode())

                    resp = cli.recv(1024).decode()
                    if resp == "OK":
                        if seleccion == "1":
                            print("[SISTEMA] Login correcto. Sesion iniciada.")
                            MI_USUARIO = user
                            MI_PASSWORD = pw
                            acceso_concedido = True
                            menu_activo = False
                        else:
                            print("[SISTEMA] Cuenta creada con exito. Por favor, inicie sesion.")
                    else:
                        print("[ERROR] Operacion denegada (Credenciales invalidas o usuario ya existente).")

                    cli.close()
                except Exception as e:
                    print(f"Ha ocurrido un error en el archivo: {e}")
            else:
                print("[SISTEMA] Los datos contienen caracteres no permitidos.")
        else:
            print("[SISTEMA] Opcion no valida.")

    return acceso_concedido


# --- BLOQUE PRINCIPAL ENCAPSULADO ---

def cliente():
    global SESION_ACTIVA
    conectado = True
    while conectado == True:
        if sistema_acceso() == True:
            print("\n[INFO] Cliente listo. Los mensajes llegaran automaticamente.")
            print("Comandos disponibles:")
            print(" - @usuario: mensaje  : Enviar un mensaje.")
            print(" - @lista             : Ver contactos disponibles.")
            print(" - @salir             : Cerrar el programa.")

            # --- INICIO DEL HILO AUTOMATICO ---
            SESION_ACTIVA = True
            t_hilo = threading.Thread(target=hilo_actualizaciones)
            t_hilo.start()
            # ----------------------------------

            bucle_principal = True
            while bucle_principal == True:
                try:
                    texto = input("> ")

                    if texto == "@salir":
                        print("[SISTEMA] Cerrando sesion...")
                        SESION_ACTIVA = False  # Detenemos el hilo
                        bucle_principal = False
                        conectado = False  # Salimos del programa completo

                    elif texto == "@lista":
                        gestionar_lista()

                    elif "@" in texto and ":" in texto:
                        partes = texto.split(":", 1)
                        dest = partes[0].replace("@", "").strip()
                        cont = partes[1].strip()

                        if cont != "":
                            enviar_mensaje(dest, cont)
                        else:
                            print("[SISTEMA] No se permite enviar mensajes vacios.")

                    else:
                        if texto.strip() != "":
                            print("[SISTEMA] Formato desconocido.")
                except Exception as e:
                    print(f"Ha ocurrido un error en el archivo: {e}")
                    SESION_ACTIVA = False
                    bucle_principal = False
                    conectado = False

            # Esperamos a que el hilo se cierre ordenadamente antes de salir
            t_hilo.join()
        else:
            # Si en el menu eligieron salir (opcion 3)
            conectado = False

    print("[SISTEMA] Aplicación finalizada.")


# Ejecutamos la funcion principal
cliente()