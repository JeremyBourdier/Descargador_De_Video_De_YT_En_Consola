#!/usr/bin/env python3
# coding: utf-8

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import time
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
from pathlib import Path
from typing import Dict, List

C = {
    "title": "black",
    "option": "yellow",
    "input": "green",
    "error": "red",
    "ok": "green",
    "bg": "#f0f0f0",
    "fg": "black"
}

def crear_carpetas() -> None:
    for carpeta in ("videos", "sounds", "ambos"):
        Path(carpeta).mkdir(exist_ok=True)

# --- Funciones para tocar la GUI (seguro desde hilos con root.after) ---

def _update_gui_status(text):
    status_text.set(text)
    progress_bar['value'] = 0
    progress_bar.stop()

def _update_gui_progress(percent, text):
    status_text.set(text)
    progress_bar['value'] = percent
    if progress_bar.cget('mode') == 'indeterminate':
       progress_bar.stop()
    progress_bar['mode'] = 'determinate'

def _update_gui_indeterminate(text):
    status_text.set(text)
    progress_bar['value'] = 0
    progress_bar['mode'] = 'indeterminate'
    progress_bar.start(10)

def _reset_gui_after_delay(delay_ms=1500):
    """ Limpia la GUI después de un tiempecito """
    def reset():
        status_text.set("Listo.")
        progress_bar['value'] = 0
        progress_bar.stop()
        progress_bar['mode'] = 'determinate'
        # Reactivar botones y campos
        descargar_button.config(state=tk.NORMAL)
        url_entry.config(state=tk.NORMAL)
        modo_combo.config(state="readonly")
        if playlist_options_frame.winfo_ismapped():
             playlist_modo_combo.config(state="readonly")
             num_hilos_spinbox.config(state=tk.NORMAL)

    # Programar el reseteo en el hilo principal
    root.after(delay_ms, reset)


# --- Hook que llama yt-dlp ---

def update_status(d):
    """ yt-dlp llama a esto para contarnos cómo va la vaina """
    status = d.get('status')
    filename = Path(d.get('filename', 'archivo')).name

    if status == 'downloading':
        total_bytes = d.get('total_bytes')
        total_bytes_estimate = d.get('total_bytes_estimate')
        downloaded_bytes = d.get('downloaded_bytes')

        total = total_bytes or total_bytes_estimate # total_bytes es más fiable

        if total and downloaded_bytes is not None:
            percent = (downloaded_bytes / total) * 100
            # Ojo: Actualizar GUI siempre desde el hilo principal!
            root.after(0, lambda p=percent, f=filename: _update_gui_progress(p, f"Bajando {f}: {p:.1f}%"))
        else:
             # Si no sabemos el tamaño, ponemos la barra loca
             root.after(0, lambda f=filename: _update_gui_indeterminate(f"Bajando {f}..."))

    elif status == 'finished':
        root.after(0, lambda f=filename: _update_gui_progress(100, f"¡Listo!: {f}"))
        # Dejar que el usuario vea el "Listo!" antes de limpiar
        _reset_gui_after_delay(2000)

    elif status == 'error':
        root.after(0, lambda f=filename: _update_gui_status(f"Error bajando {f}"))
         # Más tiempo para leer el error
        _reset_gui_after_delay(3000)


# --- Lógica de Descarga ---

def opciones_descarga(modo: str, carpeta: str) -> Dict:
    if modo == "video":
        formato = "bestvideo*+bestaudio/best"
        post = [{"key": "FFmpegVideoConvertor", "preferredformat": "mp4"}]
        plantilla = "%(title)s.%(ext)s"
    else: # audio
        formato = "bestaudio/best"
        post = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
        plantilla = "%(title)s.%(ext)s"

    return {
        "format": formato,
        "outtmpl": os.path.join(carpeta, plantilla),
        "quiet": True, # Silencioso, el hook se encarga del feedback
        "postprocessors": post,
        "ignoreerrors": True,
        "progress_hooks": [update_status],
    }

def descargar_una_url(url: str, modo: str, carpeta: str) -> None:
    opciones = opciones_descarga(modo, carpeta)
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([url])
        # El hook 'update_status' se encarga del estado final y el reseteo

    except Exception as err:
        # Este error salta si yt-dlp casca antes de empezar (ej. URL mala)
        error_msg = f"Error iniciando descarga de {url}: {err}"
        root.after(0, lambda: _update_gui_status(error_msg))
        root.after(100, lambda: messagebox.showerror("Error de Descarga", f"{error_msg}\n{err}"))
        _reset_gui_after_delay(3000)


download_executor = None # Pool de hilos para descargas

