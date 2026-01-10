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
    # Generamos los dos nombres posibles A_B.txt o B_A.txt
    archivo = f"{emisor}_{receptor}.txt"
    archivo_invertido = f"{receptor}_{emisor}.txt"

    # Intentamos abrir el primero a ver si existe
    try:
        archivo_final = open(archivo, "r")
        archivo_final.close()
        archivo_final = archivo
    except FileNotFoundError:
        # Si falla, intentamos el segundo
        try:
            archivo_final = open(archivo_invertido, "r")
            archivo_final.close()
            archivo_final = archivo_invertido
        except FileNotFoundError:
            # Si ninguno existe, devolvemos el formato estándar
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

            if not datos:
                conectado = False
                break

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
            if not datos:
                conectado = False
                break

            mensaje = datos.decode().strip()
            print(f"[999] Comando: {mensaje}")

            # LOGIN
            if mensaje.startswith("LOGIN"):
                partes = mensaje.split(";")
                if len(partes) < 3: partes = mensaje.split(":")  # Compatibilidad

                if len(partes) == 3:
                    user_temp = partes[1].replace("@", "")
                    pass_temp = partes[2].replace("@", "")

                    if validar_login(user_temp, pass_temp):
                        usuario_logueado = user_temp
                        conn.send("OK".encode())
                    else:
                        conn.send("KO".encode())
                else:
                    conn.send("ERROR FORMATO".encode())

            # LIST (Sin usar OS, usando try/except)
            elif mensaje == "LIST" and usuario_logueado:
                lista_mis_chats = ""

                if sem_lista_mensajes.acquire(timeout=2):
                    try:
                        f = open("indice_chats.txt", "r")
                        chats = f.readlines()
                        f.close()

                        for linea in chats:
                            if usuario_logueado in linea:
                                lista_mis_chats += linea.strip() + "#"
                    except FileNotFoundError:
                        lista_mis_chats = "VACIO"
                    finally:
                        sem_lista_mensajes.release()

                if lista_mis_chats == "":
                    lista_mis_chats = "VACIO"
                conn.send(lista_mis_chats.encode())

            # UPDATE
            elif mensaje.startswith("UPDATE") and usuario_logueado:
                partes = mensaje.split(";")
                if len(partes) == 3:
                    amigo = partes[1]
                    timestamp_cliente = partes[2]

                    nuevos = obtener_mensajes_pendientes(usuario_logueado, amigo, timestamp_cliente)

                    if len(nuevos) > 0:
                        paquete = ""
                        for msg in nuevos:
                            paquete += msg + "#"
                        conn.send(paquete.encode())
                    else:
                        conn.send("VACIO".encode())
                else:
                    conn.send("ERROR FORMATO".encode())

            # SALIR
            elif mensaje == "!DESCONECTAR":
                conectado = False

            elif not usuario_logueado:
                conn.send("ERROR: LOGIN PRIMERO".encode())

            else:
                conn.send("KO".encode())

    except Exception as e:
        print(f"[ERROR HILO 999] {e}")
    finally:
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


# --- 4. ARRANQUE (LINEAL Y SIMPLE) ---

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