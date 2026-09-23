"""Run ruff and fail only on violations NOT already in .lint-baseline.json.

New code (and any file touched today) must be 100% clean — the baseline
only grandfathers pre-existing debt in untouched legacy scripts (see
CLAUDE.md: "Erreurs pré-existantes -> BASELINE, jamais contourner").

Usage:
    python scripts/check_ruff_baseline.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    baseline_path = ROOT / ".lint-baseline.json"
    baseline = set(json.loads(baseline_path.read_text())["violations"])

    result = subprocess.run(
        ["ruff", "check", ".", "--output-format=json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,  # ruff exits 1 when it finds violations — expected, not an error here
    )
    violations = json.loads(result.stdout or "[]")

    new_violations = []
    for v in violations:
        filename = str(Path(v["filename"]).resolve().relative_to(ROOT))
        key = f"{filename}:{v['code']}"
        if key not in baseline:
            new_violations.append((filename, v["code"], v["location"]["row"], v["message"]))

    if new_violations:
        print(f"{len(new_violations)} nouvelle(s) violation(s) ruff hors baseline :\n")
        for filename, code, row, message in new_violations:
            print(f"  {filename}:{row}: {code} {message}")
        return 1

    print(f"OK — {len(violations)} violation(s) au total, toutes dans .lint-baseline.json ({len(baseline)} entrées grandfathered)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
