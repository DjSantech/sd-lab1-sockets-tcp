#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
servidor_r1.py
Autor: Santiago Guevara Méndez - Sistemas Distribuidos, UTP (2026-2)
Laboratorio de Sistemas Distribuidos - Reto R1: registro de conexiones
Maquina: VM-SERVIDOR

Servidor de eco (igual que servidor_eco.py: devuelve los bytes en mayusculas)
que ademas escribe en bitacora.log UNA linea por cada conexion atendida con:
  - marca de tiempo ISO 8601 del momento en que se acepto la conexion
  - IP y puerto del cliente, obtenidos con getpeername()
  - numero de mensajes (llamadas a recv() que trajeron datos)
  - bytes recibidos y bytes enviados
  - como termino la conexion (normal o el nombre del error)

La linea se escribe en un bloque finally, asi que queda registrada aunque la
conexion termine por un error (por ejemplo, un RST del cliente).

Ejecucion:  python3 servidor_r1.py
"""

import socket
from datetime import datetime

HOST = "0.0.0.0"          # escucha en todas las interfaces de la VM
PUERTO = 5000             # puerto de aplicacion
TAM_BUFFER = 1024         # maximo de bytes que pedimos al kernel en cada recv()
BITACORA = "bitacora.log" # se crea en la carpeta desde donde se ejecuta


def escribir_bitacora(linea):
    # Se abre en modo "a" (append) y se cierra en cada escritura: si el
    # servidor muere despues, la linea ya quedo en disco y no se pisan las
    # conexiones anteriores. Codificacion UTF-8 explicita y fin de linea "\n"
    # tambien en Windows.
    with open(BITACORA, "a", encoding="utf-8", newline="\n") as archivo:
        archivo.write(linea + "\n")


def atender_conexion(conexion, direccion):
    """Hace eco sobre 'conexion' hasta que el cliente cierre y registra la
    conexion en la bitacora. Devuelve el diccionario con los contadores."""
    # Marca de tiempo del inicio de la conexion, con zona horaria local,
    # en formato ISO 8601 (ej. 2026-09-30T14:05:12-05:00).
    inicio = datetime.now().astimezone().isoformat(timespec="seconds")

    # getpeername() justo despues de accept(): le pregunta al kernel por el
    # extremo REMOTO de este socket conectado (IP y puerto efimero del
    # cliente). No bloquea: el dato ya esta en la estructura del socket.
    # Si el cliente ya envio un RST, el kernel puede no tener el dato y
    # lanza OSError; en ese caso se usa la direccion devuelta por accept().
    try:
        ip_cliente, puerto_cliente = conexion.getpeername()[:2]
    except OSError:
        ip_cliente, puerto_cliente = direccion[:2]

    contadores = {"mensajes": 0, "bytes_recibidos": 0, "bytes_enviados": 0}
    cierre = "normal"

    print("\n[servidor] ---- conexion aceptada ----")
    print(f"[servidor] extremo local  : {conexion.getsockname()}")
    print(f"[servidor] extremo remoto : ({ip_cliente!r}, {puerto_cliente})"
          f"  <- getpeername()")

    try:
        while True:
            # recv(): se BLOQUEA hasta que el kernel tenga bytes de esta
            # conexion en su buffer de recepcion. Devuelve HASTA TAM_BUFFER
            # bytes, no un "mensaje": TCP no conserva fronteras.
            datos = conexion.recv(TAM_BUFFER)

            if not datos:
                # 0 bytes: llego el FIN del cliente, no habra mas datos.
                print("[servidor] recv() devolvio 0 bytes -> "
                      "el cliente cerro la conexion")
                break

            # En este servidor de eco un "mensaje" es lo que trajo un recv():
            # es la unidad que el servidor procesa y contesta.
            contadores["mensajes"] += 1
            contadores["bytes_recibidos"] += len(datos)
            print(f"[servidor] recibidos {len(datos)} bytes: {datos!r}")

            respuesta = datos.upper()
            # sendall(): repite send() hasta entregar TODOS los bytes al
            # buffer de envio del kernel (puede bloquear si esta lleno).
            # Si no lo logra lanza excepcion, asi que solo se cuentan los
            # bytes cuando retorna sin error.
            conexion.sendall(respuesta)
            contadores["bytes_enviados"] += len(respuesta)
            print(f"[servidor] enviados  {len(respuesta)} bytes: {respuesta!r}")

    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
        # RST del cliente (cerro con datos sin leer, o murio el proceso) o
        # escritura sobre una conexion ya cerrada. Se informa sin traceback.
        cierre = type(e).__name__
        print(f"[servidor] la conexion termino con error: {cierre}")
    except KeyboardInterrupt:
        # Ctrl+C en medio de una conexion: se registra y se deja subir la
        # excepcion para que main() termine el servidor.
        cierre = "KeyboardInterrupt"
        raise
    finally:
        # Se escribe SIEMPRE, termine bien o mal la conexion.
        escribir_bitacora(
            f"{inicio} cliente={ip_cliente}:{puerto_cliente} "
            f"mensajes={contadores['mensajes']} "
            f"bytes_recibidos={contadores['bytes_recibidos']} "
            f"bytes_enviados={contadores['bytes_enviados']} "
            f"cierre={cierre}"
        )
        print(f"[servidor] registrado en {BITACORA}: {contadores}, "
              f"cierre={cierre}")

    return contadores


def main():
    # socket(): crea el socket de escucha. AF_INET = IPv4, SOCK_STREAM = TCP.
    # El kernel reserva la estructura; todavia no tiene direccion.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        # SO_REUSEADDR: permite volver a hacer bind() al puerto aunque haya
        # conexiones anteriores en TIME_WAIT.
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # bind(): asocia el socket a 0.0.0.0:5000 (todas las interfaces).
        servidor.bind((HOST, PUERTO))

        # listen(): apertura pasiva. A partir de aqui el kernel completa los
        # saludos de tres vias por su cuenta y deja las conexiones en cola.
        servidor.listen(1)
        print(f"[servidor] socket de escucha en {servidor.getsockname()}")
        print(f"[servidor] bitacora: {BITACORA}")
        print("[servidor] esperando conexiones... (Ctrl+C para terminar)")

        try:
            while True:
                # accept(): se BLOQUEA hasta que haya una conexion ya
                # establecida en la cola. Devuelve un socket NUEVO para ella.
                conexion, direccion = servidor.accept()
                # with: cierra el socket de datos (close() -> FIN) al salir.
                with conexion:
                    atender_conexion(conexion, direccion)
                print("[servidor] conexion cerrada. Vuelvo a accept()")
        except KeyboardInterrupt:
            print("\n[servidor] interrumpido por el usuario")
    # Al salir del with externo se cierra tambien el socket de escucha.
    print("[servidor] socket de escucha cerrado")


if __name__ == "__main__":
    main()