def iniciar_descarga():
    global download_executor
    url = url_entry.get()
    modo_principal = modo_seleccionado.get()

    if not url:
        messagebox.showerror("Error", "Pon una URL, campeón.")
        return

    # Limpiar y bloquear controles mientras trabajamos
    root.after(0, lambda: _update_gui_status("Arrancando..."))
    descargar_button.config(state=tk.DISABLED)
    url_entry.config(state=tk.DISABLED)
    modo_combo.config(state=tk.DISABLED)
    if playlist_options_frame.winfo_ismapped():
        playlist_modo_combo.config(state=tk.DISABLED)
        num_hilos_spinbox.config(state=tk.DISABLED)

    # Configurar el pool de hilos
    num_hilos_actual = 1
    if modo_principal == "Descargar playlist":
         num_hilos_actual = num_hilos_var.get()
    else:
         num_hilos_actual = 4 # Suficiente para descargas sueltas

    # Creamos/reiniciamos el pool de hilos si hace falta
    if download_executor is None or download_executor._shutdown or download_executor._max_workers != num_hilos_actual:
        if download_executor and not download_executor._shutdown:
            download_executor.shutdown(wait=False)
        download_executor = ThreadPoolExecutor(max_workers=num_hilos_actual)

    # Mandar la tarea al pool
    if modo_principal == "Video con audio":
        carpeta = "videos"
        download_executor.submit(descargar_una_url, url, "video", carpeta)
    elif modo_principal == "Audio MP3":
        carpeta = "sounds"
        download_executor.submit(descargar_una_url, url, "audio", carpeta)
    elif modo_principal == "Video y Audio":
        download_executor.submit(descargar_una_url, url, "video", "ambos")
        download_executor.submit(descargar_una_url, url, "audio", "ambos")
    elif modo_principal == "Descargar playlist":
        playlist_url = url
        modo_playlist = modo_seleccionado_playlist.get().lower()
        carpeta_playlist = "videos" if modo_playlist == "video" else "sounds" if modo_playlist == "audio" else "ambos"
        # La extracción de playlist en su propio hilo para no congelar
        extraction_executor = ThreadPoolExecutor(max_workers=1)
        extraction_executor.submit(extraer_y_descargar_playlist, playlist_url, modo_playlist, carpeta_playlist, download_executor)
        extraction_executor.shutdown(wait=False)
    else:
        messagebox.showerror("Error", "Selecciona un modo, ¿no?")
        _reset_gui_after_delay(0)

    # Ojo: el reseteo de la GUI lo dispara la *primera* tarea que acaba/falla via el hook.
    # No es perfecto para múltiples descargas simultáneas.


def extraer_y_descargar_playlist(playlist_url: str, modo: str, carpeta_base: str, executor: ThreadPoolExecutor) -> None:
    root.after(0, lambda: _update_gui_indeterminate(f"Sacando info de la playlist..."))

    # 'extract_flat': 'discard_in_playlist' es más rápido si solo queremos URLs
    ydl_playlist = yt_dlp.YoutubeDL({'extract_flat': 'discard_in_playlist',
                                     'quiet': True,
                                     'ignoreerrors': True})
    try:
        info = ydl_playlist.extract_info(playlist_url, download=False)

        if 'entries' not in info or not info['entries']:
            msg = "Ni idea de esta playlist o está vacía."
            root.after(0, lambda m=msg: _update_gui_status(m))
            root.after(100, lambda m=msg: messagebox.showerror("Error", m))
            _reset_gui_after_delay(2000)
            return

        urls = [entry['url'] for entry in info['entries'] if entry and 'url' in entry]

        if not urls:
            msg = "No encontré videos válidos en la playlist."
            root.after(0, lambda m=msg: _update_gui_status(m))
            root.after(100, lambda m=msg: messagebox.showerror("Error", m))
            _reset_gui_after_delay(2000)
            return

        num_videos = len(urls)
        root.after(0, lambda n=num_videos, h=executor._max_workers: _update_gui_status(f"{n} videos encontrados. Bajando a {h} hilos..."))

        # Mandar todos los videos de la playlist al pool de descargas
        futures = [executor.submit(descargar_una_url, url, modo, carpeta_base) for url in urls]

    except Exception as err:
        error_msg = f"Error gordo procesando la playlist: {err}"
        root.after(0, lambda em=error_msg: _update_gui_status(em))
        root.after(100, lambda em=error_msg, e=err: messagebox.showerror("Error", f"{em}\n{e}"))
        _reset_gui_after_delay(3000)


# --- Interfaz Gráfica ---
root = tk.Tk()
root.title("Bajador de YouTube")
root.config(bg=C["bg"])

