#!/usr/bin/env python3
from pathlib import Path
import argparse
import json
import sys
from pyproj import Transformer
from fix_ingestion_smet_2 import rename_station_id_from_excel


def fix_headers_and_rename_from_json(
    json_path: Path,
    smet_dir: Path,
    out_dir: Path,
    epsg_out: str = "3035",
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg_out}", always_xy=True)

    with json_path.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    rows = meta["data"]
    by_name = {row["nome_stazione"]: row for row in rows}

    print(f"Trovate {len(by_name)} stazioni nel JSON.")
    print(f"Input SMET: {smet_dir}")
    print(f"Output SMET: {out_dir}")

    for smet_path in smet_dir.glob("*.smet"):
        text = smet_path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        try:
            data_idx = next(
                i for i, l in enumerate(lines) if l.strip().upper() == "[DATA]"
            )
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
            print(f"Nessun station_name in header di {smet_path.name}, salto.")
            continue

        row = by_name.get(station_name)

        if row is None:
            out_path = out_dir / smet_path.name
            out_path.write_text(text, encoding="utf-8")
            print(
                f"station_name '{station_name}' di {smet_path.name} non trovato nel JSON: copiato invariato come {out_path.name}"
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
        hdr["epsg"] = epsg_out

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
        out_path = out_dir / out_name
        out_path.write_text(new_content, encoding="utf-8")

        print(
            f"✅ Creato {out_path.name} da {smet_path.name} (station_name='{station_name}')"
        )

    print("Finito step JSON")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Rename SMET ingestion")

    p.add_argument(
        "--json-path",
        type=Path,
        required=True,
        help="Path al JSON anagrafica (es. ./data/anagrafica_stazioni.jsonl)",
    )

    p.add_argument(
        "--smet-dir",
        type=Path,
        default=Path("./INGESTION/arpav_filtrati/"),
        help="Directory input SMET (default: ./INGESTION/arpav_filtrati/)",
    )

    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("./meteo/arpav_rinominati/"),
        help="Directory output SMET (default: ./meteo/arpav_rinominati/)",
    )

    p.add_argument(
        "--xlsx-path",
        type=Path,
        required=True,
        help="Excel con mapping INGESTION_ID->station_id",
    )

    p.add_argument(
        "--epsg-out",
        default="3035",
        help="EPSG output per easting/northing (default: 3035)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    try:
        if not args.json_path.exists():
            raise FileNotFoundError(f"JSON non trovato: {args.json_path}")
        if not args.smet_dir.exists():
            raise FileNotFoundError(f"SMET_DIR non trovata: {args.smet_dir}")

        # step 1
        fix_headers_and_rename_from_json(
            json_path=args.json_path,
            smet_dir=args.smet_dir,
            out_dir=args.out_dir,
            epsg_out=args.epsg_out,
        )
        # step 2
        if not args.xlsx_path.exists():
            raise FileNotFoundError(f"XLSX non trovato: {args.xlsx_path}")

        rename_station_id_from_excel(
            smet_dir=args.out_dir,
            xlsx_path=args.xlsx_path,
        )
        return

    except Exception as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
