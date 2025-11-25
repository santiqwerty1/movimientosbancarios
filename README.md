# Movimientos bancarios

Aplicación de línea de comandos para cargar PDFs con resúmenes de distintos bancos/billeteras y persistir todos los movimientos en una sola tabla SQLite.

## Requisitos

- Python 3.11+
- Dependencias del proyecto: `pip install -r requirements.txt`

## Uso rápido

```bash
# Opcional: crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Procesar uno o más PDF y guardarlos en data/transactions.db
python -m movimientos.cli ingest /ruta/a/archivo.pdf

# Ver los movimientos almacenados
python -m movimientos.cli show
```

## Cómo funciona

- La app detecta automáticamente si el PDF corresponde a **Macro**, **Brubank** o **MercadoPago** a partir de palabras clave del documento.
- Para cada línea que incluya fecha y monto, se crea un registro con los campos: `provider`, `date`, `description`, `amount`, `balance` (si está presente), `currency`, `raw_reference` y `source_file`.
- Todos los registros se almacenan en `data/transactions.db` (o en la ruta que indiques con `--db-path`).

## Próximos pasos sugeridos

- Ajustar los parsers con ejemplos reales de Macro, Brubank y MercadoPago.
- Añadir pruebas automatizadas para validar distintos formatos de resúmenes.
- Incorporar detección de moneda y normalización de balances iniciales/finales.
