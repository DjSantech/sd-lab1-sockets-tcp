import socket
import threading

# Configuración del cliente
HOST = '127.0.0.1'
PORT = 55555

nickname = input("Elige tu nombre de usuario: ")

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((HOST, PORT))

def recibir_mensajes():
    """Hilo secundario: Escucha de forma permanente los mensajes del servidor."""
    while True:
        try:
            mensaje = cliente.recv(1024).decode('utf-8')
            print(mensaje)
        except:
            print("Ha ocurrido un error o te has desconectado del servidor.")
            cliente.close()
            break

def enviar_mensajes():
    """Hilo principal: Escucha lo que escribe el usuario y lo envía."""
    while True:
        try:
            texto = input("")
            mensaje_completo = f"{nickname}: {texto}"
            cliente.send(mensaje_completo.encode('utf-8'))
        except:
            cliente.close()
            break

# Iniciar el hilo para recibir datos antes de entrar al bucle de envío
hilo_recibir = threading.Thread(target=recibir_mensajes)
hilo_recibir.daemon = True  # Permite que el hilo muera si el programa principal se cierra
hilo_recibir.start()

# Ejecutar la función de envío en el hilo principal
enviar_mensajes()
