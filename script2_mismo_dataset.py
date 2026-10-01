"""Script 2: descarga repetida del mismo dataset con comparacion de hashes."""
from datetime import datetime
import hashlib
import time

import config
from utils.descarga import obtener_enlaces, seleccionar_enlaces, descargar_dataset
from utils.navegador import crear_navegador


def hash_archivo(ruta) -> str:
    """Calcula SHA-256 de un archivo por bloques."""
    sha256 = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            sha256.update(bloque)
    return sha256.hexdigest()


def main() -> None:
    """Descarga N veces el primer dataset seleccionado y compara resultados."""
    logger = config.LOGGER
    driver = None
    hashes: list[str] = []
    try:
        driver = crear_navegador()
        seleccionado = seleccionar_enlaces(obtener_enlaces(driver), cantidad=1)[0]
        logger.info("Dataset repetido: %s (%s)", seleccionado.nombre, seleccionado.tamano_texto)
        for intento in range(1, config.INTENTO_REPETIDO + 1):
            inicio = time.monotonic()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre = f"{seleccionado.nombre.rsplit('.', 1)[0]}_intento_{intento}_{timestamp}.csv"
            try:
                ruta = descargar_dataset(driver, seleccionado, nombre_destino=nombre)
                hash_actual = hash_archivo(ruta)
                hashes.append(hash_actual)
                diferencia = "IGUAL" if len(set(hashes)) == 1 else "DIFERENTE"
                logger.info("Intento %d/%d: %.2fs, %d bytes, SHA256=%s, contenido=%s", intento, config.INTENTO_REPETIDO, time.monotonic() - inicio, ruta.stat().st_size, hash_actual, diferencia)
            except Exception as error:
                logger.exception("Intento %d/%d FALLIDO: %s", intento, config.INTENTO_REPETIDO, error)
            if intento < config.INTENTO_REPETIDO:
                time.sleep(config.INTERVALO_REPETIDO)
        logger.info("Resumen repeticion: %d/%d hashes unicos", len(set(hashes)), len(hashes))
    finally:
        if driver is not None:
            driver.quit()
            logger.info("Navegador cerrado")


if __name__ == "__main__":
    main()
