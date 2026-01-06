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
    Guarda el mensaje en el archivo correcto: MIUSUARIO_OTROUSUARIO.txt
    """
    try:
        # 1. Separamos el mensaje para saber quién es el "OTRO"
        partes = mensaje_formateado.split(";")
        origen = partes[0].replace("@", "")
        destino = partes[1].replace("@", "")

        if origen == MI_USUARIO:
            otro_usuario = destino # Si yo soy el origen, el archivo es con el destino.
        else:
            otro_usuario = origen # Si yo soy el destino, el archivo es con el origen.

        # 2. Creamos el nombre del archivo
        nombre_archivo = f"{MI_USUARIO}_{otro_usuario}"

        if es_temporal:
            nombre_archivo += "_tmp.txt"  # [cite: 57]
        else:
            nombre_archivo += ".txt"

        # 3. Guardamos en la carpeta 'historiales' para ser ordenados
        if not os.path.exists("Historiales"):
            os.makedirs("Historiales")

        ruta = os.path.join("Historiales", nombre_archivo)

        # 'a' significa append (añadir al final sin borrar lo anterior)
        with open(ruta, "a") as f:
            f.write(mensaje_formateado + "\n")
    except Exception as e:
        print(f"Error guardando archivo: {e}")
# --- FUNCIONES DE RED ---

def enviar_al_666(mensaje_formateado):
    """Envía mensaje al puerto de envíos [cite: 14]"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10) # Importante el timeout [cite: 116]
        s.connect((SERVER_IP, 666))
        s.send(mensaje_formateado.encode())
        
        resp = s.recv(1024).decode()
        
        if resp == "OK":
            # TODO 9: Éxito.
            # - Cambiar estado a ENVIADO o RECIBIDO en el string?
            # - Llamar a guardar_localmente(mensaje_formateado, es_temporal=False).
            pass
        else:
            print("Error en el envío")
            
        s.close()
        
    except Exception as e:
        # TODO 10: Gestión de OFFLINE.
        # - Si entra aquí, el servidor está caído.
        # - Llamar a guardar_localmente(mensaje_formateado, es_temporal=True).
        print(f"Servidor no disponible. Guardando en _tmp. Error: {e}")

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
    
    # TODO 12: Envolver en Try/Except por si servidor no está encendido.
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