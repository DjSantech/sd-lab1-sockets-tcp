# Guía de ejecución de los experimentos E1–E6

Guía práctica para ejecutar la Parte C en las dos VM. Para cada experimento indica los comandos exactos, qué capturar y qué anotar.
Las preguntas completas están en la guía oficial y en `informe/informe.md`.

## Convenciones

- **S1, S2**: terminales en VM-SERVIDOR (192.168.56.10). **C1, C2, C3**: terminales en VM-CLIENTE (192.168.56.11).
  Lo más cómodo es abrir varias ventanas de PowerShell en el anfitrión con `ssh <usuario>@192.168.56.10` o `.11`.
- Todo se ejecuta desde `~/lab1/codigo/base` (ver `red/DESPLIEGUE.md`).
- Guarde las capturas en `capturas/` con el nombre que se indica en cada caso (`E1_...png`).
- **ANTES de ejecutar cada experimento, escriba su predicción en el informe.** La guía califica justamente la diferencia entre lo que predijo y lo que ocurrió.
- Para registrar la hora exacta de un evento use `date +%T.%N | cut -c1-12`.

```bash
cd ~/lab1/codigo/base
```

---

## E1 — La conexión tiene cuatro identificadores

| Paso | Terminal | Comando |
|---|---|---|
| 1 | S1 | `python3 servidor_eco.py` |
| 2 | C1 | `python3 cliente_eco.py 192.168.56.10 5000` |
| 3 | C2 | `python3 cliente_eco.py 192.168.56.10 5000` |
| 4 | C3 | `python3 cliente_eco.py 192.168.56.10 5000` |
| 5 | S2 | `ss -tn state established '( sport = :5000 )'` |
| 6 | S2 | `ss -ltn '( sport = :5000 )'` (Recv-Q de la fila LISTEN = conexiones esperando en la cola de `accept()`) |
| 7 | C1 | `ss -tn '( dport = :5000 )'` (en otra terminal de VM-CLIENTE; muestra la vista del cliente) |
| 8 | C2, C3 | Escriba un mensaje en C2 y otro en C3 **antes** de cerrar C1. Anote si llega el eco. |
| 9 | C1 | Escriba `salir`. Anote qué pasa en C2 y en C3 y qué imprime S1. |

**Capturas:** `E1_tres_clientes.png` (C1–C3 y S1 visibles), `E1_ss_servidor.png` (pasos 5 y 6), `E1_ss_cliente.png` (paso 7).

**Anotar:**
- Las tres cuádruplas completas (IP local, puerto local, IP remota, puerto remoto).
- Cuántas filas muestra `ss` en el servidor y el Recv-Q de la fila LISTEN.
- Si C2 y C3 reciben un error al conectar o solo quedan esperando.
- En qué momento reciben su eco.

---

## E2 — El servidor maneja dos sockets distintos

| Paso | Terminal | Comando |
|---|---|---|
| 1 | S1 | `python3 servidor_eco.py` |
| 2 | C1 | `python3 cliente_eco.py 192.168.56.10 5000` |
| 3 | S2 | `ss -tan '( sport = :5000 )'` (la fila LISTEN y la fila ESTAB se ven a la vez) |

**Capturas:** `E2_salida_servidor.png` (las líneas "socket de escucha", "extremo local" y "extremo remoto" de S1) y `E2_ss.png`.

**Anotar:** las tres direcciones que imprime el servidor, y la dirección local del socket LISTEN comparada con la del socket ESTAB en `ss`.

---

## E3 — Qué significa que recv() devuelva cero

### E3.1 / E3.2: cierre ordenado

| Paso | Terminal | Comando |
|---|---|---|
| 1 | S1 | `python3 servidor_eco.py` |
| 2 | C1 | `python3 cliente_eco.py 192.168.56.10 5000`, envíe un mensaje y escriba `salir` |
| 3 | C1 | Repita la conexión y ahora ciérrela con **Ctrl+C** |

