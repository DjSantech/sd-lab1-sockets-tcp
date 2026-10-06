#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cliente_r2.py
Autor: Santiago Guevara Méndez - Sistemas Distribuidos, UTP (2026-2)
Laboratorio de Sistemas Distribuidos - Reto R2: protocolo con fronteras
Maquina: VM-CLIENTE

Cliente interactivo para servidor_r2.py. Cada linea escrita se envia como un
mensaje terminado en \\n, y la respuesta se lee tambien linea por linea con un
buffer propio (LectorLineas), porque un recv() del cliente tampoco garantiza
traer exactamente una respuesta.

Ejecucion:  python3 cliente_r2.py <ip_servidor> <puerto>
Ejemplo  :  python3 cliente_r2.py 192.168.56.10 5000
"""

import socket
import sys

TAM_BUFFER = 1024
DELIMITADOR = b"\n"


class LectorLineas:
    """Lee un socket TCP de a una linea (mensaje terminado en \\n).

    Guarda en self.buffer los bytes que ya llegaron pero aun no forman una
    linea completa, para no perderlos entre una llamada y la siguiente.
    """

    def __init__(self, sock, tam_buffer=TAM_BUFFER):
        self.sock = sock
        self.tam_buffer = tam_buffer
        self.buffer = b""         # vive entre llamadas a leer_linea()
        self.llamadas_recv = 0    # cuantos recv() hicieron falta (didactico)

    def leer_linea(self):
        """Devuelve la siguiente linea SIN el \\n (bytes), o None si el
        servidor cerro la conexion antes de completar otra linea."""
        while DELIMITADOR not in self.buffer:
            # recv(): se bloquea hasta que lleguen bytes o el FIN del
            # servidor (b""). Puede traer media linea o varias lineas.
            datos = self.sock.recv(self.tam_buffer)
            if not datos:
                return None
            self.llamadas_recv += 1
            self.buffer += datos
        linea, self.buffer = self.buffer.split(DELIMITADOR, 1)
        return linea


def main():
    if len(sys.argv) != 3:
        print("uso: python3 cliente_r2.py <ip_servidor> <puerto>")
        sys.exit(1)

    ip_servidor = sys.argv[1]
    puerto = int(sys.argv[2])

    # socket(): IPv4 + TCP, igual que el servidor.
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # connect(): apertura activa; el kernel hace el saludo de tres vias
        # y la llamada se bloquea hasta que termina (o falla).
        print(f"[cliente] conectando a {ip_servidor}:{puerto} ...")
        cliente.connect((ip_servidor, puerto))
        print(f"[cliente] extremo local  : {cliente.getsockname()}  "
              f"<- puerto efimero asignado por el S.O.")
        print(f"[cliente] extremo remoto : {cliente.getpeername()}")
        print("[cliente] cada linea es un mensaje (tambien la linea vacia). "
              "Escriba 'salir' para terminar.\n")

        lector = LectorLineas(cliente)
        while True:
            try:
                texto = input("> ")
            except EOFError:          # Ctrl+D o fin de la entrada estandar
                break
            if texto.lower() == "salir":
                break

            # Con delimitador, la linea vacia es un mensaje valido ("\n"):
            # ya no hay riesgo de quedar esperando una respuesta que no llega.
            mensaje = texto.encode("utf-8") + DELIMITADOR
            # sendall(): entrega todos los bytes del mensaje al kernel.
            cliente.sendall(mensaje)
            print(f"[cliente] enviados  {len(mensaje)} bytes: {mensaje!r}")

            respuesta = lector.leer_linea()
            if respuesta is None:
                print("[cliente] el servidor cerro la conexion")
                break
            # Se decodifica la linea completa, nunca un pedazo de recv().
            print(f"[cliente] respuesta : {respuesta.decode('utf-8')}")
            if respuesta.startswith(b"ERROR"):
                print("[cliente] el servidor reporto un error")

    except ConnectionRefusedError:
        print(f"[cliente] ERROR: conexion rechazada. "
              f"Nadie escucha en {ip_servidor}:{puerto}")
    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
        print(f"[cliente] la conexion se interrumpio: {type(e).__name__}")
    except OSError as e:
        print(f"[cliente] ERROR de red: {e}")
    except KeyboardInterrupt:
        print("\n[cliente] interrumpido por el usuario")
    finally:
        # close(): libera el socket y el kernel envia FIN al servidor.
        cliente.close()
        print("[cliente] socket cerrado")


if __name__ == "__main__":
    main()
