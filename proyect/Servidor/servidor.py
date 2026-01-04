import socket
import threading
import os

HOST = "127.0.0.1"

# --- FUNCIONES AUXILIARES (LÓGICA) ---

def validar_login(datos):
    """
    Comprueba si el usuario y contraseña son correctos.
    Formato recibido: LOGIN:USUARIO:CONTRASEÑA [cite: 9]
    """
    # TODO 1: Implementar lectura real de 'usuarios.txt'.
    # - Abrir el archivo "usuarios.txt" en modo lectura ('r').
    # - Recorrerlo línea por línea.
    # - Hacer split(':') a cada línea para separar usuario y contraseña.
    # - Comparar con las variables que vienen en 'datos'.
    # - Si coincide, retornar True. Si termina el archivo sin coincidencia, False.

    datos = datos.split(":")
    for linea in open("usuarios.txt", "r"):
        usuario_archivo, contrasena_archivo = linea.strip().split(":")
        if datos[1] == usuario_archivo and datos[2] == contrasena_archivo:
            print(f"Validando credenciales: {datos}")
            return True
    return False

def guardar_mensaje_en_archivo(mensaje_formateado):
    """
    Recibe el string con ; y lo guarda en el archivo correspondiente.
    Busca si existe Origen_Destino.txt o Destino_Origen.txt[cite: 67, 68].
    """
    # TODO 2: Lógica de selección de archivo de chat.
    # - Extraer remitente y destinatario del 'mensaje_formateado' (split por ';').
    # - Comprobar con os.path.exists() si existe "remitente_destinatario.txt".
    # - Si no, comprobar si existe "destinatario_remitente.txt".
    # - Si no existe ninguno, crear uno nuevo (por defecto "remitente_destinatario.txt").
    
    # TODO 3: Escritura física.
    # - Abrir ese archivo en modo append ('a').
    # - Escribir 'mensaje_formateado' seguido de un salto de línea (\n).
    # - Cerrar archivo.
    print(f"DISCO DURO >> Guardando mensaje: {mensaje_formateado}")

# --- FUNCIONES NUEVAS NECESARIAS ---

def obtener_mensajes_pendientes(usuario_solicitante, usuario_destino, ultimo_timestamp):
    # TODO 4: Función para el UPDATE.
    # - Localizar el archivo de chat entre estos dos usuarios.
    # - Leer todas las líneas.
    # - Filtrar: Quedarse solo con líneas cuyo timestamp (campo 3) > ultimo_timestamp.
    # - Retornar esa lista de líneas.
    pass

# --- HILOS DE CONEXIÓN ---

def puerto_666():
    """Gestiona el ENVÍO de mensajes (Cliente -> Servidor) [cite: 14]"""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, 666))
    servidor.listen()
    print("Servidor [666]: Listo para recibir mensajes.")
    
    while True:
        conn, addr = servidor.accept()
        datos = conn.recv(1024).decode()
        
        if datos:
            # Aquí llega el mensaje formateado: Origen;Destino;...
            print(f"[666] Recibido: {datos}")
            
            # TODO 5: Cambiar estado a RECIBIDO.
            # - Antes de guardar, reemplazar en el string "ENVIADO" por "RECIBIDO"[cite: 79].
            # - Actualizar el timestamp de estado.
            guardar_mensaje_en_archivo(datos)
            
            # Confirmamos recepción obligatoria [cite: 10]
            conn.send("OK".encode())
            
        conn.close()

def puerto_999():
    """Gestiona RECEPCIÓN y LOGIN (Cliente <-> Servidor) [cite: 21]"""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, 999))
    servidor.listen()
    print("Servidor [999]: Listo para Login y Updates.")
    
    while True:
        conn, addr = servidor.accept()
        datos = conn.recv(1024).decode()
        
        if datos.startswith("LOGIN"):
            # Gestión de Login 
            if validar_login(datos):
                conn.send("OK".encode())
            else:
                conn.send("KO".encode())
                
        elif "UPDATE" in datos:
            # Petición de actualización de mensajes [cite: 105]
            print(f"[999] Petición UPDATE recibida: {datos}")
            
            # TODO 6: Implementar protocolo de entrega de mensajes[cite: 123].
            # 1. Parsear 'datos' para sacar quién pide (Origen) y la fecha (Timestamp).
            # 2. Llamar a obtener_mensajes_pendientes().
            # 3. Enviar PRIMER mensaje: Cabecera con el número total de mensajes a enviar (en el campo texto).
            # 4. Esperar recibir "OK" del cliente.
            # 5. Bucle for mensaje in mensajes:
            #    - conn.send(mensaje)
            #    - conn.recv(1024) -> Esperar "OK" de cada mensaje.
            
            conn.send("OK".encode()) # Esto es temporal, borrar al hacer el TODO 6
            
        # TODO 7: Implementar LIST[cite: 108].
        # - Añadir un elif "LIST" in datos:
        # - Buscar todos los archivos donde aparezca el nombre del usuario.
        # - Enviar la lista siguiendo la misma lógica de bucle que el UPDATE.

        conn.close()

# --- ARRANQUE ---
hilo_envios = threading.Thread(target=puerto_666)
hilo_recibos = threading.Thread(target=puerto_999)

hilo_envios.start()
hilo_recibos.start()