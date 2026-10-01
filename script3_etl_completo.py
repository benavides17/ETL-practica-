"""Script 3: orquestacion completa de extraccion, transformacion y carga."""
from pathlib import Path
import time

import config
from utils.base_datos import crear_base_datos, insertar_datos, registrar_extraccion, consultar_extracciones
from utils.descarga import obtener_enlaces, seleccionar_enlaces, descargar_dataset
from utils.navegador import crear_navegador
from utils.procesamiento import leer_y_limpiar_csv


def imprimir_resumen() -> None:
    """Imprime el control de extracciones y sus totales."""
    filas = consultar_extracciones()
    print("\nResumen de extracciones")
    print("id | dataset | encontrados | insertados | estado | fecha")
    for fila in filas:
        print(f"{fila[0]} | {fila[1]} | {fila[3]} | {fila[4]} | {fila[5]} | {fila[2]}")
    encontrados = sum(fila[3] or 0 for fila in filas)
    insertados = sum(fila[4] or 0 for fila in filas)
    print(f"Totales: registros encontrados={encontrados}, registros insertados={insertados}")


def main() -> None:
    """Ejecuta el ETL sin detenerse por el fallo de un dataset."""
    logger = config.LOGGER
    crear_base_datos()
    driver = None
    seleccionados = []
    try:
        driver = crear_navegador()
        seleccionados = seleccionar_enlaces(obtener_enlaces(driver))
        logger.info("ETL iniciado con %d datasets", len(seleccionados))
        for indice, dataset in enumerate(seleccionados, start=1):
            ruta: Path | None = None
            encontrados = 0
            insertados = 0
            try:
                logger.info("[%d/%d] Extrayendo %s", indice, len(seleccionados), dataset.nombre)
                ruta = descargar_dataset(driver, dataset)
                dataframe = leer_y_limpiar_csv(ruta)
                encontrados = len(dataframe)
                insertados = insertar_datos(dataframe, dataset.nombre)
                estado = "DUPLICADO" if encontrados and insertados == 0 else "EXITOSO" if insertados == encontrados else "PARCIAL"
                registrar_extraccion(dataset.nombre, encontrados, insertados, estado, ruta)
                logger.info("[%d/%d] %s: %d encontrados, %d insertados, %s", indice, len(seleccionados), dataset.nombre, encontrados, insertados, estado)
            except Exception as error:
                registrar_extraccion(dataset.nombre, encontrados, insertados, "FALLIDO", ruta, str(error))
                logger.exception("[%d/%d] %s FALLIDO; se continua con el siguiente", indice, len(seleccionados), dataset.nombre)
            if indice < len(seleccionados):
                time.sleep(config.INTERVALO_ENTRE_DESCARGAS)
    finally:
        if driver is not None:
            driver.quit()
            logger.info("Navegador cerrado")
    imprimir_resumen()


if __name__ == "__main__":
    main()
