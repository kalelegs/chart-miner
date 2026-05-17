from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from agents import Agent, Runner
from dotenv import load_dotenv

from chart_miner.llm import configure_llm
from chart_miner.project import ProjectContext, load_project
from chart_miner.tool_registry import load_tools


app = typer.Typer(no_args_is_help=True)


def build_instructions(project: ProjectContext) -> str:
    return "\n\n".join(
        (
            "You are ChartMiner, an LLM agent for extracting clinical research "
            "signals from medical records.",
            "Use the registered tools to retrieve patient IDs and clinical records. "
            "Analyze only the active project data. Be concise, cite patient IDs, "
            "and preserve uncertainty when the notes are ambiguous.",
            f"Active project: {project.name}",
            project.instructions,
        )
    )


async def run_project(project_name: str, max_turns: int) -> str:
    repo_root = Path(__file__).parent.resolve()
    project = load_project(project_name, repo_root)
    tools = load_tools(repo_root / "tools", progress_callback=_print_progress)
    llm_config = configure_llm()
    typer.echo(
        "Using LLM: "
        f"model={llm_config.model or 'OpenAI Agents SDK default'}, "
        f"endpoint={llm_config.endpoint}",
        err=True,
    )

    agent = Agent[ProjectContext](
        name="ChartMiner",
        instructions=build_instructions(project),
        tools=tools,
        model=llm_config.model,
    )

    result = await Runner.run(
        agent,
        input=(
            f"Run the chart mining analysis for project '{project.name}'. "
            "Follow the project instructions exactly."
        ),
        context=project,
        max_turns=max_turns,
    )
    return str(result.final_output)


def _print_progress(message: str) -> None:
    typer.echo(message, err=True)


@app.command()
def main(
    project: Annotated[
        str,
        typer.Option("--project", "-p", help="Project folder path or name under ./projects."),
    ],
    max_turns: Annotated[
        int,
        typer.Option("--max-turns", min=1, help="Maximum OpenAI Agents SDK turns."),
    ] = 20,
) -> None:
    load_dotenv()
    typer.echo(asyncio.run(run_project(project, max_turns)))


if __name__ == "__main__":
    app()
