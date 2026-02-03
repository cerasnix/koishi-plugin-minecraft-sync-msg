#!/usr/bin/env python3
import argparse
import json
import sys
import zipfile
from pathlib import Path


def find_version_jar(version_dir: Path) -> Path | None:
    expected = version_dir / f"{version_dir.name}.jar"
    if expected.is_file():
        return expected
    jars = sorted(version_dir.glob("*.jar"))
    if len(jars) == 1:
        return jars[0]
    if jars:
        return jars[0]
    return None


def load_lang_from_jar(jar_path: Path) -> tuple[dict, int]:
    merged: dict[str, str] = {}
    count = 0
    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            for name in zf.namelist():
                if not name.endswith("lang/zh_cn.json"):
                    continue
                try:
                    with zf.open(name) as fp:
                        data = json.load(fp)
                    if isinstance(data, dict):
                        merged.update(data)
                        count += 1
                except Exception as err:
                    print(f"[warn] failed to read {jar_path}::{name}: {err}", file=sys.stderr)
    except zipfile.BadZipFile:
        print(f"[warn] bad jar: {jar_path}", file=sys.stderr)
    except FileNotFoundError:
        print(f"[warn] jar not found: {jar_path}", file=sys.stderr)
    return merged, count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge zh_cn.json from a Minecraft version jar and mods."
    )
    parser.add_argument(
        "version_dir",
        help="Minecraft version directory (e.g. .../.minecraft/versions/1.21.1-NeoForge)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output JSON file path (default: <version_dir>/mcLang/zh_cn.json)",
    )
    parser.add_argument(
        "--no-mods",
        action="store_true",
        help="Skip mods directory",
    )
    args = parser.parse_args()

    version_dir = Path(args.version_dir).expanduser().resolve()
    if not version_dir.is_dir():
        print(f"[error] version_dir not found: {version_dir}", file=sys.stderr)
        return 1

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else version_dir / "mcLang" / "zh_cn.json"
    )

    merged: dict[str, str] = {}
    sources = 0

    version_jar = find_version_jar(version_dir)
    if version_jar:
        data, count = load_lang_from_jar(version_jar)
        if count:
            merged.update(data)
            sources += count
            print(f"[info] loaded {count} lang file(s) from {version_jar}")
        else:
            print(f"[warn] no zh_cn.json in {version_jar}", file=sys.stderr)
    else:
        print(f"[warn] no version jar found in {version_dir}", file=sys.stderr)

    if not args.no_mods:
        mods_dir = version_dir / "mods"
        if mods_dir.is_dir():
            mod_jars = sorted(mods_dir.glob("*.jar"))
            if not mod_jars:
                print(f"[info] no mod jars in {mods_dir}")
            for jar_path in mod_jars:
                data, count = load_lang_from_jar(jar_path)
                if count:
                    merged.update(data)
                    sources += count
                    print(f"[info] loaded {count} lang file(s) from {jar_path.name}")
        else:
            print(f"[info] mods dir not found: {mods_dir}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(merged, fp, ensure_ascii=False, indent=2)

    print(f"[done] merged {len(merged)} keys from {sources} lang file(s) -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
