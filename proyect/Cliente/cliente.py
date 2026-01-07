import socket
import threading
import time
from datetime import datetime
import os

# Configuración
SERVER_IP = "127.0.0.1"
MI_USUARIO = "" 

# --- FUNCIONES AUXILIARES ---

def obtener_timestamp():
    """Devuelve fecha hora formato YYYYMMDDhhmmss [cite: 76]"""
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S")

def formatear_mensaje(origen, destino, estado, mensaje):
    """Crea el string separado por ;"""
    ts = obtener_timestamp()
    return f"{origen};{destino};{ts};{estado};{ts};\"{mensaje}\""

def guardar_localmente(mensaje_formateado, es_temporal=False):
    """
    Guarda el mensaje en el archivo correcto: MI_USUARIO_OTROUSUARIO.txt
    (Asume que la carpeta 'Historiales' ya existe)
    """
    try:
        # 1. Separar el mensaje para saber quién es el "OTRO"
        partes = mensaje_formateado.split(";")
        origen = partes[0].replace("@", "")
        destino = partes[1].replace("@", "")

        # Determinar con quién es el historial
        if origen == MI_USUARIO:
            otro_usuario = destino
        else:
            otro_usuario = origen

        # 2. Construir nombre del archivo
        nombre_archivo = MI_USUARIO + "_" + otro_usuario
        if es_temporal:
            nombre_archivo += "_tmp.txt"
        else:
            nombre_archivo += ".txt"

        # 3. Construir ruta manualmente (sin os.path)
        ruta = "Historiales/" + nombre_archivo

        # 4. Guardar en modo append
        f = open(ruta, "a")
        f.write(mensaje_formateado + "\n")
        f.close()

    except Exception as e:
        print(f"Error guardando archivo: {e}")

# --- FUNCIONES DE RED ---

def enviar_al_666(mensaje_formateado):
    """Envía mensaje al puerto de envíos [cite: 14]"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)  # Importante el timeout [cite: 116]
        s.connect((SERVER_IP, 666))
        s.send(mensaje_formateado.encode())

        resp = s.recv(1024).decode()

        if resp == "OK":
            partes = mensaje_formateado.split(";")
            partes[3] = "ENVIADO"  # Estado confirmado por el servidor
            mensaje_ok = ";".join(partes)

            # Guardamos en local como definitivo
            guardar_localmente(mensaje_ok, es_temporal=False)

        else:
            print("Error en el envío")

        s.close()

    except Exception as e:
        print(f"Servidor no disponible. Guardando en _tmp. Error: {e}")
        guardar_localmente(mensaje_formateado, es_temporal=True)

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

def procesar_mensajes_offline():
    ###### FUNCION POR TERMINAR
    """
    [cite_start]Busca archivos _tmp, intenta enviarlos y si tiene éxito, los borra. [cite: 58]
    """
    if not os.path.exists("Historiales"):
        return

    # Buscar archivos temporales
    patron = os.path.join("Historiales", "*_tmp.txt")
    lista_archivos = glob.glob(patron)

    if lista_archivos:
        print(f"--- Procesando {len(lista_archivos)} archivos pendientes ---")

    for ruta_archivo in lista_archivos:
        enviados_ok = True
        lineas_pendientes = []

        try:
            # Leer contenido
            with open(ruta_archivo, "r") as f:
                lineas_pendientes = f.readlines()

            # Intentar reenviar uno a uno
            for linea in lineas_pendientes:
                linea = linea.strip()
                if not linea: continue

                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5)
                    s.connect((SERVER_IP, 666))
                    s.send(linea.encode())
                    resp = s.recv(1024).decode()
                    s.close()

                    if resp == "OK":
                        print("Recuperado y enviado mensaje pendiente.")
                        guardar_localmente(linea, es_temporal=False)
                    else:
                        enviados_ok = False
                except:
                    enviados_ok = False

            # Si todo salió bien, borramos el temporal
            if enviados_ok:
                os.remove(ruta_archivo)

        except Exception as e:
            print(f"Error procesando offline: {e}")


def gestionar_comando_lista():
    """Implementa el comando @lista [cite: 38]"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((SERVER_IP, 999))

        # [cite_start]Formato LIST: @Yo;@;Time;LIST;000;"" [cite: 120]
        msg = f"@{MI_USUARIO};@;{obtener_timestamp()};LIST;00000000000000;\"\""
        s.send(msg.encode())

        # Recibir cabecera con cantidad
        cabecera = s.recv(1024).decode()
        # Parsear cantidad (está en el último campo entre comillas)
        # Ejemplo: ...;LIST;...;"5"
        partes = cabecera.split(";")
        cantidad_str = partes[5].replace('"', '')
        cantidad = int(cantidad_str)

        s.send("OK".encode())  # Confirmamos cabecera

        print(f"\n--- LISTA DE CONVERSACIONES ({cantidad}) ---")
        for i in range(cantidad):
            datos_chat = s.recv(1024).decode()
            # Parsear para mostrar bonito
            # Formato recibido: Origen;Destino;...;LIST;...;"Pendientes"
            p = datos_chat.split(";")
            usuario_remoto = p[1].replace("@", "")  # El destino en la lista es el otro
            pendientes = p[5].replace('"', '')

            print(f"{i + 1}. @{usuario_remoto} ({pendientes} mensajes nuevos)")

            s.send("OK".encode())

        s.close()
    except Exception as e:
        print(f"Error al pedir lista: {e}")

