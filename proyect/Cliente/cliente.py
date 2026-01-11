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
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


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


def guardar_localmente(msg):
    if not msg or len(msg.strip()) == 0:
        return False

    escrito = False
    otro_usuario = ""

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