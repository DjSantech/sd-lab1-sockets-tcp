import socket
import sys
import threading

# Configuración del cliente
# Uso: python cliente_hilos.py [IP_DEL_SERVIDOR]
# Si el servidor está en otra máquina, pasar su IP (ver con ipconfig en esa máquina).
HOST = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
PORT = 55555

nickname = input("Elige tu nombre de usuario: ")

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))
print(f"Conectado a {HOST}:{PORT}. Escribe mensajes ('/salir' para terminar).")


def recibir_mensajes():
    """Hilo secundario: Escucha de forma permanente los mensajes del servidor."""
    while True:
        try:
            datos = cliente.recv(1024)
        except OSError:
            break
        if not datos:  # el servidor cerró la conexión
            print("Desconectado del servidor.")
            break
        print(datos.decode('utf-8', 'replace'))
    cliente.close()


def enviar_mensajes():
    """Hilo principal: Escucha lo que escribe el usuario y lo envía."""
    while True:
        try:
            texto = input("")
        except (EOFError, KeyboardInterrupt):
            break
        if texto.strip() == "/salir":
            break
        try:
            cliente.sendall(f"{nickname}: {texto}".encode('utf-8'))
        except OSError:
            break
    cliente.close()


# Iniciar el hilo para recibir datos antes de entrar al bucle de envío
hilo_recibir = threading.Thread(target=recibir_mensajes, daemon=True)
hilo_recibir.start()

# Ejecutar la función de envío en el hilo principal
enviar_mensajes()
