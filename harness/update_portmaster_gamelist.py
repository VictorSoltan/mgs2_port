#!/usr/bin/env python3
"""Install the tracked MGS2 metadata into an EmulationStation gamelist.

The current entry's usage fields and any unknown fields are preserved. Only
the three known superseded MGS2 entries are removed; their launchers no longer
exist on the measured device.
"""

from __future__ import annotations

import argparse
import copy
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


CURRENT_PATH = "./MGS2-Substance.sh"
DEPRECATED_PATHS = {
    "./mgs2.sh",
    "./MGS2.sh",
    "./MGS2-GLES.sh",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("gamelist", type=Path)
    parser.add_argument("gameinfo", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def one_metadata_game(path: Path) -> ET.Element:
    root = ET.parse(path).getroot()
    games = root.findall("game")
    if len(games) != 1:
        raise ValueError(f"{path} must contain exactly one <game>")
    game = games[0]
    entry_path = game.findtext("path")
    if entry_path != CURRENT_PATH:
        raise ValueError(
            f"{path} describes {entry_path!r}, expected {CURRENT_PATH!r}"
        )
    required = {"name", "desc", "releasedate", "developer", "publisher", "genre", "image"}
    missing = sorted(tag for tag in required if not game.findtext(tag))
    if missing:
        raise ValueError(f"{path} is missing: {', '.join(missing)}")
    return game


def patch_gamelist(gamelist: Path, gameinfo: Path, output: Path) -> tuple[int, list[str]]:
    tree = ET.parse(gamelist)
    root = tree.getroot()
    if root.tag != "gameList":
        raise ValueError(f"{gamelist} root is <{root.tag}>, expected <gameList>")

    metadata = one_metadata_game(gameinfo)
    current = [g for g in root.findall("game") if g.findtext("path") == CURRENT_PATH]
    if len(current) > 1:
        raise ValueError(f"{gamelist} contains {len(current)} entries for {CURRENT_PATH}")

    removed: list[str] = []
    for game in list(root.findall("game")):
        path = game.findtext("path")
        if path in DEPRECATED_PATHS:
            removed.append(path)
            root.remove(game)

    if current:
        old = current[0]
        old_index = list(root).index(old)
        metadata_tags = {child.tag for child in metadata}
        preserved = [copy.deepcopy(child) for child in old if child.tag not in metadata_tags]
        replacement = copy.deepcopy(metadata)
        replacement.attrib.update(old.attrib)
        replacement.extend(preserved)
        root.remove(old)
        root.insert(old_index, replacement)
    else:
        preserved = []
        root.append(copy.deepcopy(metadata))

    ET.indent(tree, space="\t")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.mgs2-new")
    tree.write(temporary, encoding="utf-8", xml_declaration=True)
    os.replace(temporary, output)
    return len(preserved), removed


def main() -> int:
    args = parse_args()
    output = args.output or args.gamelist
    try:
        preserved, removed = patch_gamelist(args.gamelist, args.gameinfo, output)
        ET.parse(output)
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"update_portmaster_gamelist: {error}", file=sys.stderr)
        return 1

    removed_text = ", ".join(removed) if removed else "none"
    print(
        f"updated {output}: preserved {preserved} existing fields; "
        f"removed deprecated entries: {removed_text}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
