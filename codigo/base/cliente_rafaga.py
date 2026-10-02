#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cliente_rafaga.py
Laboratorio de Sistemas Distribuidos - Experimento E4
Maquina: VM-CLIENTE

Envia tres "mensajes" seguidos, sin pausa entre ellos, y despues lee UNA sola
vez. Sirve para comprobar que TCP entrega un FLUJO DE BYTES y no conserva las
fronteras entre los envios: el servidor puede ver las tres cadenas pegadas en
un unico recv().

Ejecucion:  python3 cliente_rafaga.py <ip_servidor> <puerto> [pausa_segundos]
Ejemplo  :  python3 cliente_rafaga.py 192.168.56.10 5000 0
            python3 cliente_rafaga.py 192.168.56.10 5000 1
"""

import socket
import sys
import time

TAM_BUFFER = 1024
MENSAJES = [b"uno", b"dos", b"tres"]


def main():
    if len(sys.argv) not in (3, 4):
        print("uso: python3 cliente_rafaga.py <ip_servidor> <puerto> "
              "[pausa_segundos]")
        sys.exit(1)

    ip_servidor = sys.argv[1]
    puerto = int(sys.argv[2])
    pausa = float(sys.argv[3]) if len(sys.argv) == 4 else 0.0

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        cliente.connect((ip_servidor, puerto))
        print(f"[rafaga] conectado desde {cliente.getsockname()} "
              f"hacia {cliente.getpeername()}")
        print(f"[rafaga] pausa entre envios: {pausa} s\n")

        total = 0
        for m in MENSAJES:
            cliente.sendall(m)
            total += len(m)
            print(f"[rafaga] send  -> {m!r} ({len(m)} bytes)")
            if pausa > 0:
                time.sleep(pausa)

        print(f"\n[rafaga] se enviaron {total} bytes en "
              f"{len(MENSAJES)} llamadas a sendall()")
        print("[rafaga] ahora UNA sola llamada a recv()...")

        respuesta = cliente.recv(TAM_BUFFER)
        print(f"[rafaga] recv  <- {respuesta!r} ({len(respuesta)} bytes)")
        print("\n[rafaga] Pregunta: los 3 envios llegaron juntos o separados?"
              " Por que?")

    except OSError as e:
        print(f"[rafaga] ERROR de red: {e}")
    finally:
        cliente.close()


if __name__ == "__main__":
    main()
