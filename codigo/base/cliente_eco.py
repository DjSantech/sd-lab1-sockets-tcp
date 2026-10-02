#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cliente_eco.py
Laboratorio de Sistemas Distribuidos - Comunicacion por sockets TCP
Maquina: VM-CLIENTE

Cliente de eco: abre una conexion TCP contra el servidor, envia por teclado
lineas de texto y muestra la respuesta. Imprime el puerto efimero que el
sistema operativo le asigna, para que el estudiante vea la cuadrupla que
identifica la conexion.

Ejecucion:  python3 cliente_eco.py <ip_servidor> <puerto>
Ejemplo  :  python3 cliente_eco.py 192.168.56.10 5000
"""

import socket
import sys

TAM_BUFFER = 1024


def main():
    if len(sys.argv) != 3:
        print("uso: python3 cliente_eco.py <ip_servidor> <puerto>")
        sys.exit(1)

    ip_servidor = sys.argv[1]
    puerto = int(sys.argv[2])

    # PASO 1 - Crear el socket (mismo tipo que el del servidor: IPv4 + TCP).
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # PASO 2 - connect(): apertura activa. Aqui ocurre el saludo de
        # tres vias (SYN / SYN-ACK / ACK). Si el servidor no esta
        # escuchando, esta linea lanza ConnectionRefusedError.
        print(f"[cliente] conectando a {ip_servidor}:{puerto} ...")
        cliente.connect((ip_servidor, puerto))

        print(f"[cliente] conectado")
        print(f"[cliente] extremo local  : {cliente.getsockname()}  "
              f"<- puerto efimero asignado por el S.O.")
        print(f"[cliente] extremo remoto : {cliente.getpeername()}")
        print("[cliente] escriba un texto y presione Enter. "
              "Escriba 'salir' para terminar.\n")

        while True:
            texto = input("> ")
            if texto == "":
                continue
            if texto.lower() == "salir":
                break

            # PASO 3 - Codificar: por el socket viajan BYTES, no str.
            mensaje = texto.encode("utf-8")
            cliente.sendall(mensaje)
            print(f"[cliente] enviados  {len(mensaje)} bytes: {mensaje!r}")

            # PASO 4 - Esperar el eco.
            respuesta = cliente.recv(TAM_BUFFER)
            if not respuesta:
                print("[cliente] recv() devolvio 0 bytes -> "
                      "el servidor cerro la conexion")
                break
            print(f"[cliente] recibidos {len(respuesta)} bytes: "
                  f"{respuesta.decode('utf-8')}")

    except ConnectionRefusedError:
        print(f"[cliente] ERROR: conexion rechazada. "
              f"Nadie escucha en {ip_servidor}:{puerto}")
    except OSError as e:
        print(f"[cliente] ERROR de red: {e}")
    except KeyboardInterrupt:
        print("\n[cliente] interrumpido por el usuario")
    finally:
        # PASO 5 - close(): libera el socket y envia FIN al servidor.
        cliente.close()
        print("[cliente] socket cerrado")


if __name__ == "__main__":
    main()
