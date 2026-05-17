from __future__ import annotations

import asyncio
from pathlib import Path

from agents import RunContextWrapper

from chart_miner.project import ProjectContext


async def getEHR(ctx: RunContextWrapper[ProjectContext], id: str) -> list[str]:
    """Return all EHR documents for a patient ID in the active project."""

    patient_path = ctx.context.records_path / id
    if not patient_path.is_dir():
        raise FileNotFoundError(f"No EHR record directory found for patient ID {id}")

    documents: list[str] = []
    for document_path in sorted(patient_path.iterdir()):
        if document_path.is_file() and not document_path.name.startswith("."):
            contents = await asyncio.to_thread(_read_text, document_path)
            documents.append(contents.strip())

    if not documents:
        raise FileNotFoundError(f"No EHR documents found for patient ID {id}")

    return documents


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")