def hilo_recepcion_actualizaciones():
    """
    Segundo hilo: Pregunta cada X seg si hay mensajes nuevos (Puerto 999) 
    """
    while True:
        time.sleep(5) 
        
        if MI_USUARIO != "":
            try:
                # TODO 11: Implementar lógica completa UPDATE [cite: 95-98].
                # 1. Leer de mis archivos locales cuál es el último timestamp que tengo.
                # 2. Formatear mensaje UPDATE con ese timestamp.
                
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((SERVER_IP, 999))
                
                msg_update = formatear_mensaje(MI_USUARIO, "@", "UPDATE", "") # Ajustar params
                s.send(msg_update.encode())
                
                # 3. Recibir primer mensaje con la CANTIDAD (n).
                cabecera = s.recv(1024).decode()
                # Parsear cabecera para sacar 'n'.
                s.send("OK".encode()) # Confirmar cabecera.
                
                # 4. Bucle for i in range(n):
                #    - msg = s.recv(1024).decode()
                #    - guardar_localmente(msg)
                #    - print(msg) # Actualizar pantalla si procede.
                #    - s.send("OK".encode())
                
                s.close()
            except Exception:
                pass # Si falla actualización silenciosa, no pasa nada

def sistema_login():
    """Gestiona el inicio de sesión [cite: 8, 9]"""
    global MI_USUARIO
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
            return True
        else:
            print("Login Incorrecto.")
            return False
    except:
        print("No se pudo conectar al servidor para Login.")
        return False

# --- ARRANQUE ---
if sistema_login():
    # TODO 13: Revisar si hay mensajes pendientes en archivos _tmp[cite: 58].
    # - Antes de empezar, buscar archivos que acaben en _tmp.
    # - Leerlos y llamar a enviar_al_666() para cada línea.
    # - Borrar el archivo _tmp al terminar.

    t = threading.Thread(target=hilo_recepcion_actualizaciones)
    t.start()
    
    print(f"Bienvenido {MI_USUARIO}. Escribe '@Usuario: mensaje' para chatear.")
    
    seguir_ejecutando = True 

    while seguir_ejecutando:
        texto = input() 
        
        if texto == "@salir":
            # TODO 14: Enviar mensaje de fin al servidor si es necesario?
            seguir_ejecutando = False 
            
        elif texto.startswith("@lista"):
             # TODO 15: Implementar comando LIST[cite: 38].
             # - Enviar mensaje tipo LIST al puerto 999.
             # - Recibir y mostrar la lista de usuarios/mensajes.
             pass

        elif texto.startswith("@") and ":" in texto:
            partes = texto.split(":", 1) 
            destinatario = partes[0] 
            contenido = partes[1].strip() 
            
            msg_final = formatear_mensaje(MI_USUARIO, destinatario, "ENVIADO", contenido)
            enviar_al_666(msg_final)
        else:
            print("Formato incorrecto. Usa: @Nombre: Mensaje")