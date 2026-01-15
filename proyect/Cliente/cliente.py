import socket
import threading
import datetime
import time
import os  # <--- AÑADIDO PARA GESTIONAR ARCHIVOS MEJOR

# --- CONFIGURACION ---
ip_servidor = "127.0.0.1"
port_envios = 666
port_recepcion = 999

mi_usuario = ""
mi_password = ""
conectado = False

# SEMAFORO DEL PROFESOR (Binario)
sem_archivo = threading.Semaphore(1)


# --- FUNCIONES ---

def obtener_timestamp():
<<<<<<< HEAD
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
=======
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")
>>>>>>> 8594f0e78a7aac95dce665376959dc83413e4e4b


def registrar_contacto_local(amigo):
    # Intentamos entrar hasta que nos deje usando flag booleano
    guardado = False
    while not guardado:
        # Probamos coger el semaforo 1 segundo
        if sem_archivo.acquire(timeout=1):
            try:
                ya_existe = False
                # Usamos OS para ver si existe
                if os.path.exists("mis_contactos.txt"):
                    try:
                        f = open("mis_contactos.txt", "r")
                        lines = f.readlines()
                        f.close()

                        i = 0
                        while i < len(lines) and not ya_existe:
                            if lines[i].strip() == amigo:
                                ya_existe = True
                            i = i + 1
                    except:
                        error = True  # Evitamos pass

                if not ya_existe:
                    try:
                        f = open("mis_contactos.txt", "a")
                        f.write(amigo + "\n")
                        f.close()
                    except:
                        error = True
            finally:
                # IMPORTANTE: Soltarlo siempre
                sem_archivo.release()
                guardado = True
        else:
            # Si estaba ocupado, esperamos un poco
            time.sleep(0.1)


<<<<<<< HEAD
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

=======
def guardar_localmente(msg):
    if not msg or len(msg.strip()) == 0:
        return False

    escrito = False
    otro_usuario = ""
>>>>>>> 8594f0e78a7aac95dce665376959dc83413e4e4b

    # Aseguramos que la carpeta existe con OS
    if not os.path.exists("Historiales"):
        try:
            os.mkdir("Historiales")
        except:
            error = True

    # 1. PRIMER PASO: GUARDAR EL MENSAJE
    while not escrito:
        if sem_archivo.acquire(timeout=1):
            try:
                partes = msg.split(";")
                if len(partes) >= 6:
                    origen = partes[0].replace("@", "")
                    destino = partes[1].replace("@", "")

                    if origen == mi_usuario:
                        otro = destino
                    else:
                        otro = origen

                    otro_usuario = otro  # Lo guardamos para luego

                    # Rutas con OS.PATH (Mas seguro)
                    nombre_f1 = f"{mi_usuario}_{otro}.txt"
                    nombre_f2 = f"{otro}_{mi_usuario}.txt"

                    ruta1 = os.path.join("Historiales", nombre_f1)
                    ruta2 = os.path.join("Historiales", nombre_f2)

                    archivo_final = ruta1

<<<<<<< HEAD

        elif texto.startswith("@") and ":" in texto:
            partes = texto.split(":", 1)
            # CORRECCIÓN: Quitamos la @ aquí para tener el nombre limpio
            destinatario = partes[0].replace("@", "")
            contenido = partes[1].strip()
            # Ahora enviamos el nombre limpio (la función ya le pone la @ necesaria)
            enviar_confirmacion_leido(destinatario)
            msg_final = formatear_mensaje(MI_USUARIO, destinatario, "ENVIADO", contenido)
            enviar_al_666(msg_final)
=======
                    # Verificamos existencia con OS
                    if os.path.exists(ruta2):
                        archivo_final = ruta2
                    else:
                        archivo_final = ruta1

                    f = open(archivo_final, "a")
                    f.write(msg.strip() + "\n")
                    f.close()
            except:
                error = True
            finally:
                sem_archivo.release()
                escrito = True
        else:
            time.sleep(0.1)

    # 2. SEGUNDO PASO: REGISTRAR CONTACTO
    # IMPORTANTE: Lo hacemos AQUI FUERA, sin semaforo cogido
    if len(otro_usuario) > 0:
        registrar_contacto_local(otro_usuario)

    return True


