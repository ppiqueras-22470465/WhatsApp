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
# EN servidor.py

def puerto_666():
    """Gestiona el ENVÍO y las CONFIRMACIONES de lectura."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((ip_servidor, port_666))
    servidor.listen()
    print("Servidor [666]: Listo.")

    conexion_servidor = True

    while conexion_servidor:
        try:
            conn, addr = servidor.accept()
            conn.settimeout(10)

            try:
                mensaje = conn.recv(1024).decode()
                if mensaje != "":
                    partes = mensaje.split(";")

                    if mensaje == "!DESCONECTAR":
                        conexion_servidor = False

                    elif len(partes) >= 6:
                        estado = partes[3]

                        # --- CASO A: Confirmación de LECTURA (LEIDO) ---
                        if estado == "LEIDO":
                            # El cliente nos avisa que leyó el chat con X
                            # Tenemos que buscar el archivo y actualizar TODO lo que estaba ENTREGADO a LEIDO
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
                                        # Si el mensaje es PARA MÍ (Yo soy destino) y estaba ENTREGADO -> LEIDO
                                        if len(p) >= 6 and p[1].replace("@", "") == emisor and p[3] == "ENTREGADO":
                                            ts_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                                            # Actualizamos estado y timestamp de estado
                                            nuevo_m = f"{p[0]};{p[1]};{p[2]};LEIDO;{ts_now};{p[5]}"
                                            new_lines.append(nuevo_m)
                                            cambio = True
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
                            # (Lógica estándar de guardar mensaje nuevo)
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
        except:
            print("Error en el servidor 666")


def gestionar_cliente_999(conn, addr):
    """Atiende UPDATE incluyendo actualizaciones de estado para el remitente."""
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
                        ts_solicitado = partes[4]  # El cliente nos dice qué es lo último que tiene
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
                                            ts_estado = p[4]  # Cuando cambió el estado

                                            # CRITERIO 1: Mensajes para mí que debo recibir (RECIBIDO -> ENTREGADO)
                                            if destino == usuario_conectado and estado == "RECIBIDO":
                                                mensajes_a_enviar.append(m)
                                                # Cambio estado
                                                now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                                                linea_final = f"{p[0]};{p[1]};{p[2]};ENTREGADO;{now};{p[5]}"
                                                modificado = True

                                            # CRITERIO 2: Mensajes QUE YO ENVIÉ y han cambiado de estado (ENTREGADO/LEIDO)
                                            # Comparamos el TS del Estado con el TS que pide el cliente
                                            elif origen == usuario_conectado and ts_estado > ts_solicitado:
                                                # Se lo mandamos para que actualice su local de ENVIADO a ENTREGADO/LEIDO
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

                    # Enviar al cliente
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
                    # (Mismo código de LIST que tenías antes...)
                    # Para simplificar la respuesta, asumo que usas el bloque LIST previo
                    conn.send(f"SERVER;{usuario_conectado};0;LIST;0;\"0\"".encode())  # Placeholder
                    conn.recv(1024)

                else:
                    conn.send("KO".encode())
                    conexion_activa = False
        except:
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