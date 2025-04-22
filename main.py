#!/usr/bin/env python3
# coding: utf-8

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
from pathlib import Path
from typing import Dict, List

# Paleta de colores
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

def opciones_descarga(modo: str, carpeta: str) -> Dict:
    if modo == "video":
        formato = "bestvideo*+bestaudio/best" 
        post = [{"key": "FFmpegVideoConvertor", "preferredformat": "mp4"}]
        plantilla = "%(title)s.%(ext)s"
    else:  
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
        "quiet": True,
        "postprocessors": post,
        "ignoreerrors": True, # Para que la descarga de playlist no se detenga por un error
        "progress_hooks": [lambda d: update_status(d, status_text)], 
    }

# para actualizar el estado 
def update_status(d, status_var):
    if d['status'] == 'downloading':
        filename = d.get('filename', 'unknown')
        total_bytes_estimate = d.get('total_bytes_estimate')
        downloaded_bytes = d.get('downloaded_bytes')
        if total_bytes_estimate and downloaded_bytes:
            percent = (downloaded_bytes / total_bytes_estimate) * 100
            status_var.set(f"Descargando {Path(filename).name}: {percent:.1f}%")
        else:
            status_var.set(f"Descargando {Path(filename).name}...")
    elif d['status'] == 'finished':
        filename = d.get('filename', 'unknown')
        status_var.set(f"Completado: {Path(filename).name}")
    elif d['status'] == 'error':
        filename = d.get('filename', 'unknown')
        status_var.set(f"Error descargando {Path(filename).name}")


def descargar_una_url(url: str, modo: str, carpeta: str, status_label_var: tk.StringVar) -> None:
    opciones = opciones_descarga(modo, carpeta)
    try:
        
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([url])
      
    except Exception as err:
        
        status_label_var.set(f"Error al descargar {url}: {err}")
       
        root.after(0, lambda: messagebox.showerror("Error de Descarga", f"Ocurrió un error al descargar {url}:\n{err}"))



download_executor = None

def iniciar_descarga():
    global download_executor
    url = url_entry.get()
    modo_principal = modo_seleccionado.get()

    if not url:
        messagebox.showerror("Error", "Por favor, introduce una URL.")
        return


    if download_executor is None or download_executor._shutdown:
      
         num_hilos = num_hilos_var.get() if modo_principal == "Descargar playlist" else 4
         download_executor = ThreadPoolExecutor(max_workers=num_hilos)

    if modo_principal == "Video con audio":
        carpeta = "videos"
        download_executor.submit(descargar_una_url, url, "video", carpeta, status_text)
    elif modo_principal == "Audio MP3":
        carpeta = "sounds"
        download_executor.submit(descargar_una_url, url, "audio", carpeta, status_text)
    elif modo_principal == "Video y Audio":
        
        download_executor.submit(descargar_una_url, url, "video", "ambos", status_text)
        download_executor.submit(descargar_una_url, url, "audio", "ambos", status_text)
    elif modo_principal == "Descargar playlist":
        playlist_url = url
        modo_playlist = modo_seleccionado_playlist.get().lower()
        carpeta_playlist = "videos" if modo_playlist == "video" else "sounds" if modo_playlist == "audio" else "ambos"
        num_hilos = num_hilos_var.get()
        
        if download_executor is not None and not download_executor._shutdown:
            download_executor.shutdown(wait=False) 
        download_executor = ThreadPoolExecutor(max_workers=num_hilos)
        # Ejecutar la extraccion en un hilo separado para no bloquear GUI
        extraction_executor = ThreadPoolExecutor(max_workers=1)
        extraction_executor.submit(extraer_y_descargar_playlist, playlist_url, modo_playlist, carpeta_playlist, download_executor)
        extraction_executor.shutdown(wait=False) # no esperar
    else:
        messagebox.showerror("Error", "Por favor, selecciona un modo de descarga.")



