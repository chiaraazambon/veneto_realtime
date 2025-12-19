# Organize ingestion SMET
from pathlib import Path
import json
from pyproj import Transformer

JSON_PATH = Path("./data/anagrafica_stazioni.jsonl")
SMET_DIR = Path("./smet/APOLLO/arpav_filtrati_per_station_name-2025-12-18")
OUT_DIR = Path("./smet/APOLLO/smet_12_18_rinominati")
OUT_DIR.mkdir(parents=True, exist_ok=True)

transformer = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)

with JSON_PATH.open("r", encoding="utf-8") as f:
    meta = json.load(f)

rows = meta["data"]

by_name = {row["nome_stazione"]: row for row in rows}

print(f"Trovate {len(by_name)} stazioni nel JSON.")

for smet_path in SMET_DIR.glob("*.smet"):
    text = smet_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        data_idx = next(i for i, l in enumerate(lines) if l.strip().upper() == "[DATA]")
    except StopIteration:
        print(f"⚠ Nessuna sezione [DATA] in {smet_path.name}, salto.")
        continue

    header_lines = lines[:data_idx]
    data_lines = lines[data_idx:]

    if len(header_lines) < 2 or not header_lines[0].startswith("SMET"):
        print(f"⚠ Header non riconosciuto in {smet_path.name}, salto.")
        continue

    hdr = {}
    for l in header_lines[2:]:
        if "=" in l:
            key, val = l.split("=", 1)
            hdr[key.strip()] = val.strip()

    station_name = hdr.get("station_name")
    if station_name is None:
        print(f"⚠ Nessun station_name in header di {smet_path.name}, salto.")
        continue
    row = by_name.get(station_name)

    if row is None:
        # Non trovata nel JSON: copia il file così com'è nel folder di output
        out_path = OUT_DIR / smet_path.name
        out_path.write_text(text, encoding="utf-8")

        print(
            f"⚠ station_name '{station_name}' di {smet_path.name} non trovato nel JSON: copiato invariato come {out_path.name}"
        )
        continue

    codice = int(row["codice_stazione"])
    lon = float(row["longitudine"])
    lat = float(row["latitudine"])
    alt = float(row["altitude"])

    easting, northing = transformer.transform(lon, lat)

    hdr["station_id"] = str(codice)
    hdr["station_name"] = row["nome_stazione"]
    hdr["latitude"] = f"{lat:.8f}"
    hdr["longitude"] = f"{lon:.8f}"
    hdr["altitude"] = f"{alt:.1f}"

    hdr["easting"] = f"{easting:.6f}"
    hdr["northing"] = f"{northing:.6f}"
    hdr["epsg"] = "3035"

    # Ordine “pulito” per l’header
    header_order = [
        "station_id",
        "station_name",
        "latitude",
        "longitude",
        "altitude",
        "easting",
        "northing",
        "epsg",
        "provider_id",
        "nodata",
        "tz",
        "fields",
    ]

    new_header_lines = [
        "SMET 1.1 ASCII",
        "[HEADER]",
    ]

    for key in header_order:
        if key in hdr:
            new_header_lines.append(f"{key.ljust(17)}= {hdr[key]}")

    for key, val in hdr.items():
        if key not in header_order:
            new_header_lines.append(f"{key.ljust(17)}= {val}")

    new_lines = new_header_lines + data_lines
    new_content = "\n".join(new_lines) + "\n"

    out_name = f"{codice}.smet"
    out_path = OUT_DIR / out_name
    out_path.write_text(new_content, encoding="utf-8")

    print(
        f"✅ Creato {out_path.name} da {smet_path.name} (station_name='{station_name}')"
    )

print("Finito")
