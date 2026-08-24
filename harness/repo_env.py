"""Load the repository's optional .env without a third-party dependency."""

from __future__ import annotations

import os
import pathlib
import re
import shlex


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load() -> pathlib.Path:
    """Load simple KEY=VALUE lines, preserving values already exported."""
    external = set(os.environ)
    os.environ.setdefault("MGS2_REPO_ROOT", str(REPO_ROOT))
    os.environ.setdefault("MGS2_WORKSPACE", str(WORKSPACE_ROOT))
    path = pathlib.Path(os.environ.get("MGS2_ENV_FILE", REPO_ROOT / ".env"))
    if not path.is_file():
        return path

    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"{path}:{number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        if not _KEY.fullmatch(key):
            raise ValueError(f"{path}:{number}: invalid variable name {key!r}")
        lexer = shlex.shlex(value, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = "#"
        parts = list(lexer)
        parsed = " ".join(parts)
        if key not in external:
            os.environ[key] = os.path.expandvars(parsed)
    return path


def workspace_path(variable: str, relative_default: str) -> pathlib.Path:
    load()
    default = pathlib.Path(os.environ["MGS2_WORKSPACE"]) / relative_default
    return pathlib.Path(os.environ.get(variable, default))
