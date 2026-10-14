import socket
import threading

# Configuración del servidor
# 0.0.0.0 = escucha en todas las interfaces, así clientes de OTRAS máquinas pueden conectarse
HOST = '0.0.0.0'
PORT = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

clientes = []
lock = threading.Lock()  # protege la lista compartida entre hilos


def transmitir(mensaje, cliente_origen):
    """Envía el mensaje a todos los clientes excepto al que lo envió."""
    with lock:
        destinos = [c for c in clientes if c != cliente_origen]
    for cliente in destinos:
        try:
            cliente.sendall(mensaje)
        except OSError:
            remover_cliente(cliente)


def remover_cliente(cliente):
    """Elimina al cliente de la lista si se desconecta."""
    with lock:
        if cliente not in clientes:
            return
        clientes.remove(cliente)
    cliente.close()


def manejar_cliente(cliente, direccion):
    """Maneja la comunicación con un cliente en un hilo dedicado."""
    hilo = threading.current_thread().name
    while True:
        try:
            mensaje = cliente.recv(1024)
        except OSError:
            break
        if not mensaje:
            break
        print(f"[{hilo}] {direccion} -> {mensaje.decode('utf-8', 'replace')}")
        transmitir(mensaje, cliente)

    print(f"[{hilo}] {direccion} se desconectó")
    remover_cliente(cliente)
    transmitir(f"*** {direccion[0]} salió del chat ***".encode('utf-8'), None)


def iniciar_servidor():
    print(f"Servidor ejecutándose en {HOST}:{PORT}...")
    while True:
        cliente, direccion = server.accept()
        print(f"Nueva conexión desde {direccion}")

        with lock:
            clientes.append(cliente)

        # Se inicia un hilo por cada cliente conectado
        hilo = threading.Thread(target=manejar_cliente, args=(cliente, direccion), daemon=True)
        hilo.start()
        print(f"Hilos activos (clientes): {threading.active_count() - 1}")


if __name__ == "__main__":
    try:
        iniciar_servidor()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.close()
