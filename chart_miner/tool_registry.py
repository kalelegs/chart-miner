from __future__ import annotations

import importlib.util
import inspect
import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Any

from agents import Tool, function_tool
from agents.tool import FunctionTool


ProgressCallback = Callable[[str], None]


def load_tools(
    tools_dir: Path, progress_callback: ProgressCallback | None = None
) -> list[Tool]:
    """Import every public function in tools_dir as an OpenAI Agents SDK tool."""

    if not tools_dir.is_dir():
        raise FileNotFoundError(f"Tools directory not found: {tools_dir}")

    tools: list[Tool] = []
    for module_path in sorted(tools_dir.glob("*.py")):
        if module_path.name.startswith("_"):
            continue

        module = _load_module(module_path)
        tools.extend(_iter_public_tools(module, progress_callback))

    if not tools:
        raise ValueError(f"No tools found in {tools_dir}")

    return tools


def _load_module(module_path: Path) -> ModuleType:
    module_name = f"chart_miner_user_tools.{module_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not import tool module: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _iter_public_tools(
    module: ModuleType, progress_callback: ProgressCallback | None
) -> list[Tool]:
    tools: list[Tool] = []
    for name, value in inspect.getmembers(module):
        if name.startswith("_"):
            continue

        if isinstance(value, FunctionTool):
            tools.append(_with_progress(value, progress_callback))
            continue

        if inspect.isfunction(value) and value.__module__ == module.__name__:
            tools.append(_with_progress(_as_tool(value), progress_callback))

    return tools


def _as_tool(function: Callable[..., Any]) -> Tool:
    return function_tool(function)


def _with_progress(
    tool: Tool, progress_callback: ProgressCallback | None
) -> Tool:
    if progress_callback is None or not isinstance(tool, FunctionTool):
        return tool

    original_on_invoke_tool = tool.on_invoke_tool

    async def on_invoke_tool(ctx: Any, input: str) -> Any:
        params = _read_tool_params(input)
        if tool.name == "getEHR" and isinstance(params, dict) and "id" in params:
            progress_callback(f"Processing ID: {params['id']}")

        progress_callback(
            f"Calling tool {tool.name} with params {_format_tool_params(params)}"
        )
        return await original_on_invoke_tool(ctx, input)

    return replace(tool, on_invoke_tool=on_invoke_tool)


def _read_tool_params(input: str) -> Any:
    try:
        return json.loads(input) if input else {}
    except json.JSONDecodeError:
        return input


def _format_tool_params(params: Any) -> str:
    compact_params = _compact_value(params)
    return json.dumps(compact_params, ensure_ascii=False)


def _compact_value(value: Any) -> Any:
    if isinstance(value, str):
        if len(value) <= 120:
            return value
        return f"{value[:117]}..."

    if isinstance(value, list):
        return [_compact_value(item) for item in value[:10]]

    if isinstance(value, dict):
        return {key: _compact_value(item) for key, item in value.items()}

    return value