**Captura:** `E3_cierre_ordenado.png` (S1 mostrando `recv() devolvio 0 bytes`).
**Anotar:** lo que imprime S1 en cada tipo de cierre (`salir` y Ctrl+C) y si hay alguna diferencia.

### E3.3: sin la comprobación `if not datos: break`

Cree una copia sin esas 5 líneas. El original no se modifica, así que no hay que restaurar nada:

```bash
sed '/if not datos:/,/break/d' servidor_eco.py > servidor_e3.py
diff servidor_eco.py servidor_e3.py      # deben aparecer solo las 5 líneas eliminadas
```

| Paso | Terminal | Comando |
|---|---|---|
| 1 | S1 | `python3 servidor_e3.py` |
| 2 | S2 | `top -d 1` (déjelo abierto) |
| 3 | C1 | `python3 cliente_eco.py 192.168.56.10 5000`, envíe un mensaje y escriba `salir` |
| 4 | S1 | Observe unos 2–3 segundos y detenga con **Ctrl+C** |

> Advertencia: la salida en S1 puede ser muy rápida y muy larga. Detenga el servidor pronto.

**Capturas:** `E3_sin_break_salida.png` (S1) y `E3_sin_break_top.png` (el %CPU de python3 en `top`).
**Anotar:** qué se repite en pantalla, el %CPU que marca `top` y por qué no termina.

### E3.4: apagado brusco de VM-CLIENTE

| Paso | Dónde | Acción |
|---|---|---|
| 1 | S1 | `python3 servidor_eco.py` |
| 2 | C1 | Conecte `cliente_eco.py` y envíe un mensaje |
| 3 | VirtualBox | VM-CLIENTE → **Máquina → Cerrar → Apagar la máquina** (apagado sin cerrar el sistema) y anote la hora |
| 4 | S2 | `ss -tno '( sport = :5000 )'` justo después, y repítalo durante unos minutos |

**Captura:** `E3_apagado_brusco.png` (S1 y el `ss -tno` en S2).
**Anotar:** si S1 imprime algo, cuánto tiempo sigue la conexión en ESTAB y qué temporizador muestra `-o`.
Al terminar, encienda de nuevo VM-CLIENTE y detenga el servidor con Ctrl+C.

---

## E4 — TCP es un flujo de bytes (experimento central)

| Paso | Terminal | Comando |
|---|---|---|
| 1 | S1 | `python3 servidor_eco.py` |
| 2 | C1 | `python3 cliente_rafaga.py 192.168.56.10 5000 0` |
| 3 | C1 | `python3 cliente_rafaga.py 192.168.56.10 5000 0.5` |
| 4 | C1 | Cinco repeticiones con pausa 0 (E4.3): `for i in 1 2 3 4 5; do echo "== corrida $i"; python3 cliente_rafaga.py 192.168.56.10 5000 0; sleep 1; done` |

> **Si el servidor se cae con un traceback** (`ConnectionResetError`), no es un error suyo: es un hallazgo.
> En la prueba local del anfitrión (Windows, 127.0.0.1) pasó exactamente esto. El cliente leyó solo `b'UNO'`
> y cerró con `b'DOSTRES'` todavía sin leer. Al cerrar un socket con datos sin leer, el kernel envía un **RST**
> en lugar de un FIN, y `servidor_eco.py` no captura esa excepción.
> Si ocurre en las VM, anótelo, tome la captura, reinicie el servidor y continúe.
> Va a la sección de dificultades y sirve para E4.3.

**Opcional (recomendado, requiere sudo):** vea los segmentos reales en S2.
Esto confirma o descarta la explicación del RST.

```bash
sudo tcpdump -i enp0s8 -nn 'tcp port 5000'
```

**Capturas:** `E4_pausa0_cliente.png`, `E4_pausa0_servidor.png`, `E4_pausa05_cliente.png`, `E4_pausa05_servidor.png` y `E4_cinco_corridas.png`.

