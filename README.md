INSTALLATION GUIDE – YouTube Downloader (yt‑dlp)
=============================================================

Prerequisites
-------------
1. **Python 3.8 +** installed and available from the command line.
2. **FFmpeg** in your PATH (yt‑dlp lo necesita para unir video y audio y realizar conversión de formatos).

*(Opcional)*  
– **Git** para clonar el proyecto.  
– Un editor como **Visual Studio Code** para ver y editar el código.

------------------------------------------------------------
Configuración rápida (Windows, macOS o Linux)
------------------------------------------------------------

```bash
# 1 – Descarga o clona el proyecto
git clone https://github.com/JeremyBourdier/Descargador_De_Video_De_YT_En_Consola
#Entra al direcctorio y abre la terminal


# 2 – Crea y activa un entorno virtual 
python -m venv .venv

# Windows
.\\.venv\\Scripts\\activate

# macOS / Linux
source .venv/bin/activate

# 3 – Actualiza pip e instala dependencias
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