def extraer_y_descargar_playlist(playlist_url: str, modo: str, carpeta_base: str, executor: ThreadPoolExecutor) -> None:
    ydl_playlist = yt_dlp.YoutubeDL({'extract_flat': True, 'quiet': True, 'ignoreerrors': True})
    try:
        status_text.set(f"Extrayendo información de la playlist: {playlist_url}...")
        info = ydl_playlist.extract_info(playlist_url, download=False)

        if 'entries' not in info or not info['entries']:
            msg = "No se pudo extraer la información de la playlist o está vacía."
            status_text.set(msg)
            root.after(0, lambda: messagebox.showerror("Error", msg))
            return

        
        urls = [entry['url'] for entry in info['entries'] if entry and 'url' in entry]

        if not urls:
            msg = "No se encontraron URLs válidas en la playlist."
            status_text.set(msg)
            root.after(0, lambda: messagebox.showerror("Error", msg))
            return

        status_text.set(f"Se encontraron {len(urls)} videos. Descargando con hasta {executor._max_workers} hilos...")

       
        futures = [executor.submit(descargar_una_url, url, modo, carpeta_base, status_text) for url in urls]

    

     
        status_text.set(f"Descarga de {len(urls)} videos iniciada...")


    except Exception as err:
        error_msg = f"Error al procesar la playlist: {err}"
        status_text.set(error_msg)
        root.after(0, lambda: messagebox.showerror("Error", f"{error_msg}\n{err}"))
    finally:
      
        pass



# --- Interfaz Gráfica ---
root = tk.Tk()
root.title("Descargador de YouTube")
root.config(bg=C["bg"])


style = ttk.Style()
style.configure("TFrame", background=C["bg"])
style.configure("TLabel", background=C["bg"], foreground=C["fg"])
style.configure("TButton", background="#d9d9d9", foreground=C["fg"])
style.map("TButton", background=[('active', '#ececec')]) # Estilo para botón activo

# Título
title_label = ttk.Label(root, text="Descargador de YouTube", font=("Arial", 16, "bold"), foreground=C["title"], background=C["bg"])
title_label.pack(pady=10)

# URL
url_frame = ttk.Frame(root, style="TFrame")
url_label = ttk.Label(url_frame, text="URL:", style="TLabel")
url_entry = ttk.Entry(url_frame, width=50)
url_label.pack(side=tk.LEFT, padx=5)
url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
url_frame.pack(pady=5, padx=10, fill=tk.X)


modo_frame = ttk.Frame(root, style="TFrame")
modo_label = ttk.Label(modo_frame, text="Acción:", style="TLabel")
modo_seleccionado = tk.StringVar(value="Video con audio") 
modo_combo = ttk.Combobox(modo_frame, textvariable=modo_seleccionado, values=["Video con audio", "Audio MP3", "Video y Audio", "Descargar playlist"], state="readonly")
modo_label.pack(side=tk.LEFT, padx=5)
modo_combo.pack(side=tk.LEFT, padx=5)
modo_frame.pack(pady=5, padx=10, fill=tk.X)

playlist_options_frame = ttk.Frame(root, style="TFrame")
playlist_modo_label = ttk.Label(playlist_options_frame, text="Formato Playlist:", style="TLabel")
modo_seleccionado_playlist = tk.StringVar(value="video") 
playlist_modo_combo = ttk.Combobox(playlist_options_frame, textvariable=modo_seleccionado_playlist, values=["video", "audio", "ambos"], state="readonly")
num_hilos_label = ttk.Label(playlist_options_frame, text="Hilos:", style="TLabel")

default_threads = os.cpu_count() or 4 
num_hilos_var = tk.IntVar(value=default_threads)
num_hilos_spinbox = ttk.Spinbox(playlist_options_frame, from_=1, to=64, textvariable=num_hilos_var, width=5) 

playlist_modo_label.pack(side=tk.LEFT, padx=5)
playlist_modo_combo.pack(side=tk.LEFT, padx=5)
num_hilos_label.pack(side=tk.LEFT, padx=5)
num_hilos_spinbox.pack(side=tk.LEFT, padx=5)



def mostrar_opciones_playlist(*args):
    if modo_seleccionado.get() == "Descargar playlist":
        playlist_options_frame.pack(pady=5, padx=10, fill=tk.X, before=descargar_button) 
    else:
        playlist_options_frame.pack_forget()

modo_seleccionado.trace_add("write", mostrar_opciones_playlist)

descargar_button = ttk.Button(root, text="Descargar", command=iniciar_descarga, style="TButton")
descargar_button.pack(pady=20) 


status_text = tk.StringVar(value="Listo")
status_label = ttk.Label(root, textvariable=status_text, style="TLabel", wraplength=400) 
status_label.pack(pady=5, padx=10, fill=tk.X)


def on_closing():
    global download_executor
    if download_executor and not download_executor._shutdown:
        print("Cerrando hilos de descarga...")
        download_executor.shutdown(wait=False) 
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

crear_carpetas()
mostrar_opciones_playlist()
root.mainloop()