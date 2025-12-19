from pathlib import Path

SMET_DIR = Path("./smet/APOLLO/arpav_2025-12-08_2025-12-18")

for smet_path in SMET_DIR.glob("*.smet"):
    text = smet_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    fields = None
    units_multiplier_idx = None

    for i, line in enumerate(lines):
        if line.strip().startswith("fields"):
            fields = line.split("=", 1)[1].strip().split()
        if line.strip().startswith("units_multiplier"):
            units_multiplier_idx = i

    if fields is None or units_multiplier_idx is None:
        print(f"⚠️  {smet_path.name}: fields o units_multiplier non trovati")
        continue

    if "PSUM" not in fields:
        print(f"! {smet_path.name}: PSUM non presente")
        continue

    psum_idx = fields.index("PSUM")

    parts = lines[units_multiplier_idx].split("=", 1)
    multipliers = parts[1].strip().split()

    old_val = multipliers[psum_idx]
    multipliers[psum_idx] = "1"

    lines[units_multiplier_idx] = parts[0] + "= " + " ".join(multipliers)

    smet_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"✅ {smet_path.name}: PSUM multiplier {old_val} → 1")
