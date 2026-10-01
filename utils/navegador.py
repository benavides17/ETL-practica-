"""Creacion y cierre del navegador Selenium."""
from pathlib import Path
import shutil

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

import config


def _chrome_instalado() -> bool:
    """Comprueba ubicaciones habituales de Chrome en Windows y PATH."""
    candidatos = [
        shutil.which("chrome"),
        shutil.which("google-chrome"),
        Path(r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"),
        Path(r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"),
        Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
    ]
    return any(candidato and Path(candidato).exists() for candidato in candidatos)


def crear_navegador(directorio_descarga: Path | None = None, headless: bool | None = None) -> webdriver.Chrome:
    """Crea Chrome configurado para descargar CSV sin dialogos."""
    if not _chrome_instalado():
        raise RuntimeError(
            "Google Chrome no fue detectado. Instala Chrome y vuelve a ejecutar el laboratorio."
        )
    directorio = (directorio_descarga or config.DIRECTORIO_DESCARGAS).resolve()
    directorio.mkdir(parents=True, exist_ok=True)
    opciones = Options()
    opciones.add_argument("--window-size=1440,1000")
    opciones.add_argument("--disable-gpu")
    opciones.add_experimental_option("prefs", {
        "download.default_directory": str(directorio),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })
    usar_headless = config.HEADLESS if headless is None else headless
    if usar_headless:
        opciones.add_argument("--headless=new")
    try:
        servicio = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=servicio, options=opciones)
    except (WebDriverException, OSError) as error:
        raise RuntimeError(
            "No fue posible iniciar ChromeDriver. Verifica que Google Chrome este instalado "
            "y que webdriver-manager tenga acceso a Internet."
        ) from error
