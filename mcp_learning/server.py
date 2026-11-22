import json
import os
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Learning MCP")


@mcp.tool()
def save_note(title: str, text: str) -> str:
    """Save a new note using a title made of letters, numbers, underscores, or hyphens."""
    if not title or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in title):
        raise ValueError("Note title must contain only letters, numbers, underscores, or hyphens.")
    if not text.strip():
        raise ValueError("Note text cannot be empty.")
    directory = Path(__file__).resolve().parent.parent / "notes"
    directory.mkdir(exist_ok=True)
    path = directory / f"{title}.txt"
    with path.open("x", encoding="utf-8") as note:
        note.write(text)
    return f"Saved note: {title}"


@mcp.tool()
def read_note(title: str) -> str:
    """Read a saved note by its title."""
    if not title or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in title):
        raise ValueError("Note title must contain only letters, numbers, underscores, or hyphens.")
    path = Path(__file__).resolve().parent.parent / "notes" / f"{title}.txt"
    return path.read_text(encoding="utf-8")


@mcp.tool()
def edit_note(title: str, text: str) -> str:
    """Replace the full text of an existing note."""
    if not title or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in title):
        raise ValueError("Note title must contain only letters, numbers, underscores, or hyphens.")
    if not text.strip():
        raise ValueError("Note text cannot be empty.")
    path = Path(__file__).resolve().parent.parent / "notes" / f"{title}.txt"
    if not path.is_file():
        raise ValueError("Note does not exist.")
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as note:
            temporary_path = Path(note.name)
            note.write(text)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return f"Updated note: {title}"


@mcp.tool()
def save_session(name: str, history: list[dict]) -> str:
    """Save a conversation history as a JSON file in the sessions directory."""
    if not name or name in {".", ".."} or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in name):
        raise ValueError("Session name must contain only letters, numbers, underscores, or hyphens.")
    directory = Path(__file__).resolve().parent.parent / "sessions"
    directory.mkdir(exist_ok=True)
    path = directory / f"{name}.json"
    with path.open("x", encoding="utf-8") as session_file:
        json.dump(history, session_file, indent=2, ensure_ascii=False)
    return str(path)


@mcp.tool()
def multiply(x: int, y: int) -> int:
    """Multiply two integers and return the result."""
    return x * y

@mcp.tool()
def divide(x: int,y: int)-> int:
    """Divide two integers and return the integer result."""
    return x/y

@mcp.tool()
def divide1(x: int,y:int)-> float:
    """divide two integers and return the float result."""
    return x/y


if __name__ == "__main__":
    mcp.run(transport="stdio")

