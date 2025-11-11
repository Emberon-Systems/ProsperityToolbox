"""
Homunculus AutoSync Daemon — Continuous GitHub Pull + Optional Push
========================================================

This daemon periodically checks for new commits in a GitHub repository,
applies file updates or unified diff patches, and (optionally) pushes
local modifications back upstream.

Configuration (environment variables):
--------------------------------------
GITHUB_REPO        → e.g. "username/repo"
GITHUB_TOKEN       → a Personal Access Token with repo read/write rights
REPO_BRANCH        → default "main"
BASE_URL           → optional loopback API base (default "http://127.0.0.1:8000")
REPO_SYNC_INTERVAL_SEC → how often to sync (default 300)
AUTO_PUSH          → "true" to commit + push changes after sync

Dependencies:
-------------
Requires: requests, urllib, asyncio, subprocess
"""

from __future__ import annotations
import os, time, asyncio, json, urllib.request, subprocess, traceback
from datetime import datetime
from pathlib import Path
from typing import Any

# ============================================================
# CONFIG
# ============================================================
INTERVAL = int(os.getenv("REPO_SYNC_INTERVAL_SEC", "300"))
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
BRANCH = os.getenv("REPO_BRANCH", "main")
AUTO_PUSH = os.getenv("AUTO_PUSH", "false").lower() in {"1", "true", "yes"}
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

COMMIT_FILE = DATA_DIR / "runtime_commit_id"

# ============================================================
# HELPERS
# ============================================================

def _headers() -> dict:
    return {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

def _fetch_commit() -> dict[str, Any]:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{BRANCH}"
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def _safe_download(raw_url: str, dest: Path):
    """Handles blob/raw URLs, retries on 404."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    orig = raw_url
    try:
        if "github.com" in raw_url:
            parts = raw_url.split("github.com/")[1]
            parts = parts.replace("/blob/", "/").replace("/raw/", "/").split("?")[0]
            parts = parts.replace("%2F", "/")
            raw_url = f"https://raw.githubusercontent.com/{parts}"
        print(f"[AutoSync] ⬇️ Fetching {raw_url}")
        urllib.request.urlretrieve(raw_url, dest)
    except Exception as e:
        print(f"[AutoSync] ❌ Download failed for {orig}: {e}")

def _git_push_auto():
    """Commit + push automatically after patch sync."""
    try:
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"Automated patch sync: {ts}"
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = GITHUB_TOKEN
        cmds = [
            ["git", "config", "--global", "user.email", "auto@prosperitytoolbox.dev"],
            ["git", "config", "--global", "user.name", "AutoSync Daemon"],
            ["git", "pull", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git", BRANCH, "--rebase"],
            ["git", "add", "."],
            ["git", "commit", "-m", msg],
            ["git", "push", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git", BRANCH],
        ]
        for cmd in cmds:
            subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env, check=False)
        print(f"[AutoSync] 🚀 Auto-pushed: {msg}")
    except Exception as e:
        print(f"[AutoSync] ⚠️ Push failed: {e}")

# ============================================================
# CORE LOOP
# ============================================================

async def run_autosync_daemon():
    print(f"[AutoSync] 🛰️ Daemon online — syncing every {INTERVAL}s from {GITHUB_REPO}@{BRANCH}")

    while True:
        try:
            start = time.time()
            commit = _fetch_commit()
            sha = commit.get("sha")
            prev = COMMIT_FILE.read_text().strip() if COMMIT_FILE.exists() else None

            if sha == prev:
                print(f"[AutoSync] No new commits (sha={sha[:8]})")
            else:
                files = commit.get("files") or []
                for f in files:
                    if f.get("status") in {"added", "modified"}:
                        path = PROJECT_ROOT / f["filename"]
                        _safe_download(f["raw_url"], path)
                        print(f"[AutoSync] ✅ Updated {f['filename']}")
                COMMIT_FILE.write_text(sha)
                print(f"[AutoSync] 🕒 Sync complete ({round(time.time()-start,2)}s)")

                if AUTO_PUSH:
                    _git_push_auto()

        except Exception as e:
            print(f"[AutoSync] ❌ Error: {e}")
            traceback.print_exc()

        await asyncio.sleep(INTERVAL)

# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    try:
        asyncio.run(run_autosync_daemon())
    except KeyboardInterrupt:
        print("[AutoSync] 💤 Stopped manually.")
