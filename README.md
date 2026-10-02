# Laboratorio 1: comunicación entre procesos con sockets TCP

Sistemas Distribuidos, Universidad Tecnológica de Pereira (2026-2).
Autor: Santiago Guevara Méndez.

Implementé y observé una comunicación cliente/servidor sobre TCP en Python, entre dos máquinas virtuales
(VirtualBox, Ubuntu 26.04.1 LTS, Python 3.14.4) conectadas por una red Host-only. El objetivo fue comprobar
experimentalmente qué garantiza TCP y qué no: fiabilidad y orden sí, fronteras de mensaje y detección
inmediata de fallos no.

**El informe completo está en [`informe/informe.pdf`](informe/informe.pdf)** (versión en Markdown:
[`informe/informe.md`](informe/informe.md)).

## Montaje

| Máquina | Rol | IP (Host-only) |
|---|---|---|
| VM-SERVIDOR | servidor, puerto 5000/TCP | 192.168.56.10/24 |
| VM-CLIENTE | cliente | 192.168.56.11/24 |

El paso a paso del montaje y de la copia del código a las VM está en [`red/DESPLIEGUE.md`](red/DESPLIEGUE.md).

## Estructura

| Carpeta | Contenido |
|---|---|
| `codigo/base/` | Servidor de eco, cliente de eco y cliente de ráfaga (los programas de los experimentos) |
| `codigo/r1/` a `codigo/r5/` | Retos: R1 bitácora de conexiones, R2 mensajes delimitados por `\n`, R3 servidor con comandos, R4 un hilo por cliente con `Lock`, R5 medición de RTT |
| `codigo/corregido/` | Versión corregida de los programas `serverp.py` y `clientep.py` |
| `experimentos/` | Guía para ejecutar los experimentos E1 a E6 en las VM |
| `pruebas/` | Pruebas unitarias del reto R2 |
| `red/` | Configuración de red (netplan) y despliegue |
| `capturas/` | Evidencias de la ejecución, organizadas por etapa (Parte A, E1 a E6, R1 a R5) |
| `informe/` | Informe en PDF y en Markdown |

## Cómo ejecutar lo básico

En VM-SERVIDOR:

```bash
cd ~/lab1/codigo/base
python3 servidor_eco.py
```

En VM-CLIENTE:

```bash
cd ~/lab1/codigo/base
python3 cliente_eco.py 192.168.56.10 5000
```

Las pruebas del reto R2, desde `~/lab1` en VM-SERVIDOR:

```bash
python3 -m unittest -v pruebas.test_r2
```

## Qué no incluye

La carpeta `referencia/` (la guía y el material del curso) no se sube, porque no es mío.
