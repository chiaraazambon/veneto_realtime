#!/usr/bin/env python3
from pathlib import Path
import re
import shutil

SNOW_DIR = Path("./meteo/2_outSNOW")
APOLLO_DIR = Path("./meteo/smet_APOLLO")

TARGET_IDS = {37, 218, 394, 68, 76, 237, 223, 88}
FIELDS_TO_COPY = ["latitude", "longitude", "easting", "northing", "altitude"]

RE_KV = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$")


def parse_header(lines: list[str]) -> dict[str, str]:
    """Parsa le righe tra [HEADER] e [DATA] in un dizionario key->value (string)."""
    header = {}
    in_header = False
    for line in lines:
        s = line.strip()
        if s.upper() == "[HEADER]":
            in_header = True
            continue
        if s.upper() == "[DATA]":
            break
        if not in_header or not s or s.startswith("#"):
            continue
        m = RE_KV.match(line)
        if m:
            k, v = m.group(1), m.group(2)
            header[k.strip()] = v.strip()
    return header


def replace_header_fields(lines: list[str], updates: dict[str, str]) -> list[str]:
    """Sostituisce (o inserisce) le chiavi in header mantenendo il resto invariato."""
    out = []
    in_header = False
    seen = set()

    for line in lines:
        s = line.strip()
        out.append(line)

        if s.upper() == "[HEADER]":
            in_header = True
            continue
        if s.upper() == "[DATA]":
            # prima di [DATA], aggiungi eventuali campi non trovati
            if in_header:
                missing = [k for k in updates.keys() if k not in seen]
                if missing:
                    # inserisci appena prima di [DATA]
                    out.pop()  # rimuove la riga [DATA]
                    for k in missing:
                        out.append(f"{k:<15} = {updates[k]}\n")
                    out.append(line)  # rimetti [DATA]
            in_header = False
            continue

        if in_header:
            m = RE_KV.match(line)
            if m:
                k = m.group(1).strip()
                if k in updates:
                    # sovrascrivi mantenendo stile "key = value"
                    out[-1] = f"{k:<15} = {updates[k]}\n"
                    seen.add(k)

    return out


def find_apollo_file_for_station(station_id: int) -> Path | None:
    # cerca in APOLLO un .smet che contenga "station_id = <id>"
    for fp in APOLLO_DIR.rglob("*.smet"):
        txt = fp.read_text(encoding="utf-8", errors="replace")
        if re.search(
            rf"^\s*station_id\s*=\s*{station_id}\s*$", txt, flags=re.MULTILINE
        ):
            return fp
    return None


def main():
    if not SNOW_DIR.exists():
        raise FileNotFoundError(f"Cartella non trovata: {SNOW_DIR.resolve()}")
    if not APOLLO_DIR.exists():
        raise FileNotFoundError(f"Cartella non trovata: {APOLLO_DIR.resolve()}")

    snow_files = list(SNOW_DIR.rglob("*.smet"))
    if not snow_files:
        print(f"Nessun .smet trovato in {SNOW_DIR}")
        return

    updated = 0
    skipped = 0

    for snow_fp in snow_files:
        lines = snow_fp.read_text(encoding="utf-8", errors="replace").splitlines(
            keepends=True
        )
        snow_header = parse_header(lines)

        sid_str = snow_header.get("station_id")
        if sid_str is None:
            skipped += 1
            print(f"[SKIP] station_id mancante: {snow_fp}")
            continue

        try:
            sid = int(str(sid_str).strip())
        except ValueError:
            skipped += 1
            print(f"[SKIP] station_id non numerico ({sid_str}): {snow_fp}")
            continue

        if sid not in TARGET_IDS:
            continue

        apollo_fp = find_apollo_file_for_station(sid)
        if apollo_fp is None:
            skipped += 1
            print(f"[SKIP] Nessun file APOLLO trovato per station_id={sid}")
            continue

        apollo_lines = apollo_fp.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines(keepends=True)
        apollo_header = parse_header(apollo_lines)

        updates = {}
        missing_in_apollo = []
        for k in FIELDS_TO_COPY:
            if k in apollo_header:
                updates[k] = apollo_header[k]
            else:
                missing_in_apollo.append(k)

        if missing_in_apollo:
            skipped += 1
            print(
                f"[SKIP] In {apollo_fp} mancano campi {missing_in_apollo} (station_id={sid})"
            )
            continue

        # backup
        bak = snow_fp.with_suffix(snow_fp.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(snow_fp, bak)

        new_lines = replace_header_fields(lines, updates)
        snow_fp.write_text("".join(new_lines), encoding="utf-8")

        updated += 1
        print(f"[OK] {snow_fp.name} aggiornato da {apollo_fp.name} (station_id={sid})")

    print(f"\nFatto. Aggiornati: {updated} | Skippati: {skipped}")


if __name__ == "__main__":
    main()
