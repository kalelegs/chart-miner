from __future__ import annotations

import asyncio
from pathlib import Path

from agents import RunContextWrapper

from chart_miner.project import ProjectContext


async def getIds(ctx: RunContextWrapper[ProjectContext]) -> list[str]:
    """Return patient IDs for the active project.

    The project may define IDs in either `ids` or `ids.txt`; blank lines and
    comment lines starting with `#` are ignored.
    """

    for file_name in ("ids", "ids.txt"):
        ids_path = ctx.context.path / file_name
        if ids_path.is_file():
            contents = await asyncio.to_thread(_read_text, ids_path)
            return [
                line.strip()
                for line in contents.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]

    raise FileNotFoundError(f"No ids or ids.txt file found in {ctx.context.path}")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")
