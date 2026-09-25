"""The discover role (design section 8.1): before the run, one call
proposes `search.seeds.discover` further plans, each rendered into a
seed by the template's `plan_seed` and evaluated with the other seeds.
The prompt is the system text, the domain's per-round sources with no
parent (the structure table), the template's plan grammar (`plan_doc`)
and the ask; the reply is one fenced json block of named plans."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from .errors import BindError
from .instance import Instance

FILE = "discovered.json"
_FENCE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.S)
_NAME = re.compile(r"^[a-z][a-z0-9_]{0,40}$")


def discovered_plans(run: Optional[Path]) -> dict:
    """{name: plan} from `<run>/discovered.json`, or {}."""
    if run is None:
        return {}
    f = Path(run) / FILE
    if not f.is_file():
        return {}
    d = json.loads(f.read_text())
    return dict(d.get("plans") or {})


DISCOVER_KEYS = ("count", "sharing_only", "keep_families")


def discover_spec(inst: Instance) -> tuple:
    """(count, config) of `search.seeds.discover`: a count of plans, or a
    mapping with `count`, `sharing_only` (the role names sharing alone:
    the `shared` groups and the `components`, no pin, a family only from
    `keep_families`, the ones a kind of sharing itself needs) and
    `keep_families`."""
    d = (inst.search.get("seeds") or {}).get("discover") or 0
    if isinstance(d, dict):
        return int(d.get("count") or 0), dict(d)
    return int(d), {}


def discover_prompt(inst: Instance, run: Path, n: int) -> tuple:
    """(system, user) of the discover call."""
    from .composer import _sources, system_text
    system = system_text(inst)
    tpl = inst.template
    U = ["## The structures and the seeds", ""]
    U += _sources(inst, inst.archive(run), None, static=False)
    named = list((inst.search.get("seeds") or {}).get("generated") or [])
    if named:
        U += [f"The run already has the seeds {', '.join(f'`{x}`' for x in named)}; a plan that "
              "repeats one of them is wasted.", ""]
    U += ["## The plan grammar", "", (tpl.plan_doc or "").strip(), ""]
    cfg = discover_spec(inst)[1]
    if cfg.get("sharing_only"):
        keep = cfg.get("keep_families") or []
        task = (f"Propose exactly {n} plan{'s' if n != 1 else ''}, each complete on its own, that differ in a "
                "sharing decision: which structures share one datapath (the `shared` groups) and the unit-level "
                "`components`. Name no family and no choice"
                + (f" except the family a kind of sharing itself needs ({', '.join(keep)})" if keep else "")
                + "; the numeric stage chooses every family and choice under each sharing plan. Give every plan "
                "a short snake_case name and one sentence (`why`) on what sets it apart.")
    else:
        task = (f"Propose exactly {n} plan{'s' if n != 1 else ''}, each complete on its own, that differ in a "
                "sharing or family decision likely to matter for the goal. Give every plan a short "
                "snake_case name and one sentence (`why`) on what sets it apart.")
    U += ["## Your task", "", task, "",
          "## Response", "",
          "One fenced json block and nothing else:", "", "```json",
          '{"plans": {"<name>": {<a plan in the grammar above>, "why": "one sentence"}, ...}}', "```", ""]
    return system, "\n".join(U)


def parse_plans(text: str) -> dict:
    """{name: plan} from the reply's first json block that parses."""
    blocks = _FENCE.findall(text) or [text]
    for b in blocks:
        try:
            d = json.loads(b)
        except json.JSONDecodeError:
            continue
        if isinstance(d, dict):
            plans = d.get("plans") if isinstance(d.get("plans"), dict) else (
                d.get("strategies") if isinstance(d.get("strategies"), dict) else d)
            return {str(k): v for k, v in plans.items() if isinstance(v, dict)}
    raise BindError("discover", "the reply holds no json block of plans")


def sharing_only(plan: dict, keep_families: list) -> dict:
    """A plan reduced to its sharing: the `shared` groups and the
    `components`, every pin gone, a group's family kept only where it is
    one the sharing itself needs (`keep_families`), the `structures`
    entries gone; what was dropped is recorded under `dropped`."""
    if not isinstance(plan, dict):
        return plan
    out, dropped = {}, []
    shared = {}
    for gname, g in (plan.get("shared") or {}).items():
        if not isinstance(g, dict):
            continue
        h = {k: v for k, v in g.items() if k in ("members", "why")}
        fam = g.get("family")
        if fam and fam in keep_families:
            h["family"] = fam
        elif fam:
            dropped.append(f"{gname}.family={fam}")
        if g.get("pin"):
            dropped.append(f"{gname}.pin={g['pin']}")
        shared[gname] = h
    if shared:
        out["shared"] = shared
    comps = {}
    for slot, c in (plan.get("components") or {}).items():
        if isinstance(c, dict):
            comps[slot] = {k: v for k, v in c.items() if k == "family"}
            if c.get("pin"):
                dropped.append(f"components.{slot}.pin={c['pin']}")
    if comps:
        out["components"] = comps
    if plan.get("structures"):
        dropped.append(f"structures={sorted(plan['structures'])}")
    for k in ("why",):
        if plan.get(k):
            out[k] = plan[k]
    if dropped:
        out["dropped"] = "sharing only: " + "; ".join(str(d) for d in dropped)[:600]
    return out


