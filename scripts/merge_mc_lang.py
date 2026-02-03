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


def load_lang_from_assets(index_path: Path, objects_dir: Path) -> tuple[dict, int]:
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as err:
        print(f"[warn] failed to read assets index {index_path}: {err}", file=sys.stderr)
        return {}, 0

    obj = index.get("objects", {}).get("minecraft/lang/zh_cn.json")
    if not obj or "hash" not in obj:
        print(f"[warn] zh_cn.json not found in assets index {index_path}", file=sys.stderr)
        return {}, 0

    h = obj["hash"]
    file_path = objects_dir / h[:2] / h
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as err:
        print(f"[warn] failed to read assets object {file_path}: {err}", file=sys.stderr)
        return {}, 0

    if not isinstance(data, dict):
        return {}, 0

    return data, 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge zh_cn.json from a Minecraft version jar and mods."
    )
    parser.add_argument(
        "version_dir",
        nargs="?",
        help="Minecraft version directory (e.g. .../.minecraft/versions/1.21.1-NeoForge)",
    )
    parser.add_argument(
        "--base-jar",
        help="Path to vanilla Minecraft jar (e.g. .../.minecraft/versions/1.21.1/1.21.1.jar)",
    )
    parser.add_argument(
        "--assets-index",
        help="Path to assets index JSON (e.g. .../.minecraft/assets/indexes/1.21.1.json)",
    )
    parser.add_argument(
        "--assets-dir",
        help="Path to assets objects directory (e.g. .../.minecraft/assets/objects)",
    )
    parser.add_argument(
        "--mods-dir",
        help="Path to mods directory (e.g. .../.minecraft/versions/1.21.1-NeoForge/mods)",
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

    version_dir = None
    if args.version_dir:
        version_dir = Path(args.version_dir).expanduser().resolve()
        if not version_dir.is_dir():
            print(f"[error] version_dir not found: {version_dir}", file=sys.stderr)
            return 1

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    elif version_dir:
        output_path = version_dir / "mcLang" / "zh_cn.json"
    else:
        print("[error] output path required when no version_dir is provided", file=sys.stderr)
        return 1

    merged: dict[str, str] = {}
    sources = 0

    base_jar = Path(args.base_jar).expanduser().resolve() if args.base_jar else None
    assets_index = Path(args.assets_index).expanduser().resolve() if args.assets_index else None
    assets_dir = Path(args.assets_dir).expanduser().resolve() if args.assets_dir else None
    if base_jar:
        data, count = load_lang_from_jar(base_jar)
        if count:
            merged.update(data)
            sources += count
            print(f"[info] loaded {count} lang file(s) from {base_jar}")
        else:
            print(f"[warn] no zh_cn.json in {base_jar}", file=sys.stderr)
            if assets_index and assets_dir:
                data, count = load_lang_from_assets(assets_index, assets_dir)
                if count:
                    merged.update(data)
                    sources += count
                    print(f"[info] loaded {count} lang file(s) from assets index {assets_index}")
                else:
                    print(f"[warn] no zh_cn.json from assets index {assets_index}", file=sys.stderr)
    elif version_dir:
        version_jar = find_version_jar(version_dir)
        if version_jar:
            data, count = load_lang_from_jar(version_jar)
            if count:
                merged.update(data)
                sources += count
                print(f"[info] loaded {count} lang file(s) from {version_jar}")
            else:
                print(f"[warn] no zh_cn.json in {version_jar}", file=sys.stderr)
                if assets_index and assets_dir:
                    data, count = load_lang_from_assets(assets_index, assets_dir)
                    if count:
                        merged.update(data)
                        sources += count
                        print(f"[info] loaded {count} lang file(s) from assets index {assets_index}")
                    else:
                        print(f"[warn] no zh_cn.json from assets index {assets_index}", file=sys.stderr)
        else:
            print(f"[warn] no version jar found in {version_dir}", file=sys.stderr)
            if assets_index and assets_dir:
                data, count = load_lang_from_assets(assets_index, assets_dir)
                if count:
                    merged.update(data)
                    sources += count
                    print(f"[info] loaded {count} lang file(s) from assets index {assets_index}")
                else:
                    print(f"[warn] no zh_cn.json from assets index {assets_index}", file=sys.stderr)
    elif assets_index and assets_dir:
        data, count = load_lang_from_assets(assets_index, assets_dir)
        if count:
            merged.update(data)
            sources += count
            print(f"[info] loaded {count} lang file(s) from assets index {assets_index}")
        else:
            print(f"[warn] no zh_cn.json from assets index {assets_index}", file=sys.stderr)

    if not args.no_mods:
        mods_dir = Path(args.mods_dir).expanduser().resolve() if args.mods_dir else (version_dir / "mods" if version_dir else None)
        if mods_dir and mods_dir.is_dir():
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