def obtener_ultimo_timestamp_local(amigo):
    max_ts = "00000000000000"

    # Rutas limpias con OS
    nombre_f1 = f"{mi_usuario}_{amigo}.txt"
    nombre_f2 = f"{amigo}_{mi_usuario}.txt"
    ruta1 = os.path.join("Historiales", nombre_f1)
    ruta2 = os.path.join("Historiales", nombre_f2)

    rutas = [ruta1, ruta2]

    leido = False
    while not leido:
        if sem_archivo.acquire(timeout=1):
            try:
                # Recorremos la lista sin usar for-each para controlar indice si hiciera falta
                k = 0
                while k < len(rutas):
                    r = rutas[k]
                    if os.path.exists(r):
                        try:
                            f = open(r, "r")
                            lines = f.readlines()
                            f.close()

                            j = 0
                            while j < len(lines):
                                linea = lines[j].strip()
                                if len(linea) > 10:
                                    p = linea.split(";")
                                    if len(p) >= 6:
                                        ts = p[2]
                                        if ts.isdigit() and ts > max_ts:
                                            max_ts = ts
                                j = j + 1
                        except:
                            error = True
                    k = k + 1
            finally:
                sem_archivo.release()
                leido = True
        else:
            time.sleep(0.1)

    return max_ts


def mostrar_lista_contactos():
    print("\n" + "=" * 30)
    print("      MIS CONVERSACIONES      ")
    print("=" * 30)

    leido = False
    while not leido:
        if sem_archivo.acquire(timeout=1):
            try:
                if os.path.exists("mis_contactos.txt"):
                    f = open("mis_contactos.txt", "r")
                    lines = f.readlines()
                    f.close()

                    if len(lines) == 0:
                        print(" [!] No tienes chats iniciados.")
                    else:
                        c = 0
                        while c < len(lines):
                            l = lines[c].strip()
                            if len(l) > 0:
                                print(f"  -> @{l}")
                            c = c + 1
                else:
                    print(" [!] No tienes chats iniciados.")
            except:
                print(" [X] Error leyendo contactos.")
            finally:
                sem_archivo.release()
                leido = True
        else:
            time.sleep(0.1)
    print("=" * 30 + "\n")


# --- RED ---

def enviar_mensaje(dest, txt):
    t = obtener_timestamp()
    msg = f"{mi_usuario};{dest};{t};ENVIADO;{t};{txt}"

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip_servidor, port_envios))
        s.send(msg.encode())
        res = s.recv(1024).decode()
        s.close()

        if res == "OK":
            guardar_localmente(msg)
            print(f" [V] Mensaje entregado a @{dest}")
        else:
            print(f" [X] El servidor rechazó el mensaje")
    except:
        print(f" [!] Error: No se pudo conectar al servidor")


def enviar_confirmacion_leido(dest, txt_orig, t_orig):
    t_now = obtener_timestamp()
    msg = f"{mi_usuario};{dest};{t_now};LEIDO;{t_orig};{txt_orig}"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip_servidor, port_envios))
        s.send(msg.encode())
        s.recv(1024)
        s.close()
        guardar_localmente(msg)
    except:
        error = True


# --- HILO ACTUALIZADOR ---

