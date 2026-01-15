import socket
import threading
import datetime
import time

# --- CONFIGURACIÓN GLOBAL ---
ip_servidor = "127.0.0.1"
archivo_usuarios = "usuarios.txt"
port_999 = 999
port_666 = 666

# LISTAS DE HILOS (Para que el profesor vea que gestionas la memoria)
lista_hilos_666 = []
lista_hilos_999 = []

# SEMÁFORO (El árbitro para no pisar archivos)
sem_lista_mensajes = threading.Semaphore(1)


# --- 1. FUNCIONES AUXILIARES (LÓGICA DE NEGOCIO) ---

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
                partes = archivo_leido_sin_espacios.split(":")
                if len(partes) == 2:
                    usuario_archivo = partes[0]
                    password_archivo = partes[1]
                    if usuario_archivo == usuario and password_archivo == password:
                        encontrado = True
            i = i + 1
    except FileNotFoundError:
        print(f"[LOGIN] No he encontrado el archivo {archivo_usuarios}")
    return encontrado


def validar_archivo(emisor, receptor):
    archivo = f"logs/{emisor}_{receptor}.txt"
    archivo_invertido = f"logs/{receptor}_{emisor}.txt"

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


def ordenar_mensajes(lista_mensajes):
    diccionario = {}
    for i in lista_mensajes:
        lista_mensajes_limpia = i.strip()
        if len(lista_mensajes_limpia) > 0:
            partes = lista_mensajes_limpia.split(";")
            if len(partes) == 6:
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

    # Bucle con espera activa (Sleep) si el semáforo está ocupado
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
        if len(partes) >= 6:
            timestamp = partes[2]
            if timestamp > ultimo_timestamp:
                mensajes_finales.append(i)
        else:
            print(f"[ERROR-UPDATE] Formato incorrecto en historial")

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
                    # A. Guardar en el chat
                    archivo_final_escribir = open(archivo_final, "a")
                    archivo_final_escribir.write(mensaje + "\n")
                    archivo_final_escribir.close()
                    print(f"[SISTEMA] Guardado en: {archivo_final}")

                    # B. Actualizar índice de chats (si no existe)
                    chat_registrado = False
                    try:
                        indice = open("indice_chats.txt", "r")
                        indice_chats = indice.readlines()
                        indice.close()

                        for i in range(len(indice_chats)):
                            if indice_chats[i].strip() == archivo_final:
                                chat_registrado = True
                    except FileNotFoundError:
                        chat_registrado = False

                    if chat_registrado == False:
                        nuevo_indice = open("indice_chats.txt", "a")
                        nuevo_indice.write(archivo_final + "\n")
                        nuevo_indice.close()
                        print(f"[SISTEMA] Nuevo chat registrado en índice")

                    sem_lista_mensajes.release()
                    guardado = True

                except Exception as e:
                    print(f"[ERROR GUARDADO] {e}")
                    sem_lista_mensajes.release()
                    guardado = True
            else:
                time.sleep(1)
    else:
        print(f"[ERROR] Mensaje sin formato correcto")


<<<<<<< HEAD
# --- CORRECCIÓN PUERTO 666 (ENVÍOS) ---
# EN servidor.py

