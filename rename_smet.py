# rinominiamo smet files
from pathlib import Path
import shutil

SMET_DIR = Path(
    "/home/chiara/Desktop/repos/veneto_realtime/veneto_realtime/smet/ultime_ST_da_aggiungere_0"
)
OUT_DIR = Path(
    "/home/chiara/Desktop/repos/veneto_realtime/veneto_realtime/smet/smet_filtrati_rinominati"
)
OUT_DIR.mkdir(exist_ok=True)

for fp in SMET_DIR.glob("*.smet"):
    station_id = None

    with fp.open() as f:
        for line in f:
            line = line.strip()
            if line.lower().startswith("station_id"):
                station_id = line.split("=")[1].strip()
                break

    if station_id is None:
        print(f"⚠️  Nessun station_id trovato in {fp.name}, salto.")
        continue

    new_name = f"{station_id}.smet"
    out_fp = OUT_DIR / new_name

    if out_fp.exists():
        print(f"⚠️  {new_name} già presente in output, salto.")
        continue

    shutil.copy2(fp, out_fp)
    print(f"👉 Copiato e rinominato: {fp.name} → {new_name}")
