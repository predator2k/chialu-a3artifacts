"""Where a coding agent's call directories live.

opencode's `external_directory` guard only denies paths outside the
project the working directory belongs to, and the project of a directory
inside a git repository is that repository's whole worktree: an agent
working in `<repo>/run/<run>/agent/<call>/` could read every run, target
and source file of the repository (the exp3 audit found it doing so).
Outside any git repository the project is the working directory itself,
and every read, glob, grep and list outside it is denied. So a run whose
directory is inside a git repository keeps its agent directories under
`$ADIR_AGENT_ROOT` (default `$TMPDIR/adir_agent_ws`), a root that must not
be inside one, and the run links to it as `<run>/agent_ws`."""
from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Optional


def git_root(path) -> Optional[Path]:
    """The git worktree containing `path` (a `.git` file, or a `.git`
    directory with a HEAD, in it or a parent; an empty `.git` directory is
    no repository to git or opencode), else None."""
    p = Path(path).resolve()
    for d in (p, *p.parents):
        g = d / ".git"
        if g.is_file() or (g / "HEAD").exists():
            return d
    return None


def agent_base() -> Path:
    base = Path(os.environ.get("ADIR_AGENT_ROOT") or Path(tempfile.gettempdir()) / "adir_agent_ws").resolve()
    if git_root(base) is not None:
        raise RuntimeError(f"ADIR_AGENT_ROOT {base} is inside the git repository {git_root(base)}: "
                           "an agent working there could read the whole repository")
    return base


def run_agent_root(run_dir, name: str = "agent") -> Path:
    """The directory a run's agent calls are made under: `<run>/<name>`
    when the run is outside every git repository, else
    `<agent_base>/<run name>-<hash of its path>/<name>`, with `RUN` beside
    it naming the run and the link `<run>/agent_ws` to it."""
    run = Path(run_dir).resolve()
    if git_root(run) is None:
        return run / name
    key = f"{run.name}-{hashlib.sha1(str(run).encode()).hexdigest()[:8]}"
    top = agent_base() / key
    real = top / name
    real.mkdir(parents=True, exist_ok=True)
    marker = top / "RUN"
    if not marker.exists():
        marker.write_text(f"{run}\n")
    link = run / "agent_ws"
    if run.is_dir() and not link.exists() and not link.is_symlink():
        try:
            link.symlink_to(top, target_is_directory=True)
        except OSError:
            pass
    return real


def run_of_agent_dir(work_dir) -> Optional[Path]:
    """The run a directory from `run_agent_root` belongs to, else None."""
    d = Path(work_dir)
    if d.name != "agent":
        return None
    marker = d.parent / "RUN"
    if marker.is_file():
        return Path(marker.read_text().strip())
    return d.parent


def assert_confinable(work_dir) -> None:
    """Refuse an opencode working directory inside a git repository (see the module text)."""
    if os.environ.get("ADIR_ALLOW_GIT_WORKSPACE") == "1":
        return
    root = git_root(work_dir or os.getcwd())
    if root is not None:
        raise RuntimeError(f"opencode working directory {work_dir or os.getcwd()} is inside the git repository "
                           f"{root}: its file tools could read the whole repository (set ADIR_AGENT_ROOT; "
                           "ADIR_ALLOW_GIT_WORKSPACE=1 overrides)")


# One iteration is one prompt, one submission and one evaluation by the harness: the agent runs nothing (bash is
# denied for every method). Every method's solution prompt carries this sentence, word for word, so the budgets
# stay comparable -- and so it says nothing about how the change is handed in, which differs by method (ADIR's
# agents have edit denied and answer with SEARCH/REPLACE blocks; the plain loop's agent edits its files).
SUBMISSION_NOTE = ("Each submission is synthesized and verified once by the harness after you finish; you cannot "
                   "run synthesis, simulation or any tool yourself.")


# A target whose evaluation injects faults into the unit instances (chiALU's int ALU: the fault gate fails a
# design that exposes no or too few unit sites) states that rule too, for every method alike; the launcher sets
# ADIR_UNIT_HIERARCHY_NOTE=1 for such targets only.
UNIT_HIERARCHY_NOTE = ("Keep the design's unit hierarchy: the top module must keep instantiating the unit modules "
                       "of the program (the fault-injection campaign targets every unit instance); a design that "
                       "flattens, renames or removes the unit modules is rejected.")


def with_submission_note(system: str) -> str:
    """`system` ending with SUBMISSION_NOTE (once), and UNIT_HIERARCHY_NOTE when ADIR_UNIT_HIERARCHY_NOTE=1."""
    import os
    notes = [SUBMISSION_NOTE] + ([UNIT_HIERARCHY_NOTE] if os.environ.get("ADIR_UNIT_HIERARCHY_NOTE") == "1" else [])
    for note in notes:
        if note not in system:
            system = f"{system.rstrip()}\n\n{note}\n"
    return system
