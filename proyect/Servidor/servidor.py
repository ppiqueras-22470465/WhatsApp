import socket
import threading
import datetime
import time

# Configuración
ip_servidor = "127.0.0.1"
archivo_usuarios = "usuarios.txt"
port_999 = 999
port_666 = 666
lista_mensajes = []

sem_lista_mensajes = threading.Semaphore(1)


# --- FUNCIONES AUXILIARES (LÓGICA) ---
# (validar_login, validar_archivo, ordenar_mensajes,
#  obtener_mensajes_pendientes, guardar_mensaje_en_archivo SE QUEDAN IGUAL)
# Copia aquí tus funciones auxiliares existentes sin cambios...
# ... (Para ahorrar espacio asumo que las mantienes igual) ...

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
    archivo = f"{emisor}_{receptor}.txt"
    archivo_invertido = f"{receptor}_{emisor}.txt"
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


def guardar_mensaje_en_archivo(mensaje_formateado):
    # (Manten tu función original aquí)
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
                    archivo_final_escribir = open(archivo_final, "a")
                    archivo_final_escribir.write(mensaje + "\n")
                    archivo_final_escribir.close()
                    print(f"[SISTEMA] Guardado en: {archivo_final}")

                    chat_registrado = False
                    try:
                        indice = open("indice_chats.txt", "r")
                        indice_chats = indice.readlines()
                        indice.close()
                        for i in range(len(indice_chats)):
                            if indice_chats[i].strip() == archivo_final:
                                chat_registrado = True
                    except FileNotFoundError:
                        chat_ya_registrado = False

                    if chat_registrado == False:
                        nuevo_indice = open("indice_chats.txt", "a")
                        nuevo_indice.write(archivo_final + "\n")
                        nuevo_indice.close()

                    sem_lista_mensajes.release()
                    guardado = True
                except Exception as e:
                    print(f"[ERROR GUARDADO] {e}")
                    sem_lista_mensajes.release()
                    guardado = True
            else:
                time.sleep(1)
    else:
        print(f"[ERROR] El mensaje recibido no tiene el formato correcto")


