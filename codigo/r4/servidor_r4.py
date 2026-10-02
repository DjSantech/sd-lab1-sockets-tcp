#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
servidor_r4.py
Laboratorio de Sistemas Distribuidos - Reto R4: varios clientes a la vez
Maquina: VM-SERVIDOR

Mismos comandos que R3 (HORA, ECO, ESTADISTICAS, ADIOS), pero cada socket que
devuelve accept() se atiende en su propio hilo (threading), asi que un cliente
lento no bloquea a los demas.

Problema que aparece al combinar R3 + R4: el contador de ESTADISTICAS es UNO
solo y ahora lo modifican varios hilos. "valor += 1" no es atomico: es leer,
sumar y escribir. Si dos hilos leen el mismo valor antes de que alguno
escriba, los dos escriben valor+1 y se pierde un incremento (condicion de
carrera). Solucion: un threading.Lock alrededor del incremento, de modo que
leer-sumar-escribir (y leer el resultado) lo haga un hilo a la vez.
Ver demo_carrera.py para verlo ocurrir.

Ejecucion:  python3 servidor_r4.py [puerto]
Cliente  :  python3 ../r2/cliente_r2.py 192.168.56.10 5000   (varios a la vez)
Requiere :  ../r3/servidor_r3.py (se copia toda la carpeta codigo/)
"""

import os
import sys
import threading

# servidor_r3.py esta en la carpeta hermana r3/.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "r3"))

from servidor_r3 import (Contador, atender_conexion,  # noqa: E402
                         crear_servidor, log)

HOST = "0.0.0.0"
PUERTO = 5000
COLA = 16          # con hilos si tiene sentido una cola mas larga


class ContadorSeguro(Contador):
    """Contador de R3 protegido con un Lock para uso desde varios hilos."""

    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()

    def incrementar(self):
        # Solo un hilo a la vez ejecuta este bloque: la lectura, la suma, la
        # escritura y el valor devuelto son consistentes entre si.
        with self._lock:
            self.valor += 1
            return self.valor


def atender_en_hilo(conexion, direccion, contador):
    """Cuerpo de cada hilo: atiende la conexion y la cierra al terminar."""
    # Se imprime desde el propio hilo (y no desde el principal) para que las
    # lineas de distintos hilos no se mezclen en la terminal.
    # -1 porque el hilo principal tambien cuenta.
    log(f"{threading.current_thread().name} atiende "
        f"{direccion[0]}:{direccion[1]} (hilos de clientes activos: "
        f"{threading.active_count() - 1})")
    with conexion:   # close() -> FIN al cliente, aunque haya error
        atender_conexion(conexion, direccion, contador)


def main():
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else PUERTO
    contador = ContadorSeguro()
    with crear_servidor(HOST, puerto, COLA) as servidor:
        print(f"[servidor] R4 (un hilo por cliente) en {servidor.getsockname()}")
        print("[servidor] comandos: HORA, ECO <texto>, ESTADISTICAS, ADIOS")
        try:
            while True:
                # accept(): el hilo principal SOLO acepta. Bloquea hasta que
                # haya una conexion y la entrega enseguida a un hilo nuevo,
                # para volver de inmediato a accept().
                conexion, direccion = servidor.accept()
                hilo = threading.Thread(target=atender_en_hilo,
                                        args=(conexion, direccion, contador),
                                        daemon=True)
                hilo.start()
        except KeyboardInterrupt:
            # Los hilos son daemon: terminan junto con el proceso.
            print("\n[servidor] interrumpido por el usuario")
    print("[servidor] socket de escucha cerrado")


if __name__ == "__main__":
    main()
