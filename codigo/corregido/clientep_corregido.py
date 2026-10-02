#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clientep_corregido.py
Version corregida de clientep.py (chat por turnos con serverp_corregido.py).

Problemas del original y como se corrigen aqui:
  1. IP 172.16.0.64 y puerto 12345 fijos en el codigo.
     -> se pasan por linea de comandos, como en la guia.
  2. Mensaje vacio: sendall(b"") no envia nada y el cliente se queda bloqueado
     para siempre en recv().  -> cada mensaje termina en \\n.
  3. Un solo recv(1024) por respuesta: puede traer media respuesta o varias.
     -> buffer y lectura de lineas completas.
  4. Si el servidor cerraba, recv() devolvia b"" y el cliente mostraba una
     respuesta vacia como si fuera valida.  -> se detecta el cierre.
  5. Sin manejo de errores (servidor apagado, conexion reiniciada) ni cierre
     garantizado.  -> try/finally y mensajes claros.

Ejecucion:  python3 clientep_corregido.py <ip_servidor> <puerto>
Ejemplo  :  python3 clientep_corregido.py 192.168.56.10 5000
"""

import socket
import sys

TAM_BUFFER = 1024
DELIMITADOR = b"\n"


def leer_linea(sock, estado):
    """Siguiente linea completa del servidor (str) o None si cerro."""
    while DELIMITADOR not in estado["buffer"]:
        datos = sock.recv(TAM_BUFFER)   # bloquea hasta tener bytes o FIN
        if not datos:
            return None
        estado["buffer"] += datos
    linea, estado["buffer"] = estado["buffer"].split(DELIMITADOR, 1)
    return linea.decode("utf-8", errors="replace")


def main():
    if len(sys.argv) != 3:
        print("uso: python3 clientep_corregido.py <ip_servidor> <puerto>")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # connect(): apertura activa (saludo de tres vias en el kernel).
        sock.connect((host, port))
        print(f"Conectado a {host}:{port} desde {sock.getsockname()}")
        estado = {"buffer": b""}

        while True:
            message = input("Ingrese un mensaje para el servidor: ")
            # El mensaje vacio viaja como b"\n": el servidor SI lo recibe.
            sock.sendall(message.encode("utf-8") + DELIMITADOR)

            data = leer_linea(sock, estado)
            if data is None:
                print("El servidor cerro la conexion")
                break
            print(f"Respuesta del servidor: {data!r}")

            continuar = input("¿Desea enviar otro mensaje? (s/n): ")
            if continuar.strip().lower() != "s":
                break

    except ConnectionRefusedError:
        print(f"Conexion rechazada: nadie escucha en {host}:{port}")
    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
        print(f"La conexion se interrumpio: {type(e).__name__}")
    except OSError as e:
        print(f"Error de red: {e}")
    except (KeyboardInterrupt, EOFError):
        print("\nCliente terminado por el usuario")
    finally:
        sock.close()    # close(): libera el socket y envia FIN


if __name__ == "__main__":
    main()
