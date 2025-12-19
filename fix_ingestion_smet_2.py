from pathlib import Path
import pandas as pd

# ⚙️ CONFIG
SMET_DIR = Path("./smet/APOLLO/smet_12_18_rinominati")
XLSX_PATH = Path("./smet/APOLLO/rename_id.xlsx")

df = pd.read_excel(XLSX_PATH)

df.columns = [c.strip() for c in df.columns]

# dizionario: INGESTION_ID (stringa) -> station_id (stringa)
map_ingestion_to_id = dict(
    zip(
        df["INGESTION_ID"].astype(str),
        df["station_id"].astype(str),
    )
)

print("Trovate", len(map_ingestion_to_id), "mappature da INGESTION_ID a station_id.")

# 2️Loop su tutti i file .smet nella cartella
for smet_fp in sorted(SMET_DIR.glob("*.smet")):
    text = smet_fp.read_text()

    lines = text.splitlines()
    station_id_line_idx = None
    old_station_id = None

    # Trovo la riga con station_id nell'header
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

    # Aggiorno la riga dell'header
    # (mantengo un po' di spaziatura, ma non è fondamentale)
    lines[station_id_line_idx] = f"station_id       = {new_station_id}"

    new_text = "\n".join(lines)
    smet_fp.write_text(new_text)

    # 6️ Rinomino il file con il nuovo station_id
    new_fp = smet_fp.with_name(f"{new_station_id}.smet")

    # Se esiste già un file con lo stesso nome, avvisa e non sovrascrivere
    if new_fp.exists() and new_fp != smet_fp:
        print(f"[ATTENZIONE] {new_fp.name} esiste già, non rinomino {smet_fp.name}.")
        continue

    smet_fp.rename(new_fp)
