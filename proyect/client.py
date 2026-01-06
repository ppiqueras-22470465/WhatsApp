import socket

# --- CONFIGURACIÓN DE RED ---
ip = "127.0.0.1"
puerto_envios = 666  # Puerto para LOGIN y ENVIAR mensajes [cite: 14]
puerto_recepcion = 999  # Puerto para RECIBIR (lo usaremos más adelante) [cite: 21]

# ¡IMPORTANTE! Nos conectamos al puerto 666, no al 999
direccion_envio = (ip, puerto_envios)

# Variables de control
mensaje_desconexion = "!DISCONNECT"
mensaje_error_conexion = "[ERROR] No se pudo conectar al servidor"


def iniciar_cliente_envios():
    # Creamos el socket
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Intentamos conectar
    try:
        cliente.connect(direccion_envio)
    except:
        print(mensaje_error_conexion)
        return

    print(f"[CONECTADO] Conectado al servidor de envíos en {ip}:{puerto_envios}")

    # --- PASO 1: AUTENTICACIÓN (LOGIN) ---
    # [cite_start]Según la práctica, esto es lo primero que se debe hacer [cite: 7, 8]
    usuario = input("Introduce tu Usuario: ")
    clave = input("Introduce tu Contraseña: ")

    # Preparamos el mensaje con el formato: LOGIN:USUARIO:CONTRASEÑA
    trama_login = f"LOGIN:{usuario}:{clave}"
    cliente.send(trama_login.encode())

    # [cite_start]Esperamos la respuesta del servidor (OK o KO) [cite: 10]
    try:
        respuesta_servidor = cliente.recv(1024).decode()
    except:
        print("[ERROR] El servidor cerró la conexión inesperadamente.")
        return

    conectado = False

    if respuesta_servidor == "OK":
        print("[LOGIN CORRECTO] Acceso concedido. Ya puedes escribir.")
        conectado = True
    else:
        # Si falla, cerramos y salimos
        print(f"[LOGIN FALLIDO] El servidor rechazó la conexión: {respuesta_servidor}")
        cliente.close()

    # --- PASO 2: BUCLE DE CHAT ---
    while conectado:
        try:
            # El usuario escribe el mensaje
            mensaje = input("> ")

            # Comprobamos si quiere desconectarse
            if mensaje == mensaje_desconexion:
                cliente.send(mensaje.encode())
                conectado = False
            else:
                # Enviamos el mensaje al servidor
                cliente.send(mensaje.encode())

                # [cite_start]Esperamos confirmación (ACK) del servidor [cite: 115]
                # El PDF dice que toda comunicación debe verificar con OK/KO
                respuesta = cliente.recv(1024).decode()
                print(f"[SERVIDOR CONFIRMA] {respuesta}")

        except:
            print("[ERROR CRÍTICO] Se perdió la conexión con el servidor.")
            conectado = False

    cliente.close()
    print("[DESCONECTADO] Programa finalizado.")


# Ejecutamos la función principal
iniciar_cliente_envios()