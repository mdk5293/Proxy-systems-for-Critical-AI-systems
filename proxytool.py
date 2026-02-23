# proxytool.py - Refactored for Type Safety

from __future__ import annotations

import argparse
import json
import math
import re
import statistics as stats
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Iterator, Any

import requests
from tqdm import tqdm  # pip install --upgrade tqdm

VERBOSE: bool = False
QUIET: bool = False

def _log(msg: str, level: str = "info") -> None:
    """Minimal logger with quiet/verbose control."""
    if level == "debug" and not VERBOSE:
        return
    if QUIET and level in ("info", "debug"):
        return
    print(msg)

github_token: str = "<REDACTED_GITHUB_PAT>"

CACHE_DIR: Path = Path(".proxytool_cache")
CACHE_DIR.mkdir(exist_ok=True)

def cache_key(owner: str, repo: str, since: Optional[str], until: Optional[str]) -> str:
    return f"{owner}_{repo}_{since or 'none'}_{until or 'none'}.json"

def load_cached_commits(owner: str, repo: str, since: Optional[str], until: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    path = CACHE_DIR / cache_key(owner, repo, since, until)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data: List[Dict[str, Any]] = json.load(f)
                _log(f"  [Cache hit] Loaded {len(data)} commits", "debug")
                return data
        except Exception as e:
            _log(f"  [Cache error] {e}", "debug")
    return None

def save_cached_commits(owner: str, repo: str, since: Optional[str], until: Optional[str], commits: List[Dict[str, Any]]) -> None:
    path = CACHE_DIR / cache_key(owner, repo, since, until)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(commits, f, indent=None)
        _log(f"  [Cache saved] {len(commits)} commits", "debug")
    except Exception as e:
        _log(f"  [Cache save failed] {e}", "debug")

@dataclass
class CommitRecord:
    repo_id: str
    author: str
    email: str
    date: datetime
    message: str
    files_changed: int
    insertions: int
    deletions: int
    touched_files: List[str] = field(default_factory=list)

    @property
    def lines_changed(self) -> int:
        return (self.insertions or 0) + (self.deletions or 0)

def run_git_log(
    repo: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
    max_commits: Optional[int] = None,
) -> List[CommitRecord]:
    repo_path = Path(repo)
    if not repo_path.exists():
        raise FileNotFoundError(f"Local repo not found: {repo}")

    fmt: str = "@@@%H\x1f%an\x1f%ae\x1f%ad\x1f%s"
    args: List[str] = [
        "git", "-C", str(repo_path), "log", "--no-merges",
        f"--pretty=format:{fmt}", "--date=iso-strict", "--numstat"
    ]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    if max_commits:
        args.append(f"-n{int(max_commits)}")

    try:
        out: str = subprocess.check_output(args, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git log failed: {e.output}")

    recs: List[CommitRecord] = []
    current: Optional[Dict[str, Any]] = None

    def flush() -> None:
        nonlocal current, recs
        if not current:
            return
        dt: datetime = datetime.fromisoformat(current["date"])
        recs.append(CommitRecord(
            repo_id=str(repo_path.resolve()),
            author=current.get("author", "unknown"),
            email=current.get("email", "unknown"),
            date=dt,
            message=current.get("message", ""),
            files_changed=int(current.get("files_changed", 0)),
            insertions=int(current.get("insertions", 0)),
            deletions=int(current.get("deletions", 0)),
            touched_files=current.get("touched_files", []),
        ))
        current = None

    for line in out.splitlines():
        if line.startswith("@@@"):
            flush()
            parts: List[str] = line[3:].split("\x1f")
            if len(parts) < 5:
                continue
            current = {
                "files_changed": 0, "insertions": 0, "deletions": 0,
                "author": parts[1].strip(), "email": parts[2].strip(),
                "date": parts[3].strip(), "message": parts[4].strip(),
                "touched_files": [],
            }
        elif line.strip() and current is not None:
            ins, dels, path = line.split("\t")[:3]
            current["files_changed"] += 1
            current["insertions"] += int(ins) if ins.isdigit() else 0  # '-' for binaries
            current["deletions"] += int(dels) if dels.isdigit() else 0
            current["touched_files"].append(path)
    flush()
    return recs

# ...existing code...
