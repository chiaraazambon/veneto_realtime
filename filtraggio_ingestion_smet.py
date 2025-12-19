from pathlib import Path
import shutil

# Cartella in cui si trova questo script
ROOT = Path(__file__).resolve().parent

# Cartelle di input
DIR_REF = ROOT / "./smet/APOLLO/smet_12_05"  # contiene i 111 file "di riferimento"
DIR_ALL = (
    ROOT / "./smet/APOLLO/arpav_2025-12-08_2025-12-18"
)  # contiene i 222 file totali

# Cartella di output
OUT_DIR = ROOT / "./smet/APOLLO/arpav_filtrati_per_station_name-2025-12-18"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Cartella riferimento: {DIR_REF}")
print(f"Cartella completa:    {DIR_ALL}")
print(f"Output:               {OUT_DIR}")


def extract_station_name(fp: Path) -> str | None:
    """Legge l'header di un file SMET e restituisce lo station_name (stringa)."""
    with fp.open() as f:
        for line in f:
            line_stripped = line.strip()
            if line_stripped.startswith("[DATA]"):
                break
            if line_stripped.startswith("station_name"):
                # parte dopo '=' senza spazi
                return line_stripped.split("=", 1)[1].strip()
    return None


# Costruisco l'insieme degli station_name presenti nella cartella di riferimento
station_names_ref: set[str] = set()

ref_files = list(DIR_REF.glob("*.smet"))
print(f"Trovati {len(ref_files)} file in {DIR_REF}")

for fp in ref_files:
    name = extract_station_name(fp)
    if name is None:
        print(f"[WARN] Nessuno station_name trovato in {fp.name}")
        continue
    station_names_ref.add(name)

print(
    f"Trovati {len(station_names_ref)} station_name unici nella cartella di riferimento."
)
print("Esempi:", list(station_names_ref)[:5])

# Scorro i file della cartella "grande" e copio solo quelli con station_name presente
all_files = list(DIR_ALL.glob("*.smet"))
print(f"Trovati {len(all_files)} file in {DIR_ALL}")

copied = 0

for fp in all_files:
    name = extract_station_name(fp)
    if name is None:
        print(f"[SKIP] {fp.name}: nessuno station_name nell'header.")
        continue

    if name in station_names_ref:
        dest = OUT_DIR / fp.name
        shutil.copy2(fp, dest)
        copied += 1
        print(f"[COPY] {fp.name} (station_name='{name}') -> {dest.name}")
    else:
        # se dà fastidio troppa stampa, puoi commentare la riga sotto
        print(f"[NO MATCH] {fp.name} (station_name='{name}')")

print(f"\n✅ Copiati {copied} file in {OUT_DIR}")
