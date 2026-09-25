"""Tactics (design section 9.5): one tactic per iteration from the
sources of `search.tactics`, the source chosen by a UCB over child
improvement. The composer appends the tactic to the user message and
logs its id through the sidecar the evaluator entry reads."""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Optional

from .archive import Archive
from .instance import Instance
from .registry import TACTIC_SOURCES

SIDECAR = "last_prompt.json"     # the last call's sidecar, for a reader
CALLS_DIR = "calls"              # one sidecar per pending call
SIDECAR_MAX_AGE_S = 24 * 3600


def tried_values(archive: Archive) -> tuple:
    """(values, at_default): per searched variable the json of every value
    an evaluated candidate stood at, from its completed declaration (the
    `decl.*` outputs of the declaration node, the defaults filled in),
    else from its VAR lines; `at_default` names the variables some
    candidate without a completed declaration left undeclared, which is
    its default."""
    seen: dict = {}
    at_default: set = set()
    for r in archive.records():
        m = ((r.get("measurements") or {}).get("declaration") or {}).get("value")
        if isinstance(m, dict) and any(k.startswith("decl.") for k in m):
            for k, v in m.items():
                if k.startswith("decl.") and not isinstance(v, list):
                    seen.setdefault(k[5:], set()).add(json.dumps(v, default=str))
            continue
        vars_ = (r.get("declarations") or {}).get("vars") or {}
        for k, v in vars_.items():
            seen.setdefault(k, set()).add(json.dumps(v, default=str))
        at_default.add(("*", frozenset(vars_)))
    return seen, at_default


def unexplored_values(inst: Instance, archive: Archive, parent=None, limit: int = 12,
                      names=None, rng=None) -> list:
    """Members of finite searched domains no evaluated candidate has
    stood at, an undeclared decision counting as its default; `names`
    restricts the variables (the region in focus); `rng` draws the
    `limit` entries at random rather than in binding order."""
    seen, at_default = tried_values(archive)
    wanted = set(names) if names is not None else None
    out = []
    for b in (inst.bindings.values() if wanted is None else
              [inst.bindings[n] for n in names if n in inst.bindings]):
        if b.time != "search" or not b.domain.finite():
            continue
        members = b.domain.members()
        if len(members) > 64:
            continue
        tried = set(seen.get(b.name, set()))
        if any(b.name not in declared for _, declared in at_default):
            tried.add(json.dumps(b.domain.default(), default=str))
        missing = [m for m in members if json.dumps(m, default=str) not in tried]
        if missing and len(missing) < len(members):
            from .composer import _condition_text
            out.append(f"`{b.name}`: no candidate has tried "
                       + ", ".join(str(m) + _condition_text(inst, b.variable, m) for m in missing[:6]))
        if rng is None and len(out) >= limit:
            break
    if rng is not None and len(out) > limit:
        out = rng.sample(out, limit)
    return out


def worst_constraint(inst: Instance, archive: Archive, parent=None) -> list:
    if not parent:
        return []
    rows = [c for c in parent.get("constraints") or []
            if not c.get("hard") and isinstance(c.get("slack"), (int, float))]
    if not rows:
        return []
    c = min(rows, key=lambda c: c["slack"])
    return [f"the soft constraint `{c['text']}` has the least slack ({c['slack']:.4g}); "
            f"{'it is violated' if c.get('status') == 'violated' else 'keep it satisfied'}"]


BUILTIN_SOURCES = {"unexplored_values": unexplored_values, "worst_constraint": worst_constraint}
# the sources whose tactics propose declaration values, which the `local` operator keeps
DECLARATION_SOURCES = {"unexplored_values"}


def tactic_menu(inst: Instance, archive: Archive, parent: Optional[dict], operator: Optional[str] = None,
                focus_vars: Optional[list] = None, rng=None) -> dict:
    """{source: [tactic text]} of the sources named under `search.tactics`.
    Under the `local` operator a declaration source is left out; under a
    region in focus `unexplored_values` addresses its variables alone."""
    out = {}
    for src in (inst.search.get("tactics") or {}).get("sources") or []:
        if operator == "local" and src in DECLARATION_SOURCES:
            continue
        try:
            if src == "unexplored_values":
                items = unexplored_values(inst, archive, parent, names=focus_vars or None, rng=rng)
            elif src in BUILTIN_SOURCES:
                items = BUILTIN_SOURCES[src](inst, archive, parent)
            else:
                items = TACTIC_SOURCES[src].render(inst, archive, parent)
        except Exception as e:  # noqa: BLE001
            items = [f"(tactic source {src} failed: {e})"]
        items = [str(x) for x in (items or []) if str(x).strip()]
        if items:
            out[src] = items
    return out


def _arm_stats(archive: Archive, arms: list, window: int) -> dict:
    """(count, mean child improvement) per tactic source over the last
    `window` non-seed records."""
    recs = [r for r in archive.records() if not r.get("is_seed")][-window:]
    by_id = {r["candidate_id"]: r for r in archive.records()}
    sums = {a: [0, 0.0] for a in arms}
    for r in recs:
        tid = r.get("tactic_id")
        if not tid:
            continue
        arm = tid.split(":", 1)[0]
        if arm not in sums:
            continue
        parent = by_id.get(r.get("parent_id") or "")
        child = (r.get("score") or {}).get("combined_score")
        if parent is None or child is None:
            continue
        ps = (parent.get("score") or {}).get("combined_score") or 0.0
        sums[arm][0] += 1
        sums[arm][1] += float(child) - float(ps)
    return {a: (n, (s / n if n else 0.0)) for a, (n, s) in sums.items()}


