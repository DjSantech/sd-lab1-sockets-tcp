import socket
import threading

# Configuración del servidor
HOST = '127.0.0.1'  # Localhost
PORT = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clientes = []

def transmitir(mensaje, cliente_origen):
    """Envía el mensaje a todos los clientes excepto al que lo envió."""
    for cliente in clientes:
        if cliente != cliente_origen:
            try:
                cliente.send(mensaje)
            except:
                remover_cliente(cliente)

def remover_cliente(cliente):
    """Elimina al cliente de la lista si se desconecta."""
    if cliente in clientes:
        clientes.remove(cliente)
        cliente.close()

def manejar_cliente(cliente):
    """Maneja la comunicación con un cliente en un hilo dedicado."""
    while True:
        try:
            mensaje = cliente.recv(1024)
            if not mensaje:
                break
            transmitir(mensaje, cliente)
        except:
            break
    
    remover_cliente(cliente)

def iniciar_servidor():
    print(f"Servidor ejecutándose en {HOST}:{PORT}...")
    while True:
        cliente, direccion = server.accept()
        print(f"Nueva conexión desde {str(direccion)}")
        
        clientes.append(cliente)
        
        # Se inicia un hilo por cada cliente conectado
        hilo = threading.Thread(target=manejar_cliente, args=(cliente,))
        hilo.start()

if __name__ == "__main__":
    iniciar_servidor()
