#!/usr/bin/env python3
# coding: utf-8

# Descargador sencillo con menú coloreado
# Autor: Jeremy Bourdier

from pathlib import Path
from typing import Dict
import os
import sys

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
        "quiet": False,
        "postprocessors": post,
    }


def descargar(url: str, modo: str, carpeta: str) -> None:
    """
    Descarga usando el modo indicado y guarda en la carpeta indicada
    """
    opciones = opciones_descarga(modo, carpeta)

    with yt_dlp.YoutubeDL(opciones) as ydl:
        ydl.download([url])


def cabecera() -> None:
    """
    Imprime el título con estilo
    """
    print(C["title"] + "=" * 60)
    print(C["title"] + "      DESCARGADOR YOUTUBE SIMPLE CON yt‑dlp      ")
    print(C["title"] + "=" * 60)
    print()


def mostrar_menu() -> str:
    """
    Imprime el menú y devuelve la opción elegida
    """
    print(C["option"] + "1" + Style.RESET_ALL + ". Descargar VIDEO con audio")
    print(C["option"] + "2" + Style.RESET_ALL + ". Descargar AUDIO MP3")
    print(C["option"] + "3" + Style.RESET_ALL + ". Descargar VIDEO y AUDIO")
    print(C["option"] + "4" + Style.RESET_ALL + ". Salir")
    return input(C["input"] + "\nElige una opción (1‑4): ").strip()


def main() -> None:
    crear_carpetas()
    cabecera()

    while True:
        opcion = mostrar_menu()

        if opcion not in {"1", "2", "3", "4"}:
            print(C["error"] + "Opción no válida\n")
            continue
        if opcion == "4":
            print(C["ok"] + "Hasta luego")
            break

        url = input(C["input"] + "Pega la URL de YouTube: ").strip()

        try:
            if opcion == "1":
                descargar(url, "video", "videos")
                print(C["ok"] + "Video descargado en videos\n")
            elif opcion == "2":
                descargar(url, "audio", "sounds")
                print(C["ok"] + "Audio descargado en sounds\n")
            else:  # opción 3
                descargar(url, "video", "ambos")
                descargar(url, "audio", "ambos")
                print(C["ok"] + "Video y audio descargados en ambos\n")
        except Exception as err:
            print(C["error"] + f"Error: {err}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nInterrumpido por el usuario")
