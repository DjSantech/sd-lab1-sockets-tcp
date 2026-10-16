import json
import os
import sys
import threading
import time
from datetime import datetime
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

# Uso: python servidor_rpc.py [PUERTO]
HOST = '0.0.0.0'  # escucha en todas las interfaces, para que otras máquinas se conecten
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
TIMEOUT_CONEXION = 6  # segundos sin "latido" y el usuario se considera desconectado

ARCHIVO_USUARIOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'usuarios.json')
ARCHIVO_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'servidor_log.txt')

lock = threading.Lock()  # protege los diccionarios compartidos entre los hilos de las peticiones
usuarios = {}   # nombre -> último latido (0 si nunca se ha conectado en esta ejecución)
pendientes = {}  # nombre -> lista de mensajes/archivos que aún no ha recogido


def log(texto):
    """Muestra el registro en pantalla y lo guarda en servidor_log.txt."""
    linea = f"[{datetime.now().strftime('%H:%M:%S')}] {texto}"
    print(linea, flush=True)
    with open(ARCHIVO_LOG, 'a', encoding='utf-8') as f:
        f.write(linea + '\n')


def guardar_usuarios():
    with open(ARCHIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(sorted(usuarios), f)


def esta_conectado(nombre):
    return time.time() - usuarios.get(nombre, 0) < TIMEOUT_CONEXION


# ---------------- Funciones remotas (lo que el cliente puede invocar) ----------------

def registrar(nombre):
    """El cliente entra al sistema. Si es nuevo queda en el directorio."""
    with lock:
        nuevo = nombre not in usuarios
        usuarios[nombre] = time.time()
        pendientes.setdefault(nombre, [])
        guardar_usuarios()
    log(f"REGISTRO   {nombre} {'(usuario nuevo) ' if nuevo else ''}se conectó")
    return True


def desconectar(nombre):
    with lock:
        if nombre in usuarios:
            usuarios[nombre] = 0
    log(f"SALIDA     {nombre} se desconectó")
    return True


def listar_usuarios(nombre):
    """Devuelve el directorio [(usuario, conectado?)]. También sirve de latido del que pregunta."""
    with lock:
        if nombre in usuarios:
            usuarios[nombre] = time.time()
        return [[u, esta_conectado(u)] for u in sorted(usuarios)]


def enviar_mensaje(de, para, texto):
    with lock:
        if para not in usuarios:
            return False
        pendientes[para].append({'tipo': 'texto', 'de': de, 'texto': texto,
                                 'hora': datetime.now().strftime('%H:%M')})
        estado = 'en línea' if esta_conectado(para) else 'DESCONECTADO (queda en cola)'
    log(f"MENSAJE    {de} -> {para} [{estado}]: {texto}")
    return True


def enviar_archivo(de, para, nombre_archivo, contenido):
    """contenido llega como xmlrpc.client.Binary: sirve para imágenes, textos y sonidos."""
    datos = contenido.data
    with lock:
        if para not in usuarios:
            return False
        pendientes[para].append({'tipo': 'archivo', 'de': de, 'nombre': nombre_archivo,
                                 'contenido': datos, 'hora': datetime.now().strftime('%H:%M')})
        estado = 'en línea' if esta_conectado(para) else 'DESCONECTADO (queda en cola)'
    log(f"ARCHIVO    {de} -> {para} [{estado}]: {nombre_archivo} ({len(datos)} bytes)")
    return True


def recibir_pendientes(nombre):
    """El cliente pregunta si tiene algo nuevo. Entrega y vacía su cola. También es latido."""
    with lock:
        if nombre not in usuarios:
            return []
        usuarios[nombre] = time.time()
        cola, pendientes[nombre] = pendientes[nombre], []
    for item in cola:
        detalle = item['texto'] if item['tipo'] == 'texto' else item['nombre']
        log(f"ENTREGA    {item['de']} -> {nombre}: {detalle}")
    return cola


class ServidorHilos(ThreadingMixIn, SimpleXMLRPCServer):
    """Un hilo por cada petición RPC, así varios clientes se atienden a la vez."""
    daemon_threads = True
    allow_reuse_address = True


class Manejador(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


if __name__ == "__main__":
    if os.path.exists(ARCHIVO_USUARIOS):
        with open(ARCHIVO_USUARIOS, encoding='utf-8') as f:
            for u in json.load(f):
                usuarios[u] = 0
                pendientes[u] = []

    servidor = ServidorHilos((HOST, PORT), requestHandler=Manejador, logRequests=False,
                             allow_none=True)
    for funcion in (registrar, desconectar, listar_usuarios, enviar_mensaje,
                    enviar_archivo, recibir_pendientes):
        servidor.register_function(funcion)

    log(f"Servidor RPC ejecutándose en {HOST}:{PORT}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        log("Servidor detenido.")
        servidor.server_close()
