#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_r2.py
Autor: Santiago Guevara Méndez - Sistemas Distribuidos, UTP (2026-2)
Pruebas del reto R2 (mensajes delimitados por \\n).

Levanta servidor_r2 en un hilo, en 127.0.0.1 y en un puerto efimero (bind al
puerto 0), y prueba las formas en que TCP puede partir o juntar los mensajes.
Cada prueba abre su propia conexion; el hilo del servidor deja en una cola el
resumen que devuelve atender_conexion() para poder revisar tambien que vio el
servidor.

Ejecucion (desde la carpeta SD_Lab1):
    python3 -m unittest -v pruebas.test_r2
    python3 pruebas/test_r2.py -v
"""

import io
import os
import queue
import socket
import sys
import threading
import time
import unittest

# Permite importar servidor_r2 y cliente_r2 desde codigo/r2.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "codigo", "r2"))

import servidor_r2                    # noqa: E402
from cliente_r2 import LectorLineas   # noqa: E402

LIMITE_PRUEBA = 32      # limite pequeno para poder probar el desbordamiento
TIMEOUT = 5             # ninguna prueba debe quedarse colgada


def bucle_servidor(servidor, resultados):
    """Acepta conexiones una por una y guarda el resumen de cada una."""
    while True:
        try:
            conexion, direccion = servidor.accept()
        except OSError:        # el socket de escucha se cerro: fin del hilo
            return
        with conexion:
            resultados.put(servidor_r2.atender_conexion(
                conexion, direccion, LIMITE_PRUEBA))


class PruebasR2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Los print() del servidor se guardan aparte para no ensuciar la
        # salida de unittest (que va por stderr).
        cls.stdout_original = sys.stdout
        sys.stdout = cls.salida_servidor = io.StringIO()

        cls.servidor = servidor_r2.crear_servidor("127.0.0.1", 0)
        cls.puerto = cls.servidor.getsockname()[1]
        cls.resultados = queue.Queue()
        cls.hilo = threading.Thread(target=bucle_servidor,
                                    args=(cls.servidor, cls.resultados),
                                    daemon=True)
        cls.hilo.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.close()
        cls.hilo.join(TIMEOUT)
        sys.stdout = cls.stdout_original

    # ---------------------------------------------------------- utilidades
    def conectar(self):
        cliente = socket.create_connection(("127.0.0.1", self.puerto),
                                           timeout=TIMEOUT)
        # Sin Nagle: cada sendall() pequeno sale en su propio segmento, asi
        # las pruebas de envios partidos de verdad llegan partidos.
        cliente.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return cliente

    def cerrar_y_resumen(self, cliente):
        """Cierra el cliente y devuelve lo que reporto el servidor."""
        cliente.close()
        return self.resultados.get(timeout=TIMEOUT)

    # -------------------------------------------------------------- pruebas
    def test_1_tres_mensajes_en_un_solo_sendall(self):
        cliente = self.conectar()
        cliente.sendall(b"uno\ndos\ntres\n")
        lector = LectorLineas(cliente)
        respuestas = [lector.leer_linea() for _ in range(3)]
        resumen = self.cerrar_y_resumen(cliente)

        self.assertEqual(respuestas, [b"UNO", b"DOS", b"TRES"])
        self.assertEqual(resumen["mensajes"], ["uno", "dos", "tres"])
        self.assertEqual(resumen["residuo"], b"")

    def test_2_mensaje_enviado_byte_por_byte(self):
        cliente = self.conectar()
        for byte in b"hola mundo\n":
            cliente.sendall(bytes([byte]))
            time.sleep(0.01)
        respuesta = LectorLineas(cliente).leer_linea()
        resumen = self.cerrar_y_resumen(cliente)

        self.assertEqual(respuesta, b"HOLA MUNDO")
        self.assertEqual(resumen["mensajes"], ["hola mundo"])
        # Comprueba que el mensaje de verdad llego en varios recv().
        self.assertGreater(resumen["llamadas_recv"], 1)

    def test_3_mensaje_dividido_en_dos_envios(self):
        cliente = self.conectar()
        cliente.sendall(b"mensaje divi")
        time.sleep(0.2)
        cliente.sendall(b"dido\n")
        respuesta = LectorLineas(cliente).leer_linea()
        resumen = self.cerrar_y_resumen(cliente)

        self.assertEqual(respuesta, b"MENSAJE DIVIDIDO")
        self.assertEqual(resumen["mensajes"], ["mensaje dividido"])
        self.assertGreaterEqual(resumen["llamadas_recv"], 2)

    def test_4_caracter_multibyte_partido(self):
        datos = "año ñandú\n".encode("utf-8")
        # Corte justo despues del primer byte de la "ñ" (0xC3 0xB1).
        corte = datos.index("ñ".encode("utf-8")) + 1
        parte1, parte2 = datos[:corte], datos[corte:]
        # Decodificar la primera parte sola fallaria: por eso el servidor
        # solo decodifica mensajes completos.
        with self.assertRaises(UnicodeDecodeError):
            parte1.decode("utf-8")

        cliente = self.conectar()
        cliente.sendall(parte1)
        time.sleep(0.2)
        cliente.sendall(parte2)
        respuesta = LectorLineas(cliente).leer_linea()
        resumen = self.cerrar_y_resumen(cliente)

        self.assertEqual(respuesta.decode("utf-8"), "AÑO ÑANDÚ")
        self.assertEqual(resumen["mensajes"], ["año ñandú"])
        self.assertGreaterEqual(resumen["llamadas_recv"], 2)

    def test_5_mensaje_vacio(self):
        cliente = self.conectar()
        lector = LectorLineas(cliente)
        cliente.sendall(b"\n")
        vacia = lector.leer_linea()
        # Despues del mensaje vacio la conexion sigue funcionando.
        cliente.sendall(b"sigue\n")
        siguiente = lector.leer_linea()
        resumen = self.cerrar_y_resumen(cliente)

        self.assertEqual(vacia, b"")
        self.assertEqual(siguiente, b"SIGUE")
        self.assertEqual(resumen["mensajes"], ["", "sigue"])

    def test_6_desbordamiento_del_limite(self):
        cliente = self.conectar()
        cliente.sendall(b"x" * (LIMITE_PRUEBA * 3))    # sin \n
        lector = LectorLineas(cliente)
        error = lector.leer_linea()
        # Despues del error el servidor cierra: recv() devuelve b"".
        fin = lector.leer_linea()
        resumen = self.cerrar_y_resumen(cliente)

        self.assertTrue(error.startswith(b"ERROR"), error)
        self.assertIsNone(fin)
        self.assertEqual(resumen["motivo"], "limite superado")
        self.assertEqual(resumen["mensajes"], [])

    def test_7_residuo_sin_salto_de_linea_al_cerrar(self):
        cliente = self.conectar()
        cliente.sendall(b"completo\nincomple")
        respuesta = LectorLineas(cliente).leer_linea()
        # shutdown(SHUT_WR): el cliente envia FIN sin cerrar la lectura.
        cliente.shutdown(socket.SHUT_WR)
        resumen = self.cerrar_y_resumen(cliente)

        self.assertEqual(respuesta, b"COMPLETO")
        self.assertEqual(resumen["mensajes"], ["completo"])
        self.assertEqual(resumen["residuo"], b"incomple")
        self.assertIn("mensaje incompleto descartado",
                      self.salida_servidor.getvalue())


if __name__ == "__main__":
    unittest.main()
