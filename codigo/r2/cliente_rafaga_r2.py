#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cliente_rafaga_r2.py
Autor: Santiago Guevara Méndez - Sistemas Distribuidos, UTP (2026-2)
Laboratorio de Sistemas Distribuidos - Reto R2 (repite el experimento E4)
Maquina: VM-CLIENTE

Igual que cliente_rafaga.py, pero cada "mensaje" termina en \\n. Envia los
tres seguidos (o con la pausa indicada) y luego lee las respuestas con el
buffer de LectorLineas hasta tener las tres, mostrando cuantos recv() hicieron
falta. Asi se ve que, aunque los bytes se agrupen distinto en cada corrida,
el servidor y el cliente recuperan exactamente tres mensajes.

Ejecucion:  python3 cliente_rafaga_r2.py <ip_servidor> <puerto> [pausa_segundos]
Ejemplo  :  python3 cliente_rafaga_r2.py 192.168.56.10 5000 0
"""

import socket
import sys
import time

from cliente_r2 import LectorLineas

TAM_BUFFER = 1024
MENSAJES = [b"uno\n", b"dos\n", b"tres\n"]


def main():
    if len(sys.argv) not in (3, 4):
        print("uso: python3 cliente_rafaga_r2.py <ip_servidor> <puerto> "
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
        print("[rafaga] ahora se leen las respuestas linea por linea...")

        lector = LectorLineas(cliente, TAM_BUFFER)
        for i in range(len(MENSAJES)):
            linea = lector.leer_linea()
            if linea is None:
                print("[rafaga] el servidor cerro la conexion antes de tiempo")
                break
            print(f"[rafaga] respuesta {i + 1}: {linea.decode('utf-8')!r}")

        print(f"\n[rafaga] {len(MENSAJES)} mensajes enviados, "
              f"{lector.llamadas_recv} llamada(s) a recv() para leer las "
              f"respuestas")

    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
        print(f"[rafaga] la conexion se interrumpio: {type(e).__name__}")
    except OSError as e:
        print(f"[rafaga] ERROR de red: {e}")
    finally:
        cliente.close()


if __name__ == "__main__":
    main()
