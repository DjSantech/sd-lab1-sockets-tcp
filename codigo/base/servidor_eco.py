#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
servidor_eco.py
Laboratorio de Sistemas Distribuidos - Comunicacion por sockets TCP
Maquina: VM-SERVIDOR

Servidor de eco: acepta una conexion TCP, recibe bytes y los devuelve
convertidos a mayusculas. Imprime en pantalla cada paso del ciclo de vida
del socket para que el estudiante pueda observarlo.

Ejecucion:  python3 servidor_eco.py
"""

import socket

HOST = "0.0.0.0"   # escucha en todas las interfaces de la VM
PUERTO = 5000      # puerto de aplicacion (> 1023, no requiere privilegios)
TAM_BUFFER = 1024  # maximo de bytes que pedimos al kernel en cada recv()


def main():
    # PASO 1 - Crear el socket de escucha.
    # AF_INET  -> familia de direcciones IPv4 (direccion = IP + puerto)
    # SOCK_STREAM -> servicio de flujo de bytes fiable y ordenado = TCP
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Permite reutilizar el puerto inmediatamente tras cerrar el proceso,
    # sin esperar el estado TIME_WAIT de TCP.
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # PASO 2 - bind(): asociar el socket a una direccion local concreta.
    servidor.bind((HOST, PUERTO))

    # PASO 3 - listen(): apertura pasiva. El socket queda marcado como
    # "dispuesto a aceptar conexiones". El argumento es el tamano de la
    # cola de conexiones pendientes (backlog).
    servidor.listen(1)
    print(f"[servidor] socket de escucha en {servidor.getsockname()}")
    print("[servidor] esperando conexiones... (Ctrl+C para terminar)")

    try:
        while True:
            # PASO 4 - accept(): se BLOQUEA hasta que llega un cliente.
            # Devuelve un socket NUEVO y distinto, dedicado a esa conexion.
            conexion, direccion = servidor.accept()

            print("\n[servidor] ---- conexion aceptada ----")
            print(f"[servidor] cliente remoto : {direccion[0]}:{direccion[1]}")
            print(f"[servidor] extremo local  : {conexion.getsockname()}")
            print(f"[servidor] extremo remoto : {conexion.getpeername()}")
            print(f"[servidor] socket de escucha sigue siendo: "
                  f"{servidor.getsockname()} (distinto objeto)")

            with conexion:
                while True:
                    # PASO 5 - recv(): se bloquea hasta que haya bytes.
                    # Devuelve HASTA TAM_BUFFER bytes, no necesariamente
                    # un "mensaje" completo: TCP no conserva fronteras.
                    datos = conexion.recv(TAM_BUFFER)

                    if not datos:
                        # recv() devolvio 0 bytes: el otro extremo cerro.
                        print("[servidor] recv() devolvio 0 bytes -> "
                              "el cliente cerro la conexion")
                        break

                    print(f"[servidor] recibidos {len(datos)} bytes: {datos!r}")

                    # PASO 6 - sendall(): envia TODOS los bytes, repitiendo
                    # send() internamente hasta agotar el buffer.
                    respuesta = datos.upper()
                    conexion.sendall(respuesta)
                    print(f"[servidor] enviados  {len(respuesta)} bytes: "
                          f"{respuesta!r}")

            # Al salir del "with", close() libera el socket de datos.
            print("[servidor] conexion cerrada. Vuelvo a accept()\n")

    except KeyboardInterrupt:
        print("\n[servidor] interrumpido por el usuario")
    finally:
        servidor.close()
        print("[servidor] socket de escucha cerrado")


if __name__ == "__main__":
    main()
