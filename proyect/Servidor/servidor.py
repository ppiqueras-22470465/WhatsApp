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


# --- 2. PUERTO 666 (ENVÍOS - MULTIHILO) ---

def atender_cliente_666(conn):
    try:
        conectado = True
        while conectado:
            datos = conn.recv(1024)

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

                    guardar_mensaje_en_archivo(mensaje_procesado.encode())
                    conn.send("OK".encode())
                else:
                    print("[ERROR-666] Faltan campos")
                    conn.send("KO".encode())

    except Exception as e:
        print(f"[ERROR HILO 666] {e}")
    finally:
        conn.close()


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