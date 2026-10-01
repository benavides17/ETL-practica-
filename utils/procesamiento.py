"""Lectura y transformacion de CSV LCD con Pandas."""
from datetime import datetime
from pathlib import Path
import re
from typing import Any

import pandas as pd

from config import LOGGER


def normalizar_nombre_columna(nombre: Any) -> str:
    """Normaliza un nombre a identificador SQLite estable."""
    resultado = re.sub(r"[^a-zA-Z0-9_]+", "_", str(nombre).strip().lower())
    return re.sub(r"_+", "_", resultado).strip("_") or "columna"


def leer_y_limpiar_csv(ruta: Path) -> pd.DataFrame:
    """Lee, inspecciona y prepara un CSV para insercion en SQLite."""
    if not ruta.exists() or ruta.stat().st_size == 0:
        raise ValueError(f"El archivo esta vacio o no existe: {ruta}")
    try:
        dataframe = pd.read_csv(ruta, low_memory=False, encoding="utf-8")
    except UnicodeDecodeError:
        dataframe = pd.read_csv(ruta, low_memory=False, encoding="latin-1")
    except pd.errors.EmptyDataError as error:
        raise ValueError(f"El CSV no contiene datos: {ruta}") from error
    dataframe.columns = [normalizar_nombre_columna(columna) for columna in dataframe.columns]
    dataframe = dataframe.dropna(how="all").replace(r"^\s*$", pd.NA, regex=True)
    if "date" in dataframe.columns:
        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")
    dataframe["archivo_origen"] = ruta.name
    dataframe["fecha_carga"] = datetime.now().isoformat(timespec="seconds")
    LOGGER.info("Procesado %s: %d filas, columnas=%s", ruta.name, len(dataframe), list(dataframe.columns))
    LOGGER.info("Tipos de datos de %s:\n%s", ruta.name, dataframe.dtypes.to_string())
    return dataframe
