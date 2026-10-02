#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
servidor_r2.py
Laboratorio de Sistemas Distribuidos - Reto R2: protocolo con fronteras
Maquina: VM-SERVIDOR

Servidor de eco con mensajes delimitados por salto de linea (\\n).
Protocolo:
  - cliente -> servidor: texto UTF-8 terminado en \\n (un mensaje por linea)
  - servidor -> cliente: el mismo texto en mayusculas, terminado en \\n
  - si un mensaje supera el limite sin que aparezca el \\n, el servidor
    responde "ERROR ...\\n" y cierra la conexion

Como TCP es un flujo de bytes, un recv() puede traer medio mensaje, un
mensaje o varios. Por eso los bytes se acumulan en un buffer y solo se
procesan los mensajes COMPLETOS (los que ya tienen su \\n).

Ejecucion:  python3 servidor_r2.py [puerto] [limite_bytes]
Ejemplo  :  python3 servidor_r2.py 5000 65536
"""

import socket
import sys

HOST = "0.0.0.0"             # escucha en todas las interfaces de la VM
PUERTO = 5000                # puerto de aplicacion
TAM_BUFFER = 1024            # maximo de bytes que pedimos al kernel por recv()
LIMITE_MENSAJE = 64 * 1024   # tamano maximo de un mensaje (sin contar el \n)
DELIMITADOR = b"\n"          # frontera de mensaje acordada con el cliente


def corto(valor, maximo=60):
    """repr() recortado, para que un mensaje grande no inunde la terminal."""
    r = repr(valor)
    return r if len(r) <= maximo else f"{r[:maximo]}... ({len(valor)} en total)"


def procesar(texto):
    """Logica de la aplicacion: el eco en mayusculas. Recibe y devuelve str."""
    return texto.upper()


def atender_conexion(conexion, direccion, limite=LIMITE_MENSAJE):
    """Atiende una conexion hasta que el cliente cierre o se supere el limite.

    Devuelve un diccionario con los mensajes completos procesados, el residuo
    que quedo sin \\n al cerrar, el motivo del cierre y cuantos recv() con
    datos hubo (se usa en las pruebas).
    """
    print(f"\n[servidor] ---- conexion aceptada desde "
          f"{direccion[0]}:{direccion[1]} ----")

    # El buffer se declara FUERA del bucle de recv(): asi el pedazo de
    # mensaje que sobre en una vuelta se conserva para la siguiente.
    buffer = b""
    mensajes = []
    motivo = "cierre del cliente"
    llamadas_recv = 0

    try:
        while True:
            # recv(): se bloquea hasta que el kernel tenga bytes de esta
            # conexion. Devuelve un pedazo arbitrario del flujo (1..TAM_BUFFER
            # bytes) o b"" si el cliente envio FIN.
            datos = conexion.recv(TAM_BUFFER)
            if not datos:
                break
            llamadas_recv += 1
            buffer += datos    # lo nuevo se suma a lo que sobro antes
            completos = 0

            # while y no if: un solo recv() puede traer VARIOS mensajes.
            while DELIMITADOR in buffer:
                # split(..., 1) corta solo en el PRIMER \n: a la izquierda
                # queda un mensaje completo y a la derecha el resto (que
                # puede contener otros mensajes o un mensaje a medias).
                crudo, buffer = buffer.split(DELIMITADOR, 1)
                completos += 1

                if len(crudo) > limite:
                    enviar_error(conexion, f"mensaje de {len(crudo)} bytes "
                                           f"supera el limite de {limite}")
                    motivo = "limite superado"
                    return resultado(mensajes, buffer, motivo, llamadas_recv)

                # Se decodifica SOLO el mensaje completo. Si un caracter
                # multibyte (ej. la n con tilde = 2 bytes) quedo partido entre
                # dos recv(), a estas alturas ya esta entero en 'crudo'.
                try:
                    texto = crudo.decode("utf-8")
                except UnicodeDecodeError:
                    enviar_error(conexion, "el mensaje no es UTF-8 valido")
                    continue

                mensajes.append(texto)
                respuesta = procesar(texto).encode("utf-8") + DELIMITADOR
                # sendall(): entrega TODA la respuesta al buffer de envio del
                # kernel, repitiendo send() internamente si hace falta.
                conexion.sendall(respuesta)
                print(f"[servidor] mensaje #{len(mensajes)}: {corto(texto)} -> "
                      f"{corto(respuesta)}")

            print(f"[servidor] recv() #{llamadas_recv}: {len(datos)} bytes "
                  f"{corto(datos)} -> {completos} mensaje(s) completo(s), "
                  f"{len(buffer)} byte(s) esperando su \\n")

            # Lo que queda en el buffer es un mensaje a medias. Si ya es mas
            # grande que el limite y aun no llega el \n, se corta la conexion
            # para que un cliente no pueda llenar la memoria del servidor.
            if len(buffer) > limite:
                enviar_error(conexion, f"mas de {limite} bytes sin \\n")
                motivo = "limite superado"
                return resultado(mensajes, buffer, motivo, llamadas_recv)

    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
        # RST del cliente o escritura sobre una conexion que ya no existe.
        motivo = type(e).__name__
        print(f"[servidor] la conexion termino con error: {motivo}")

    return resultado(mensajes, buffer, motivo, llamadas_recv)


def enviar_error(conexion, detalle):
    """Envia una linea de error al cliente (el cierre lo hace quien llama)."""
    linea = f"ERROR {detalle}".encode("utf-8") + DELIMITADOR
    print(f"[servidor] {linea!r}")
    try:
        conexion.sendall(linea)
    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
        pass


def resultado(mensajes, residuo, motivo, llamadas_recv):
    """Informa el residuo sin \\n (si lo hay) y arma el resumen de la conexion."""
    if residuo:
        print(f"[servidor] mensaje incompleto descartado ({len(residuo)} "
              f"bytes sin \\n): {corto(residuo)}")
    print(f"[servidor] fin de la conexion ({motivo}): "
          f"{len(mensajes)} mensaje(s) en {llamadas_recv} recv()")
    return {"mensajes": mensajes, "residuo": residuo, "motivo": motivo,
            "llamadas_recv": llamadas_recv}


def crear_servidor(host, puerto):
    """Crea el socket de escucha: socket() + SO_REUSEADDR + bind() + listen()."""
    # socket(): IPv4 (AF_INET) + flujo de bytes fiable (SOCK_STREAM = TCP).
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # SO_REUSEADDR: permite reiniciar el servidor sin esperar TIME_WAIT.
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind(): asocia el socket a (host, puerto). Puerto 0 = el kernel
        # elige uno libre (lo usan las pruebas).
        servidor.bind((host, puerto))
        # listen(): apertura pasiva; el kernel empieza a aceptar saludos de
        # tres vias y a encolar conexiones establecidas (cola de 1, como en
        # servidor_eco.py).
        servidor.listen(1)
    except OSError:
        servidor.close()
        raise
    return servidor


def main():
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else PUERTO
    limite = int(sys.argv[2]) if len(sys.argv) > 2 else LIMITE_MENSAJE

    with crear_servidor(HOST, puerto) as servidor:
        print(f"[servidor] socket de escucha en {servidor.getsockname()}")
        print(f"[servidor] mensajes delimitados por \\n, limite {limite} bytes")
        print("[servidor] esperando conexiones... (Ctrl+C para terminar)")
        try:
            while True:
                # accept(): se BLOQUEA hasta que haya una conexion
                # establecida en la cola; devuelve un socket NUEVO para ella.
                conexion, direccion = servidor.accept()
                # with: al salir se hace close() del socket de datos (FIN).
                with conexion:
                    atender_conexion(conexion, direccion, limite)
                print("[servidor] conexion cerrada. Vuelvo a accept()")
        except KeyboardInterrupt:
            print("\n[servidor] interrumpido por el usuario")
    print("[servidor] socket de escucha cerrado")


if __name__ == "__main__":
    main()