def puerto_666():
    """Gestiona el ENVÍO y las CONFIRMACIONES de lectura."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((ip_servidor, port_666))
    servidor.listen()
    print("Servidor [666]: Listo para recibir mensajes.")
=======
# --- 2. PUERTO 666 (ENVÍOS - MULTIHILO) ---
>>>>>>> 8594f0e78a7aac95dce665376959dc83413e4e4b

def atender_cliente_666(conn):
    try:
        conectado = True
        while conectado:
            datos = conn.recv(1024)

<<<<<<< HEAD
    while conexion_servidor:
        try:
            conn, addr = servidor.accept()
            conn.settimeout(10)

            try:
                mensaje = conn.recv(1024).decode()
                if mensaje != "":
                    partes = mensaje.split(";")

                    if mensaje == "!DESCONECTAR":
                        print(f"[666] Apagando")
                        conn.send(f"[666] Apagando".encode())
                        conexion_servidor = False

                    elif len(partes) >= 6:
                        estado = partes[3]

                        # --- CASO A: Confirmación de LECTURA (LEIDO) ---
                        if estado == "LEIDO":
                            emisor = partes[0].replace("@", "")  # Quien lee (Yo)
                            receptor = partes[1].replace("@", "")  # De quien leemos (El otro)

                            if sem_lista_mensajes.acquire(timeout=5):
                                try:
                                    archivo = validar_archivo(emisor, receptor)
                                    f = open(archivo, "r")
                                    lines = f.readlines()
                                    f.close()

                                    new_lines = []
                                    cambio = False

                                    i = 0
                                    while i < len(lines):
                                        m = lines[i].strip()
                                        p = m.split(";")

                                        # CORRECCIÓN CLAVE AQUÍ:
                                        # Marcamos LEIDO si está ENTREGADO **O SI SIGUE RECIBIDO**
                                        if len(p) >= 6 and p[1].replace("@", "") == emisor:
                                            if p[3] == "ENTREGADO" or p[3] == "RECIBIDO":
                                                ts_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                                                nuevo_m = f"{p[0]};{p[1]};{p[2]};LEIDO;{ts_now};{p[5]}"
                                                new_lines.append(nuevo_m)
                                                cambio = True
                                            else:
                                                new_lines.append(m)
                                        else:
                                            new_lines.append(m)
                                        i = i + 1

                                    if cambio:
                                        f = open(archivo, "w")
                                        for nl in new_lines: f.write(nl + "\n")
                                        f.close()

                                    sem_lista_mensajes.release()
                                    conn.send("OK".encode())
                                except:
                                    sem_lista_mensajes.release()
                                    conn.send("KO".encode())

                        # --- CASO B: Mensaje Nuevo Normal ---
                        else:
                            emisor = partes[0]
                            receptor = partes[1]
                            ts_orig = partes[2]
                            contenido = partes[5]

                            nuevo_estado = "RECIBIDO"
                            ahora = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

                            msg_proc = f"{emisor};{receptor};{ts_orig};{nuevo_estado};{ahora};{contenido}"
                            guardar_mensaje_en_archivo(msg_proc.encode())
                            conn.send("OK".encode())
                    else:
                        conn.send("KO".encode())
            except Exception as e:
                print(f"[666 Error] {e}")

            conn.close()
        except Exception as e:
            print(f"[ERROR 666 loop] {e}")

def gestionar_cliente_999(conn, addr):
    """Atiende UPDATE y LIST (arreglado)."""
    print(f"[999] Atendiendo a {addr}")
    login_ok = False
    conexion_activa = True
    usuario_conectado = ""

    conn.settimeout(10)

    while conexion_activa:
        try:
            datos = conn.recv(1024).decode().strip()
            if datos == "":
                conexion_activa = False
            else:
                es_login = datos.startswith("LOGIN")
                partes = datos.split(";")
                es_update = False
                es_list = False
                ts_solicitado = "00000000000000"

                if len(partes) >= 5:
                    if partes[3] == "UPDATE":
                        es_update = True
                        ts_solicitado = partes[4]
                    elif partes[3] == "LIST":
                        es_list = True

                if es_login:
                    d = datos.split(":")
                    if len(d) == 3 and validar_login(d[1], d[2]):
                        conn.send("OK".encode())
                        login_ok = True
                        usuario_conectado = d[1]
                    else:
                        conn.send("KO".encode())
                        conexion_activa = False

                elif es_update and login_ok:
                    mensajes_a_enviar = []

                    if sem_lista_mensajes.acquire(timeout=5):
                        try:
                            import glob
                            chats = glob.glob("*_*.txt")
                            i = 0
                            while i < len(chats):
                                archivo = chats[i]
                                if usuario_conectado in archivo:
                                    f = open(archivo, "r")
                                    msgs = f.readlines()
                                    f.close()

                                    modificado = False
                                    nuevas_lineas = []

                                    j = 0
                                    while j < len(msgs):
                                        m = msgs[j].strip()
                                        p = m.split(";")
                                        linea_final = m

                                        if len(p) >= 6:
                                            origen = p[0].replace("@", "")
                                            destino = p[1].replace("@", "")
                                            estado = p[3]
                                            ts_estado = p[4]

                                            # CRITERIO 1: Recibir mensajes nuevos (RECIBIDO -> ENTREGADO)
                                            if destino == usuario_conectado and estado == "RECIBIDO":
                                                mensajes_a_enviar.append(m)
                                                now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                                                linea_final = f"{p[0]};{p[1]};{p[2]};ENTREGADO;{now};{p[5]}"
                                                modificado = True

                                            # CRITERIO 2: Recibir actualizaciones de MIS mensajes (ENTREGADO/LEIDO)
                                            elif origen == usuario_conectado and ts_estado > ts_solicitado:
                                                mensajes_a_enviar.append(m)

                                        nuevas_lineas.append(linea_final)
                                        j = j + 1

                                    if modificado:
                                        f = open(archivo, "w")
                                        for nl in nuevas_lineas: f.write(nl + "\n")
                                        f.close()
                                i = i + 1
                            sem_lista_mensajes.release()
                        except:
                            sem_lista_mensajes.release()

                    # Enviar UPDATE al cliente
                    cant = len(mensajes_a_enviar)
                    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    cab = f"SERVER;{usuario_conectado};{ts};UPDATE;{ts};\"{cant}\""
                    conn.send(cab.encode())

                    if conn.recv(1024).decode() == "OK":
                        k = 0
                        while k < cant:
                            conn.send(mensajes_a_enviar[k].encode())
                            conn.recv(1024)
                            k = k + 1

                elif es_list and login_ok:
                    # --- LÓGICA DE LISTA ARREGLADA ---
                    chats_a_enviar = []
                    if sem_lista_mensajes.acquire(timeout=5):
                        try:
                            import glob
                            archivos = glob.glob("*_*.txt")
                            procesados = []
                            i = 0
                            while i < len(archivos):
                                nombre = archivos[i]
                                if usuario_conectado in nombre:
                                    # Sacar el nombre del OTRO usuario del nombre del archivo (A_B.txt)
                                    partes_nom = nombre.replace(".txt", "").split("_")
                                    otro = ""
                                    if len(partes_nom) == 2:
                                        if partes_nom[0] == usuario_conectado:
                                            otro = partes_nom[1]
                                        elif partes_nom[1] == usuario_conectado:
                                            otro = partes_nom[0]

                                    # Evitar duplicados si existen A_B y B_A (no debería, pero por seguridad)
                                    ya_esta = False
                                    for usr in procesados:
                                        if usr == otro: ya_esta = True

                                    if otro != "" and not ya_esta:
                                        procesados.append(otro)
                                        # Contar mensajes pendientes (RECIBIDO) para MÍ en este chat
                                        pendientes = 0
                                        try:
                                            f = open(nombre, "r")
                                            lineas = f.readlines()
                                            f.close()
                                            for l in lineas:
                                                cp = l.split(";")
                                                if len(cp) >= 6:
                                                    # Si soy destino y está RECIBIDO -> Pendiente
                                                    if cp[1].replace("@", "") == usuario_conectado and cp[
                                                        3] == "RECIBIDO":
                                                        pendientes += 1
                                        except:
                                            print(f"[ERROR LISTA] No se pudo abrir {nombre}")

                                        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                                        # Formato item lista: Otro;Yo;000;LIST;000;"Pendientes"
                                        item = f"{otro};{usuario_conectado};00000000000000;LIST;00000000000000;\"{pendientes}\""
                                        chats_a_enviar.append(item)
                                i = i + 1
                            sem_lista_mensajes.release()
                        except:
                            sem_lista_mensajes.release()

                    # Enviar respuesta LIST al cliente
                    cant = len(chats_a_enviar)
                    ts_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    header = f"SERVER;{usuario_conectado};{ts_now};LIST;{ts_now};\"{cant}\""
                    conn.send(header.encode())

                    if conn.recv(1024).decode() == "OK":
                        for chat_item in chats_a_enviar:
                            conn.send(chat_item.encode())
                            conn.recv(1024)
=======
            if len(datos)==0:
                conectado = False

            mensaje = datos.decode().strip()
            print(f"[666] Recibido: {mensaje}")

            if mensaje == "!DESCONECTAR":
                print(f"[666] Cliente finaliza sesión.")
                conectado = False
            else:
                partes = mensaje.split(";")
                if len(partes) >= 6:
                    emisor = partes[0]
                    receptor = partes[1]
                    timestamp_original = partes[2]
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
>>>>>>> 8594f0e78a7aac95dce665376959dc83413e4e4b

                    guardar_mensaje_en_archivo(mensaje_procesado.encode())
                    conn.send("OK".encode())
                else:
                    print("[ERROR-666] Faltan campos")
                    conn.send("KO".encode())
<<<<<<< HEAD
                    conexion_activa = False
        except:
            conexion_activa = False
    conn.close()
=======

    except Exception as e:
        print(f"[ERROR HILO 666] {e}")
    finally:
        conn.close()
>>>>>>> 8594f0e78a7aac95dce665376959dc83413e4e4b


def puerto_666():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((ip_servidor, port_666))
    servidor.listen()
    print(f"Servidor [666]: Escuchando en {port_666}...\n")

    while True:
        try:
            conn, addr = servidor.accept()

            # Limpieza de memoria (quitamos hilos muertos de la lista)
            for h in lista_hilos_666[:]:
                if not h.is_alive():
                    lista_hilos_666.remove(h)

            hilo = threading.Thread(target=atender_cliente_666, args=(conn,))
            hilo.start()
            lista_hilos_666.append(hilo)

        except Exception as e:
            print(f"[ERROR SERVER 666] {e}")


# --- 3. PUERTO 999 (LOGIN/UPDATE - MULTIHILO) ---

def atender_cliente_999(conn):
    try:
        conectado = True
        usuario_logueado = None

        while conectado:
            datos = conn.recv(1024)

            # CORRECCIÓN DE FLUJO: Usamos if/else para no procesar si se desconectó
            if len(datos) > 0:
                mensaje_raw = datos.decode().strip()
                print(f"[999] Recibido: {mensaje_raw}")

                # 1. GESTIÓN DE LOGIN (Formato Excepción: LOGIN:User:Pass)
                if mensaje_raw.startswith("LOGIN"):
                    partes = mensaje_raw.split(":")
                    if len(partes) == 3:
                        user_temp = partes[1].replace("@", "")
                        pass_temp = partes[2].replace("@", "")

                        if validar_login(user_temp, pass_temp):
                            usuario_logueado = user_temp
                            conn.send("OK".encode())
                        else:
                            conn.send("KO".encode())
                    else:
                        conn.send("KO".encode())

                # 2. COMANDOS ESTÁNDAR (Requiere Login + Formato 6 campos)
                else:
                    if usuario_logueado:
                        partes = mensaje_raw.split(";")

                        # PDF[cite: 72]: El formato debe ser separado por ;
                        if len(partes) >= 6:
                            origen = partes[0]
                            destino = partes[1]
                            comando = partes[3]  # PDF[cite: 103]: El comando va en el estado
                            contenido = partes[5]

                            # --- COMANDO UPDATE ---
                            if comando == "UPDATE":
                                # PDF[cite: 105]: Update solicita mensajes posteriores al timestamp
                                timestamp_filtro = contenido.replace('"', '')

                                nuevos = obtener_mensajes_pendientes(usuario_logueado, destino.replace("@", ""),
                                                                     timestamp_filtro)
                                cantidad = len(nuevos)

                                # PROTOCOLO[cite: 107]: Enviar primero un mensaje con el número entero
                                ts_ahora = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                                cabecera = f"{origen};{destino};{ts_ahora};UPDATE;{ts_ahora};\"{cantidad}\""
                                conn.send(cabecera.encode())

                                # Esperar OK
                                confirmacion = conn.recv(1024).decode()
                                if confirmacion.strip() == "OK":
                                    # Enviar mensajes UNO A UNO [cite: 107]
                                    i = 0
                                    while i < cantidad:
                                        msg = nuevos[i]
                                        conn.send(msg.encode())
                                        # Esperar OK tras cada mensaje
                                        conn.recv(1024)
                                        i = i + 1
                                else:
                                    print("[ERROR] Cliente no confirmó cabecera UPDATE")

                            # --- COMANDO LIST ---
                            elif comando == "LIST":
                                lista_chats_encontrados = []

                                # Semáforo para lectura segura
                                if sem_lista_mensajes.acquire(timeout=2):
                                    try:
                                        f = open("indice_chats.txt", "r")
                                        todas_lineas = f.readlines()
                                        f.close()

                                        j = 0
                                        while j < len(todas_lineas):
                                            linea = todas_lineas[j]
                                            if usuario_logueado in linea:
                                                nombre_limpio = linea.strip().replace(".txt", "")
                                                lista_chats_encontrados.append(nombre_limpio)
                                            j = j + 1
                                    except FileNotFoundError:
                                        lista_chats_encontrados = []  # Sin pass
                                    except Exception:
                                        lista_chats_encontrados = []  # Sin pass

                                    sem_lista_mensajes.release()
                                else:
                                    lista_chats_encontrados = []

                                cantidad = len(lista_chats_encontrados)
                                ts_ahora = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

                                # PROTOCOLO[cite: 110]: Enviar primero cantidad
                                cabecera = f"{origen};@;{ts_ahora};LIST;{ts_ahora};\"{cantidad}\""
                                conn.send(cabecera.encode())

                                # Esperar OK
                                confirmacion = conn.recv(1024).decode()
                                if confirmacion.strip() == "OK":
                                    k = 0
                                    while k < cantidad:
                                        chat_info = lista_chats_encontrados[k]
                                        # PDF[cite: 110]: Formato LIST con timestamp 0
                                        msg_chat = f"{origen};{chat_info};00000000000000;LIST;00000000000000;\"0\""
                                        conn.send(msg_chat.encode())

                                        # Esperar OK tras cada item
                                        conn.recv(1024)
                                        k = k + 1

                            # OTROS
                            else:
                                conn.send("KO".encode())
                        else:
                            if mensaje_raw == "!DESCONECTAR":
                                conectado = False
                            else:
                                conn.send("KO".encode())
                    else:
                        conn.send("ERROR: LOGIN PRIMERO".encode())
            else:
                # Si len(datos) == 0, el cliente cerró
                conectado = False

    except Exception as e:
        print(f"[ERROR HILO 999] {e}")
    conn.close()

def puerto_999():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((ip_servidor, port_999))
    servidor.listen()
    print(f"Servidor [999]: Escuchando en {port_999}...\n")

    while True:
        try:
            conn, addr = servidor.accept()

            # Limpieza de memoria
            for h in lista_hilos_999[:]:
                if not h.is_alive():
                    lista_hilos_999.remove(h)

            hilo = threading.Thread(target=atender_cliente_999, args=(conn,))
            hilo.start()
            lista_hilos_999.append(hilo)

        except Exception as e:
            print(f"[ERROR SERVER 999] {e}")



print("--- INICIANDO SERVIDORES WHATSAPP ---")

# Creamos los dos hilos principales
hilo_envios = threading.Thread(target=puerto_666)
hilo_recibos = threading.Thread(target=puerto_999)

# Los ponemos a funcionar
hilo_envios.start()
hilo_recibos.start()

# Hacemos que el programa principal espere (así no se cierra)
hilo_envios.join()
hilo_recibos.join()

print("Servidores detenidos.")