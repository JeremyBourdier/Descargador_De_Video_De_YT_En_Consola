#!/usr/bin/env python3
# coding: utf-8

# Descargador sencillo con menú coloreado y descarga paralela de playlists (con ThreadPoolExecutor)
# Autor: Jeremy Bourdier (modificado para paralelización de playlists con ThreadPoolExecutor)

from pathlib import Path
from typing import Dict, List
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from colorama import init, Fore, Style
import yt_dlp


# Inicializa colorama para Windows y Unix
init(autoreset=True)

# Paleta de colores
C = {
    "title": Fore.CYAN + Style.BRIGHT,
    "option": Fore.YELLOW + Style.BRIGHT,
    "input": Fore.GREEN,
    "error": Fore.RED + Style.BRIGHT,
    "ok": Fore.GREEN + Style.BRIGHT,
}


def crear_carpetas() -> None:
    """
    Crea las carpetas base si aún no existen
    """
    for carpeta in ("videos", "sounds", "ambos"):
        Path(carpeta).mkdir(exist_ok=True)


def opciones_descarga(modo: str, carpeta: str) -> Dict:
    """
    Devuelve el diccionario de opciones para yt_dlp según el modo
    """
    if modo == "video":
        formato = "bestvideo*+bestaudio"
        post = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
        plantilla = "%(title)s.%(ext)s"
    else:  # audio
        formato = "bestaudio"
        post = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
        plantilla = "%(title)s.%(ext)s"

    return {
        "format": formato,
        "outtmpl": os.path.join(carpeta, plantilla),
        "quiet": True,  #para evitar desorden
        "postprocessors": post,
    }


def descargar_una_url(url: str, modo: str, carpeta: str) -> None:
    """
    Descarga una URL usando el modo indicado y guarda en la carpeta indicada
    """
    opciones = opciones_descarga(modo, carpeta)
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([url])
        print(C["ok"] + f"Descarga de {url} completada en {carpeta}")
    except Exception as err:
        print(C["error"] + f"Error al descargar {url}: {err}")


def cabecera() -> None:
    """
    Imprime el título con estilo
    """
    print(C["title"] + "=" * 60)
    print(C["title"] + "     DESCARGADOR YOUTUBE SIMPLE CON yt‑dlp (PARALELO)     ")
    print(C["title"] + "=" * 60)
    print()


def mostrar_menu() -> str:
    """
    Imprime el menú y devuelve la opción elegida
    """
    print(C["option"] + "1" + Style.RESET_ALL + ". Descargar VIDEO con audio")
    print(C["option"] + "2" + Style.RESET_ALL + ". Descargar AUDIO MP3")
    print(C["option"] + "3" + Style.RESET_ALL + ". Descargar VIDEO y AUDIO")
    print(C["option"] + "4" + Style.RESET_ALL + ". Descargar playlist en paralelo")
    print(C["option"] + "5" + Style.RESET_ALL + ". Salir")
    return input(C["input"] + "\nElige una opción (1‑5): ").strip()


def descargar_playlist_paralelo(playlist_url: str, modo: str, carpeta_base: str, max_hilos: int = 14) -> None:
    """
    Descarga los videos de una playlist en paralelo usando ThreadPoolExecutor.
    """
    ydl_playlist = yt_dlp.YoutubeDL({'extract_flat': True, 'quiet': True})
    try:
        info = ydl_playlist.extract_info(playlist_url, download=False)
        if 'entries' not in info:
            print(C["error"] + "No se pudo extraer la información de la playlist.")
            return
        urls = [entry['url'] for entry in info['entries'] if 'url' in entry]
        print(C["option"] + f"Se encontraron {len(urls)} videos en la playlist. Descargando con hasta {max_hilos} hilos...\n")

        with ThreadPoolExecutor(max_workers=max_hilos) as executor:
            futures = [executor.submit(descargar_una_url, url, modo, carpeta_base) for url in urls]
            for future in futures:
                try:
                    future.result()  # Espera a que la tarea termine y maneja posibles excepciones
                except Exception as e:
                    print(C["error"] + f"Error en una descarga: {e}")

        print(C["ok"] + "Descarga de la playlist completada.\n")

    except Exception as err:
        print(C["error"] + f"Error al procesar la playlist: {err}")


def main() -> None:
    crear_carpetas()
    cabecera()

    while True:
        opcion = mostrar_menu()

        if opcion not in {"1", "2", "3", "4", "5"}:
            print(C["error"] + "Opción no válida\n")
            continue
        if opcion == "5":
            print(C["ok"] + "Hasta luego")
            break

        if opcion in {"1", "2", "3"}:
            url = input(C["input"] + "Pega la URL de YouTube: ").strip()
            if opcion == "1":
                descargar_una_url(url, "video", "videos")
                print("\n")
            elif opcion == "2":
                descargar_una_url(url, "audio", "sounds")
                print("\n")
            else:  # opción 3
                descargar_una_url(url, "video", "ambos")
                descargar_una_url(url, "audio", "ambos")
                print("\n")
        elif opcion == "4":
            playlist_url = input(C["input"] + "Pega la URL de la playlist de YouTube: ").strip()
            modo_playlist = input(C["input"] + "Descargar como (video/audio/ambos): ").strip().lower()
            carpeta_playlist = "videos" if modo_playlist == "video" else "sounds" if modo_playlist == "audio" else "ambos"
            descargar_playlist_paralelo(playlist_url, modo_playlist, carpeta_playlist, max_hilos=14) # límite de hilos
        else:
            print(C["error"] + "Opción no implementada.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nInterrumpido por el usuario")