**Anotar**, para cada corrida:
- Cuántas líneas `recibidos` muestra el servidor y con qué bytes.
- Qué devolvió el único `recv()` del cliente.

Con eso se llena esta tabla:

| Corrida | Pausa | recv() en el servidor (bytes de cada uno) | recv() del cliente |
|---|---|---|---|
| 1 | 0 | | |
| 2 | 0.5 | | |
| 3–7 | 0 | | |

**Contraste con R2** (para la sección de R2 del informe): repita el paso 2 con el servidor y el cliente del reto.

```bash
# S1
cd ~/lab1/codigo/r2 && python3 servidor_r2.py
# C1
cd ~/lab1/codigo/r2 && python3 cliente_rafaga_r2.py 192.168.56.10 5000 0
```

---

## E5 — TIME_WAIT y SO_REUSEADDR

Cree una copia con la línea de `SO_REUSEADDR` comentada:

```bash
sed 's/^\( *\)servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)/\1# servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)/' servidor_eco.py > servidor_e5.py
diff servidor_eco.py servidor_e5.py      # debe cambiar solo esa línea
```

| Paso | Terminal | Comando |
|---|---|---|
| 1 | S1 | `python3 servidor_e5.py` |
| 2 | C1 | `python3 cliente_eco.py 192.168.56.10 5000` y envíe un mensaje |
| 3 | S1 | **Ctrl+C** en el servidor. Es el servidor el que cierra primero. |
| 4 | C1 | Cierre el cliente con **Ctrl+C**, sin escribir texto. Si envía datos a un socket que el servidor ya cerró, el servidor responde con RST y la conexión no pasa por TIME_WAIT. |
| 5 | S2 | `date +%T; ss -tano state time-wait` (el temporizador `timewait,XXsec` indica cuánto falta) |
| 6 | S1 | Enseguida: `python3 servidor_e5.py` |
| 7 | S1 | Si falla, mida cuánto tarda en liberarse el puerto: `date +%T; until python3 -c 'import socket; s=socket.socket(); s.bind(("0.0.0.0",5000))' 2>/dev/null; do sleep 1; done; date +%T` |
| 8 | S1 | Repita los pasos 1–6 con `servidor_eco.py` (con SO_REUSEADDR) para comparar |

**Capturas:** `E5_bind_error.png` (la excepción completa), `E5_time_wait.png` (el `ss`) y `E5_con_reuseaddr.png` (el paso 8).
**Anotar:** el nombre exacto de la excepción y el errno, las dos horas del paso 7 (su diferencia es el tiempo de espera) y el temporizador de `ss`.

---

## E6 — Diagnóstico por capas: fallos provocados

Mida el tiempo de cada fallo con `time`. Distinguir "falla al instante" de "falla tras esperar" es la mitad del diagnóstico.

| # | Fallo | Preparación en VM-SERVIDOR | Comando en VM-CLIENTE | Verificación en VM-SERVIDOR |
|---|---|---|---|---|
| F1 | Servidor no está ejecutándose | Detener el servidor (Ctrl+C) | `time python3 cliente_eco.py 192.168.56.10 5000` | `ss -ltnp` (nadie en :5000) |
| F2 | Puerto equivocado | `python3 servidor_eco.py` | `time python3 cliente_eco.py 192.168.56.10 5001` | `ss -ltnp` (escucha en :5000, no en :5001) |
| F3 | IP inexistente en la subred | (no aplica) | `time python3 cliente_eco.py 192.168.56.99 5000` | En C2 mientras espera: `ip neigh show 192.168.56.99` |
| F4 | Servidor solo en localhost | `sed 's/^HOST = "0.0.0.0"/HOST = "127.0.0.1"/' servidor_eco.py > servidor_f4.py` y `python3 servidor_f4.py` | `time python3 cliente_eco.py 192.168.56.10 5000` | `ss -ltnp` (dirección local 127.0.0.1:5000) y `nc -vz 127.0.0.1 5000` desde la propia VM-SERVIDOR |
| F5 | Cortafuegos | `python3 servidor_eco.py` y en S2 `sudo ufw enable` (**ver la advertencia**) | `time python3 cliente_eco.py 192.168.56.10 5000` | `sudo ufw status verbose` y `ss -ltnp` |

