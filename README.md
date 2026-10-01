# Laboratorio ETL de Local Climatological Data

Proyecto Python 3.10+ para extraer automaticamente datasets CSV de Local Climatological Data (LCD) de NOAA/NCEI, limpiarlos con Pandas y cargarlos en SQLite.

## Requisitos e instalacion

Se requiere Google Chrome instalado. `webdriver-manager` descarga ChromeDriver automaticamente. Si Chrome no esta instalado, el programa muestra un error claro y termina.

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

La configuracion principal esta en `config.py`: URL, cantidad de datasets, intervalos, timeout, modo de seleccion (`pequenos`, `primeros`, `aleatorio`), limite de tamano y modo headless.

## Ejecucion

Desde la raiz del proyecto y con el entorno virtual activo:

```bash
python script1_multiples_datasets.py
python script2_mismo_dataset.py
python script3_etl_completo.py
```

El primer script descarga cinco archivos distintos por defecto, priorizando los de hasta 2 MB y esperando 10 segundos entre descargas. El segundo descarga el mismo archivo cinco veces, lo guarda con un sufijo de intento y timestamp, y compara SHA-256, tamano y tiempos con espera de 5 segundos. El tercero ejecuta todo el ETL y continua aunque falle un dataset.

## Estructura

- `descargas/`: CSV obtenidos automaticamente.
- `db/clima.db`: base SQLite.
- `logs/etl.log`: log de consola y archivo con fecha, nivel y mensaje.
- `utils/`: navegador, descarga, validacion, procesamiento y persistencia.

## Base de datos

`lcd_datos` se crea dinamicamente. Incluye una columna por cada columna normalizada del CSV, `archivo_origen`, `fecha_carga` y una clave primaria tecnica. Si un CSV futuro trae una columna nueva, se agrega con `ALTER TABLE`. La clave natural `(station, date, report_type, archivo_origen)` tiene indice unico y las cargas usan `INSERT OR IGNORE`.

`extracciones` contiene `id`, `nombre_dataset`, `fecha_hora_extraccion`, `registros_encontrados`, `registros_insertados`, `estado`, `ruta_archivo` y `mensaje_error`. Los estados son `EXITOSO`, `FALLIDO`, `PARCIAL` y `DUPLICADO`.

Consultas de verificacion:

```sql
SELECT * FROM extracciones;
SELECT COUNT(*) FROM lcd_datos;
SELECT estado, SUM(registros_encontrados), SUM(registros_insertados)
FROM extracciones GROUP BY estado;
```

## Prueba paso a paso

1. Activa el entorno e instala dependencias. Confirma que Chrome abre normalmente.
2. Ejecuta `script1_multiples_datasets.py`. Espera cinco nombres, hora, tamano y resultado en consola; los CSV apareceran en `descargas/` y el avance en `logs/etl.log`.
3. Ejecuta `script2_mismo_dataset.py`. Veras cinco intentos del mismo dataset, cada uno con tamano, segundos y SHA-256. Apareceran archivos con `_intento_1_...csv`, `_intento_2_...csv`, etc.
4. Ejecuta `script3_etl_completo.py`. Para cada archivo se mostrara lectura, columnas, dtypes, filas e insercion. Al final imprime la tabla de `extracciones` y los totales encontrados frente a insertados.
5. Abre `db/clima.db` con SQLite y ejecuta las consultas anteriores. Las cargas repetidas no incrementan filas cuando coincide la clave natural.

Si la red, NOAA o Chrome no estan disponibles, el error queda en `logs/etl.log`; el tercer script registra el dataset afectado como `FALLIDO` y continua con los restantes cuando la etapa de navegador ya pudo iniciarse.
