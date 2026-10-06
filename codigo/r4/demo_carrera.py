#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
demo_carrera.py
Autor: Santiago Guevara Méndez - Sistemas Distribuidos, UTP (2026-2)
Reto R4 - por que el contador de ESTADISTICAS necesita un Lock.

Varios hilos llaman incrementar() sobre el MISMO contador, como hacen los
hilos de servidor_r4.py con cada mensaje. Se comparan tres casos:

  1. Contador de R3 (sin Lock), tal cual.
  2. Contador de R3 (sin Lock) con la ventana de carrera AMPLIADA: entre leer
     y escribir el valor se cede el procesador con time.sleep(0). Asi se ve en
     segundos lo que en el servidor real pasa rara vez (y justo por eso es
     peligroso: las pruebas suelen pasar).
  3. ContadorSeguro de R4 (con Lock) con la misma ventana ampliada.

Ejecucion:  python3 demo_carrera.py
"""

import os
import sys
import threading
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "r3"))
sys.path.insert(0, AQUI)

from servidor_r3 import Contador        # noqa: E402
from servidor_r4 import ContadorSeguro  # noqa: E402

HILOS = 8
INCREMENTOS = 2000


class ContadorLento(Contador):
    """Contador de R3 con la ventana entre leer y escribir ampliada."""

    def incrementar(self):
        leido = self.valor          # 1) leer
        time.sleep(0)               # otro hilo puede ejecutarse aqui
        self.valor = leido + 1      # 2) escribir (puede pisar a otro hilo)
        return self.valor


class ContadorSeguroLento(ContadorSeguro):
    """ContadorSeguro de R4 con la misma ventana ampliada, dentro del Lock."""

    def incrementar(self):
        with self._lock:
            leido = self.valor
            time.sleep(0)
            self.valor = leido + 1
            return self.valor


def probar(nombre, contador):
    def trabajo():
        for _ in range(INCREMENTOS):
            contador.incrementar()

    hilos = [threading.Thread(target=trabajo) for _ in range(HILOS)]
    inicio = time.perf_counter()
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    esperado = HILOS * INCREMENTOS
    perdidos = esperado - contador.valor
    print(f"{nombre:<42} esperado={esperado}  obtenido={contador.valor}  "
          f"perdidos={perdidos}  ({time.perf_counter() - inicio:.2f} s)")


def main():
    print(f"{HILOS} hilos x {INCREMENTOS} incrementos sobre un mismo contador\n")
    probar("1. R3 sin Lock (valor += 1)", Contador())
    probar("2. R3 sin Lock, ventana ampliada", ContadorLento())
    probar("3. R4 con Lock, ventana ampliada", ContadorSeguroLento())


if __name__ == "__main__":
    main()