> **Advertencia F5:** `ufw enable` con la política por defecto bloquea **todo** lo entrante, incluido SSH (22).
> Si trabaja por SSH, ejecute primero `sudo ufw allow 22/tcp` o haga F5 desde la consola de VirtualBox.
> Al terminar: `sudo ufw disable`.

> **F3:** anote el error y el tiempo **exactos** que obtenga, aunque no coincidan con la pista de la guía
> ("se agota un temporizador"). Si difieren, explíquelo en el informe. Pista: una IP de la misma subred se busca
> primero con ARP; revise lo que muestra `ip neigh` mientras el cliente espera.

**Opcional (sudo):** con `sudo tcpdump -i enp0s8 -nn 'tcp port 5000 or arp'` en VM-SERVIDOR, o en VM-CLIENTE para F3, se ve qué segmento responde en cada caso: RST, nada, o ARP sin respuesta.

**Capturas:** `E6_F1.png` … `E6_F5.png`. Cada una con el error del cliente y la verificación del servidor.

**Anotar**, completando la tabla de E6.1:

| # | Error exacto (tipo y mensaje) | Tiempo hasta el error | ¿Qué respondió el destino? | Capa |
|---|---|---|---|---|
| F1 | | | | |
| F2 | | | | |
| F3 | | | | |
| F4 | | | | |
| F5 | | | | |

---

## Parte A y R1/R2 en las VM (evidencias complementarias)

- **Parte A:** `A_ip_servidor.png`, `A_ip_cliente.png` (`ip -br addr`), `A_ping.png`, `A_nc_refused.png`, `A_ss_ltnp.png`, `A_nc_ok.png` y `A_eco_lado_a_lado.png`.
- **R1:** en S1 `cd ~/lab1/codigo/r1 && python3 servidor_r1.py`. Desde C1, conecte dos clientes seguidos (`cliente_eco.py` y `cliente_rafaga.py ... 0`). Detenga el servidor y ejecute `cat bitacora.log`. Captura: `R1_bitacora.png`.
- **R2:** `cd ~/lab1 && python3 -m unittest -v pruebas.test_r2` en VM-SERVIDOR (captura `R2_tests.png`) y el contraste con `cliente_rafaga_r2.py` descrito en E4 (captura `R2_rafaga.png`).

## Retos adicionales en las VM

| Reto | VM-SERVIDOR | VM-CLIENTE | Captura / dato |
|---|---|---|---|
| R3 | `cd ~/lab1/codigo/r3 && python3 servidor_r3.py` | `cd ~/lab1/codigo/r2 && python3 cliente_r2.py 192.168.56.10 5000` y probar `HORA`, `ECO hola`, `ESTADISTICAS`, `XYZ`, `ADIOS` | `R3_comandos.png` |
| R4 | `cd ~/lab1/codigo/r4 && python3 servidor_r4.py` | En C1, C2 y C3, `python3 ~/lab1/codigo/r2/cliente_r2.py 192.168.56.10 5000`. Deje C1 sin escribir y compruebe que C2 y C3 responden. Repita con `servidor_r3.py` para comparar. | `R4_tres_clientes.png` y `R4_vs_R3.png` |
| R4 (Lock) | `cd ~/lab1/codigo/r4 && python3 demo_carrera.py` | (no aplica) | `R4_demo_carrera.png` |
| R5 | `cd ~/lab1/codigo/r2 && python3 servidor_r2.py` | `cd ~/lab1/codigo/r5 && python3 cliente_rtt.py 192.168.56.10 5000` | `R5_rtt.png`: la tabla mín/máx/media |
