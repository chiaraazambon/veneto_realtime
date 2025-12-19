#!/usr/bin/env python3
from pathlib import Path
import pandas as pd


def rename_station_id_from_excel(
    smet_dir: Path,
    xlsx_path: Path,
) -> None:
    if not smet_dir.exists():
        raise FileNotFoundError(f"SMET_DIR non trovata: {smet_dir}")
    if not xlsx_path.exists():
        raise FileNotFoundError(f"XLSX_PATH non trovato: {xlsx_path}")

    df = pd.read_excel(xlsx_path)
    df.columns = [c.strip() for c in df.columns]

    map_ingestion_to_id = dict(
        zip(
            df["INGESTION_ID"].astype(str),
            df["station_id"].astype(str),
        )
    )

    print(
        "Trovate", len(map_ingestion_to_id), "mappature da INGESTION_ID a station_id."
    )

    for smet_fp in sorted(smet_dir.glob("*.smet")):
        text = smet_fp.read_text(encoding="utf-8", errors="ignore")

        lines = text.splitlines()
        station_id_line_idx = None
        old_station_id = None

        for i, line in enumerate(lines):
            if line.strip().startswith("station_id"):
                station_id_line_idx = i
                old_station_id = line.split("=", 1)[1].strip()
                break

        if station_id_line_idx is None or old_station_id is None:
            print(f"[SKIP] {smet_fp.name}: nessuna riga 'station_id' trovata.")
            continue

        if old_station_id not in map_ingestion_to_id:
            print(
                f"[SKIP] {smet_fp.name}: station_id={old_station_id} NON presente in Excel."
            )
            continue

        new_station_id = map_ingestion_to_id[old_station_id]
        print(f"[OK] {smet_fp.name}: {old_station_id} -> {new_station_id}")

        # aggiorno header
        lines[station_id_line_idx] = f"station_id       = {new_station_id}"

        new_text = "\n".join(lines) + "\n"
        smet_fp.write_text(new_text, encoding="utf-8")

        # rinomino file
        new_fp = smet_fp.with_name(f"{new_station_id}.smet")

        if new_fp.exists() and new_fp != smet_fp:
            print(
                f"[ATTENZIONE] {new_fp.name} esiste già, non rinomino {smet_fp.name}."
            )
            continue

        smet_fp.rename(new_fp)
