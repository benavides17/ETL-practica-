"""Configuracion central del laboratorio ETL de NOAA LCD."""
from pathlib import Path
import logging
import sys

BASE_DIR = Path(__file__).resolve().parent
URL_BASE = "https://www.ncei.noaa.gov/data/local-climatological-data/access/2021/"
DIRECTORIO_DESCARGAS = BASE_DIR / "descargas"
DIRECTORIO_DB = BASE_DIR / "db"
DIRECTORIO_LOGS = BASE_DIR / "logs"
RUTA_DB = DIRECTORIO_DB / "clima.db"
RUTA_LOG = DIRECTORIO_LOGS / "etl.log"

CANTIDAD_DATASETS = 5
INTENTO_REPETIDO = 5
INTERVALO_ENTRE_DESCARGAS = 10
INTERVALO_REPETIDO = 5
TIMEOUT_DESCARGA = 120
TIMEOUT_PAGINA = 30
TAMANO_MAX_MB = 2
MODO_SELECCION = "pequenos"  # pequenos, primeros o aleatorio
HEADLESS = True

for directorio in (DIRECTORIO_DESCARGAS, DIRECTORIO_DB, DIRECTORIO_LOGS):
    directorio.mkdir(parents=True, exist_ok=True)


def configurar_logging() -> logging.Logger:
    """Configura logging para consola y para logs/etl.log."""
    logger = logging.getLogger("etl_lcd")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formato = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    consola = logging.StreamHandler(sys.stdout)
    consola.setFormatter(formato)
    archivo = logging.FileHandler(RUTA_LOG, encoding="utf-8")
    archivo.setFormatter(formato)
    logger.addHandler(consola)
    logger.addHandler(archivo)
    return logger


LOGGER = configurar_logging()