def hilo_actualizador():
    while conectado:
        try:
            # Espera rapida: 1 segundo (10 trozos de 0.1)
            c = 0
            while c < 10 and conectado:
                time.sleep(0.1)
                c = c + 1

            if conectado:
                cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cli.connect((ip_servidor, port_recepcion))
                cli.send(f"LOGIN:{mi_usuario}:{mi_password}".encode())

                if cli.recv(1024).decode() == "OK":

                    # 1. LIST
                    t = obtener_timestamp()
                    cli.send(f"{mi_usuario};@;{t};LIST;{t};\"\"".encode())

                    cab = cli.recv(1024).decode()
                    p_cab = cab.split(";")

                    if len(p_cab) >= 6:
                        cant = int(p_cab[5].replace('"', ''))
                        cli.send("OK".encode())

                        chats = []
                        k = 0
                        while k < cant:
                            raw = cli.recv(1024).decode()
                            cli.send("OK".encode())

                            p = raw.split(";")
                            if len(p) >= 6:
                                # Usamos OS para limpiar el nombre del archivo
                                ruta_sucia = p[1]
                                # os.path.basename coge "Juan_Pepe.txt" de "logs/Juan_Pepe.txt"
                                nombre_base = os.path.basename(ruta_sucia.replace("\\", "/"))
                                limpio = nombre_base.replace(".txt", "")
                                partes = limpio.split("_")

                                m = 0
                                while m < len(partes):
                                    x = partes[m]
                                    if x != mi_usuario and len(x) > 0:
                                        # ANTI-DUPLICADOS
                                        esta = False
                                        z = 0
                                        while z < len(chats):
                                            if chats[z] == x:
                                                esta = True
                                            z = z + 1

                                        if not esta:
                                            chats.append(x)
                                    m = m + 1
                            k = k + 1

                        # 2. UPDATE
                        m = 0
                        while m < len(chats):
                            amigo = chats[m]
                            last_ts = obtener_ultimo_timestamp_local(amigo)

                            cli.send(f"{mi_usuario};{amigo};{t};UPDATE;{t};\"{last_ts}\"".encode())

                            cab_u = cli.recv(1024).decode()
                            p_u = cab_u.split(";")

                            if len(p_u) >= 6:
                                num_msgs = int(p_u[5].replace('"', ''))
                                cli.send("OK".encode())

                                n = 0
                                while n < num_msgs:
                                    m_new = cli.recv(1024).decode()
                                    cli.send("OK".encode())

                                    if len(m_new) > 0:
                                        guardar_localmente(m_new)

                                        pm = m_new.split(";")
                                        if len(pm) >= 6:
                                            ori = pm[0]
                                            ts_o = pm[2]
                                            st = pm[3]
                                            txt = pm[5]

                                            es_txt = (st == "RECIBIDO" or st == "ENVIADO")
                                            no_soy_yo = (ori != mi_usuario)

                                            if es_txt and no_soy_yo and len(txt.strip()) > 0:
                                                print("\n" + "*" * 35)
                                                print(f" [NUEVO MENSAJE] De: @{ori}")
                                                print(f" Mensaje: {txt}")
                                                print("*" * 35)
                                                print(" >> ", end="")
                                                enviar_confirmacion_leido(ori, txt, ts_o)
                                    n = n + 1
                            m = m + 1
                cli.close()
        except:
            error = True


# --- PRINCIPAL ---

print("\n")
print("  ################################")
print("  #       CLIENTE WHATSAPP       #")
print("  ################################")
print("\n")

mi_usuario = input(" -> Usuario: ")
mi_password = input(" -> Password: ")

print("\n [.] Conectando con servidor...")
try:
    test = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test.connect((ip_servidor, port_recepcion))
    test.send(f"LOGIN:{mi_usuario}:{mi_password}".encode())
    res = test.recv(1024).decode()
    test.close()
    if res == "OK":
        conectado = True
    else:
        conectado = False
except:
    conectado = False

if conectado:
    print(f" [+] Login correcto. Bienvenido {mi_usuario}")
    print(" -----------------------------------------")
    print("  COMANDOS:")
    print("   @Amigo: Mensaje  -> Enviar mensaje")
    print("   @lista           -> Ver conversaciones")
    print("   @salir           -> Desconectar")
    print(" -----------------------------------------")

    h = threading.Thread(target=hilo_actualizador)
    h.start()

    while conectado:
        try:
            txt = input(" >> ")
            if len(txt) > 0:
                if txt == "@salir":
                    print(" [.] Cerrando sesion...")
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((ip_servidor, port_envios))
                        s.send("!DESCONECTAR".encode())
                        s.close()
                    except:
                        error = True
                    conectado = False
                elif txt == "@lista":
                    mostrar_lista_contactos()
                elif ":" in txt and txt.startswith("@"):
                    p = txt.split(":", 1)
                    dest = p[0][1:].strip()
                    c = p[1].strip()
                    if len(c) > 0:
                        enviar_mensaje(dest, c)
                    else:
                        print(" [!] El mensaje no puede estar vacio")
                else:
                    print(" [?] Formato incorrecto. Usa @Nombre: Mensaje")
        except:
            conectado = False

    print("\n [OFF] Programa finalizado.")
else:
    print("\n [X] Error: Usuario incorrecto o servidor apagado.")
>>>>>>> 8594f0e78a7aac95dce665376959dc83413e4e4b
