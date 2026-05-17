from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectContext(BaseModel):
    """Runtime context shared with all ChartMiner tools."""

    model_config = ConfigDict(frozen=True)

    name: str
    path: Path
    repo_root: Path
    instructions: str = Field(min_length=1)

    @field_validator("path", "repo_root")
    @classmethod
    def resolve_path(cls, value: Path) -> Path:
        return value.expanduser().resolve()

    @property
    def records_path(self) -> Path:
        return self.path / "records"


def resolve_project_path(project: str, repo_root: Path) -> Path:
    candidate = Path(project).expanduser()
    if candidate.exists():
        return candidate.resolve()

    return (repo_root / "projects" / project).resolve()


def load_project(project: str, repo_root: Path) -> ProjectContext:
    project_path = resolve_project_path(project, repo_root)
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project directory not found: {project_path}")

    instructions_path = project_path / "instructions.md"
    if not instructions_path.is_file():
        raise FileNotFoundError(f"Project instructions not found: {instructions_path}")

    instructions = instructions_path.read_text(encoding="utf-8").strip()
    if not instructions:
        raise ValueError(f"Project instructions are empty: {instructions_path}")

    return ProjectContext(
        name=project_path.name,
        path=project_path,
        repo_root=repo_root,
        instructions=instructions,
    )

