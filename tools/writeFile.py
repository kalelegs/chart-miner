from __future__ import annotations

import asyncio
from pathlib import Path

from agents import RunContextWrapper

from chart_miner.project import ProjectContext


async def writeFile(ctx: RunContextWrapper[ProjectContext], path: str, content: str) -> str:
    """Write string content to a UTF-8 file under the active project directory."""

    relative_path = Path(path)
    if relative_path.is_absolute():
        raise ValueError("writeFile path must be relative to the active project")

    target_path = (ctx.context.path / relative_path).resolve()
    if not target_path.is_relative_to(ctx.context.path):
        raise ValueError("writeFile path must stay within the active project")

    await asyncio.to_thread(_write_text, target_path, content)
    return f"Wrote {len(content)} characters to {target_path.relative_to(ctx.context.path)}"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
