"""Script 1: descarga consecutiva de varios datasets distintos."""
from datetime import datetime
import time

import config
from utils.descarga import obtener_enlaces, seleccionar_enlaces, descargar_dataset
from utils.navegador import crear_navegador


def main() -> None:
    """Descarga datasets pequenos y registra el avance."""
    logger = config.LOGGER
    driver = None
    try:
        driver = crear_navegador()
        enlaces = obtener_enlaces(driver)
        seleccionados = seleccionar_enlaces(enlaces)
        logger.info("Seleccionados %d datasets de %d enlaces", len(seleccionados), len(enlaces))
        for indice, dataset in enumerate(seleccionados, start=1):
            inicio = datetime.now()
            try:
                ruta = descargar_dataset(driver, dataset)
                logger.info("[%d/%d] %s - %s - OK - %d bytes - %s", indice, len(seleccionados), dataset.nombre, inicio.isoformat(timespec="seconds"), ruta.stat().st_size, ruta)
            except Exception as error:
                logger.exception("[%d/%d] %s - FALLIDO: %s", indice, len(seleccionados), dataset.nombre, error)
            if indice < len(seleccionados):
                time.sleep(config.INTERVALO_ENTRE_DESCARGAS)
    finally:
        if driver is not None:
            driver.quit()
            logger.info("Navegador cerrado")


if __name__ == "__main__":
    main()