def choose_tactic(inst: Instance, archive: Archive, parent: Optional[dict], rng,
                  operator: Optional[str] = None, focus_vars: Optional[list] = None) -> tuple:
    """(tactic id `<source>:<index>`, text) or (None, None)."""
    menu = tactic_menu(inst, archive, parent, operator, focus_vars, rng)
    if not menu:
        return None, None
    t = inst.search.get("tactics") or {}
    arms = list(menu)
    if t.get("select", "ucb") == "ucb" and len(arms) > 1:
        stats = _arm_stats(archive, arms, int(t.get("window") or 20))
        untried = [a for a in arms if stats[a][0] == 0]
        if untried:
            arm = rng.choice(untried)
        else:
            total = sum(n for n, _ in stats.values())
            arm = max(arms, key=lambda a: stats[a][1] + math.sqrt(2 * math.log(total) / stats[a][0]))
    else:
        arm = rng.choice(arms)
    i = rng.randrange(len(menu[arm]))
    return f"{arm}:{i}", menu[arm][i]


def write_sidecar(run: Path, side: dict) -> Path:
    """The sidecar of one solution call: `<run>/calls/<stamp>-<id>.json`,
    which the evaluator of that call's program takes; `last_prompt.json`
    is a copy of the newest, for a reader."""
    import uuid
    d = Path(run) / CALLS_DIR
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{time.time_ns()}-{uuid.uuid4().hex[:6]}.json"
    text = json.dumps(side, default=str)
    f.write_text(text)
    (Path(run) / SIDECAR).write_text(text)
    return f


def pending_sidecars(run: Path) -> list:
    """[(file, side)] of the calls whose program has not been evaluated,
    oldest first; a sidecar older than a day is dropped."""
    d = Path(run) / CALLS_DIR
    out = []
    for f in sorted(d.glob("*.json")) if d.is_dir() else []:
        try:
            side = json.loads(f.read_text())
        except Exception:  # noqa: BLE001
            continue
        if time.time() - float(side.get("time") or f.stat().st_mtime) > SIDECAR_MAX_AGE_S:
            f.unlink(missing_ok=True)
            continue
        out.append((f, side))
    return out


def _line_distance(program: str, other: str) -> int:
    """The lines of `program` that `other` lacks: a candidate differs
    from its parent in the lines of one edit, from another program in
    the lines of every region that program has differently."""
    return len(set(program.splitlines()) - set(other.splitlines()))


def mark_answered(sidecar: Path, history: Optional[list] = None) -> None:
    """Record in a call's sidecar that the model answered, so the
    evaluator can tell a call that produced a program from one still
    in flight or one that produced nothing.

    `history` is the entries `record_history` left for this call, as
    `{region, edit}` pairs. The note is written when the agent answers,
    before anything has been built, so nothing yet says whether the edit
    survives; the evaluator of this call's candidate carries them into
    the record and a `rollback` node's verdict decides."""
    try:
        d = json.loads(Path(sidecar).read_text())
    except Exception:  # noqa: BLE001
        return
    d["answered"] = time.time()
    if history:
        d["history"] = list(history)
    Path(sidecar).write_text(json.dumps(d, default=str))


def take_sidecar(run: Path, program: Optional[str] = None, inst=None) -> dict:
    """The sidecar of the call that produced `program`, removed from the
    pending ones. The backend evaluates a program right after its call
    answers, so the newest answered call is the one; a call still in
    flight cannot have produced a program, and an older answered call
    whose program never reached the evaluator (an answer without a
    usable change) stays behind until it expires. Among sidecars that
    carry no answer mark (an older ADIR wrote them) the one whose
    parent program the candidate differs from in the fewest lines is
    taken, else the oldest."""
    pend = pending_sidecars(run)
    if not pend:
        return {}
    answered = [(f, side) for f, side in pend if side.get("answered")]
    if answered:
        chosen = max(answered, key=lambda fs: float(fs[1]["answered"]))
    else:
        chosen = pend[0]
        if len(pend) > 1 and program is not None and inst is not None:
            from .composer import program_ext, program_path
            ext = program_ext(inst)
            best = None
            for f, side in pend:
                pp = program_path(run, side.get("parent_id") or "", ext) if side.get("parent_id") else None
                if pp is None or not pp.is_file():
                    continue
                try:
                    d = _line_distance(program, pp.read_text())
                except OSError:
                    continue
                if best is None or d < best[0]:
                    best = (d, (f, side))
            if best is not None:
                chosen = best[1]
    chosen[0].unlink(missing_ok=True)
    return chosen[1]


def read_sidecar(run: Path) -> dict:
    """The newest call's sidecar (`last_prompt.json`), for a reader."""
    f = Path(run) / SIDECAR
    try:
        return json.loads(f.read_text()) if f.is_file() else {}
    except Exception:  # noqa: BLE001
        return {}


def stamp(side: dict) -> dict:
    side = dict(side)
    side.setdefault("time", time.time())
    return side
