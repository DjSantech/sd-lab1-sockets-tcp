import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from xmlrpc.client import Binary, ServerProxy

# Uso: python cliente_rpc.py <nombre_de_usuario> [IP_DEL_SERVIDOR] [PUERTO]
# Si el servidor está en otra máquina, pasar su IP (ver con ipconfig en esa máquina).
if len(sys.argv) < 2:
    print("Uso: python cliente_rpc.py <nombre_de_usuario> [IP_DEL_SERVIDOR] [PUERTO]")
    sys.exit(1)

NOMBRE = sys.argv[1]
HOST = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'
PUERTO = sys.argv[3] if len(sys.argv) > 3 else '8000'
URL = f"http://{HOST}:{PUERTO}/RPC2"

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_HISTORIAL = os.path.join(BASE, 'datos', NOMBRE, 'historial')   # conversaciones guardadas
CARPETA_RECIBIDOS = os.path.join(BASE, 'datos', NOMBRE, 'recibidos')   # archivos que me llegan
os.makedirs(CARPETA_HISTORIAL, exist_ok=True)
os.makedirs(CARPETA_RECIBIDOS, exist_ok=True)

TIPOS_ARCHIVO = [("Imágenes, textos y sonidos", "*.png *.jpg *.jpeg *.gif *.txt *.wav *.mp3"),
                 ("Todos los archivos", "*.*")]

proxy = ServerProxy(URL, allow_none=True)  # proxy del hilo principal (enviar mensajes/archivos)
cola_eventos = queue.Queue()               # el hilo de sondeo deja aquí lo que llega del servidor


# ---------------- Persistencia de las conversaciones ----------------

def ruta_historial(otro):
    return os.path.join(CARPETA_HISTORIAL, f"{otro}.json")


