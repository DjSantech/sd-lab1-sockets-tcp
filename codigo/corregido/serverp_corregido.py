#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
serverp_corregido.py
Version corregida de serverp.py (chat por turnos: el cliente escribe, el
servidor responde lo que teclea su usuario).

Problemas del original y como se corrigen aqui:
  1. IP fija 172.16.0.64 en bind(): falla en cualquier maquina que no tenga
     esa IP ("Cannot assign requested address").     -> bind a 0.0.0.0.
  2. Puerto fijo 12345.        -> 5000 por defecto, configurable por argumento.
  3. Sin SO_REUSEADDR: tras reiniciar, "Address already in use" (TIME_WAIT).
  4. Mensaje vacio: sendall(b"") no envia NADA, asi que el otro extremo se
     queda bloqueado en recv() esperando algo que nunca llega (y el primero
     espera su respuesta): los dos procesos quedan bloqueados.
     -> cada mensaje termina en \\n; el mensaje vacio viaja como b"\\n".
  5. recv(1024) puede traer medio mensaje o varios, y decodificar medio
     caracter UTF-8 lanza UnicodeDecodeError.  -> buffer + lineas completas.
  6. Sin manejo de errores ni cierre garantizado.   -> with / try y
     excepciones de conexion sin traceback.
  7. Atendia una sola conversacion y terminaba.   -> vuelve a accept().

Ejecucion:  python3 serverp_corregido.py [puerto]
"""

import socket
import sys

HOST = "0.0.0.0"    # todas las interfaces (corrige la IP fija)
PUERTO = 5000
TAM_BUFFER = 1024
DELIMITADOR = b"\n"


def leer_linea(conexion, estado):
    """Devuelve la siguiente linea completa (str, sin \\n) o None si el otro
    extremo cerro. estado["buffer"] guarda lo recibido que aun no es linea."""
    while DELIMITADOR not in estado["buffer"]:
        # recv(): bloquea hasta que lleguen bytes o el FIN (b"").
        datos = conexion.recv(TAM_BUFFER)
        if not datos:
            return None
        estado["buffer"] += datos
    linea, estado["buffer"] = estado["buffer"].split(DELIMITADOR, 1)
    return linea.decode("utf-8", errors="replace")


def atender_conexion(conexion, direccion):
    """Conversacion por turnos con un cliente."""
    print(f"Conexion establecida desde: {direccion[0]}:{direccion[1]}")
    estado = {"buffer": b""}
    try:
        while True:
            mensaje = leer_linea(conexion, estado)
            if mensaje is None:
                print("El cliente cerro la conexion")
                break
            print(f"Mensaje recibido del cliente: {mensaje!r}")

            try:
                respuesta = input("Ingrese la respuesta para el cliente: ")
            except EOFError:        # fin de la entrada del servidor
                print("Sin mas respuestas: se cierra la conexion")
                break
            # La respuesta vacia tambien viaja: es b"\n", nunca b"".
            conexion.sendall(respuesta.encode("utf-8") + DELIMITADOR)
    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
        print(f"La conexion termino con error: {type(e).__name__}")


def main():
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else PUERTO
    # socket(): IPv4 + TCP. with: se cierra aunque ocurra una excepcion.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, puerto))     # bind(): 0.0.0.0:puerto
        sock.listen(1)                # listen(): apertura pasiva
        print(f"Servidor escuchando en {HOST}:{puerto} (Ctrl+C para terminar)")
        try:
            while True:
                # accept(): bloquea hasta que llegue un cliente; devuelve un
                # socket nuevo para esa conversacion.
                conn, addr = sock.accept()
                with conn:
                    atender_conexion(conn, addr)
                print("Esperando otro cliente...")
        except KeyboardInterrupt:
            print("\nServidor detenido por el usuario")


if __name__ == "__main__":
    main()
