# Despliegue de la red y del código en las dos VM

Montaje según la guía (Parte A):

| Máquina | Interfaz NAT | Interfaz del laboratorio | IP fija |
|---|---|---|---|
| VM-SERVIDOR | enp0s3 (DHCP) | enp0s8 (Host-only) | 192.168.56.10/24 |
| VM-CLIENTE | enp0s3 (DHCP) | enp0s8 (Host-only) | 192.168.56.11/24 |

Puerto de la aplicación: **5000/TCP**. En los comandos, `<usuario>` es el usuario que creó al instalar Ubuntu Server.

> **Anfitrión Windows:** en VirtualBox para Windows la red `vboxnet0` aparece como
> *"VirtualBox Host-Only Ethernet Adapter"*. El anfitrión tiene la IP 192.168.56.1 en esa red.
> Los comandos `scp` y `ssh` de abajo se ejecutan en **PowerShell**, dentro de la carpeta `SD_Lab1`
> (Windows 10/11 ya trae el cliente OpenSSH).

---

## 0. Antes de empezar (VirtualBox, con las VM apagadas)

En cada VM, en **Configuración → Red**:

- Adaptador 1: **NAT**.
- Adaptador 2: **Adaptador solo-anfitrión**, red `vboxnet0` / "VirtualBox Host-Only Ethernet Adapter".

En VM-CLIENTE, que es un clon, cambie el nombre de host:

```bash
sudo hostnamectl set-hostname vm-cliente
```

## 1. Llevar el archivo netplan a cada VM

Todavía no hay IP fija, así que hay dos caminos.

### Opción A: scp usando una IP temporal (si enp0s8 recibió una por DHCP)

En la **consola de VirtualBox** de cada VM:

```bash
ip -br addr show enp0s8
```

Si aparece una dirección del tipo `192.168.56.1xx/24`, úsela como `<IP_TEMPORAL>` desde PowerShell en el anfitrión:

```powershell
scp red\99-laboratorio-servidor.yaml <usuario>@<IP_TEMPORAL_SERVIDOR>:~/
scp red\99-laboratorio-cliente.yaml  <usuario>@<IP_TEMPORAL_CLIENTE>:~/
```

> Si las dos VM clonadas recibieron **la misma** IP temporal, se debe a que el clon comparte el
> `/etc/machine-id` y el servidor DHCP las ve como el mismo cliente. En ese caso use la opción B.

### Opción B: crear el archivo directamente en la consola de la VM

En VM-SERVIDOR:

```bash
sudo tee /etc/netplan/99-laboratorio.yaml > /dev/null <<'EOF'
network:
  version: 2
  ethernets:
    enp0s3:
      dhcp4: true
    enp0s8:
      dhcp4: false
      addresses:
        - 192.168.56.10/24
EOF
```

En VM-CLIENTE use el mismo comando, cambiando la última línea de datos por `- 192.168.56.11/24`.

## 2. Instalar y aplicar netplan (en cada VM)

Si usó la opción A, mueva primero el archivo a su sitio.

En VM-SERVIDOR:

```bash
sudo mv ~/99-laboratorio-servidor.yaml /etc/netplan/99-laboratorio.yaml
```

En VM-CLIENTE:

```bash
sudo mv ~/99-laboratorio-cliente.yaml /etc/netplan/99-laboratorio.yaml
```

Luego, en las dos VM (opción A o B):

```bash
sudo chown root:root /etc/netplan/99-laboratorio.yaml
sudo chmod 600 /etc/netplan/99-laboratorio.yaml   # evita la advertencia de permisos de netplan
ls -l /etc/netplan/                               # revisar que no haya otro archivo que configure enp0s8
sudo netplan apply
ip -br addr show enp0s8
```

> Si estaba conectado por SSH a la IP temporal, esa sesión se corta al aplicar netplan, porque enp0s8
> deja de usar DHCP. Es normal: reconéctese a la IP fija.

## 3. Copiar el código (desde PowerShell en el anfitrión)

```powershell
ssh <usuario>@192.168.56.10 "mkdir -p ~/lab1"
scp -r codigo pruebas <usuario>@192.168.56.10:~/lab1/

ssh <usuario>@192.168.56.11 "mkdir -p ~/lab1"
scp -r codigo <usuario>@192.168.56.11:~/lab1/
```

Así quedan `~/lab1/codigo/base`, `~/lab1/codigo/r1`, `~/lab1/codigo/r2`, etc. en cada VM.
`cliente_rafaga_r2.py` importa `cliente_r2.py`, por eso se copia la carpeta completa.

## 4. Verificación por capas (Parte A.4)

El orden va de abajo hacia arriba: enlace/red → red → transporte.

| Paso | Capa | Dónde | Comando | Resultado esperado según la guía |
|---|---|---|---|---|
| 1 | Enlace / Red | las dos VM | `ip -br addr` | enp0s8 `UP` con su IP /24 |
| 2 | Red | VM-CLIENTE | `ping -c 4 192.168.56.10` | 4 respuestas, 0 % de pérdida |
| 3 | Transporte | VM-CLIENTE | `nc -vz 192.168.56.10 5000` | `Connection refused` (sin servidor) |
| 4 | Transporte | VM-SERVIDOR | `cd ~/lab1/codigo/base && python3 servidor_eco.py` | queda escuchando |
| 5 | Transporte | VM-SERVIDOR (otra terminal) | `ss -ltnp` | una línea `LISTEN 0.0.0.0:5000` con `python3` |
| 6 | Transporte | VM-CLIENTE | `nc -vz 192.168.56.10 5000` | `Connection ... succeeded` |
| 7 | Aplicación | VM-CLIENTE | `cd ~/lab1/codigo/base && python3 cliente_eco.py 192.168.56.10 5000` | eco en mayúsculas |

Si el ping falla, revise que los dos adaptadores estén en la misma red Host-only y que las IP estén en la misma /24.
Si el ping funciona pero la conexión no, revise el cortafuegos:

```bash
sudo ufw status
sudo ufw allow 5000/tcp    # solo si ufw está activo
```

Guarde capturas o salidas de los pasos 1, 2, 5 y 7 en `capturas/`, porque son evidencia de la Parte A.
