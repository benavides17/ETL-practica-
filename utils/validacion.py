"""Validacion de descargas completas y legibles."""
from pathlib import Path
import time
from typing import Iterable

import pandas as pd

import config


class DescargaIncompletaError(TimeoutError):
    """Indica que una descarga no finalizo dentro del tiempo limite."""


def _temporales(directorio: Path, nombre: str) -> list[Path]:
    """Devuelve temporales relacionados con el nombre esperado."""
    return [
        directorio / f"{nombre}.crdownload",
        directorio / f"{nombre}.tmp",
        *directorio.glob(f"{Path(nombre).stem}*.crdownload"),
        *directorio.glob(f"{Path(nombre).stem}*.tmp"),
    ]


def esperar_descarga(
    ruta: Path,
    timeout: int = config.TIMEOUT_DESCARGA,
    comprobar_csv: bool = False,
    intervalo_estabilidad: float = 1.5,
) -> Path:
    """Espera un archivo no vacio, estable y sin temporales de navegador."""
    inicio = time.monotonic()
    tamano_anterior = -1
    while time.monotonic() - inicio < timeout:
        temporales = [temporal for temporal in _temporales(ruta.parent, ruta.name) if temporal.exists()]
        if ruta.exists() and ruta.stat().st_size > 0 and not temporales:
            tamano_actual = ruta.stat().st_size
            if tamano_actual == tamano_anterior:
                if comprobar_csv:
                    try:
                        pd.read_csv(ruta, nrows=1, encoding="utf-8", low_memory=False)
                    except (UnicodeDecodeError, pd.errors.ParserError):
                        pd.read_csv(ruta, nrows=1, encoding="latin-1", low_memory=False)
                return ruta
            tamano_anterior = tamano_actual
        time.sleep(intervalo_estabilidad)
    raise DescargaIncompletaError(f"La descarga no termino a tiempo: {ruta}")


def localizar_descarga(directorio: Path, nombre: str) -> Path | None:
    """Localiza el nombre exacto o una copia renombrada por Chrome."""
    exacta = directorio / nombre
    if exacta.exists():
        return exacta
    candidatos = sorted(directorio.glob(f"{Path(nombre).stem}*{Path(nombre).suffix}"), key=lambda p: p.stat().st_mtime)
    return candidatos[-1] if candidatos else None
