import os
import sys
import requests
import subprocess
from datetime import date
from pathlib import Path

# Configuración
FEED_URL = 'https://peapix.com/bing/feed?country='
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0',
}

def get_feed(country: str) -> list:
    """Obtiene el feed de imágenes de Peapix"""
    url = f"{FEED_URL}{country}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def download_wallpaper(item: dict, wallpapers_dir: Path) -> Path:
    """Descarga la imagen si no existe aún"""
    date_str = item.get("date", date.today().isoformat())
    image_url = item.get("imageUrl")
    
    if not image_url:
        raise ValueError("Campo 'imageUrl' no encontrado en el item del feed")

    image_path = wallpapers_dir / f"{date_str}.jpg"
    if not image_path.exists():
        response = requests.get(image_url, headers=HEADERS)
        response.raise_for_status()
        with open(image_path, "wb") as f:
            f.write(response.content)
    return image_path

def get_connected_monitors() -> list:
    """Detecta monitores conectados vía xrandr"""
    result = subprocess.run(
        ["xrandr"], capture_output=True, text=True
    )
    lines = result.stdout.splitlines()
    return [line.split()[0] for line in lines if " connected" in line]

def set_wallpaper(image_path: Path, monitors: list) -> None:
    """Actualiza el fondo de pantalla en XFCE para cada monitor"""
    for monitor in monitors:
        prop = f"/backdrop/screen0/monitor{monitor}/workspace0/last-image"
        subprocess.run([
            "xfconf-query", "-c", "xfce4-desktop",
            "-p", prop, "-s", str(image_path)
        ])

def main():
    if not os.environ.get("DISPLAY"):
        print("DISPLAY no está definido. ¿Estás en modo gráfico?")
        sys.exit(1)

    # Variables desde entorno o valores por defecto
    country = os.environ.get("BING_WALLPAPER_COUNTRY", "")
    wallpapers_dir = Path(os.environ.get("BING_WALLPAPER_PATH", str(Path.home() / ".wallpapers")))
    wallpapers_dir.mkdir(parents=True, exist_ok=True)

    try:
        images = get_feed(country)
    except Exception as e:
        print(f"Error al obtener el feed: {e}")
        sys.exit(1)

    today_str = date.today().isoformat()
    today_image_path = wallpapers_dir / f"{today_str}.jpg"

    for item in images:
        try:
            image_path = download_wallpaper(item, wallpapers_dir)
            if image_path == today_image_path:
                break
        except Exception as e:
            print(f"Error descargando imagen: {e}")

    if not today_image_path.exists():
        print(f"No se encontró wallpaper para hoy: {today_str}")
        sys.exit(1)

    try:
        monitors = get_connected_monitors()
        set_wallpaper(today_image_path, monitors)
        print(f"Wallpaper actualizado para {today_str}")
    except Exception as e:
        print(f"Error al configurar el fondo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