def cargar_historial(otro):
    try:
        with open(ruta_historial(otro), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def guardar_entrada(otro, entrada):
    historial = cargar_historial(otro)
    historial.append(entrada)
    with open(ruta_historial(otro), 'w', encoding='utf-8') as f:
        json.dump(historial, f, ensure_ascii=False, indent=1)


def borrar_historial(otro):
    try:
        os.remove(ruta_historial(otro))
    except OSError:
        pass


# ---------------- Hilo que pregunta al servidor por novedades ----------------

def sondear():
    """Hilo secundario. XML-RPC es petición/respuesta, así que el cliente pregunta cada segundo."""
    mi_proxy = ServerProxy(URL, allow_none=True)  # ServerProxy no es seguro entre hilos: uno propio
    while True:
        try:
            for item in mi_proxy.recibir_pendientes(NOMBRE):
                cola_eventos.put(('nuevo', item))
            cola_eventos.put(('directorio', mi_proxy.listar_usuarios(NOMBRE)))
        except OSError:
            cola_eventos.put(('error', None))
        time.sleep(1)


# ---------------- Ventana de conversación (solo entre 2 personas) ----------------

class VentanaChat:
    def __init__(self, app, otro):
        self.app, self.otro = app, otro
        self.win = tk.Toplevel(app.root)
        self.win.title(f"{NOMBRE}  ↔  {otro}")
        self.win.geometry("440x480")
        self.win.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.texto = tk.Text(self.win, state='disabled', wrap='word', bg='#f4f4f4')
        self.texto.pack(fill='both', expand=True, padx=6, pady=6)
        self.texto.tag_config('yo', foreground='#0b5394', justify='right')
        self.texto.tag_config('otro', foreground='#38761d')
        self.texto.tag_config('archivo', underline=True)

        barra = tk.Frame(self.win)
        barra.pack(fill='x', padx=6, pady=(0, 6))
        self.entrada = tk.Entry(barra)
        self.entrada.pack(side='left', fill='x', expand=True)
        self.entrada.bind('<Return>', lambda e: self.enviar())
        self.entrada.focus_set()
        tk.Button(barra, text="Enviar", command=self.enviar).pack(side='left', padx=2)
        tk.Button(barra, text="📎 Archivo", command=self.enviar_archivo).pack(side='left', padx=2)
        tk.Button(barra, text="🗑 Borrar", command=self.borrar).pack(side='left', padx=2)

        for entrada in cargar_historial(otro):  # recupera la conversación guardada
            self.pintar(entrada)

    def pintar(self, e):
        self.texto.config(state='normal')
        etiqueta = 'yo' if e['de'] == NOMBRE else 'otro'
        quien = 'Yo' if e['de'] == NOMBRE else e['de']
        if e['tipo'] == 'texto':
            self.texto.insert('end', f"[{e['hora']}] {quien}: {e['texto']}\n", etiqueta)
        else:
            inicio = self.texto.index('end-1c')
            self.texto.insert('end', f"[{e['hora']}] {quien}: 📎 {e['nombre']} (clic para abrir)\n",
                              (etiqueta,))
            fin = self.texto.index('end-1c')
            marca = f"arch{inicio}".replace('.', '_')
            self.texto.tag_add(marca, inicio, fin)
            self.texto.tag_config(marca, underline=True)
            self.texto.tag_bind(marca, '<Button-1>', lambda ev, r=e['ruta']: self.abrir(r))
        self.texto.config(state='disabled')
        self.texto.see('end')

    def abrir(self, ruta):
        if os.path.exists(ruta):
            os.startfile(ruta)
        else:
            messagebox.showwarning("Archivo", "El archivo ya no existe en el disco.", parent=self.win)

    def enviar(self):
        texto = self.entrada.get().strip()
        if not texto:
            return
        try:
            proxy.enviar_mensaje(NOMBRE, self.otro, texto)   # <- llamada RPC
        except OSError:
            messagebox.showerror("Error", "No se pudo contactar al servidor.", parent=self.win)
            return
        entrada = {'tipo': 'texto', 'de': NOMBRE, 'texto': texto, 'hora': time.strftime('%H:%M')}
        guardar_entrada(self.otro, entrada)
        self.pintar(entrada)
        self.entrada.delete(0, 'end')

    def enviar_archivo(self):
        ruta = filedialog.askopenfilename(parent=self.win, filetypes=TIPOS_ARCHIVO)
        if not ruta:
            return
        with open(ruta, 'rb') as f:
            datos = f.read()
        nombre = os.path.basename(ruta)
        try:
            proxy.enviar_archivo(NOMBRE, self.otro, nombre, Binary(datos))  # <- llamada RPC
        except OSError:
            messagebox.showerror("Error", "No se pudo contactar al servidor.", parent=self.win)
            return
        entrada = {'tipo': 'archivo', 'de': NOMBRE, 'nombre': nombre, 'ruta': ruta,
                   'hora': time.strftime('%H:%M')}
        guardar_entrada(self.otro, entrada)
        self.pintar(entrada)

    def borrar(self):
        if messagebox.askyesno("Borrar", f"¿Borrar toda la conversación con {self.otro}?",
                               parent=self.win):
            borrar_historial(self.otro)
            self.texto.config(state='normal')
            self.texto.delete('1.0', 'end')
            self.texto.config(state='disabled')

    def cerrar(self):
        # Cerrar la ventana NO borra nada: la conversación sigue guardada en disco.
        self.app.ventanas.pop(self.otro, None)
        self.win.destroy()


# ---------------- Ventana principal: directorio de usuarios ----------------

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Mensajero RPC — {NOMBRE}")
        self.root.geometry("280x380")
        self.root.protocol("WM_DELETE_WINDOW", self.salir)
        self.ventanas = {}     # otro -> VentanaChat abierta
        self.usuarios = []     # nombres en el orden mostrado
        self.sin_leer = {}     # otro -> cantidad de mensajes nuevos con la ventana cerrada

        tk.Label(self.root, text=f"Conectado como {NOMBRE}", font=('Segoe UI', 11, 'bold')).pack(pady=6)
        tk.Label(self.root, text="Doble clic en un usuario para hablarle").pack()
        self.lista = tk.Listbox(self.root, font=('Segoe UI', 11))
        self.lista.pack(fill='both', expand=True, padx=8, pady=8)
        self.lista.bind('<Double-Button-1>', self.abrir_chat)
        self.estado = tk.Label(self.root, text="", fg='gray')
        self.estado.pack()

        try:
            proxy.registrar(NOMBRE)  # <- llamada RPC
        except OSError:
            messagebox.showerror("Error", f"No se pudo conectar a {URL}")
            sys.exit(1)
        threading.Thread(target=sondear, daemon=True).start()
        self.root.after(300, self.procesar_eventos)

    def abrir_chat(self, _=None):
        seleccion = self.lista.curselection()
        if not seleccion:
            return
        otro = self.usuarios[seleccion[0]]
        if otro == NOMBRE:
            return
        self.sin_leer.pop(otro, None)
        if otro in self.ventanas:
            self.ventanas[otro].win.lift()
        else:
            self.ventanas[otro] = VentanaChat(self, otro)

    def procesar_eventos(self):
        try:
            while True:
                tipo, dato = cola_eventos.get_nowait()
                if tipo == 'directorio':
                    self.estado.config(text="")
                    self.pintar_directorio(dato)
                elif tipo == 'error':
                    self.estado.config(text="Sin conexión con el servidor…", fg='red')
                elif tipo == 'nuevo':
                    self.recibir(dato)
        except queue.Empty:
            pass
        self.root.after(300, self.procesar_eventos)

    def pintar_directorio(self, directorio):
        self.usuarios = [u for u, _ in directorio]
        self.lista.delete(0, 'end')
        for i, (usuario, conectado) in enumerate(directorio):
            marca = '🟢' if conectado else '⚪'
            extra = f"  ({self.sin_leer[usuario]} nuevos)" if self.sin_leer.get(usuario) else ''
            yo = '  (tú)' if usuario == NOMBRE else ''
            self.lista.insert('end', f"{marca} {usuario}{yo}{extra}")
            self.lista.itemconfig(i, fg='black' if conectado else 'gray')

    def recibir(self, item):
        otro = item['de']
        entrada = {'tipo': item['tipo'], 'de': otro, 'hora': item['hora']}
        if item['tipo'] == 'texto':
            entrada['texto'] = item['texto']
        else:
            ruta = os.path.join(CARPETA_RECIBIDOS, f"{otro}_{int(time.time())}_{item['nombre']}")
            with open(ruta, 'wb') as f:
                f.write(item['contenido'].data)
            entrada.update(nombre=item['nombre'], ruta=ruta)
        guardar_entrada(otro, entrada)  # se guarda aunque la ventana esté cerrada
        if otro in self.ventanas:
            self.ventanas[otro].pintar(entrada)
        else:
            self.sin_leer[otro] = self.sin_leer.get(otro, 0) + 1

    def salir(self):
        try:
            proxy.desconectar(NOMBRE)  # <- llamada RPC
        except OSError:
            pass
        self.root.destroy()


if __name__ == "__main__":
    App().root.mainloop()
