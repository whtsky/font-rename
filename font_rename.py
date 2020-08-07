#!/usr/bin/env python3
import sys
from pathlib import Path
import cchardet as chardet
import os
from fontTools.ttLib import TTFont, TTCollection
from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e as NameTable, NameRecord


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


def decode_name(name: NameRecord):
    try:
        return name.toUnicode().strip()
    except:
        raw = name.toBytes()
        guess = chardet.detect(raw)
        return raw.decode(guess["encoding"]).strip()


def get_current_family_name(table: NameTable):
    for plat_id, enc_id, lang_id in PREFERRED_IDS:
        for name_id in PREFERRED_NAME_IDS:
            family_name_rec = table.getName(
                nameID=name_id, platformID=plat_id, platEncID=enc_id, langID=lang_id
            )
            if family_name_rec:
                return decode_name(family_name_rec)
    for name_id in PREFERRED_NAME_IDS:
        results = []
        for name_record in table.names:
            if name_record.nameID == name_id:
                results.append(decode_name(name_record))
        if results:
            return sorted(results, key=len)[-1]
    raise ValueError("family name not found; can't add suffix")


def get_font_name(font: TTFont):
    return get_current_family_name(font["name"])


def rename_font(filepath: Path):
    try:
        font = TTFont(str(filepath.resolve()))
    except:
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


def unpack_ttc(filepath: Path):
    collection = TTCollection(str(filepath.resolve()))
    for font in collection.fonts:
        ttf_path = filepath.parent / f"{get_font_name(font)}.ttf"
        font.save(ttf_path)
        print(f"{filepath} -> {ttf_path}")
    filepath.unlink()


def handle_file(filepath: Path):
    suffix = filepath.suffix.lower()
    if suffix == ".ttc":
        unpack_ttc(filepath)
    else:
        rename_font(filepath)


def handle_path(path: Path):
    if path.stem.startswith("."):
        return
    if path.is_dir():
        for f in path.iterdir():
            handle_path(f)
    else:
        handle_file(path)


def main():
    if len(sys.argv) == 1:
        print(f"Usage: {sys.argv[0]} [<files>]")
    else:
        for path in sys.argv[1:]:
            handle_path(Path(path))


if __name__ == "__main__":
    main()
