"""A small MCP server for inspecting GitHub repositories, cloning them, and creating issues."""

import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path, PureWindowsPath
from typing import Union
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("GitHub learning server")


def validate_repository(owner: str, repo: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo) or repo in {".", ".."}:
        raise ValueError("Enter a valid GitHub owner and repository name.")


@mcp.tool()
def get_repository(owner: str, repo: str) -> dict:
    """Get details about a public GitHub repository by owner and repository name."""
    validate_repository(owner, repo)

    request = Request(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "github-mcp-learning"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            data = json.load(response)
    except HTTPError as exc:
        raise ValueError(f"GitHub returned HTTP {exc.code} for {owner}/{repo}.") from exc
    except (URLError, TimeoutError) as exc:
        raise ValueError("Could not connect to the GitHub API.") from exc

    return {
        "full_name": data["full_name"],
        "description": data["description"],
        "url": data["html_url"],
        "default_branch": data["default_branch"],
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "language": data["language"],
        "open_issues": data["open_issues_count"],
    }


def checkout_path(owner: str, repo: str) -> Path:
    validate_repository(owner, repo)
    if repo.endswith(".") or any(PureWindowsPath(name).is_reserved() for name in (owner, repo)):
        raise ValueError("This owner or repository name cannot be used as a Windows folder.")

    downloads = (Path.home() / "Downloads").resolve()
    destination = downloads / owner / repo
    if destination.resolve() != destination:
        raise ValueError("The checkout path must not use redirected paths.")
    return destination


def git_executable() -> str:
    git = shutil.which("git") or shutil.which(r"C:\Program Files\Git\cmd\git.exe")
    if git is None:
        raise ValueError("Git is required. Install Git and add it to PATH.")
    return git


@mcp.tool()
def clone_repository(owner: str, repo: str) -> dict:
    """Clone a GitHub repository with full history into Downloads/owner/repo using local Git credentials if needed."""
    destination = checkout_path(owner, repo)
    git = git_executable()

    url = f"https://github.com/{owner}/{repo}.git"
    try:
        destination.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError(f"The destination already exists: {destination}") from exc

    try:
        subprocess.run(
            [git, "-c", "http.proactiveAuth=none", "clone", "--", url, str(destination)],
            stdin=subprocess.DEVNULL,
            check=True,
            capture_output=True,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        try:
            destination.rmdir()
        except OSError:
            pass
        raise ValueError(f"Could not clone {owner}/{repo}. Check the repository name, network connection, and GitHub access.") from exc

    return {"full_name": f"{owner}/{repo}", "path": str(destination)}


@mcp.tool()
def list_recent_commits(owner: str, repo: str) -> list[dict[str, str]]:
    """List up to five commits from a public GitHub repository's default branch."""
    validate_repository(owner, repo)
    request = Request(
        f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=5",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "github-mcp-learning"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            commits = json.load(response)
    except HTTPError as exc:
        if exc.code == 409:
            return []
        raise ValueError(f"GitHub returned HTTP {exc.code} for {owner}/{repo}.") from exc
    except (URLError, TimeoutError) as exc:
        raise ValueError("Could not connect to the GitHub API.") from exc

    return [
        {
            "sha": entry["sha"],
            "subject": entry["commit"]["message"].partition("\n")[0],
            "date": entry["commit"]["committer"]["date"],
            "url": entry["html_url"],
        }
        for entry in commits
    ]


@mcp.tool()
def list_open_issues(owner: str, repo: str) -> list[dict[str, Union[int, str]]]:
    """List up to five recently opened issues in a public GitHub repository."""
    validate_repository(owner, repo)
    issues = []
    page = 1
    while len(issues) < 5:
        request = Request(
            f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&sort=created&direction=desc&per_page=30&page={page}",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "github-mcp-learning"},
        )
        try:
            with urlopen(request, timeout=10) as response:
                entries = json.load(response)
                has_next_page = 'rel="next"' in response.headers.get("Link", "")
        except HTTPError as exc:
            raise ValueError(f"GitHub returned HTTP {exc.code} for {owner}/{repo}.") from exc
        except (URLError, TimeoutError) as exc:
            raise ValueError("Could not connect to the GitHub API.") from exc

        issues.extend(
            {"number": entry["number"], "title": entry["title"], "url": entry["html_url"]}
            for entry in entries
            if "pull_request" not in entry
        )
        if not has_next_page:
            break
        page += 1

    return issues[:5]


@mcp.tool()
def list_open_pull_requests(owner: str, repo: str) -> list[dict[str, Union[int, str, bool]]]:
    """List up to five recently opened pull requests, including drafts, in a public GitHub repository."""
    validate_repository(owner, repo)
    request = Request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls?state=open&sort=created&direction=desc&per_page=5",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "github-mcp-learning"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            pull_requests = json.load(response)
    except HTTPError as exc:
        raise ValueError(f"GitHub returned HTTP {exc.code} for {owner}/{repo}.") from exc
    except (URLError, TimeoutError) as exc:
        raise ValueError("Could not connect to the GitHub API.") from exc

    return [
        {"number": pr["number"], "title": pr["title"], "url": pr["html_url"], "draft": pr["draft"]}
        for pr in pull_requests
    ]


def desktop_path() -> Path:
    if os.name == "nt":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
                desktop, _ = winreg.QueryValueEx(key, "Desktop")
            return Path(winreg.ExpandEnvironmentStrings(desktop))
        except OSError:
            pass
    return Path.home() / "Desktop"


@mcp.tool()
def list_local_repositories() -> list[dict[str, str]]:
    """Find Git checkouts under Desktop and Downloads and return their names and paths."""
    repositories = set()
    pending = [root.resolve() for root in (desktop_path(), Path.home() / "Downloads")]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.name == ".git":
                        if entry.is_file(follow_symlinks=False) or entry.is_dir(follow_symlinks=False):
                            repositories.add(directory)
                    elif entry.is_dir(follow_symlinks=False):
                        attributes = entry.stat(follow_symlinks=False)
                        if getattr(attributes, "st_reparse_tag", 0) != stat.IO_REPARSE_TAG_MOUNT_POINT:
                            pending.append(Path(entry.path))
        except OSError:
            continue

    return [{"name": checkout.name, "path": str(checkout)} for checkout in sorted(repositories)]


@mcp.tool()
def create_issue(owner: str, repo: str, title: str, body: str = "") -> dict[str, Union[int, str]]:
    """Post a new GitHub issue using the locally authenticated GitHub CLI."""
    validate_repository(owner, repo)
    if not title.strip():
        raise ValueError("Enter a nonempty issue title.")

    issue = post_github(owner, repo, "issues", {"title": title, "body": body}, "issue")
    return {"number": issue["number"], "title": issue["title"], "url": issue["html_url"]}


@mcp.tool()
def create_pull_request(
    owner: str, repo: str, head: str, base: str, title: str, body: str = ""
) -> dict[str, Union[int, str, bool]]:
    """Create a draft GitHub pull request from an already-pushed head branch into a base branch."""
    validate_repository(owner, repo)
    if not (head.strip() and base.strip() and title.strip()):
        raise ValueError("Enter a source branch, target branch, and pull request title.")

    payload = {"head": head, "base": base, "title": title, "body": body, "draft": True}
    pr = post_github(owner, repo, "pulls", payload, "pull request")
    return {"number": pr["number"], "title": pr["title"], "url": pr["html_url"], "draft": pr["draft"]}


def post_github(owner: str, repo: str, resource: str, payload: dict, label: str) -> dict:
    gh = shutil.which("gh")
    local_app_data = os.environ.get("LOCALAPPDATA")
    if gh is None and local_app_data:
        gh = shutil.which(str(Path(local_app_data) / "Programs" / "GitHub CLI" / "gh.exe"))
    if gh is None:
        raise ValueError("Install GitHub CLI and make gh available on PATH.")

    try:
        result = subprocess.run(
            [gh, "api", "--hostname", "github.com", "--method", "POST", f"repos/{owner}/{repo}/{resource}", "--input", "-"],
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True,
            check=True,
            timeout=30,
            env={**os.environ, "GH_PROMPT_DISABLED": "1"},
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"{label.capitalize()} creation timed out. Check GitHub before retrying to avoid a duplicate.") from exc
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"Could not confirm {label} creation in {owner}/{repo}. Check GitHub before retrying, then verify gh auth status and repository access.") from exc

    return json.loads(result.stdout)


if __name__ == "__main__":
    mcp.run(transport="stdio")
