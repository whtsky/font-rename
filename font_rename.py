#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import List

import cchardet as chardet
from fontTools.ttLib import TTCollection
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e as NameTable

PREFERRED_IDS = (
    (3, 1, 0x0C04),
    (3, 1, 0x0804),
    (3, 1, 0x0404),
    (3, 1, 0x0411),
    (1, 0, 0),
)

FAMILY_RELATED_IDS = dict(
    LEGACY_FAMILY=1,
    TRUETYPE_UNIQUE_ID=3,
    FULL_NAME=4,
    POSTSCRIPT_NAME=6,
    PREFERRED_FAMILY=16,
    WWS_FAMILY=21,
)
PREFERRED_NAME_IDS = (
    FAMILY_RELATED_IDS["FULL_NAME"],
    FAMILY_RELATED_IDS["POSTSCRIPT_NAME"],
    FAMILY_RELATED_IDS["PREFERRED_FAMILY"],
    FAMILY_RELATED_IDS["LEGACY_FAMILY"],
)


def decode_name(name: NameRecord) -> str:
    try:
        return name.toUnicode().strip()
    except:
        raw = name.toBytes()
        guess = chardet.detect(raw)
        return raw.decode(guess["encoding"]).strip()


def get_current_family_name(table: NameTable) -> str:
    for plat_id, enc_id, lang_id in PREFERRED_IDS:
        for name_id in PREFERRED_NAME_IDS:
            family_name_rec = table.getName(
                nameID=name_id, platformID=plat_id, platEncID=enc_id, langID=lang_id
            )
            if family_name_rec:
                return decode_name(family_name_rec)
    for name_id in PREFERRED_NAME_IDS:
        results: List[str] = []
        for name_record in table.names:
            if name_record.nameID == name_id:
                results.append(decode_name(name_record))
        if results:
            return sorted(results, key=len)[-1]
    raise ValueError("family name not found; can't add suffix")


def get_font_name(font: TTFont):
    return get_current_family_name(font["name"])


def rename_font(filepath: Path, remove_unparsable: bool) -> None:
    try:
        font = TTFont(str(filepath.resolve()))
    except:
        if remove_unparsable:
            print(f"Failed to parse {filepath}, removing")
            filepath.unlink()
            return
        else:
            print(f"Failed to parse {filepath}, ignore")
            return
    new_path = filepath.parent / f"{get_font_name(font)}{filepath.suffix.lower()}"
    if filepath != new_path:
        if new_path.exists():
            print(f"{new_path} exist, remove: {filepath}")
            filepath.unlink()
        else:
            print(f"{filepath} -> {new_path}")
            filepath.rename(new_path)


def unpack_ttc(filepath: Path) -> None:
    try:
        collection = TTCollection(str(filepath.resolve()))
    except:
        print(f"Failed to parse {filepath}, ignore")
        return
    for font in collection.fonts:
        ttf_path = filepath.parent / f"{get_font_name(font)}.ttf"
        font.save(ttf_path)
        print(f"{filepath} -> {ttf_path}")
    filepath.unlink()


def unpack_otc(filepath: Path) -> None:
    try:
        collection = TTCollection(str(filepath.resolve()))
    except:
        print(f"Failed to parse {filepath}, ignore")
        return
    for font in collection.fonts:
        ttf_path = filepath.parent / f"{get_font_name(font)}.otf"
        font.save(ttf_path)
        print(f"{filepath} -> {ttf_path}")
    filepath.unlink()


def handle_file(filepath: Path, remove_unparsable: bool) -> None:
    suffix = filepath.suffix.lower()
    if suffix == ".ttc":
        unpack_ttc(filepath)
    elif suffix == ".otc":
        unpack_otc(filepath)
    else:
        rename_font(filepath, remove_unparsable=remove_unparsable)


def handle_path(path: Path, remove_unparsable: bool) -> None:
    if path.stem.startswith("."):
        return
    if path.is_dir():
        for f in path.iterdir():
            handle_path(f, remove_unparsable=remove_unparsable)
    else:
        handle_file(path, remove_unparsable=remove_unparsable)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-ru",
        "--remove-unparsable",
        dest="remove_unparsable",
        action="store_true",
        help="Remove unparsable fonts instead of ignore",
    )

    parser.add_argument("files", nargs="+")

    args = parser.parse_args()

    for path in args.files:
        handle_path(Path(path), remove_unparsable=args.remove_unparsable)


if __name__ == "__main__":
    main()
