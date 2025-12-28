# WhatsApp
Sistema de chat estilo WhatsApp en consola (CLI) sobre sockets TCP. Arquitectura Cliente-Servidor con autenticación, doble canal para envío/recepción simultáneos y persistencia de logs. Gestiona estados de mensajes (Enviado/Entregado/Leído), sincronización automática y cola offline. Sin GUI, enfocado en protocolos de comunicación robustos.
# Console WhatsApp (TCP Sockets Implementation)

![Status](https://img.shields.io/badge/Status-Development-yellow) ![Java/Python](https://img.shields.io/badge/Language-Any-blue) ![Protocol](https://img.shields.io/badge/Protocol-TCP%2FIP-red)

Sistema de mensajería instantánea asíncrona en modo consola (CLI), implementado sobre Sockets TCP puros sin interfaz gráfica. El proyecto simula la arquitectura de una aplicación tipo WhatsApp con arquitectura Cliente-Servidor, gestión de estados de mensajes y colas de persistencia offline.

## 📋 Descripción del Proyecto

El objetivo es crear un sistema de comunicación robusto donde un **Servidor Central** desatendido gestiona el enrutamiento de mensajes entre múltiples **Clientes**.

### Características Principales
* **Comunicación Asíncrona:** Uso de hilos separados para envío y recepción simultánea.
* **Doble Canal TCP:** Puertos diferenciados para tráfico de salida (envíos) y entrada (actualizaciones).
* **Persistencia Local y Remota:** Logs de conversación completos en ambos extremos.
* **Gestión de Estados:** Trazabilidad completa del mensaje (Enviado → Recibido → Entregado → Leído).
* **Cola Offline:** Almacenamiento temporal (`_tmp`) de mensajes cuando el servidor no está disponible.
* **Autenticación:** Sistema de Login simple contra archivo de usuarios.

---

## ⚙️ Arquitectura Técnica

El sistema opera sobre dos conexiones TCP independientes por cada cliente conectado:

| Puerto | Servicio | Descripción |
| :--- | :--- | :--- |
| **666** | **Canal de Envíos** | Conexión efímera para enviar mensajes o comandos al servidor. |
| **999** | **Canal de Recepción** | Conexión para *polling* de actualizaciones y descarga de mensajes nuevos. |

### Timeouts y Control
* Todas las conexiones tienen un **Timeout de 10 segundos**.
* Protocolo de verificación `OK` / `KO` para cada transacción.

---

## 📡 Protocolo de Comunicación

### 1. Autenticación (Handshake)
Al iniciar cualquier conexión (puerto 666 o 999), se debe enviar la siguiente cabecera:
```text
LOGIN:USUARIO:CONTRASEÑA
