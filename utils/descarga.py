"""Descubrimiento y descarga automatica de datasets LCD."""
from dataclasses import dataclass
from pathlib import Path
import random
import re
import time
from typing import Iterable
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver

import config
from .validacion import esperar_descarga


@dataclass(frozen=True)
class DatasetLink:
    """Enlace de dataset junto con su tamano publicado."""
    nombre: str
    url: str
    tamano_bytes: int
    tamano_texto: str


def convertir_tamano_bytes(valor: str) -> int:
    """Convierte valores como 50K, 1.2M o 12 MB a bytes."""
    texto = valor.strip().upper().replace(",", ".")
    coincidencia = re.search(r"(\d+(?:\.\d+)?)\s*(B|KB|K|MB|M|GB|G)?", texto)
    if not coincidencia:
        return 0
    numero = float(coincidencia.group(1))
    unidad = coincidencia.group(2) or "B"
    multiplicadores = {"B": 1, "K": 1024, "KB": 1024, "M": 1024**2, "MB": 1024**2, "G": 1024**3, "GB": 1024**3}
    return int(numero * multiplicadores[unidad])


def obtener_enlaces(driver: WebDriver, url: str = config.URL_BASE) -> list[DatasetLink]:
    """Abre el listado y obtiene enlaces CSV con su columna de tamano."""
    driver.get(url)
    WebDriverWait(driver, config.TIMEOUT_PAGINA).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href$='.csv']"))
    )
    enlaces: list[DatasetLink] = []
    for anchor in driver.find_elements(By.CSS_SELECTOR, "a[href$='.csv']"):
        href = anchor.get_attribute("href")
        nombre = (anchor.text or Path(href or "dataset.csv").name).strip()
        if not href or not nombre.lower().endswith(".csv"):
            continue
        tamano_texto = ""
        try:
            fila = anchor.find_element(By.XPATH, "./ancestor::tr[1]")
            tamano_texto = fila.text
        except Exception:
            tamano_texto = anchor.find_element(By.XPATH, "..").text
        valores = re.findall(r"\b\d+(?:[\.,]\d+)?\s*(?:B|KB|K|MB|M|GB|G)\b", tamano_texto, flags=re.IGNORECASE)
        tamano = convertir_tamano_bytes(valores[-1]) if valores else 0
        enlaces.append(DatasetLink(nombre, urljoin(url, href), tamano, valores[-1] if valores else "desconocido"))
    return list({enlace.nombre: enlace for enlace in enlaces}.values())


def seleccionar_enlaces(
    enlaces: Iterable[DatasetLink],
    cantidad: int = config.CANTIDAD_DATASETS,
    modo: str = config.MODO_SELECCION,
    max_mb: float = config.TAMANO_MAX_MB,
) -> list[DatasetLink]:
    """Selecciona datasets pequenos, primeros o aleatorios sin repetir nombres."""
    disponibles = list(enlaces)
    if modo == "pequenos":
        limite = max_mb * 1024 * 1024
        candidatos = [enlace for enlace in disponibles if enlace.tamano_bytes <= limite and enlace.tamano_bytes > 0]
        candidatos.sort(key=lambda enlace: enlace.tamano_bytes)
        if len(candidatos) < cantidad:
            restantes = sorted(
                [enlace for enlace in disponibles if enlace not in candidatos],
                key=lambda enlace: enlace.tamano_bytes or float("inf"),
            )
            candidatos.extend(restantes)
    elif modo == "primeros":
        candidatos = disponibles
    elif modo == "aleatorio":
        candidatos = disponibles[:]
        random.shuffle(candidatos)
    else:
        raise ValueError("MODO_SELECCION debe ser: pequenos, primeros o aleatorio")
    return candidatos[:cantidad]


def descargar_dataset(
    driver: WebDriver,
    dataset: DatasetLink,
    directorio: Path = config.DIRECTORIO_DESCARGAS,
    nombre_destino: str | None = None,
) -> Path:
    """Descarga un CSV y devuelve la ruta real, incluso si Chrome lo renombra."""
    directorio.mkdir(parents=True, exist_ok=True)
    patron = Path(dataset.nombre).stem
    existentes = set(directorio.glob(f"{patron}*.csv"))
    driver.get(dataset.url)
    limite = time.monotonic() + config.TIMEOUT_DESCARGA
    while time.monotonic() < limite:
        nuevos = [ruta for ruta in directorio.glob(f"{patron}*.csv") if ruta not in existentes]
        if nuevos:
            ruta = max(nuevos, key=lambda item: item.stat().st_mtime)
            ruta = esperar_descarga(ruta, config.TIMEOUT_DESCARGA, comprobar_csv=True)
            if nombre_destino:
                destino = directorio / nombre_destino
                if destino.exists():
                    destino.unlink()
                ruta.replace(destino)
                return destino
            return ruta
        time.sleep(1)
    raise TimeoutError(f"No se encontro el archivo descargado para {dataset.nombre}")
