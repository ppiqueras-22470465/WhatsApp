import socket
import threading
import datetime
import time

# --- CONFIGURACION ---
ip_servidor = "127.0.0.1"
archivo_usuarios = "logs/usuarios.txt"
archivo_indice = "logs/indice_chats.txt"
port_999 = 999
port_666 = 666

sem_archivos = threading.Semaphore(1)
timeout_conexion = 60.0




def es_entrada_segura(texto):
    es_valido = True
    if ":" in texto or ";" in texto or ".txt" in texto or texto.strip() == "":
        es_valido = False
    return es_valido


def obtener_timestamp_actual():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")


def validar_login(usuario, password):
    encontrado = False
    if sem_archivos.acquire(timeout=5):
        try:
            f = open(archivo_usuarios, "r")
            lineas = f.readlines()
            f.close()
            sem_archivos.release()
            i = 0
            while i < len(lineas) and encontrado == False:
                linea_limpia = lineas[i].strip()
                if len(linea_limpia) > 0:
                    partes = linea_limpia.split(":")
                    if len(partes) == 2 and partes[0] == usuario and partes[1] == password:
                        encontrado = True
                i = i + 1
        except Exception as e:
            print(f"Ha ocurrido un error en el archivo: {e}")
            sem_archivos.release()
    return encontrado


def registrar_usuario(usuario, password):
    exito = False
    if es_entrada_segura(usuario) and es_entrada_segura(password):
        if sem_archivos.acquire(timeout=5):
            try:
                ya_existe = False
                try:
                    f_r = open(archivo_usuarios, "r")
                    lineas = f_r.readlines()
                    f_r.close()
                    j = 0
                    while j < len(lineas) and ya_existe == False:
                        if lineas[j].strip().split(":")[0] == usuario:
                            ya_existe = True
                        j = j + 1
                except Exception:
                    ya_existe = False

                if ya_existe == False:
                    f_a = open(archivo_usuarios, "a")
                    f_a.write(usuario + ":" + password + "\n")
                    f_a.close()
                    exito = True
                    print("[SISTEMA] Nuevo usuario registrado: " + usuario)

                sem_archivos.release()
            except Exception as e:
                print(f"Ha ocurrido un error en el archivo: {e}")
                sem_archivos.release()
    return exito


def validar_nombre_archivo_chat(emisor, receptor):
    u1 = emisor.replace(".txt", "").strip()
    u2 = receptor.replace(".txt", "").strip()
    archivo1 = u1 + "_" + u2 + ".txt"
    archivo2 = u2 + "_" + u1 + ".txt"
    nombre_final = archivo1
    try:
        f = open(archivo1, "r")
        f.close()
        nombre_final = archivo1
    except Exception:
        try:
            f = open(archivo2, "r")
            f.close()
            nombre_final = archivo2
        except Exception:
            nombre_final = archivo1
    return nombre_final


def registrar_en_indice(nombre_archivo):
    try:
        ya_en_indice = False
        try:
            f_r = open(archivo_indice, "r")
            lineas = f_r.readlines()
            f_r.close()
            k = 0
            while k < len(lineas) and ya_en_indice == False:
                if lineas[k].strip() == nombre_archivo:
                    ya_en_indice = True
                k = k + 1
        except Exception:
            ya_en_indice = False

        if ya_en_indice == False:
            f_a = open(archivo_indice, "a")
            f_a.write(nombre_archivo + "\n")
            f_a.close()
    except Exception as e:
        print(f"Ha ocurrido un error en el archivo: {e}")


def guardar_mensaje_en_archivo(datos, addr, conn):
    realizado = False
    datos_limpios = datos.strip()
    partes = datos_limpios.split(";")
    if len(partes) >= 6:
        emisor = partes[0].replace("@", "")
        receptor = partes[1].replace("@", "")

        if es_entrada_segura(emisor) and es_entrada_segura(receptor):
            archivo_chat = validar_nombre_archivo_chat(emisor, receptor)
            while realizado == False:
                if sem_archivos.acquire(timeout=5):
                    try:
                        f = open(archivo_chat, "a")
                        f.write(datos_limpios + "\n")
                        f.close()
                        registrar_en_indice(archivo_chat)
                        sem_archivos.release()
                        conn.send("OK".encode())
                        print("[INFO] Mensaje de @" + emisor + " guardado en " + archivo_chat)
                        realizado = True
                    except Exception as e:
                        print(f"Ha ocurrido un error en el archivo: {e}")
                        sem_archivos.release()
                        try:
                            conn.send("KO".encode())
                        except:
                            pass
                        realizado = True
                else:
                    print("[SISTEMA] Reintentando semaforo...")
        else:
            print("[ERROR] Datos corruptos recibidos.")
            realizado = True
    else:
        print("[ERROR] Formato incorrecto recibido.")
        realizado = True


