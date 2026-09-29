"""Catálogo ficticio de César Tech. Idempotente; no actualiza filas existentes.
Ejecutar dentro del contenedor API: python - --apply < scripts/catalogo_tech.py
Sin --apply sólo muestra los productos que faltan.
"""
import json
import sys
from app.db import cursor_db

PRODUCTOS = [
    [
        "Laptop Nova 14 | 16 GB RAM · SSD 512 GB",
        "649.00",
        12
    ],
    [
        "Laptop Studio 16 | 32 GB RAM · SSD 1 TB",
        "1099.00",
        8
    ],
    [
        "Laptop Gaming Pulse 15 | 16 GB RAM · SSD 1 TB",
        "1299.00",
        6
    ],
    [
        "PC Gamer Aurora | 32 GB RAM · SSD 1 TB",
        "1499.00",
        5
    ],
    [
        "PC Oficina Essential | 16 GB RAM · SSD 512 GB",
        "549.00",
        10
    ],
    [
        "Mini PC Compact | 16 GB RAM · SSD 512 GB",
        "399.00",
        9
    ],
    [
        "Memoria RAM DDR5 32 GB | Kit 2 × 16 GB",
        "109.00",
        24
    ],
    [
        "Memoria RAM DDR4 16 GB | 3200 MHz",
        "49.00",
        30
    ],
    [
        "SSD NVMe M.2 1 TB | PCIe 4.0",
        "89.00",
        22
    ],
    [
        "SSD SATA 2.5 pulgadas | 480 GB",
        "39.00",
        25
    ],
    [
        "Disco externo portátil | 2 TB USB 3.0",
        "79.00",
        16
    ],
    [
        "Memoria USB 3.2 | 128 GB",
        "19.00",
        40
    ],
    [
        "Procesador 8 núcleos | Hasta 4.5 GHz",
        "259.00",
        12
    ],
    [
        "Tarjeta gráfica | 8 GB GDDR6",
        "329.00",
        7
    ],
    [
        "Tarjeta madre ATX | DDR5 · WiFi",
        "179.00",
        10
    ],
    [
        "Fuente de poder modular | 750 W",
        "99.00",
        14
    ],
    [
        "Gabinete ATX | Cristal templado · 3 ventiladores",
        "85.00",
        11
    ],
    [
        "Kit de enfriamiento | 3 ventiladores de 120 mm",
        "35.00",
        20
    ],
    [
        "Monitor Gaming 27 pulgadas | QHD · 165 Hz",
        "289.00",
        8
    ],
    [
        "Monitor UltraWide 34 pulgadas | WQHD",
        "429.00",
        5
    ],
    [
        "Audífonos Gaming | Micrófono integrado",
        "59.00",
        20
    ],
    [
        "Webcam Full HD | 1080p · USB",
        "39.00",
        18
    ],
    [
        "Teclado mecánico compacto | 75% · RGB",
        "89.00",
        17
    ],
    [
        "Mouse Gaming | 6 botones · RGB",
        "35.00",
        24
    ],
    [
        "Router WiFi 6 | Doble banda",
        "79.00",
        12
    ],
    [
        "Hub USB-C | HDMI · USB · Lector SD",
        "45.00",
        18
    ],
    [
        "Kit de electrónica | Protoboard y componentes",
        "29.00",
        20
    ],
    [
        "Placa microcontrolador | USB-C · WiFi",
        "15.00",
        30
    ]
]
with cursor_db() as cur:
    cur.execute("SELECT pg_advisory_xact_lock(%s)", (94082820260929,))
    cur.execute("SELECT id,nombre,precio,stock FROM productos ORDER BY id")
    before = cur.fetchall()
    existing = {p["nombre"].casefold() for p in before}
    missing = [p for p in PRODUCTOS if p[0].casefold() not in existing]
    inserted = []
    if "--apply" in sys.argv:
        for name, price, stock in missing:
            cur.execute("INSERT INTO productos(nombre,precio,stock) VALUES (%s,%s,%s) RETURNING id", (name,price,stock))
            inserted.append({"id":cur.fetchone()["id"],"nombre":name})
    cur.execute("SELECT count(*) AS total FROM productos")
    total = cur.fetchone()["total"]
    print(json.dumps({"modo":"aplicar" if "--apply" in sys.argv else "consulta","existentes_antes":before,"faltantes":len(missing),"insertados":inserted,"total":total},ensure_ascii=False,default=str,indent=2))