def discover_plans(inst: Instance, run: Path, ask, log=None) -> dict:
    """Call the discover role, keep the plans `plan_seed` accepts, write
    `<run>/discovered.json`; `ask(system, user) -> text`."""
    run = Path(run)
    n, cfg = discover_spec(inst)
    tpl = inst.template
    if not n or tpl.plan_seed is None:
        return {}
    system, user = discover_prompt(inst, run, n)
    (run / "discover_prompt.md").write_text(f"# System\n\n{system}\n\n# User\n\n{user}\n")
    reply = ask(system, user)
    with open(run / "discover_prompt.md", "a") as f:
        f.write(f"\n\n# Reply\n\n{reply}\n")
    plans = parse_plans(reply)
    if cfg.get("sharing_only"):
        plans = {name: sharing_only(plan, cfg.get("keep_families") or []) for name, plan in plans.items()}
    taken = set((inst.search.get("seeds") or {}).get("generated") or [])
    kept, rejected = {}, {}
    ctx = inst.ctx(run_dir=run)
    for name, plan in plans.items():
        if not _NAME.match(name) or name in taken:
            rejected[name] = "name"
            continue
        try:
            tpl.plan_seed(ctx, name, plan)
        except Exception as e:  # noqa: BLE001
            # a plan whose unit-level entries name what the space lacks keeps its
            # sharing groups, which are the point, without those entries
            if isinstance(plan, dict) and plan.get("components"):
                trimmed = {k: v for k, v in plan.items() if k != "components"}
                try:
                    tpl.plan_seed(ctx, name, trimmed)
                except Exception as e2:  # noqa: BLE001
                    rejected[name] = f"{type(e2).__name__}: {e2}"
                    continue
                trimmed["dropped"] = f"components: {type(e).__name__}: {e}"
                plan = trimmed
            else:
                rejected[name] = f"{type(e).__name__}: {e}"
                continue
        if len(kept) >= n:
            rejected[name] = f"beyond the {n} asked for"
            continue
        kept[name] = plan
    (run / FILE).write_text(json.dumps({"plans": kept, "rejected": rejected, "reply": reply[-4000:]},
                                       indent=1))
    if log:
        log(f"discover: {len(kept)} plan(s) kept ({', '.join(kept) or 'none'})"
            + (f", {len(rejected)} rejected" if rejected else ""))
    return kept


# ---------------------------------------------------------------- the task brief

BRIEF_OUTLINE = """## Objective
## The unit
## What varies
## What the evaluation rewards and rejects
## Pitfalls
## Where to start"""


def brief_prompt(inst: Instance, run: Path) -> tuple:
    """(system, user) of the task-brief call: the facts of the unit as
    the system text states them, the domain's structure table, the run
    file's own task notes, and the outline of the brief."""
    from .composer import _sources, system_text
    system = system_text(inst)
    U = ["## The structures", ""]
    U += _sources(inst, inst.archive(run), None, static=False)
    notes = inst.task_text.strip()
    if notes:
        U += ["## The task as its author wrote it", "", notes, ""]
    U += ["## Your task", "",
          "Write the task brief that the system text's `## Task` section will carry in every round of the "
          "search. Its reader is a hardware engineer who edits one unit module of the program per round "
          "and declares its decisions; the brief tells that engineer what the unit is for, which levers "
          "the search has, what a strong design does on this unit, what the evaluation rejects, and where "
          "the area and the delay are likely to go. Use the facts above and the cards you may read; state "
          "nothing the facts do not support. 200 to 400 words, plain declarative prose, in this outline:",
          "", "```", BRIEF_OUTLINE, "```", "",
          "## Response", "", "The brief alone, as markdown starting with `## Objective`; no preamble.", ""]
    return system, "\n".join(U)


def task_brief(inst: Instance, run: Path, ask, log=None) -> str:
    """Call the discover role once for the task brief and write
    `<run>/task_brief.md` (`task_brief_prompt.md` holds the exchange)."""
    run = Path(run)
    system, user = brief_prompt(inst, run)
    (run / "task_brief_prompt.md").write_text(f"# System\n\n{system}\n\n# User\n\n{user}\n")
    reply = ask(system, user)
    with open(run / "task_brief_prompt.md", "a") as f:
        f.write(f"\n\n# Reply\n\n{reply}\n")
    text = reply.strip()
    if "## Objective" in text:
        text = text[text.index("## Objective"):]
    text = text.replace("```", "").strip()
    if len(text) < 80:
        raise BindError("task.author", "the discover role returned no brief")
    (run / "task_brief.md").write_text(text + "\n")
    if log:
        log(f"task brief: {len(text)} chars from the discover role")
    return text
