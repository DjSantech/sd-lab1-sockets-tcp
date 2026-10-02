#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
servidor_r3.py
Laboratorio de Sistemas Distribuidos - Reto R3: comandos en lugar de eco
Maquina: VM-SERVIDOR

Usa el mismo protocolo de R2 (una linea terminada en \\n por mensaje) pero en
vez de hacer eco interpreta comandos:

  HORA           -> fecha y hora del servidor (ISO 8601)
  ECO <texto>    -> devuelve <texto>
  ESTADISTICAS   -> mensajes atendidos desde que arranco el servidor
                    (de todas las conexiones, incluido este)
  ADIOS          -> responde ADIOS y cierra la conexion
  otra cosa      -> ERROR comando desconocido

El nombre del comando no distingue mayusculas/minusculas; el texto de ECO se
devuelve tal cual. Este servidor atiende UN cliente a la vez (ver R4).

Ejecucion:  python3 servidor_r3.py [puerto]
Cliente  :  python3 ../r2/cliente_r2.py 192.168.56.10 5000
"""

import socket
import sys
from datetime import datetime

HOST = "0.0.0.0"
PUERTO = 5000
TAM_BUFFER = 1024
LIMITE_MENSAJE = 64 * 1024
DELIMITADOR = b"\n"


def log(mensaje):
    """print() de una linea en UNA sola escritura: cuando R4 atiende en varios
    hilos, las lineas no se mezclan (print normal escribe texto y \\n aparte)."""
    print(f"[servidor] {mensaje}\n", end="", flush=True)


class Contador:
    """Mensajes atendidos desde el arranque, compartido por todas las
    conexiones. En este servidor de un solo hilo no necesita proteccion."""

    def __init__(self):
        self.valor = 0

    def incrementar(self):
        self.valor += 1
        return self.valor


def ejecutar(linea, contador):
    """Interpreta una linea. Devuelve (respuesta, cerrar_conexion)."""
    atendidos = contador.incrementar()
    comando, _, argumento = linea.partition(" ")
    comando = comando.upper()

    if comando == "HORA":
        return datetime.now().astimezone().isoformat(timespec="seconds"), False
    if comando == "ECO":
        return argumento, False
    if comando == "ESTADISTICAS":
        return f"mensajes atendidos desde el arranque: {atendidos}", False
    if comando == "ADIOS":
        return "ADIOS", True
    return "ERROR comando desconocido", False


def atender_conexion(conexion, direccion, contador, limite=LIMITE_MENSAJE):
    """Lee lineas de 'conexion' (buffer como en R2) y responde cada comando."""
    log(f"conexion desde {direccion[0]}:{direccion[1]}")
    buffer = b""                   # fuera del bucle: conserva el resto parcial
    try:
        while True:
            # recv(): bloquea hasta que haya bytes o llegue el FIN (b"").
            datos = conexion.recv(TAM_BUFFER)
            if not datos:
                break
            buffer += datos

            while DELIMITADOR in buffer:          # puede haber varias lineas
                crudo, buffer = buffer.split(DELIMITADOR, 1)
                try:
                    linea = crudo.decode("utf-8")  # solo lineas completas
                except UnicodeDecodeError:
                    linea = None
                if linea is None:
                    respuesta, cerrar = "ERROR el mensaje no es UTF-8 valido", False
                else:
                    respuesta, cerrar = ejecutar(linea, contador)
                # sendall(): entrega la respuesta completa al kernel.
                conexion.sendall(respuesta.encode("utf-8") + DELIMITADOR)
                log(f"{direccion[1]}: {linea!r} -> {respuesta!r}")
                if cerrar:
                    return

            if len(buffer) > limite:
                conexion.sendall(f"ERROR mas de {limite} bytes sin \\n"
                                 .encode("utf-8") + DELIMITADOR)
                return
    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
        log(f"{direccion[1]}: la conexion termino con error: "
            f"{type(e).__name__}")
    finally:
        if buffer:
            log(f"{direccion[1]}: mensaje incompleto descartado "
                f"({len(buffer)} bytes sin \\n)")
        log(f"{direccion[1]}: fin de la conexion")


def crear_servidor(host, puerto, cola=1):
    """socket() + SO_REUSEADDR + bind() + listen(cola)."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((host, puerto))
        servidor.listen(cola)
    except OSError:
        servidor.close()
        raise
    return servidor


def main():
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else PUERTO
    contador = Contador()
    with crear_servidor(HOST, puerto) as servidor:
        print(f"[servidor] R3 (un cliente a la vez) en {servidor.getsockname()}")
        print("[servidor] comandos: HORA, ECO <texto>, ESTADISTICAS, ADIOS")
        try:
            while True:
                # accept(): bloquea hasta que haya una conexion en la cola.
                conexion, direccion = servidor.accept()
                with conexion:     # close() al terminar -> FIN al cliente
                    atender_conexion(conexion, direccion, contador)
        except KeyboardInterrupt:
            print("\n[servidor] interrumpido por el usuario")
    print("[servidor] socket de escucha cerrado")


if __name__ == "__main__":
    main()
