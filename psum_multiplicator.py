#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys


def fix_psum_multiplier(
    smet_dir: Path,
    target_value: str = "1",
) -> None:
    if not smet_dir.exists():
        raise FileNotFoundError(f"Directory non trovata: {smet_dir}")

    smet_files = list(smet_dir.glob("*.smet"))
    if not smet_files:
        print(f"---> Nessun file .smet trovato in {smet_dir}")
        return

    for smet_path in smet_files:
        text = smet_path.read_text(encoding="utf-8")
        lines = text.splitlines()

        fields = None
        units_multiplier_idx = None

        for i, line in enumerate(lines):
            line_strip = line.strip()
            if line_strip.startswith("fields"):
                fields = line.split("=", 1)[1].strip().split()
            elif line_strip.startswith("units_multiplier"):
                units_multiplier_idx = i

        if fields is None or units_multiplier_idx is None:
            print(f"{smet_path.name}: fields o units_multiplier non trovati")
            continue

        if "PSUM" not in fields:
            print(f"!! {smet_path.name}: PSUM non presente → skip")
            continue

        psum_idx = fields.index("PSUM")

        key, values = lines[units_multiplier_idx].split("=", 1)
        multipliers = values.strip().split()

        old_val = multipliers[psum_idx]

        if old_val == target_value:
            print(f"✔️  {smet_path.name}: PSUM già = {target_value}")
            continue

        multipliers[psum_idx] = target_value
        new_line = key + "= " + " ".join(multipliers)

        lines[units_multiplier_idx] = new_line
        smet_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"✅ {smet_path.name}: PSUM multiplier {old_val} → {target_value}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fix PSUM units_multiplier in SMET files"
    )
    parser.add_argument(
        "--smet-dir",
        type=Path,
        required=True,
        help="Directory contenente i file .smet",
    )
    parser.add_argument(
        "--value",
        default="1",
        help="Valore target del units_multiplier per PSUM (default: 1)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        fix_psum_multiplier(
            smet_dir=args.smet_dir,
            target_value=args.value,
        )
    except Exception as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
