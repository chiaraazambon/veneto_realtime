#!/usr/bin/env python3
from pathlib import Path
import argparse
import shutil
import sys


def extract_station_name(fp: Path) -> str | None:
    with fp.open(encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_stripped = line.strip()
            if line_stripped.startswith("[DATA]"):
                break
            if line_stripped.startswith("station_name"):
                return line_stripped.split("=", 1)[1].strip()
    return None


def filter_by_station_name(dir_ref: Path, dir_all: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Cartella riferimento: {dir_ref}")
    print(f"Cartella completa:    {dir_all}")
    print(f"Output:               {out_dir}")
    station_names_ref: set[str] = set()

    ref_files = list(dir_ref.glob("*.smet"))
    print(f"Trovati {len(ref_files)} file in {dir_ref}")

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

    all_files = list(dir_all.glob("*.smet"))
    print(f"Trovati {len(all_files)} file in {dir_all}")

    copied = 0

    for fp in all_files:
        name = extract_station_name(fp)
        if name is None:
            print(f"[SKIP] {fp.name}: nessuno station_name nell'header.")
            continue

        if name in station_names_ref:
            dest = out_dir / fp.name
            shutil.copy2(fp, dest)
            copied += 1
            print(f"-->{fp.name} (station_name='{name}') -> {dest.name}")
        else:
            print(f"{fp.name} (station_name='{name}')")

    print(f"\n✅ Copiati {copied} file in {out_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir-ref",
        type=Path,
        required=True,
        help="Cartella con i file SMET di riferimento (es. 111 file).",
    )
    parser.add_argument(
        "--dir-all",
        type=Path,
        required=True,
        help="Cartella con tutti i file SMET da filtrare (es. 222 file).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Cartella di output dove copiare i file filtrati.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.dir_ref.exists():
        print(f"Directory riferimento non trovata: {args.dir_ref}", file=sys.stderr)
        sys.exit(1)
    if not args.dir_all.exists():
        print(f"Directory completa non trovata: {args.dir_all}", file=sys.stderr)
        sys.exit(1)

    filter_by_station_name(args.dir_ref, args.dir_all, args.out_dir)


if __name__ == "__main__":
    main()
