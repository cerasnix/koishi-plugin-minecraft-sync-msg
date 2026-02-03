#!/usr/bin/env python3
import argparse
import json
import sys
import zipfile
from pathlib import Path


def scan_jar(jar_path: Path) -> list[dict]:
    results = []
    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                if not name.startswith("data/") or "/advancements/" not in name or not name.endswith(".json"):
                    continue
                try:
                    with zf.open(name) as fp:
                        data = json.load(fp)
                except Exception as err:
                    results.append({
                        "jar": jar_path.name,
                        "path": name,
                        "status": "invalid_json",
                        "reason": str(err),
                    })
                    continue

                display = data.get("display") if isinstance(data, dict) else None
                if not display:
                    results.append({
                        "jar": jar_path.name,
                        "path": name,
                        "status": "no_display",
                        "announce_to_chat": None,
                    })
                    continue

                announce = display.get("announce_to_chat") if isinstance(display, dict) else None
                if announce is False:
                    results.append({
                        "jar": jar_path.name,
                        "path": name,
                        "status": "announce_to_chat_false",
                        "announce_to_chat": False,
                    })
    except zipfile.BadZipFile:
        results.append({
            "jar": jar_path.name,
            "path": "",
            "status": "bad_jar",
            "reason": "bad zip",
        })
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan mod jars for advancements with announce_to_chat=false or missing display."
    )
    parser.add_argument("mods_dir", help="Path to mods directory")
    parser.add_argument("-o", "--output", help="Output JSON report file")
    args = parser.parse_args()

    mods_dir = Path(args.mods_dir).expanduser().resolve()
    if not mods_dir.is_dir():
        print(f"[error] mods dir not found: {mods_dir}", file=sys.stderr)
        return 1

    report = {
        "mods_dir": str(mods_dir),
        "total_jars": 0,
        "flagged": [],
    }

    jars = sorted(mods_dir.glob("*.jar"))
    report["total_jars"] = len(jars)

    for jar_path in jars:
        report["flagged"].extend(scan_jar(jar_path))

    if args.output:
        out_path = Path(args.output).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as fp:
            json.dump(report, fp, ensure_ascii=False, indent=2)
        print(f"[done] report saved to {out_path}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
