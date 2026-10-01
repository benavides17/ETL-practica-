"""Persistencia SQLite del laboratorio LCD."""
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterator

import pandas as pd

import config


@contextmanager
def _conexion(ruta: Path) -> Iterator[sqlite3.Connection]:
    """Abre una conexion, confirma la transaccion y la cierra siempre."""
    conexion = sqlite3.connect(ruta)
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def _identificador(nombre: str) -> str:
    """Protege nombres de columnas usados como identificadores SQLite."""
    limpio = re.sub(r"[^a-zA-Z0-9_]", "_", str(nombre)).strip("_") or "columna"
    if limpio[0].isdigit():
        limpio = f"col_{limpio}"
    return limpio.lower()


def _comillas(nombre: str) -> str:
    return '"' + _identificador(nombre).replace('"', '""') + '"'


def crear_base_datos(ruta: Path = config.RUTA_DB) -> None:
    """Crea la base, la tabla de datos y la tabla de control."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with _conexion(ruta) as conexion:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS lcd_datos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station TEXT,
                date TEXT,
                report_type TEXT,
                archivo_origen TEXT,
                fecha_carga TEXT
            )
        """)
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS extracciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_dataset TEXT NOT NULL,
                fecha_hora_extraccion TEXT NOT NULL,
                registros_encontrados INTEGER DEFAULT 0,
                registros_insertados INTEGER DEFAULT 0,
                estado TEXT NOT NULL,
                ruta_archivo TEXT,
                mensaje_error TEXT
            )
        """)
        conexion.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_lcd_datos_natural
            ON lcd_datos (station, date, report_type, archivo_origen)
        """)


def _agregar_columnas(conexion: sqlite3.Connection, columnas: list[str]) -> list[str]:
    """Agrega columnas nuevas y devuelve los nombres SQL normalizados."""
    existentes = {fila[1] for fila in conexion.execute("PRAGMA table_info(lcd_datos)")}
    resultado: list[str] = []
    for columna in columnas:
        normalizada = _identificador(columna)
        resultado.append(normalizada)
        if normalizada not in existentes:
            conexion.execute(f"ALTER TABLE lcd_datos ADD COLUMN {_comillas(normalizada)} TEXT")
            existentes.add(normalizada)
    for columna in ("station", "date", "report_type", "archivo_origen"):
        if columna not in existentes:
            conexion.execute(f"ALTER TABLE lcd_datos ADD COLUMN {_comillas(columna)} TEXT")
            existentes.add(columna)
    return resultado


def insertar_datos(df: pd.DataFrame, nombre: str, ruta: Path = config.RUTA_DB) -> int:
    """Inserta filas con INSERT OR IGNORE y devuelve las realmente insertadas."""
    if df.empty:
        return 0
    crear_base_datos(ruta)
    columnas = [_identificador(columna) for columna in df.columns]
    dataframe = df.copy()
    dataframe.columns = columnas
    dataframe = dataframe.where(pd.notna(dataframe), None)
    with _conexion(ruta) as conexion:
        _agregar_columnas(conexion, columnas)
        placeholders = ", ".join("?" for _ in columnas)
        sql = f"INSERT OR IGNORE INTO lcd_datos ({', '.join(_comillas(col) for col in columnas)}) VALUES ({placeholders})"
        valores = [tuple(None if pd.isna(valor) else str(valor) for valor in fila) for fila in dataframe.itertuples(index=False, name=None)]
        cursor = conexion.executemany(sql, valores)
        return cursor.rowcount


def registrar_extraccion(
    nombre_dataset: str,
    registros_encontrados: int,
    registros_insertados: int,
    estado: str,
    ruta_archivo: str | Path | None = None,
    mensaje_error: str | None = None,
    ruta: Path = config.RUTA_DB,
) -> None:
    """Registra siempre el resultado de una extraccion."""
    crear_base_datos(ruta)
    with _conexion(ruta) as conexion:
        conexion.execute(
            """INSERT INTO extracciones
            (nombre_dataset, fecha_hora_extraccion, registros_encontrados,
             registros_insertados, estado, ruta_archivo, mensaje_error)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nombre_dataset, datetime.now().isoformat(timespec="seconds"), registros_encontrados,
             registros_insertados, estado, str(ruta_archivo) if ruta_archivo else None, mensaje_error),
        )


def consultar_extracciones(ruta: Path = config.RUTA_DB) -> list[tuple[Any, ...]]:
    """Devuelve las extracciones ordenadas desde la mas reciente."""
    crear_base_datos(ruta)
    with _conexion(ruta) as conexion:
        return conexion.execute("SELECT * FROM extracciones ORDER BY id DESC").fetchall()
