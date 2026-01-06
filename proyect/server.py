import socket
import threading

# Configuración
ip_servidor = "127.0.0.1"
puerto_envios = 666
puerto_recepcion = 999
archivo_usuarios = "usuarios.txt"


def validar_credenciales(usuario_recibido, clave_recibida):
    """
    Lee el archivo usuarios.txt y comprueba si existe la pareja usuario:clave.
    Devuelve True si es correcto, False si no.
    """
    es_valido = False
    try:
        archivo = open(archivo_usuarios, "r")
        lineas = archivo.readlines()
        archivo.close()

        # Recorremos el archivo línea a línea buscando coincidencia
        # Usamos un índice manual para evitar 'for' complejos si prefieres,
        # pero el 'for' es necesario para leer listas.
        for linea in lineas:
            # Limpiamos espacios y saltos de línea
            linea = linea.strip()
            if linea:  # Si la línea no está vacía
                partes = linea.split(":")
                if len(partes) == 2:
                    u_archivo = partes[0]
                    c_archivo = partes[1]

                    # Comprobamos si coincide exactamente
                    if u_archivo == usuario_recibido and c_archivo == clave_recibida:
                        es_valido = True
                        # No usamos break, así que el bucle sigue pero ya tenemos el True
    except FileNotFoundError:
        print(f"[ERROR] No se encuentra el archivo {archivo_usuarios}")

    return es_valido


def manejar_cliente_666(socket_cliente, direccion):
    print(f"[CONEXION 666] Nueva conexión desde {direccion}")

    conectado = True
    login_exitoso = False

    # --- FASE 1: LOGIN CON VALIDACIÓN REAL ---
    try:
        mensaje_login = socket_cliente.recv(1024).decode()

        # El formato debe ser LOGIN:USUARIO:CONTRASEÑA
        partes = mensaje_login.split(":")

        # Verificamos estructura (3 partes) y cabecera "LOGIN"
        if len(partes) == 3 and partes[0] == "LOGIN":
            usuario = partes[1]
            clave = partes[2]

            # LLAMAMOS A LA NUEVA FUNCIÓN DE VALIDACIÓN
            if validar_credenciales(usuario, clave):
                print(f"[LOGIN OK] Usuario aceptado: {usuario}")
                socket_cliente.send("OK".encode())
                login_exitoso = True
            else:
                print(f"[LOGIN FALLIDO] Credenciales incorrectas para: {usuario}")
                socket_cliente.send("KO".encode())
                conectado = False
        else:
            print(f"[LOGIN ERROR] Formato incorrecto: {mensaje_login}")
            socket_cliente.send("KO".encode())
            conectado = False

    except:
        print(f"[ERROR] Fallo durante el login con {direccion}")
        conectado = False

    while conectado and login_exitoso:
        try:
            mensaje = socket_cliente.recv(1024).decode()
            if mensaje:
                print(f"[MENSAJE] {mensaje}")
                socket_cliente.send("OK".encode())
                if mensaje == "!DISCONNECT":
                    conectado = False
            else:
                conectado = False
        except:
            conectado = False

    socket_cliente.close()
    print(f"[DESCONEXION] {direccion}")


# --- RESTO DEL CÓDIGO (Igual que antes) ---

def iniciar_servicio_666():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        servidor.bind((ip_servidor, puerto_envios))
        servidor.listen()
        print(f"[ARRANCADO] Servidor de ENVÍOS (666) listo.")
        activo = True
        while activo:
            cliente, direcc = servidor.accept()
            hilo = threading.Thread(target=manejar_cliente_666, args=(cliente, direcc))
            hilo.start()
    except OSError:
        print(f"[ERROR] Puerto {puerto_envios} ocupado.")


def iniciar_servicio_999():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        servidor.bind((ip_servidor, puerto_recepcion))
        servidor.listen()
        print(f"[ARRANCADO] Servidor de RECEPCIÓN (999) listo.")
        activo = True
        while activo:
            cliente, direcc = servidor.accept()
            cliente.close()
    except OSError:
        print(f"[ERROR] Puerto {puerto_recepcion} ocupado.")


print("---SERVIDOR WHATSAPP---")
# Asi no tengo que hacer dos hilos distintos para inicializarlos
servicios= [iniciar_servicio_666, iniciar_servicio_999]
hilos=[]
for servicio in servicios:
    t = threading.Thread(target=servicio)
    t.start()
    hilos.append(t)

for i in hilos:
    t.join()