def gestionar_cliente_999(conn, addr):
    login_ok = False
    usuario_conectado = ""
    cliente_activo = True
    conn.settimeout(timeout_conexion)

    while cliente_activo == True:
        try:
            buffer = conn.recv(1024).decode().strip()
            if buffer == "":
                cliente_activo = False
            else:
                if buffer.startswith("LOGIN"):
                    d = buffer.split(":")
                    if len(d) == 3 and validar_login(d[1], d[2]):
                        conn.send("OK".encode())
                        login_ok = True
                        usuario_conectado = d[1]
                        # Comentado para no saturar la consola con cada reconexion del hilo
                        # print("[LOGIN] Sesion iniciada: " + usuario_conectado)
                    else:
                        conn.send("KO".encode())

                elif buffer.startswith("REGISTER"):
                    d = buffer.split(":")
                    if len(d) == 3 and registrar_usuario(d[1], d[2]):
                        conn.send("OK".encode())
                    else:
                        conn.send("KO".encode())

                elif login_ok == True and ";LIST;" in buffer:
                    lista_usuarios = []
                    if sem_archivos.acquire(timeout=5):
                        try:
                            f = open(archivo_usuarios, "r")
                            lineas = f.readlines()
                            f.close()
                            idx = 0
                            while idx < len(lineas):
                                p = lineas[idx].strip().split(":")
                                if len(p) >= 1:
                                    nombre = p[0]
                                    if nombre != usuario_conectado:
                                        lista_usuarios.append(nombre)
                                idx = idx + 1
                            sem_archivos.release()
                        except Exception as e:
                            print(f"Ha ocurrido un error en el archivo: {e}")
                            sem_archivos.release()

                    ts = obtener_timestamp_actual()
                    conn.send(("SERVER;" + usuario_conectado + ";" + ts + ";LIST;" + ts + ";\"" + str(
                        len(lista_usuarios)) + "\"").encode())
                    if conn.recv(1024).decode() == "OK":
                        x = 0
                        while x < len(lista_usuarios):
                            conn.send(lista_usuarios[x].encode())
                            conn.recv(1024)
                            x = x + 1

                elif login_ok == True and ";UPDATE;" in buffer:
                    # --- LOGICA CRITICA: BUSCAR Y ENTREGAR MENSAJES ---
                    mensajes_para_enviar = []
                    if sem_archivos.acquire(timeout=5):
                        try:
                            # 1. Obtenemos lista de chats
                            try:
                                f_idx = open(archivo_indice, "r")
                                archivos = f_idx.readlines()
                                f_idx.close()
                            except:
                                archivos = []

                            k = 0
                            while k < len(archivos):
                                nombre_archivo = archivos[k].strip()
                                # Solo miramos archivos donde participe el usuario
                                if usuario_conectado in nombre_archivo:
                                    cambios_fichero = False
                                    lineas_nuevas = []
                                    try:
                                        f_lectura = open(nombre_archivo, "r")
                                        lineas_chat = f_lectura.readlines()
                                        f_lectura.close()

                                        m = 0
                                        while m < len(lineas_chat):
                                            linea = lineas_chat[m].strip()
                                            partes = linea.split(";")
                                            if len(partes) >= 6:
                                                dest = partes[1].replace("@", "")
                                                estado = partes[3]

                                                # SI YO SOY EL DESTINO Y ESTA EN 'RECIBIDO'
                                                if dest == usuario_conectado and estado == "RECIBIDO":
                                                    mensajes_para_enviar.append(linea)
                                                    # Marcamos como entregado
                                                    ts_now = obtener_timestamp_actual()
                                                    nueva_l = partes[0] + ";" + partes[1] + ";" + partes[
                                                        2] + ";ENTREGADO;" + ts_now + ";" + partes[5]
                                                    lineas_nuevas.append(nueva_l)
                                                    cambios_fichero = True
                                                else:
                                                    lineas_nuevas.append(linea)
                                            else:
                                                lineas_nuevas.append(linea)
                                            m = m + 1

                                        if cambios_fichero == True:
                                            f_escritura = open(nombre_archivo, "w")
                                            w = 0
                                            while w < len(lineas_nuevas):
                                                f_escritura.write(lineas_nuevas[w] + "\n")
                                                w = w + 1
                                            f_escritura.close()
                                    except Exception:
                                        pass
                                k = k + 1
                            sem_archivos.release()
                        except Exception as e:
                            print(f"Ha ocurrido un error en el archivo: {e}")
                            sem_archivos.release()

                    # Enviar los mensajes encontrados al cliente
                    ts = obtener_timestamp_actual()
                    conn.send(("SERVER;" + usuario_conectado + ";" + ts + ";UPDATE;" + ts + ";\"" + str(
                        len(mensajes_para_enviar)) + "\"").encode())

                    if conn.recv(1024).decode() == "OK":
                        z = 0
                        while z < len(mensajes_para_enviar):
                            conn.send(mensajes_para_enviar[z].encode())
                            conn.recv(1024)
                            z = z + 1

        except Exception as e:
            cliente_activo = False
    conn.close()


def puerto_666():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((ip_servidor, port_666))
    servidor.listen(15)
    print("[PUERTO 666] Escuchando recepcion de mensajes...")
    while True:
        try:
            conn, addr = servidor.accept()
            try:
                datos = conn.recv(1024).decode()
                if datos != "":
                    guardar_mensaje_en_archivo(datos, addr, conn)
            except Exception as e:
                print(f"Ha ocurrido un error en el archivo (666): {e}")
            conn.close()
        except Exception as e:
            print(f"Ha ocurrido un error en el archivo: {e}")


def puerto_999():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((ip_servidor, port_999))
    servidor.listen(15)
    print("[PUERTO 999] Escuchando comandos de login y registro...")
    while True:
        try:
            conn, addr = servidor.accept()
            t = threading.Thread(target=gestionar_cliente_999, args=(conn, addr))
            t.start()
        except Exception as e:
            print(f"Ha ocurrido un error en el archivo: {e}")


hilo_msj = threading.Thread(target=puerto_666)
hilo_cmd = threading.Thread(target=puerto_999)
hilo_msj.start()
hilo_cmd.start()