# --- CORRECCIÓN PUERTO 666 (ENVÍOS) ---
def puerto_666():
    """Gestiona el ENVÍO de mensajes. Bucle corregido."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((ip_servidor, port_666))
    servidor.listen()
    print("Servidor [666]: Listo para recibir mensajes.")

    conexion_servidor = True

    while conexion_servidor:
        try:
            conn, addr = servidor.accept()
            # Quitamos el timeout para recibir bien el mensaje
            conn.settimeout(10)

            try:
                mensaje = conn.recv(1024).decode()
                if mensaje != "":
                    print(f"[666] Recibido: {mensaje}")
                    partes = mensaje.split(";")

                    if mensaje == "!DESCONECTAR":
                        print(f"[666] Apagando")
                        conn.send(f"[666] Apagando".encode())
                        conexion_servidor = False

                    elif len(partes) >= 6:
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
                print(f"[ERROR-666 procesamiento] {e}")

            conn.close()
            # IMPORTANTE: NO ponemos conexion_servidor = False aquí.
            # Solo salimos si recibimos !DESCONECTAR.

        except Exception as e:
            print(f"[ERROR-666 accept] {e}")


# --- CORRECCIÓN PUERTO 999 (HILOS INDIVIDUALES) ---

def gestionar_cliente_999(conn, addr):
    """Función para atender a UN cliente en el puerto 999 (hilo)."""
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
                # --- DETECTAR TIPO DE MENSAJE ---
                es_login = False
                es_update = False
                es_list = False

                if datos.startswith("LOGIN"):
                    es_login = True

                partes = datos.split(";")
                if len(partes) >= 4:
                    comando = partes[3]
                    if comando == "UPDATE":
                        es_update = True
                    elif comando == "LIST":
                        es_list = True

                # --- PROCESAR COMANDOS ---

                if es_login:
                    datos_login = datos.split(":")
                    if len(datos_login) == 3:
                        usuario = datos_login[1].replace("@", "")
                        password = datos_login[2].replace("@", "")
                        if validar_login(usuario, password):
                            conn.send("OK".encode())
                            login_ok = True
                            usuario_conectado = usuario
                        else:
                            conn.send("KO".encode())
                            conexion_activa = False
                    else:
                        conn.send("KO".encode())
                        conexion_activa = False

                elif es_update and login_ok:
                    mensajes_a_enviar = []

                    # Usamos el semáforo para leer Y MODIFICAR el archivo de forma segura
                    if sem_lista_mensajes.acquire(timeout=5):
                        try:
                            import glob
                            chats = glob.glob("*_*.txt")
                            i = 0
                            while i < len(chats):
                                archivo = chats[i]
                                if usuario_conectado in archivo:
                                    # 1. Leemos todo el archivo
                                    f = open(archivo, "r")
                                    msgs = f.readlines()
                                    f.close()

                                    archivo_modificado = False
                                    nuevas_lineas = []

                                    # 2. Procesamos línea a línea
                                    j = 0
                                    while j < len(msgs):
                                        m = msgs[j].strip()
                                        p = m.split(";")
                                        linea_final = m  # Por defecto guardamos la línea igual

                                        if len(p) >= 6:
                                            destino = p[1].replace("@", "")
                                            estado = p[3]

                                            # Si es para mí y está RECIBIDO -> Lo envío y cambio a ENTREGADO
                                            if destino == usuario_conectado and estado == "RECIBIDO":
                                                mensajes_a_enviar.append(m)

                                                # Actualizamos estado a ENTREGADO
                                                ts_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                                                # Reconstruimos: Origen;Destino;TS;ENTREGADO;TS_Now;Msg
                                                linea_final = f"{p[0]};{p[1]};{p[2]};ENTREGADO;{ts_now};{p[5]}"
                                                archivo_modificado = True

                                        nuevas_lineas.append(linea_final)
                                        j = j + 1

                                    # 3. Si hubo cambios, reescribimos el archivo
                                    if archivo_modificado:
                                        f = open(archivo, "w")
                                        for lin in nuevas_lineas:
                                            f.write(lin + "\n")
                                        f.close()

                                i = i + 1
                            sem_lista_mensajes.release()
                        except Exception as e:
                            print(f"Error procesando update: {e}")
                            sem_lista_mensajes.release()

                    # Enviar respuesta al cliente
                    cantidad = len(mensajes_a_enviar)
                    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    cabecera = f"SERVER;{usuario_conectado};{ts};UPDATE;{ts};\"{cantidad}\""
                    conn.send(cabecera.encode())

                    conf = conn.recv(1024).decode()
                    if conf == "OK":
                        k = 0
                        while k < cantidad:
                            conn.send(mensajes_a_enviar[k].encode())
                            conn.recv(1024)
                            k = k + 1

                elif es_list and login_ok:
                    # (Tu lógica de LIST corregida en la respuesta anterior estaba bien, mantenla igual)
                    # Resumida para ahorrar espacio en esta respuesta:
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
                                    partes_nom = nombre.replace(".txt", "").split("_")
                                    otro = ""
                                    if len(partes_nom) == 2:
                                        if partes_nom[0] == usuario_conectado:
                                            otro = partes_nom[1]
                                        elif partes_nom[1] == usuario_conectado:
                                            otro = partes_nom[0]

                                    ya_esta = False
                                    for user_chk in procesados:
                                        if user_chk == otro: ya_esta = True

                                    if otro != "" and not ya_esta:
                                        procesados.append(otro)
                                        pendientes = 0
                                        f = open(nombre, "r")
                                        ll = f.readlines()
                                        f.close()
                                        for lin in ll:
                                            cp = lin.split(";")
                                            if len(cp) >= 6:
                                                if cp[1].replace("@", "") == usuario_conectado and cp[3] == "RECIBIDO":
                                                    pendientes += 1
                                        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                                        item = f"{otro};{usuario_conectado};{ts};LIST;{ts};\"{pendientes}\""
                                        chats_a_enviar.append(item)
                                i = i + 1
                            sem_lista_mensajes.release()
                        except:
                            sem_lista_mensajes.release()

                    cant = len(chats_a_enviar)
                    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    header = f"SERVER;{usuario_conectado};{ts};LIST;{ts};\"{cant}\""
                    conn.send(header.encode())
                    ack = conn.recv(1024).decode()
                    if ack == "OK":
                        for chat_item in chats_a_enviar:
                            conn.send(chat_item.encode())
                            conn.recv(1024)

                else:
                    conn.send("KO".encode())
                    conexion_activa = False

        except Exception as e:
            print(f"[ERROR-999] {e}")
            conexion_activa = False

    conn.close()


def puerto_999():
    """Listener principal del puerto 999 (Multihilo)."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((ip_servidor, port_999))
    servidor.listen()
    print("Servidor [999]: Listo para Login y Updates (Multihilo).")

    while True:
        try:
            conn, addr = servidor.accept()
            # Lanzamos un hilo por cada cliente, igual que en Ej3Server
            t = threading.Thread(target=gestionar_cliente_999, args=(conn, addr))
            t.start()
        except Exception as e:
            print(f"[ERROR ACCEPT 999] {e}")


# --- ARRANQUE ---
hilo_envios = threading.Thread(target=puerto_666)
hilo_recibos = threading.Thread(target=puerto_999)

hilo_envios.start()
hilo_recibos.start()

hilo_envios.join()
hilo_recibos.join()