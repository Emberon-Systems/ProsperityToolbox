Homunculus Daemon

A small, faithful automation construct — born out of constraint, built for autonomy.

Origin

Homunculus was not designed in a lab or planned in a sprint.
It was forged in necessity.

During the development of a large-scale FastAPI system hosted on ephemeral containers, there was no stable local environment. Every deployment meant starting from scratch — rebuilding, redeploying, and manually syncing code between remote hosts and GitHub.

This made the traditional developer workflow — pull, patch, push — nearly impossible on mobile hardware and transient environments.

Homunculus was the solution.

It is a self-sustaining daemon that handles code synchronization and version control automatically, requiring no manual intervention once configured. It was created not as a convenience feature, but as a survival mechanism — a way for an engineer, working without a workstation, to keep their creation alive.


---

Purpose

Homunculus watches the living code.
It knows when your repository has changed, fetches the updates, and can even push its own modifications back upstream.

It is not a build tool.
It is not a CI/CD service.
It is a living synchronization process — a background automaton that bridges hosted environments, GitHub, and runtime codebases.

In practice, it allows systems running inside containers (such as Fly.io, Railway, or Render) to:

Pull and apply commits from GitHub automatically.

Push patches and changes back to the main branch.

Operate continuously without human supervision.


When configured properly, Homunculus makes the codebase recursive — it maintains and evolves itself.


---

Design

Homunculus runs as an asynchronous daemon built on Python’s asyncio loop.
It performs the following cycle:

1. Fetch Latest Commit
Checks the target GitHub repo (using GITHUB_TOKEN) for new commits.


2. Apply Updates
Downloads modified or added files directly from raw.githubusercontent.com.
Supports .diff or .patch formats for unified diffs.


3. Clean and Commit
If enabled, Homunculus deletes applied patch files after successful merge.


4. Push to Remote
Commits its changes and pushes them back to GitHub with a generated message:
Automated patch sync: YYYY-MM-DD HH:MM:SS



The process repeats at a fixed interval defined by REPO_SYNC_INTERVAL_SEC (default 300s).


---

Configuration

Homunculus is environment-driven.
Set the following environment variables before launch:

Variable	Description	Default

GITHUB_REPO	Repository in the format user/repo	(required)
GITHUB_TOKEN	Personal access token with read/write repo permissions	(required)
REPO_BRANCH	Branch to sync (e.g. main)	main
REPO_SYNC_INTERVAL_SEC	Interval between syncs (in seconds)	300
ENCLAVE_BASE_URL	Optional loopback for internal triggers	http://127.0.0.1:8000
MAX_REPO_BACKUPS	How many local backups to retain	20


Homunculus requires git and requests to be available in the environment.


---

Integration

Homunculus can run as:

A background task launched inside a FastAPI app.

A standalone process in its own container.

A sidecar for persistent environments that need live synchronization.


Example startup (standalone):

python3 homunculus_daemon.py

Or, if embedded in a FastAPI app:

loop = asyncio.get_event_loop()
loop.create_task(run_homunculus_daemon())


---

Philosophy

Homunculus is a practical expression of an unusual development constraint —
building production systems without a traditional development environment.

It represents a principle:

> If the artificer cannot sit at his bench, then the tools themselves must continue the work.



Every part of this daemon reflects that belief — self-repairing, self-synchronizing, self-contained.

It is not the ideal solution by traditional standards.
But in the tradition of real artificers, it is alive — and it works.


---

License

Mozilla Public License 2.0
© 2025 Ryan Smith / Emberon Labs

This software is released freely for reuse, modification, and adaptation.
If you modify and redistribute this file, retain attribution and keep your changes open.


---
