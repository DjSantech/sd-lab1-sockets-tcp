#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cliente_rtt.py
Laboratorio de Sistemas Distribuidos - Reto R5: tiempo de ida y vuelta (RTT)
Maquina: VM-CLIENTE   (servidor: ../r2/servidor_r2.py en VM-SERVIDOR)

Envia 100 mensajes de 10 bytes y 100 de 8000 bytes, de a uno: envia, espera
la respuesta completa y solo entonces envia el siguiente. El RTT de cada
mensaje es el tiempo entre justo antes de sendall() y el momento en que llega
la linea de respuesta completa. Al final imprime minimo, maximo y media.

"Mensaje de N bytes" = N bytes en el cable, incluido el \\n final.
El reloj es time.perf_counter() (monotono, alta resolucion) del cliente, asi
que no importa que los relojes de las dos VM no esten sincronizados.

Ejecucion:  python3 cliente_rtt.py <ip_servidor> <puerto> [repeticiones]
Ejemplo  :  python3 cliente_rtt.py 192.168.56.10 5000
"""

import os
import socket
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "r2"))

from cliente_r2 import LectorLineas   # noqa: E402

TAMANOS = [10, 8000]      # bytes por mensaje, incluido el \n
REPETICIONES = 100


def medir_serie(cliente, lector, tamano, repeticiones):
    """Devuelve la lista de RTT (en milisegundos) de una serie."""
    # tamano-1 letras + "\n". Se usan minusculas para que la respuesta
    # (mayusculas) tenga el mismo tamano y se pueda verificar.
    mensaje = b"a" * (tamano - 1) + b"\n"
    esperado = b"A" * (tamano - 1)
    rtts = []
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        cliente.sendall(mensaje)
        respuesta = lector.leer_linea()
        fin = time.perf_counter()
        if respuesta is None:
            raise ConnectionError("el servidor cerro la conexion")
        if respuesta != esperado:
            raise ValueError(f"respuesta inesperada de {len(respuesta)} bytes")
        rtts.append((fin - inicio) * 1000)
    return rtts


def main():
    if len(sys.argv) not in (3, 4):
        print("uso: python3 cliente_rtt.py <ip_servidor> <puerto> "
              "[repeticiones]")
        sys.exit(1)
    ip_servidor = sys.argv[1]
    puerto = int(sys.argv[2])
    repeticiones = int(sys.argv[3]) if len(sys.argv) == 4 else REPETICIONES

    # Una sola conexion para todas las mediciones: asi el saludo de tres
    # vias (connect) no entra en el RTT de ningun mensaje.
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        cliente.connect((ip_servidor, puerto))
        print(f"[rtt] conectado desde {cliente.getsockname()} "
              f"hacia {cliente.getpeername()}")
        lector = LectorLineas(cliente)

        resultados = {}
        for tamano in TAMANOS:
            print(f"[rtt] midiendo {repeticiones} mensajes de {tamano} bytes...")
            resultados[tamano] = medir_serie(cliente, lector, tamano,
                                             repeticiones)

        print()
        print(f"{'Tamano (B)':>10} | {'N':>4} | {'Min (ms)':>9} | "
              f"{'Max (ms)':>9} | {'Media (ms)':>10}")
        print("-" * 55)
        for tamano, rtts in resultados.items():
            print(f"{tamano:>10} | {len(rtts):>4} | {min(rtts):>9.3f} | "
                  f"{max(rtts):>9.3f} | {statistics.mean(rtts):>10.3f}")

    except ConnectionRefusedError:
        print(f"[rtt] ERROR: nadie escucha en {ip_servidor}:{puerto}")
    except (ConnectionError, ValueError) as e:
        print(f"[rtt] ERROR: {e}")
    except OSError as e:
        print(f"[rtt] ERROR de red: {e}")
    except KeyboardInterrupt:
        print("\n[rtt] interrumpido por el usuario")
    finally:
        cliente.close()


if __name__ == "__main__":
    main()