style = ttk.Style()
style.configure("TFrame", background=C["bg"])
style.configure("TLabel", background=C["bg"], foreground=C["fg"])
style.configure("TButton", padding=6, relief="flat", background="#d9d9d9", foreground=C["fg"])
style.map("TButton",
          background=[('pressed', '#c0c0c0'), ('active', '#ececec'), ('disabled', '#f0f0f0')],
          foreground=[('disabled', '#a3a3a3')])
style.configure("TProgressbar", thickness=15, background='green', troughcolor=C["bg"])

title_label = ttk.Label(root, text="Descargar MP4/MP3 de YouTube", font=("Arial", 16, "bold"), foreground=C["title"], background=C["bg"])
title_label.pack(pady=(10, 5))

url_frame = ttk.Frame(root, style="TFrame")
url_label = ttk.Label(url_frame, text="URL:", style="TLabel")
url_entry = ttk.Entry(url_frame, width=60, font=("Arial", 10))
url_label.pack(side=tk.LEFT, padx=(5, 2))
url_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
url_frame.pack(pady=5, padx=10, fill=tk.X)

modo_frame = ttk.Frame(root, style="TFrame")
modo_label = ttk.Label(modo_frame, text="Acción:", style="TLabel")
modo_seleccionado = tk.StringVar(value="Video con audio")
modo_combo = ttk.Combobox(modo_frame, textvariable=modo_seleccionado, values=["Video con audio", "Audio MP3", "Video y Audio", "Descargar playlist"], state="readonly", width=18)
modo_label.pack(side=tk.LEFT, padx=5)
modo_combo.pack(side=tk.LEFT, padx=5)
modo_frame.pack(pady=5, padx=10, anchor='w')

playlist_options_frame = ttk.Frame(root, style="TFrame")
playlist_modo_label = ttk.Label(playlist_options_frame, text="Formato Playlist:", style="TLabel")
modo_seleccionado_playlist = tk.StringVar(value="video")
playlist_modo_combo = ttk.Combobox(playlist_options_frame, textvariable=modo_seleccionado_playlist, values=["video", "audio", "ambos"], state="readonly", width=8)
num_hilos_label = ttk.Label(playlist_options_frame, text="Hilos:", style="TLabel")
default_threads = os.cpu_count() or 4
num_hilos_var = tk.IntVar(value=default_threads)
# Readonly es mejor para que no escriban letras aquí
num_hilos_spinbox = ttk.Spinbox(playlist_options_frame, from_=1, to=64, textvariable=num_hilos_var, width=5, state="readonly")

playlist_modo_label.pack(side=tk.LEFT, padx=(5,2))
playlist_modo_combo.pack(side=tk.LEFT, padx=2)
num_hilos_label.pack(side=tk.LEFT, padx=(10,2))
num_hilos_spinbox.pack(side=tk.LEFT, padx=2)

descargar_button = ttk.Button(root, text="Iniciar descarga", command=iniciar_descarga, style="TButton")

def mostrar_opciones_playlist(*args):
    if modo_seleccionado.get() == "Descargar playlist":
        if not playlist_options_frame.winfo_ismapped():
             playlist_options_frame.pack(pady=5, padx=10, fill=tk.X, before=descargar_button)
    else:
        playlist_options_frame.pack_forget()

modo_seleccionado.trace_add("write", mostrar_opciones_playlist)

descargar_button.pack(pady=(10, 5)) # Ahora sí, el botón

status_frame = ttk.Frame(root, style="TFrame")
status_text = tk.StringVar(value="Listo.")
status_label = ttk.Label(status_frame, textvariable=status_text, style="TLabel", wraplength=500, anchor='w', justify=tk.LEFT)
status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=(0,2))
status_frame.pack(pady=(0, 5), padx=10, fill=tk.X)

progress_bar = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=100, mode='determinate', style="TProgressbar")
progress_bar.pack(pady=(0, 10), padx=10, fill=tk.X)

def on_closing():
    global download_executor
    if download_executor and not download_executor._shutdown:
        print("Cerrando hilos...")
        # wait=False para no bloquear la GUI al cerrar, aunque algo quede a medias
        if hasattr(download_executor, '_threads'):
             if os.sys.version_info >= (3, 9):
                  # Intenta cancelar lo pendiente si se puede (Python 3.9+)
                  download_executor.shutdown(wait=False, cancel_futures=True)
             else:
                  download_executor.shutdown(wait=False) # La opción menos mala para Python viejo
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

crear_carpetas()
mostrar_opciones_playlist()
root.mainloop()