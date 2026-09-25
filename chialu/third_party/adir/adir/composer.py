"""The prompt composer (design section 7). ADIR owns the prompt
skeleton: the section order, the wording, the response format, the
declaration-block and EVOLVE-BLOCK rules. The content comes from three
sources: the yaml objects (variables, constraints, goal, nodes, seeds),
the evaluation and the archive (the parent, its feedback artifacts and
metrics, the context programs, the tactic, a prior table), and authored
markdown (the instance's task file and the knowledge cards). Users and
domain libraries write no prompt text; a domain registers PromptSources
(data) and TacticSources.

One `prompt_config` (the values of the composer knobs, the operator,
the tactic and the instruction) is sampled per iteration from
`search.prompts.variants` and recorded in the candidate record, so the
effect of every knob is measurable from the archive."""
from __future__ import annotations

import itertools
import json
import math
import os
import random
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional, Sequence

from .archive import Archive
from .declaration import MARK_END, MARK_START, render_block
from .errors import BindError
from .instance import Instance
from .registry import PRIORS, PROMPT_SOURCES

COMPOSER_VERSION = "2"

# the composer knobs: name -> the admitted values (a tuple) or a type
KNOBS: dict = {
    "operator": ("structural", "local", "free"),
    "ambition": ("conservative", "moderate", "aggressive"),
    "show": ("path", "declarations_metrics", "declarations_only", "full"),
    "context_programs": int,
    "feedback_depth": ("none", "summary", "full", "files"),
    "member_focus": ("none", "one", "all"),
    "show_plan_table": bool,
    "knowledge_depth": ("path", "index", "cards"),
    "decisions": ("kinds", "families", "choices"),
}
CARDS_MAX_CHARS = 16000
INDEX_CARDS = 40             # cards listed under knowledge_depth: index (the nearest first)
SHORT_FEEDBACK_CHARS = 240   # a one-line feedback artifact up to this length is its own index line under `files`
DECISION_LINES_MAX = 400     # the decisions slot under `families` or `choices`
DEFAULT_VARIANTS = {"operator": ["structural", "local", "free"]}
MAX_CONFIGS = 256

# the markers of the backend-side template: what SkyDiscover renders is
# parsed out of these sections and re-composed
MARK_CURRENT = "<<ADIR:current>>"
MARK_INSPIRATIONS = "<<ADIR:inspirations>>"
MARK_ATTEMPTS = "<<ADIR:attempts>>"
MARK_END_BACKEND = "<<ADIR:end>>"
_CANDIDATE_ID = re.compile(r"candidate_id:\s*(\S+)")

SKELETON_SYSTEM = ("role", "conduct", "task", "files", "unit", "decisions", "domain_static", "rules", "format",
                   "knowledge", "seeds")
# The user message is ordered by how often a section changes, the steady ones first: a prompt
# cache keeps only the prefix up to the first byte that differs, and with `current` leading the
# way it used to, nothing here was reusable between two calls of one run. The gain is modest --
# the assembled prompt is about 4% of a call's input, the rest being what the agent reads with
# its file tools -- but it costs nothing, and it also reads better: the standing rules, then what
# kind of change to make, then the material this particular round works on.
SKELETON_USER = ("domain", "response", "operator", "ambition", "tactic", "guidance",
                 "current", "context", "history", "backend")

# the ambition knob: how far one round's change reaches (a prompt variant the sampler weighs like the others)
AMBITION = {
    "conservative": (
        "Make one contained change: a rewrite inside one module or one expression, a resized block, a "
        "reordered chain, a removed redundancy. Keep the structure, the interfaces and every declaration "
        "except the one the change needs. A small, verified step is the aim of this round."),
    "moderate": (
        "Rework one unit: re-express a stage of its datapath, merge or split a stage, change a family "
        "or several choices of one structure, or move logic across the boundary between two stages of "
        "the same unit. The rest of the design stays."),
    "aggressive": (
        "Redesign the region: a different algorithm or family, a new sharing of datapaths between "
        "modes or structures, several structures changed together, a new decomposition of the "
        "critical path. A large diff is expected; a candidate that fails a gate still informs the "
        "next round, so do not hold back to stay safe."),
}


# the same knob for a run with nothing to declare (`prompts.declarations: false`): the reach of a change in
# terms of the text alone
AMBITION_PLAIN = {
    "conservative": (
        "Make one contained change: a rewrite inside one module or one expression, a resized block, a "
        "reordered chain, a removed redundancy. Keep the structure and the interfaces. A small, verified "
        "step is the aim of this round."),
    "moderate": (
        "Rework one part of the design: re-express a stage of its datapath, merge or split a stage, "
        "replace the algorithm of one block, or move logic across the boundary between two stages. The "
        "rest of the design stays."),
    "aggressive": (
        "Redesign a large part: a different algorithm, a new sharing of datapaths between modes, several "
        "blocks changed together, a new decomposition of the critical path. A large diff is expected; a "
        "candidate that fails a gate still informs the next round, so do not hold back to stay safe."),
}


def declares(inst: Instance) -> bool:
    """False when the run file says `prompts.declarations: false`: a program with no declaration behind it
    (a generic-evolution control, a hand design), whose prompt then names no decision menu, no declaration
    block and no declared choice; the bindings stay as the template needs them."""
    return (inst.search.get("prompts") or {}).get("declarations", True) is not False


def ambition_section(name: str, plain: bool = False) -> list:
    table = AMBITION_PLAIN if plain else AMBITION
    return [f"## Ambition: {name}", "", table.get(name, table["moderate"]), ""]


# ------------------------------------------------------------- knobs

def defaults(inst: Instance) -> dict:
    ctx = inst.search.get("context") or {}
    # every agent reads files, so the knowledge root is named and the cards stay on disk
    return {"operator": "free", "ambition": "moderate", "show": str(ctx.get("show") or "path"),
            "context_programs": int(ctx.get("programs", 1)), "feedback_depth": "full",
            "member_focus": "none", "show_plan_table": True, "knowledge_depth": "path",
            "decisions": "kinds"}


def variant_space(inst: Instance) -> dict:
    v = (inst.search.get("prompts") or {}).get("variants")
    return {k: list(vals) for k, vals in (v or DEFAULT_VARIANTS).items()}


def check_variants(inst: Instance, path: str = "search.prompts.variants"):
    """Bind-time check: every knob is known and every value admitted."""
    for k, vals in variant_space(inst).items():
        if k not in KNOBS:
            raise BindError(path, f"unknown knob {k!r} (knobs: {sorted(KNOBS)})")
        if not isinstance(vals, list) or not vals:
            raise BindError(f"{path}.{k}", "a non-empty list of values")
        adm = KNOBS[k]
        for val in vals:
            if isinstance(adm, tuple):
                if val not in adm:
                    raise BindError(f"{path}.{k}", f"{val!r} is not one of {adm}")
            elif adm is bool:
                if not isinstance(val, bool):
                    raise BindError(f"{path}.{k}", f"{val!r} is not a boolean")
            elif adm is int:
                if not isinstance(val, int) or isinstance(val, bool) or val < 0:
                    raise BindError(f"{path}.{k}", f"{val!r} is not a non-negative integer")
    if len(configs(inst)) > MAX_CONFIGS:
        raise BindError(path, f"more than {MAX_CONFIGS} knob combinations")


def configs(inst: Instance) -> list:
    """Every knob combination of the variant space, over the defaults."""
    base = defaults(inst)
    space = variant_space(inst)
    keys = sorted(space)
    out = []
    for combo in itertools.product(*[space[k] for k in keys]):
        c = dict(base)
        c.update(dict(zip(keys, combo)))
        out.append(c)
        if len(out) > MAX_CONFIGS:
            break
    return out


def config_key(cfg: dict) -> str:
    return json.dumps({k: cfg[k] for k in sorted(cfg)}, sort_keys=True)


def choose_config(inst: Instance, archive: Archive, rng: random.Random) -> dict:
    """One config per iteration: uniform, or a UCB over the child
    improvement each config produced in the last `window` records."""
    cands = configs(inst)
    p = inst.search.get("prompts") or {}
    if len(cands) == 1 or p.get("sample", "uniform") != "ucb":
        return dict(rng.choice(cands))
    stats = _stats(archive, [config_key(c) for c in cands], int(p.get("window") or 40),
                   lambda r: config_key(r.get("prompt_config") or {}) if r.get("prompt_config") else None)
    untried = [c for c in cands if stats[config_key(c)][0] == 0]
    if untried:
        return dict(rng.choice(untried))
    total = sum(n for n, _ in stats.values())
    best = max(cands, key=lambda c: stats[config_key(c)][1]
               + math.sqrt(2 * math.log(total) / stats[config_key(c)][0]))
    return dict(best)


def _stats(archive: Archive, arms: list, window: int, arm_of) -> dict:
    """(count, mean child improvement) per arm over the last `window`
    non-seed records; `arm_of(record)` names the record's arm."""
    recs = [r for r in archive.records() if not r.get("is_seed")][-window:]
    by_id = {r["candidate_id"]: r for r in archive.records()}
    sums = {a: [0, 0.0] for a in arms}
    for r in recs:
        arm = arm_of(r)
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


# ------------------------------------------------------------- rendering helpers

def _fmt(v) -> str:
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_fmt(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {_fmt(x)}" for k, x in v.items()) + "}"
    return str(v)


def _members(dom, limit: int = 64) -> Optional[list]:
    return dom.members() if dom.finite() and len(dom.members()) <= limit else None


def _block(record: Optional[dict], max_lines: int = 12) -> str:
    """The parent's declaration block: every VAR line, and the domain
    lines when few; a long table (a STRUCTURE line per structure) is
    counted instead, since the file holds it and the domain's table
    renders it."""
    if not record:
        return "(none)"
    d = record.get("declarations") or {}
    lines = [tuple(x) for x in d.get("lines") or []]
    if len(lines) > max_lines:
        kinds: dict = {}
        for k, _ in lines:
            kinds[k] = kinds.get(k, 0) + 1
        summary = ", ".join(f"{n} {k} lines" for k, n in kinds.items())
        return (render_block(d.get("vars") or {}, [], "").strip().replace(f"\n{MARK_END}", "")
                + f"\n... {summary}, unchanged unless the operator says so (in the program file)\n{MARK_END}")
    return render_block(d.get("vars") or {}, lines, "").strip()


def _goal_text(record: dict) -> str:
    """The goal values of a record in words: `none` where a level has no
    value (a hard failure before the goal's node ran)."""
    gv = record.get("goal_values") or []
    if not gv or all(v is None for v in gv):
        return "none"
    return "[" + ", ".join("none" if v is None else _fmt(v) for v in gv) + "]"


def _metrics_lines(record: dict) -> list:
    L = [f"* score {record['score']['combined_score']:.4f}; goal {_goal_text(record)}; "
         f"{'feasible' if record.get('feasible') else 'infeasible'}"
         + (" (hard failure)" if record.get("hard_fail") else "")]
    for n, m in (record.get("measurements") or {}).items():
        v = m.get("value") if isinstance(m, dict) else m
        if isinstance(v, dict):
            if n == "declaration":
                # the declared and defaulted values are the block's business, not a metric
                v = {k: x for k, x in v.items() if not k.startswith("decl.") and k != "defaulted"}
            nums = {k: x for k, x in v.items() if isinstance(x, (int, float)) and not isinstance(x, bool)}
            bools = {k: x for k, x in v.items() if isinstance(x, bool)}
            parts = [f"{k} {x:.4g}" if isinstance(x, float) else f"{k} {x}" for k, x in nums.items()]
            parts += [f"{k} {'yes' if x else 'no'}" for k, x in bools.items()]
            if parts:
                L.append(f"* `{n}`: " + ", ".join(parts[:12]))
    for c in record.get("constraints") or []:
        if c.get("status") != "satisfied":
            L.append(f"* {'HARD' if c.get('hard') else 'soft'} `{c.get('text')}`: {c.get('status')}"
                     + (f" (slack {c['slack']:.4g})" if isinstance(c.get("slack"), (int, float)) else ""))
    return L


def _feedback(record: dict, depth: str, workspace: Optional[Path] = None) -> list:
    """The parent's feedback artifacts: none, a summary (a text cut to
    400 characters at a line end, a table longer than that replaced by
    its entry count), full (cut at 4000) or files (every artifact whole
    under `<workspace>/feedback/<key>.txt`, one index line each in the
    prompt). Under summary and full an artifact longer than the cap is
    written whole to the same file when a call directory is given, and
    the prompt names it."""
    if depth == "none":
        return []
    if depth == "files" and workspace is not None:
        L = []
        for k, v in (record.get("feedback") or {}).items():
            text = v if isinstance(v, str) else json.dumps(v, default=str, indent=1)
            if not text.strip():
                continue
            if len(text) <= SHORT_FEEDBACK_CHARS and "\n" not in text.strip():
                # a one-line artifact costs the agent a read as a file; its text is the index line
                L.append(f"* feedback `{k}`: {text.strip()}")
                continue
            f = feedback_file(workspace, k, text)
            L.append(_index_line(f"feedback/{Path(f).name}", text, f"the parent's feedback `{k}`"))
        if record.get("stderr"):
            text = str(record["stderr"])
            f = feedback_file(workspace, "failure", text)
            L.append(_index_line(f"feedback/{Path(f).name}", text, "the failure detail of the parent's evaluation"))
        return L
    cap = 400 if depth == "summary" else 4000
    L = []
    for k, v in (record.get("feedback") or {}).items():
        if isinstance(v, str):
            text = v
        else:
            text = json.dumps(v, default=str)
            if depth == "summary" and len(text) > cap and isinstance(v, (dict, list)):
                L.append(f"`{k}`: a table of {len(v)} entries (shown under feedback_depth full)")
                continue
        if not text.strip():
            continue
        if len(text) > cap:
            whole = feedback_file(workspace, k, text)
            cut = text.rfind("\n", 0, cap)
            text = text[:cut if cut > cap // 2 else cap] + (f"\n... (the whole text is in `{whole}`)" if whole
                                                             else "\n... (truncated)")
        L.append(f"`{k}`:\n```\n{text}\n```")
    if record.get("stderr") and depth != "none":
        L.append("failure detail:\n```\n" + str(record["stderr"])[:cap] + "\n```")
    return L


def _fence(lang: str, text: str) -> str:
    return f"```{lang}\n{text.rstrip()}\n```"


# ------------------------------------------------------------- the system text

def _searched_groups(inst: Instance) -> list:
    """Searched variables grouped by template: [(template name,
    [bindings])], an indexed family collapsed to one entry. The
    bindings are the materialized ones (the seed's view) for the root
    templates; a template none of whose instances is materialized is
    bound through its first index, so every searched template of the
    tree appears."""
    groups: dict = {}
    seen_templates = set()
    for b in list(inst.bindings.values()):
        if b.time != "search":
            continue
        key = getattr(b.variable, "template_name", None) or b.name
        groups.setdefault(key, []).append(b)
        seen_templates.add(key)
    tree = getattr(inst, "tree", None)
    if tree is not None:
        # the family roots below a non-default family are not in the seed's view:
        # one instance of each is bound so the listing shows every root; the
        # choices under a root are counted from the templates, unbound
        for t in tree.templates:
            if t.name in seen_templates or not (t.name.endswith(".family") or t.when is None):
                continue
            if t.indexed_by and not tree.index_sets.get(t.indexed_by):
                continue
            probe = t.expand(tree.index_sets.get(t.indexed_by, [])[:1])[0] if t.indexed_by else t
            b = inst.bindings.get(probe.name)
            if b is not None and b.time == "search":
                groups.setdefault(t.name, []).append(b)
    return list(groups.items())


def _template_children(inst: Instance) -> dict:
    """The choice templates under each family template, by the parent
    value that opens them: {parent template: {value: [(template name,
    domain)]}}, from the tree (no binding)."""
    tree = getattr(inst, "tree", None)
    if tree is None:
        return {}
    out: dict = {}
    for t in tree.templates:
        w = t.when
        if w is None or t.name.endswith(".family") or w[0] not in tree.by_name:
            continue
        for v in w[1]:
            out.setdefault(w[0], {}).setdefault(_fmt(v), []).append((t.name, t.domain))
    return out


def _pattern(inst: Instance, name: str) -> str:
    b = inst.bindings.get(name)
    return (getattr(b.variable, "template_name", None) or name) if b else name


def _condition_of(var, m):
    """(sibling, allowed, doc) of a member condition on `m`, or None."""
    for k, cond in (getattr(var, "member_when", None) or {}).items():
        if k == m:
            return cond
    return None


def _condition_text(inst: Instance, var, m, pattern: bool = True) -> str:
    """` (when `sibling` is one of [...])` for a conditioned member, else
    ''; the sibling as its template pattern in a template-level listing."""
    cond = _condition_of(var, m)
    if cond is None:
        return ""
    sib, allowed, _doc = cond
    return f" (when `{_pattern(inst, sib) if pattern else sib}` is one of {_fmt(list(allowed))})"


def _member_list(inst: Instance, var, members: list) -> str:
    return ", ".join(_fmt(m) + _condition_text(inst, var, m) for m in members)


def _decided_of(inst: Instance, decl: dict):
    """A `lookup` for the member conditions under a parent's declaration:
    a declared value, else the default the bindings compute under the
    same declaration (a plain dict of bindings knows no siblings' values)."""
    from .variables import ABSENT, binding_lookup
    default_of = getattr(inst.bindings, "default_of", None)
    if default_of is None:
        return binding_lookup(inst.bindings, lambda n: decl[n] if n in decl else ABSENT)
    return binding_lookup(inst.bindings, lambda n: decl[n] if n in decl else default_of(n, decl))


def _decision_lines(inst: Instance, depth: str = "choices") -> list:
    """The searched variables, compact: an indexed family is one line
    with its instance count, a family root lists its members, and the
    choices a member opens are named under it with their domain sizes
    rather than listed as variables of their own (`depth: families`
    omits the choices)."""
    groups = _searched_groups(inst)
    by_key = dict(groups)
    # the choices under a parent value: parent pattern -> value -> [(choice pattern, domain)]
    children: dict = _template_children(inst)
    roots = []
    for key, bs in groups:
        b = bs[0]
        w = b.variable.when
        if w is not None and _pattern(inst, w[0]) in by_key and _pattern(inst, w[0]) != key \
                and not key.endswith(".family"):
            if not children:
                children.setdefault(_pattern(inst, w[0]), {})
                for v in w[1]:
                    children[_pattern(inst, w[0])].setdefault(_fmt(v), []).append((key, b.domain))
        else:
            roots.append((key, bs))
    root_keys = {key for key, _ in roots}
    nested: dict = {}
    if depth == "families":
        # a family whose condition parent is another family root is nested: fold it under its top ancestor
        parent_of = {}
        for key, bs in roots:
            w = bs[0].variable.when
            pk = _pattern(inst, w[0]) if w is not None else None
            parent_of[key] = pk if pk in root_keys and pk != key else None
        top = []
        for key, bs in roots:
            anc = key
            while parent_of.get(anc):
                anc = parent_of[anc]
            if anc == key:
                top.append((key, bs))
            else:
                nested.setdefault(anc, []).append(key)
        roots = top
    if depth == "kinds":
        return _kind_lines(inst, roots, children, root_keys)
    L = []
    for key, bs in roots:
        b = bs[0]
        members = _members(b.domain)
        dom = _member_list(inst, b.variable, members) if members else b.domain.describe()
        cond = ""
        if b.variable.when is not None:
            cond = f" (iff `{_pattern(inst, b.variable.when[0])}` in {_fmt(b.variable.when[1])})"
        head = f"* `{key}`"
        if len(bs) > 1:
            ids = [getattr(x.variable, "index", None) or x.name for x in bs]
            head += f" over {len(bs)} instances ({', '.join(str(i) for i in ids[:6])}{', ...' if len(ids) > 6 else ''})"
        doc = b.variable.doc or ""
        if depth == "families" and len(doc) > 160:
            doc = doc[:157] + "..."
        L.append(f"{head}{cond}: {dom}" + (f". {doc}" if doc else ""))
        if depth == "families":
            n = sum(len(v) + _nested_count(children, v) for v in (children.get(key) or {}).values())
            sub = nested.get(key) or []
            parts = []
            if n:
                parts.append(f"{n} choices under its members")
            if sub:
                parts.append(f"{len(sub)} nested family decisions ({', '.join(k.split('.')[-2] for k in sub[:4])}"
                             f"{', ...' if len(sub) > 4 else ''})")
            if parts:
                L.append("    * opens " + " and ".join(parts) + "; the parent's declaration block names the active ones")
            continue
        for value, choices in (children.get(key) or {}).items():
            names = [f"{c.split('.')[-1]} ({len(d.members()) if d.finite() else d.describe()})"
                     for c, d in choices[:14]]
            names += _nested_names(children, choices[:14])
            more = f", and {len(choices) - 14} more" if len(choices) > 14 else ""
            L.append(f"    * under {value}: " + ", ".join(names) + more)
    if len(L) > DECISION_LINES_MAX:
        L = L[:DECISION_LINES_MAX] + [f"* ... {len(L) - DECISION_LINES_MAX} further lines (the `decisions` knob at "
                                      f"`{depth}` lists every slot; `kinds` counts them)"]
    return L


def _nested_names(children: dict, choices: list) -> list:
    """The choices conditioned on a choice of `choices` rather than on
    the family (a nested choice): `split_string_select (2, under
    string_form=dual_pos_neg_strings)`."""
    out = []
    for c, _d in choices:
        for value, nested in (children.get(c) or {}).items():
            out += [f"{cc.split('.')[-1]} ({len(d2.members()) if d2.finite() else d2.describe()}, "
                    f"under {c.split('.')[-1]}={value})" for cc, d2 in nested]
    return out


def _nested_count(children: dict, choices: list) -> int:
    return sum(len(nested) for c, _d in choices for nested in (children.get(c) or {}).values())


def _kind_lines(inst: Instance, roots: list, children: dict, root_keys: set) -> list:
    """The `kinds` depth: one line per top-level decision, an indexed
    family with its instance count and its members; the choices under
    a member and the slots a member opens are counted, not listed,
    since an undeclared one stands at its default (its card names
    them). A root conditioned on another root's member is folded
    under that root."""
    parent_of = {}
    for key, bs in roots:
        w = bs[0].variable.when
        pk = _pattern(inst, w[0]) if w is not None else None
        parent_of[key] = pk if pk in root_keys and pk != key else None
    nested: dict = {}
    top = []
    for key, bs in roots:
        anc = key
        while parent_of.get(anc):
            anc = parent_of[anc]
        (top if anc == key else nested.setdefault(anc, [])).append((key, bs))
    L = []
    for key, bs in top:
        b = bs[0]
        members = _members(b.domain)
        dom = _member_list(inst, b.variable, members) if members else b.domain.describe()
        head = f"* `{key}`"
        if len(bs) > 1:
            head += f" ({len(bs)} instances)"
        cond = ""
        if b.variable.when is not None and _pattern(inst, b.variable.when[0]) not in root_keys:
            cond = f" (iff `{_pattern(inst, b.variable.when[0])}` in {_fmt(b.variable.when[1])})"
        L.append(f"{head}{cond}: {dom}")
        n = sum(len(v) + _nested_count(children, v) for v in (children.get(key) or {}).values())
        sub = nested.get(key) or []
        parts = []
        if n:
            parts.append(f"{n} choice{'s' if n != 1 else ''} under its members, each at its default unless declared")
        if sub:
            parts.append(f"{len(sub)} nested slots ({', '.join(k.split('.')[-2] for k, _ in sub[:5])}"
                         f"{', ...' if len(sub) > 5 else ''}), each with a family of its own")
        if parts:
            L.append("    * " + "; ".join(parts))
    return L


def knowledge_path(inst: Instance) -> Optional[Path]:
    k = inst.knowledge
    return Path(k) if k else None


def agent_dir(inst: Instance) -> Path:
    """`<run>/agent`, the root of the call directories (design section
    7.7); nothing else of the run is named to the agent."""
    d = Path(inst.agent_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def feedback_file(workspace: Optional[Path], key: str, text: str) -> Optional[str]:
    """Write one feedback artifact under `<workspace>/feedback/<key>.txt`
    and return the path the prompt names, or None without a workspace."""
    if workspace is None:
        return None
    d = Path(workspace) / "feedback"
    d.mkdir(exist_ok=True)
    f = d / (re.sub(r"[^\w.-]+", "_", key) + ".txt")
    f.write_text(text)
    return str(f)


def _index_line(rel: str, text: str, doc: str) -> str:
    """One line of a files index: the path relative to the call's
    directory, the size, what the file holds."""
    n = text.count("\n") + (0 if text.endswith("\n") else 1)
    size = f"{len(text) / 1024:.1f} KB" if len(text) >= 1024 else f"{len(text)} chars"
    return f"* `{rel}` ({size}, {n} line{'s' if n != 1 else ''}): {doc}"


def write_context(workspace: Path, name: str, text: str, doc: str) -> str:
    """Write one context text to `<workspace>/context/<name>.md` and
    return its index line."""
    d = Path(workspace) / "context"
    d.mkdir(exist_ok=True)
    f = d / (re.sub(r"[^\w.:-]+", "_", name) + ".md")
    f.write_text(text.rstrip() + "\n")
    return _index_line(f"context/{f.name}", text, doc)


def call_workspace(inst: Instance, run: Path, tag: str, parent: Optional[dict] = None,
                   context_ids: Sequence[str] = (), ext: str = "", lineage: Optional[set] = None) -> Path:
    """The directory of one model call, `<run>/agent/<stamp>-<id>-<tag>/`,
    the coding agent's working directory for that call: a copy of the
    knowledge base under `knowledge/`, a copy of the parent's program as
    `program<ext>` when there is one, and a copy of each context program
    the round names as `context/<id><ext>`. Copies rather than links:
    the agent's file tools are confined to this directory, and every
    file it can read is the call's own. `lineage` (the ids of the parent
    and its ancestors) keeps in each history file only the entries those
    candidates made; None copies the histories whole."""
    d = agent_dir(inst) / f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}-{tag}"
    d.mkdir(parents=True, exist_ok=True)
    kp = knowledge_path(inst)
    if kp is not None:
        if kp.is_dir():
            shutil.copytree(kp, d / "knowledge", ignore=shutil.ignore_patterns(".*", "__pycache__"))
        else:
            (d / "knowledge").mkdir(exist_ok=True)
    # the histories the prompt and `regions.md` point the agent at; without the copy every read of
    # `history/<region>.md` came back "File not found" and no round saw what an earlier one had tried
    hist = sorted(history_dir(run).glob("*.md")) if history_dir(run).is_dir() else []
    index = lineage_index(run) if lineage is not None else {}
    for f in hist:
        if lineage is None:
            (d / "history").mkdir(exist_ok=True)
            shutil.copyfile(f, d / "history" / f.name)
            continue
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        kept = lineage_history(f.stem, text, lineage, index)
        if kept:
            (d / "history").mkdir(exist_ok=True)
            (d / "history" / f.name).write_text(render_history(kept, history_effects(text)))
    if parent:
        src = program_path(run, parent["candidate_id"], ext)
        if src.is_file():
            shutil.copyfile(src, d / f"program{ext}")
            member_files(inst, d, src.read_text(), ext)
            regions_file(inst, d, src.read_text(), ext)
        if context_ids:
            (d / "context").mkdir(exist_ok=True)
        for cid in context_ids:
            p = program_path(run, cid, ext)
            if p.is_file():
                shutil.copyfile(p, d / "context" / f"{cid}{ext}")
    return d


def regions_file(inst: Instance, d: Path, program: str, ext: str) -> list:
    """`regions.md` of a call directory: the program's mutable regions, one line each.

    The names have to reach the agent or it invents them -- `<region name>` with no referent is
    what filed one program's history under six labels the agent had read off its own variables.
    They go in a file rather than in the prompt for the same reason the histories themselves do:
    the list grows with the artifact while the sentence pointing at it does not, so the prompt is
    the same size on a seed with forty regions as on one with two.

    Each line carries what the agent needs in order to act: the region's name, where it sits in
    the program, the file holding its own text where there is one, and the file holding what has
    already been tried there.
    """
    spans = region_spans(inst, program)
    if not spans:
        return []
    has_members = (d / "members").is_dir()
    lines = ["# The mutable regions of this program", "",
             "These are the names this run uses for the parts you may change. A HISTORY block is",
             "filed under one of them, and what has already been tried in each is in the history",
             "file named beside it -- read that before you change the region again.", "",
             "| region | lines | its text | what has been tried there |",
             "| --- | --- | --- | --- |"]
    for name, first, last in spans:
        own = f"`members/{name}{ext}`" if has_members else f"`program{ext}` lines {first}-{last}"
        lines.append(f"| `{name}` | {first}-{last} | {own} | `history/{name}.md` |")
    (d / "regions.md").write_text("\n".join(lines) + "\n")
    return [name for name, _f, _l in spans]


def member_files(inst: Instance, d: Path, program: str, ext: str) -> list:
    """A family seed's members as files under `members/` of a call
    directory: one file per member with that member's text of the
    program (markers included), so an agent reads one structure's file
    rather than the whole program. The program file stays the text a
    SEARCH block is matched against; the member files are views."""
    from . import artifacts as A
    seeds = inst.seed_artifacts()
    if not seeds or not seeds[0].is_family:
        return []
    try:
        parts = A.split_program(seeds[0], program)
    except BindError:
        return []
    m = d / "members"
    m.mkdir(exist_ok=True)
    out = []
    for name, text in parts.items():
        (m / f"{name}{ext}").write_text(text)
        out.append(name)
    return out


def task_section(inst: Instance) -> str:
    """The task text of the system text: the brief the discover role
    wrote (`<run>/task_brief.md`, under `task.author: discover`) when
    it exists, else the run file's task script rendered, else its task
    context file."""
    brief = Path(inst.run_dir) / "task_brief.md"
    if brief.is_file():
        return brief.read_text().strip()
    script = (inst.task or {}).get("script")
    if script:
        return script_text(inst, str(script), "task").strip()
    return inst.task_text.strip()


def role_section(inst: Instance) -> str:
    """The role text: the run file's `role.script` rendered, else its
    `role.file`; empty without either."""
    script = (getattr(inst, "role", None) or {}).get("script")
    if script:
        return script_text(inst, str(script), "role").strip()
    return (getattr(inst, "role_text", "") or "").strip()


def script_text(inst: Instance, spec: str, what: str) -> str:
    """The text a prompt script renders for this instance: `<path>.py`
    defining `render(instance) -> str`, or `module:function`. Rendered
    once per instance and kept, so every call's system text is the
    same."""
    cache = inst.__dict__.setdefault("_script_texts", {})
    if spec in cache:
        return cache[spec]
    import importlib
    import importlib.util
    if spec.endswith(".py"):
        path = Path(spec)
        mod_spec = importlib.util.spec_from_file_location(f"adir_prompt_{what}_{abs(hash(spec))}", path)
        mod = importlib.util.module_from_spec(mod_spec)
        mod_spec.loader.exec_module(mod)  # type: ignore[union-attr]
        fn = getattr(mod, "render", None)
    else:
        modname, _, fname = spec.partition(":")
        fn = getattr(importlib.import_module(modname), fname, None)
    if fn is None:
        raise BindError(f"{what}.script", f"{spec} defines no render(instance)")
    text = str(fn(inst) or "")
    cache[spec] = text
    return text


def _strip_heading(text: str) -> str:
    """A text without its leading `# ...` heading line (the section
    supplies its own)."""
    text = text.strip()
    if text.startswith("# "):
        text = text.split("\n", 1)[1].strip() if "\n" in text else ""
    return text


def system_text(inst: Instance, seed_records: Optional[list] = None,
                archive: Optional[Archive] = None, cfg: Optional[dict] = None,
                workspace: Optional[Path] = None) -> str:
    """The static part of every prompt (problem.md): the task, the unit,
    the decisions, the static domain sources, the rules, the format,
    the knowledge path, the seeds. With a call directory the unit, the
    decisions, the static sources and the seeds are files under its
    `context/`, and the text carries their index (section 7.7)."""
    tpl = inst.template
    S: dict = {k: [] for k in SKELETON_SYSTEM}
    cfg = cfg or defaults(inst)
    # no title: the same first bytes in every call keep the prefix cache warm, and the role is what
    # the model needs first
    role = _strip_heading(role_section(inst))
    S["role"] = ["## Your role", "", role, ""] if role else []
    task = _strip_heading(task_section(inst))
    S["task"] = ["## Task", "", task, ""] if task else []
    unit = ["## The unit", ""]
    info = inst.elaboration.info or {}
    # the elaboration names the fixed options that do not apply to the bound
    # unit (chiALU: a NaN convention of an integer ALU); they are counted here
    omit = set(info.get("prompt_omit") or [])
    omitted = 0
    import fnmatch
    hidden = list((inst.search.get("prompts") or {}).get("omit_vars") or [])
    for b in inst.bindings.values():
        if any(fnmatch.fnmatchcase(b.name, pat) for pat in hidden):
            continue                       # `prompts.omit_vars`: options the run's prompt does not name
        if b.time == "search" and not declares(inst):
            continue
        if b.time == "fixed":
            if b.name in omit:
                omitted += 1
                continue
            unit.append(f"* `{b.name}` is fixed to {_fmt(b.value)}"
                        + (f": {b.variable.doc}" if b.variable.doc else ""))
        elif b.time == "runtime":
            unit.append(f"* `{b.name}` is selected at run time among {_fmt(b.members)}"
                        + (f": {b.variable.doc}" if b.variable.doc else ""))
    for k, v in info.items():
        if isinstance(v, str) and not any(fnmatch.fnmatchcase(k, pat) for pat in hidden):
            unit.append(f"* {k}: {v}")
    if omitted:
        unit.append(f"* {omitted} further option{'s are' if omitted != 1 else ' is'} fixed at "
                    f"{'values' if omitted != 1 else 'a value'} that do{'' if omitted != 1 else 'es'} "
                    f"not apply to this unit")
    S["unit"] = unit + [""]
    dec = ["## The decisions open to you", "",
           "Each searched variable takes one member per candidate. A candidate declares a "
           "decision with a VAR line only where it departs from the default, which is the "
           "first member listed; an undeclared decision stands at its default. A "
           "conditional variable exists only under the parent value named. A member listed "
           "with a condition (`when` another variable `is one of` some values) is admissible "
           "only while that variable, your decision too, holds one of them; a VAR line naming "
           "it otherwise is rejected, and an undeclared decision whose first member the "
           "condition excludes stands at the first admissible one. An indexed "
           "family has one variable per instance, named with the instance in place of `*`.", ""]
    S["decisions"] = dec + _decision_lines(inst, str(cfg.get("decisions", "choices"))) + [""]
    S["domain_static"] = _sources(inst, archive, None, static=True, workspace=workspace)
    rules = ["## Metrics, constraints, goal", ""]
    for c in inst.constraints:
        if not declares(inst) and c.text.startswith("declaration."):
            continue                       # the empty block's check: nothing the program's author acts on
        rules.append(f"* {'HARD' if c.hard else 'soft'}: `{c.text}`")
    g = inst.goal
    if g.kind == "fidelity":
        rules.append("* goal, by fidelity level (cheap to expensive; the last is the level of record):")
        for i, (d, e) in enumerate(g.levels):
            rules.append(f"    {i + 1}. {d} `{e.text}`")
    elif g.kind == "pareto":
        rules.append("* goal: Pareto over " + ", ".join(f"{d} `{e.text}`" for d, e in g.levels))
    else:
        d, e = g.levels[0]
        rules.append(f"* goal: {d} `{e.text}`")
    rules.append(f"* score rule: {g.score_rule} (the seed scores 1.0; infeasible: {g.infeasible})")
    rules.append("* the nodes that measure, in schedule order:")
    for n in inst.graph.active:
        ni = inst.nodes[n]
        if not declares(inst) and ni.node == "adir.declaration":
            continue
        when = f", runs when {' and '.join(w.text for w in ni.when)}" if ni.when else ""
        rules.append(f"    * `{n}` = {ni.node}{when}" + (" (report only)" if ni.report_only else ""))
    S["rules"] = rules + [""]
    S["conduct"] = ["## Conduct", "",
                    "* Every round returns a changed candidate. Do not conclude that the design cannot be "
                    "improved further, and do not present an analysis of the metrics, the seeds or the "
                    "history as evidence that the current result is at its limit: the archive decides "
                    "what an improvement is, and a rejected attempt is information for the next round.",
                    "* When a change you expected to help did not, say which assumption failed and change "
                    "a different thing; do not restate the current design as the answer.",
                    "* State what the change is expected to move (which metric, which path) and why, "
                    "in the reasoning paragraph, before the change.",
                    "* A round is one change, not a survey: read the feedback files and the few cards the change "
                    "needs, then answer; the call has a time limit and an unanswered round is a lost one.", ""]
    fmt = ["## The declaration block", "",
           "A candidate keeps a block at the top of its first mutable region:", "",
           "```", MARK_START, "VAR <variable>=<member>        one line per decision that departs from its default"]
    for lk in tpl.line_kinds:
        fmt.append(f"{lk.name} ...                  a domain line")
    fmt += [MARK_END, "```", "",
            "Everything outside the EVOLVE-BLOCK markers is fixed; a change there is rejected. "
            "The block and the text must agree: the text realizes what the block declares.", ""]
    S["format"] = fmt
    if not declares(inst):
        S["decisions"] = []
        S["format"] = ["## The program", "", "Everything outside the EVOLVE-BLOCK markers is fixed; a change there "
                       "is rejected.", ""]
    kp = knowledge_path(inst)
    if kp is not None:
        layout = _knowledge_layout(kp)
        S["knowledge"] = ["## Knowledge", "", "The knowledge base is the directory `knowledge/` of this "
                          "call's directory" + (f": {layout}" if layout else "") + ". List it with your file "
                          "tools and read the cards the change needs; each names a mechanism, its trade-offs "
                          "and references. A card path in this text is relative to that directory.", ""]
    seeds = []
    if seed_records:
        seeds = ["## Seeds", "", "| seed | declared decisions | domain lines | goal | score | feasible |",
                 "| --- | --- | --- | --- | --- | --- |"]
        first = seed_records[0]
        first_lines = _line_set(first)
        for r in seed_records:
            dv = (r.get("declarations") or {}).get("vars") or {}
            shown = ", ".join(f"{k}={_fmt(v)}" for k, v in list(dv.items())[:6])
            if len(dv) > 6:
                shown += f", ... ({len(dv)} lines)"
            lines = _line_set(r)
            if r is first:
                kinds: dict = {}
                for k, _t in lines:
                    kinds[k] = kinds.get(k, 0) + 1
                ls = ", ".join(f"{n} {k}" for k, n in kinds.items()) or "none"
            else:
                differ = len(lines - first_lines)
                ls = (f"{differ} of {len(lines)} differ from `{first['seed_name']}`" if differ
                      else f"the same as `{first['seed_name']}`")
            seeds.append(f"| `{r['seed_name']}` | {shown or '(defaults)'} | {ls} | {_goal_text(r)} | "
                         f"{r['score']['combined_score']:.3f} | {'yes' if r.get('feasible') else 'no'} |")
        seeds.append("")
    if seeds and not declares(inst):
        seeds = ["## Seeds", "", "| seed | goal | score | feasible |", "| --- | --- | --- | --- |"] + [
            f"| `{r['seed_name']}` | {_goal_text(r)} | {r['score']['combined_score']:.3f} | "
            f"{'yes' if r.get('feasible') else 'no'} |" for r in seed_records] + [""]
    S["seeds"] = seeds
    if workspace is not None:
        idx = [write_context(workspace, "unit", "\n".join(S["unit"]),
                             "the unit: its fixed options and its run-time selections")]
        if S["decisions"]:
            idx.append(write_context(workspace, "decisions", "\n".join(S["decisions"]),
                                     "the decisions open to you: every searched variable, its members and the choices under them"))
        idx += S["domain_static"]
        if seeds:
            idx.append(write_context(workspace, "seeds", "\n".join(seeds),
                                     "the seeds: their declared decisions, domain lines, goal, score and feasibility"))
        S["files"] = ["## Files of this call", "",
                      "The call's directory, which the message names, holds these files; a path here is relative "
                      "to it. Read the ones the change needs with your file tools; nothing outside the directory is "
                      "readable.", ""] + idx + [""]
        S["unit"] = S["decisions"] = S["domain_static"] = S["seeds"] = []
    return "\n".join(line for k in SKELETON_SYSTEM for line in S[k])


def _knowledge_layout(kp: Path) -> str:
    """One line on what the knowledge base holds: the card count, the
    top-level directories with their counts, the domains under `arch/`.
    The agent lists the directory itself for the file names."""
    cards = [f.relative_to(kp).parts for f in kp.rglob("*.md")] if kp.is_dir() else []
    if not cards:
        return ""
    tops: dict = {}
    for parts in cards:
        tops[parts[0] if len(parts) > 1 else "(top)"] = tops.get(parts[0] if len(parts) > 1 else "(top)", 0) + 1
    shown = ", ".join(f"`{t}/` {n}" if t != "(top)" else f"{n} at the top" for t, n in sorted(tops.items()))
    domains = sorted({parts[1] for parts in cards if len(parts) > 2 and parts[0] == "arch"})
    return (f"{len(cards)} cards, {shown}"
            + (f"; under `arch/` a directory per domain ({', '.join(domains)}) with one card per family" if domains else ""))


def _line_set(record: dict) -> set:
    """The domain lines of a record's block as (kind, tokens) pairs."""
    return {(k, tuple(str(x) for x in t)) for k, t in ((record.get("declarations") or {}).get("lines") or [])}


def _sources(inst: Instance, archive: Optional[Archive], parent: Optional[dict], static: bool,
             focus: Optional[str] = None, workspace: Optional[Path] = None) -> list:
    """The run file's PromptSources of one kind (static or per round),
    rendered: inline text without a call directory, else one file
    `context/<source>.md` each with its index line returned."""
    import inspect
    names = (inst.search.get("prompts") or {}).get("sources") or []
    L = []
    for n in names:
        src = PROMPT_SOURCES.get(n)
        if src is None or src.static != static:
            continue
        try:
            params = inspect.signature(src.render).parameters
            if "focus" in params:
                text = src.render(inst, archive, parent, focus=focus)
            else:
                text = src.render(inst, archive, parent)
        except Exception as e:  # noqa: BLE001
            text = f"(source {n} failed: {e})"
        if text and str(text).strip():
            if workspace is not None:
                L.append(write_context(workspace, n, str(text), src.doc or f"the `{n}` source"))
            else:
                L += [str(text).rstrip(), ""]
    return L


# ------------------------------------------------------------- the operator sections

def _prior_table(inst: Instance, parent: dict, names: list) -> list:
    """The registered prior's prediction for each alternative member of
    the named searched variables, substituted into the parent."""
    prior_name = ((inst.search.get("seeds") or {}).get("rank") or {}).get("prior")
    prior = PRIORS.get(prior_name) if prior_name else (next(iter(PRIORS.values())) if PRIORS else None)
    if prior is None:
        return []
    decl = dict((parent.get("declarations") or {}).get("vars") or {})
    rows = []
    for name in names[:8]:
        b = inst.bindings.get(name)
        members = _members(b.domain, 16) if b else None
        if not members:
            continue
        for m in members:
            try:
                value, lo, hi = prior.predict({**decl, name: m})
            except Exception:  # noqa: BLE001
                continue
            if value in (0.0, float("inf")) and lo == 0.0:
                continue
            mark = " (parent)" if decl.get(name) == m else ""
            rows.append(f"| `{name}` | {_fmt(m)}{mark} | {value:.4g} [{lo:.4g}, {hi:.4g}] |")
    if not rows:
        return []
    return ["Prior `" + prior.name + "` (predicted goal per alternative):", "",
            "| variable | member | prediction [low, high] |", "| --- | --- | --- |"] + rows[:40] + [""]


def _active_searched(inst: Instance, parent: dict) -> list:
    """The active searched variables of the parent, declared or at their
    default, in variable order: the top-level decisions (a family, or a
    variable without a searched parent) first."""
    from .declaration import check_declaration, Declaration
    d = parent.get("declarations") or {}
    decl = Declaration(vars=dict(d.get("vars") or {}), lines=[tuple(x) for x in d.get("lines") or []],
                       present=True)
    try:
        outs = check_declaration(inst, decl, inst.ctx(declaration=decl))
    except Exception:  # noqa: BLE001
        outs = {}
    active = {k[5:] for k in outs if k.startswith("decl.") and not isinstance(outs[k], list)}
    if not active:
        active = set(decl.vars)
    order = [v.name for v in inst.variable_order() if v.name in active
             and inst.bindings.get(v.name) and inst.bindings[v.name].time == "search"]
    tops = [n for n in order if n.endswith(".family") or inst.bindings[n].variable.when is None]
    return tops + [n for n in order if n not in tops]


def regions_of_program(inst: Instance, program: str) -> list:
    """The names of the program's mutable regions (a family's members,
    else the regions the seed artifact's `evolve` names)."""
    return [name for name, _, _ in region_spans(inst, program)]


def region_spans(inst: Instance, program: str) -> list:
    """(name, first line, last line) of every mutable region of the
    program as written (1-based, the marker lines included), so an agent
    reads the region in focus as a slice of the file."""
    from . import artifacts as A
    seeds = inst.seed_artifacts()
    if not seeds:
        return []
    a = seeds[0]
    if a.is_family and not a.evolve:
        marks = [i for i, l in enumerate(program.splitlines()) if A.MEMBER_MARK in l]
        n = program.count("\n") + 1
        out = []
        for k, m in enumerate(a.members):
            if k < len(marks):
                out.append((m, marks[k] + 1, (marks[k + 1] if k + 1 < len(marks) else n)))
        return out
    try:
        names = [name for _, _, name in A.find_regions(A.strip_markers(program), a.evolve, a.language)]
    except Exception:  # noqa: BLE001
        return []
    lines = program.splitlines()
    starts = [i for i, l in enumerate(lines) if A.EVOLVE_START in l]
    ends = [i for i, l in enumerate(lines) if A.EVOLVE_END in l]
    return [(name, starts[k] + 1, ends[k] + 1) for k, name in enumerate(names)
            if k < len(starts) and k < len(ends)]


def choose_focus(inst: Instance, parent: Optional[dict], program: str, cfg: dict,
                 rng: random.Random) -> tuple:
    """(region name, [variable names]) for `member_focus: one`: a region
    the template's focus_map ties to variables when it has one, else
    any region; (None, []) without focus."""
    if cfg.get("member_focus", "none") != "one" or not parent:
        return None, []
    fm = getattr(inst.template, "focus_map", None)
    mapping = {}
    if fm is not None:
        try:
            mapping = dict(fm(inst.ctx(), parent) or {})
        except Exception:  # noqa: BLE001
            mapping = {}
    regions = regions_of_program(inst, program)
    # a template's focus map names the regions that decide variables; a whole-text
    # region (`*`) or a region without variables is no focus when the map has better
    cands = [r for r in regions if mapping.get(r)] or (list(mapping) if mapping else [r for r in regions if r != "*"])
    if not cands:
        return None, []
    region = rng.choice(cands)
    names = [n for n in mapping.get(region, []) if inst.bindings.get(n) and inst.bindings[n].time == "search"]
    return region, names


def _structural(inst: Instance, parent: Optional[dict], cfg: dict, rng: random.Random,
                focus_region: Optional[str] = None, focus_vars: Optional[list] = None) -> list:
    L = ["Change one or more decisions of the parent: edit their VAR lines in the declaration "
         "block (a VAR line only where the value departs from its default) and leave the "
         "region's text as it is. The template re-renders the region whose declaration changed "
         "from its library, so the new family or choice arrives as generated text; a region "
         "whose text you also edit keeps your text instead, so edit the text only where you "
         "want your own realization. Prefer a member the archive has not tried at that "
         "variable.", ""]
    if not parent:
        return L
    names = _active_searched(inst, parent)
    decl = (parent.get("declarations") or {}).get("vars") or {}
    focus = cfg.get("member_focus", "none")
    if focus == "one":
        if focus_region:
            L += [f"Focus: the region `{focus_region}` alone; every other region stays as it is.", ""]
            names = [n for n in focus_vars or [] if n in names] or (focus_vars or names[:1])
        elif names:
            names = [rng.choice(names)]
            L += [f"Focus: change `{names[0]}` alone (its value in the parent is {_fmt(decl.get(names[0]))}).", ""]
    if focus == "all":
        # every structure's family and the choices the parent declares; an undeclared
        # choice stands at its default and its card names it
        shown = [n for n in names if n.endswith(".family") or n in decl]
        hidden = len(names) - len(shown)
    else:
        shown = names if focus != "none" else names[:24]
        hidden = 0
    if shown:
        L.append("Decisions of the parent and their alternatives (the parent's value marked, "
                 "`default` where it is undeclared):")
        L.append("")
        from .variables import member_exclusions
        lookup = _decided_of(inst, decl)
        for n in shown:
            b = inst.bindings[n]
            members = _members(b.domain, 32)
            conditioned = bool(getattr(b.variable, "member_when", None))
            # a conditioned variable's default and its excluded members follow the parent's other values
            cur = decl.get(n, _default_of(inst, n, decl) if conditioned else b.domain.default())
            excl = member_exclusions(b.variable, b.domain, lookup) if conditioned else {}
            tag = "*" if n in decl else " (default)"
            if members:
                L.append(f"* `{n}`: " + ", ".join(f"{_fmt(m)}{tag if m == cur else ''}"
                                                  + _condition_text(inst, b.variable, m, pattern=False)
                                                  + _excluded_text(lookup, b.variable, m, excl)
                                                  for m in members))
            else:
                L.append(f"* `{n}` = {_fmt(cur)}{'' if n in decl else ' (default)'}: {b.domain.describe()}")
        if hidden:
            L.append(f"* ... {hidden} choices under these families at their defaults; their cards name them")
        elif len(names) > len(shown):
            L.append(f"* ... {len(names) - len(shown)} further declared variables")
        L.append("")
    L += _prior_table(inst, parent, shown[:8] if shown else [])
    return L


def _default_of(inst: Instance, name: str, decl: dict):
    """The default of a conditioned variable under the parent's declaration."""
    from .variables import default_under
    default_of = getattr(inst.bindings, "default_of", None)
    if default_of is not None:
        return default_of(name, decl)
    b = inst.bindings[name]
    return default_under(b.variable, b.domain, _decided_of(inst, decl))


def _excluded_text(lookup, var, m, excl: dict) -> str:
    """` (not under the parent's `sibling`=value)` for a member the
    parent's values exclude, else ''."""
    if not any(k == m for k in excl):
        return ""
    sib = _condition_of(var, m)[0]
    time, value = lookup(sib)
    if time == "absent":
        return f" (not here: `{sib}` is absent)"
    if time == "runtime":
        return f" (not under `{sib}` selected at run time among {_fmt(value)})"
    return f" (not under the parent's `{sib}`={_fmt(value)})"


def _local(inst: Instance, parent: Optional[dict], cfg: dict, focus_region: Optional[str] = None) -> list:
    L = ["Keep every declaration of the parent. Rewrite within the mutable region only: the "
         "same families and the same plan, a better realization. Use the feedback of the "
         "current program (the failing check, the critical path, the attribution) to choose "
         "what to rewrite.", ""]
    if focus_region:
        L += [f"Focus: rewrite the region `{focus_region}` alone; every other region stays as it is.", ""]
    return L


def _free(inst: Instance) -> list:
    if not declares(inst):
        return ["Improve the candidate in any way that raises the score under the constraints.", ""]
    return ["Improve the candidate in any way that raises the score under the constraints. "
            "Declarations may change; the block must stay consistent with the text.", ""]


def operator_section(inst: Instance, name: str, parent: Optional[dict], cfg: dict,
                     rng: random.Random, focus_region: Optional[str] = None,
                     focus_vars: Optional[list] = None) -> list:
    override = (inst.search.get("operators") or {}).get("override")
    if override:
        p = Path(override)
        if not p.is_absolute():
            p = inst.base_dir / p
        text = p.read_text()
        text = text.replace("{parent_declarations}", _block(parent))
        return [f"## Operator: {name} (override)", "", text.strip(), ""]
    head = [f"## Operator: {name}", ""]
    if name == "structural":
        return head + _structural(inst, parent, cfg, rng, focus_region, focus_vars)
    if name == "local":
        return head + _local(inst, parent, cfg, focus_region)
    return head + _free(inst)


# ------------------------------------------------------------- instructions

INSTRUCTIONS_FILE = "instructions.jsonl"


def load_instructions(run: Path) -> list:
    f = Path(run) / INSTRUCTIONS_FILE
    out = []
    if f.is_file():
        for line in f.read_text().splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def append_instruction(run: Path, text: str, origin_iteration: int, source: str) -> dict:
    row = {"id": f"ins-{uuid.uuid4().hex[:8]}", "text": text.strip(), "origin_iteration": origin_iteration,
           "source": source, "created": time.time()}
    with open(Path(run) / INSTRUCTIONS_FILE, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def instruction_stats(archive: Archive, ids: list, window: int) -> dict:
    # a record the composer produced without an instruction is the `none` arm; a
    # record with no prompt config (a seed's child evaluated by hand) is no arm
    return _stats(archive, ids + ["none"], window,
                  lambda r: r.get("instruction_id") or ("none" if r.get("prompt_config") else None))


def choose_instruction(inst: Instance, run: Path, archive: Archive, rng: random.Random) -> Optional[dict]:
    """The instruction for this iteration: a UCB over the rows (and no
    instruction) by child improvement in the last `window` records."""
    cfg = inst.search.get("instructions") or {}
    if not cfg.get("enabled"):
        return None
    rows = load_instructions(run)
    seed = cfg.get("seed")
    if not rows and seed:
        rows = [append_instruction(run, str(seed), 0, "seed")]
    if not rows:
        return None
    ids = [r["id"] for r in rows]
    if cfg.get("select", "ucb") == "ucb":
        stats = instruction_stats(archive, ids, int(cfg.get("window") or 40))
        untried = [i for i in ids + ["none"] if stats[i][0] == 0]
        if untried:
            pick = rng.choice(untried)
        else:
            total = sum(n for n, _ in stats.values())
            pick = max(ids + ["none"], key=lambda i: stats[i][1] + math.sqrt(2 * math.log(total) / stats[i][0]))
    else:
        pick = rng.choice(ids + ["none"])
    if pick == "none":
        return None
    return next(r for r in rows if r["id"] == pick)


def reflection_prompt(inst: Instance, run: Path, archive: Archive, current: Optional[dict]) -> str:
    """The reflective mutation (GEPA's form): the task, the current
    instruction, the recent parent-child pairs with their feedback and
    score deltas, and the request for an improved instruction."""
    cfg = inst.search.get("instructions") or {}
    sources = list((cfg.get("propose") or {}).get("from") or ["feedback", "declarations", "metrics"])
    recs = [r for r in archive.records() if not r.get("is_seed")]
    by_id = {r["candidate_id"]: r for r in archive.records()}
    L = ["# Improve the guidance for the next candidates", "",
         "The solution model rewrites a candidate each iteration under the guidance below. "
         "Its children were evaluated; each pair shows the parent's declarations, the child's, "
         "the score delta and the evaluator's feedback. Write an improved guidance: what to "
         "change, what to avoid, in the domain's terms, at most "
         f"{int(cfg.get('max_chars') or 1200)} characters. Answer with the guidance alone inside "
         "one fenced block.", "",
         "## Current guidance", "", "```", (current or {}).get("text", "(none)"), "```", ""]
    L += ["## Recent iterations", ""]
    for r in recs[-8:]:
        parent = by_id.get(r.get("parent_id") or "")
        ps = (parent.get("score") or {}).get("combined_score") if parent else None
        cs = r["score"]["combined_score"]
        L.append(f"### {r['candidate_id']} (parent {r.get('parent_id')}; score {cs:.4f}"
                 + (f", delta {cs - ps:+.4f}" if isinstance(ps, (int, float)) else "") + ")")
        if "declarations" in sources:
            L += ["parent declarations:", "```", _block(parent), "```", "child declarations:", "```",
                  _block(r), "```"]
        if "metrics" in sources:
            L += _metrics_lines(r)
        if "feedback" in sources:
            L += _feedback(r, "summary")
        L.append("")
    return "\n".join(L)


def maybe_propose(inst: Instance, run: Path, archive: Archive, ask, log=None) -> Optional[dict]:
    """Every `propose.every` non-seed records, ask the `propose.role`
    model for an improved instruction and append it as a row."""
    cfg = inst.search.get("instructions") or {}
    prop = cfg.get("propose") or {}
    if not cfg.get("enabled") or not prop:
        return None
    every = int(prop.get("every") or 10)
    recs = [r for r in archive.records() if not r.get("is_seed")]
    rows = load_instructions(run)
    last = max((r.get("origin_iteration", 0) for r in rows if r.get("source") == "proposed"), default=0)
    if len(recs) < every or len(recs) - last < every:
        return None
    current = None
    if rows:
        stats = instruction_stats(archive, [r["id"] for r in rows], int(cfg.get("window") or 40))
        current = max(rows, key=lambda r: (stats[r["id"]][1], stats[r["id"]][0]))
    prompt = reflection_prompt(inst, run, archive, current)
    try:
        answer = ask(str(prop.get("role") or "strategy"), "You improve the guidance of a design search.", prompt)
    except Exception as e:  # noqa: BLE001
        if log:
            log(f"instruction proposal failed: {e}")
        return None
    m = re.search(r"```[a-z]*\n(.*?)```", answer or "", re.S)
    text = (m.group(1) if m else (answer or "")).strip()
    if not text:
        return None
    text = text[: int(cfg.get("max_chars") or 1200)]
    row = append_instruction(run, text, len(recs), "proposed")
    if log:
        log(f"instruction {row['id']} proposed at iteration {len(recs)}")
    return row


# ------------------------------------------------------------- the backend message

def parse_backend(user_message: str) -> dict:
    """What the backend's rendering carries: the parent's id, the
    inspiration ids, the previous attempts text, the failed attempts of
    a retry, and the sections the backend appended after the template."""
    out = {"parent_id": None, "inspiration_ids": [], "attempts": "", "failed": "", "backend": "",
           "parent_text": None}
    if MARK_CURRENT not in user_message:
        return out

    def section(a, b):
        i = user_message.find(a)
        j = user_message.find(b, i + len(a)) if i >= 0 else -1
        return user_message[i + len(a):j] if i >= 0 and j >= 0 else ""
    cur = section(MARK_CURRENT, MARK_INSPIRATIONS)
    insp = section(MARK_INSPIRATIONS, MARK_ATTEMPTS)
    att = section(MARK_ATTEMPTS, MARK_END_BACKEND)
    m = _CANDIDATE_ID.search(cur)
    out["parent_id"] = m.group(1) if m else None
    fm = re.search(r"```[a-z_]*\n(.*?)\n```", cur, re.S)
    out["parent_text"] = fm.group(1) if fm else None
    k = insp.find("Previous Failed Attempts")
    if k >= 0:
        out["failed"] = insp[k:].strip()
        insp = insp[:k]
    out["inspiration_ids"] = [x for x in _CANDIDATE_ID.findall(insp) if x != out["parent_id"]]
    out["attempts"] = att.strip()
    i = user_message.find(MARK_END_BACKEND)
    tail = user_message[i + len(MARK_END_BACKEND):].strip() if i >= 0 else ""
    # the backend's own copy of the parent's feedback duplicates the current-program slot
    tail = re.sub(r"## Evaluator Feedback.*?(?=\n## |\Z)", "", tail, flags=re.S).strip()
    out["backend"] = tail
    return out


def _demote(text: str) -> str:
    """The backend's own markdown with its headings one level down, so
    they sit under the notes slot's heading."""
    return re.sub(r"^(#{1,5}) ", lambda m: "#" + m.group(1) + " ", text, flags=re.M)


def program_path(run: Path, candidate_id: str, ext: str) -> Path:
    return Path(run) / "programs" / (candidate_id.replace(":", "_") + ext)


def save_program(run: Path, candidate_id: str, ext: str, text: str):
    p = program_path(run, candidate_id, ext)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def program_ext(inst: Instance) -> str:
    seeds = inst.seed_artifacts()
    lang = seeds[0].language if seeds else "text"
    return {"c": ".c", "cpp": ".cc", "systemverilog": ".sv", "verilog": ".v", "python": ".py",
            "chisel": ".scala", "scala": ".scala", "yosys_script": ".ys", "tcl": ".tcl",
            "rust": ".rs", "go": ".go"}.get(lang, ".txt")


HISTORY_ENTRIES = 7          # entries of a region's history the prompt summarizes
HISTORY_DIR = "history"


def _history_names_hint(names: list, listed: bool = True) -> str:
    """How the response section names the region a HISTORY block is filed under.

    It points at `regions.md` rather than listing the names: the list grows with the artifact and
    the prompt should not grow with it. One region is the exception -- there is no choice to make,
    so naming it costs a word and saves the agent a file read.

    `listed` is whether that file was written. A call whose parent carries no record has the
    program text but no program file, so `call_workspace` writes neither, and pointing at a file
    that is not there is what sending the agent after a name with no referent was. The names go
    inline in that case: there is no file to grow instead of the prompt.
    """
    if not names:
        return "-- the `Current program` section names them"
    if len(names) == 1:
        return f"-- this program has one, `{names[0]}`"
    if not listed:
        shown = ", ".join(f"`{n}`" for n in names[:12])
        return f"-- one of {shown}{', ...' if len(names) > 12 else ''}"
    return "-- `regions.md` lists them"


def history_dir(run) -> Path:
    return Path(run) / HISTORY_DIR


def _history_entries(text: str) -> list:
    """The entries of one member's history file, oldest first.

    The file is append-only and oldest-first so that the long prefix an
    agent re-reads each call stays byte-identical and keeps hitting the
    provider's cache -- across this project's runs cache reads have run
    about four times the fresh input, so a file that rewrote its head
    every round would cost real money. The prompt reverses them.
    """
    out = []
    for block in text.split("\n## "):
        block = block.strip()
        if not block:
            continue
        if not block.startswith("## "):
            block = "## " + block
        out.append(block)
    return out


RETRACTED = "retracted.json"


def retracted_entries(run) -> dict:
    """`{region: [edit numbers]}` the run has retracted."""
    f = history_dir(run) / RETRACTED
    try:
        d = json.loads(f.read_text())
    except Exception:  # noqa: BLE001 -- no file is no retraction
        return {}
    regions = d.get("regions") if isinstance(d, dict) else None
    if not isinstance(regions, dict):
        return {}
    return {str(k): [int(n) for n in v] for k, v in regions.items()}


def retract_history(run, entries: list, reason: str) -> list:
    """Hide the entries a call left, naming why.

    The index is a file of its own and the `.md` is never rewritten. A
    run with several evaluations in flight does not retract its newest
    entry but some earlier one, and deleting from the middle would
    renumber what follows and change the prefix every later call
    re-reads -- the thing the append-only order exists to keep byte
    identical for the provider's cache. Keeping the entry and hiding it
    is also the honest record: the edit was made and did not survive,
    which is not the same as never having been made.
    """
    if not entries:
        return []
    d = history_dir(run)
    d.mkdir(parents=True, exist_ok=True)
    cur = retracted_entries(run)
    try:
        why = dict(json.loads((d / RETRACTED).read_text()).get("reasons") or {})
    except Exception:  # noqa: BLE001 -- no file is no reason recorded yet
        why = {}
    done = []
    for e in entries:
        region, n = str(e.get("region") or ""), int(e.get("edit") or 0)
        if not region or n <= 0:
            continue
        cur.setdefault(region, [])
        if n not in cur[region]:
            cur[region].append(n)
        why[f"{region}#{n}"] = reason
        done.append(f"{region}#{n}")
    # two named parts rather than one mapping with a magic key: the numbers and the
    # reasons have different shapes, and a reader that walked them together broke
    (d / RETRACTED).write_text(json.dumps(
        {"regions": {k: sorted(v) for k, v in cur.items()}, "reasons": why},
        indent=1, sort_keys=True))
    return done


# One line per evaluated edit, appended to the region's history when the evaluation of the call
# that wrote the entry ends. The agent cannot write it -- when it writes its note nothing has been
# built -- and the composer cannot wait to write it when the candidate becomes a parent: an edit
# that made things worse is never picked as one, so the entries that most need an effect would be
# the ones never given it. The line goes at the end, not under its entry, since the file is
# append-only (see `_history_entries`) and with several evaluations in flight the entry is not
# always the last; it names its entry's number instead, and starts with no `## ` so that it opens
# no entry of its own.
EFFECT_RE = re.compile(r"^effect of edit (\d+)\b.*$", re.M)


def history_effects(text: str) -> dict:
    """`{edit number: its effect line}` of one region's history file."""
    return {int(m.group(1)): m.group(0).strip() for m in EFFECT_RE.finditer(text)}


def note_effect(run, entries: list, text: str, candidate_id: Optional[str] = None,
                parent_id: Optional[str] = None) -> list:
    """Append `effect of edit N (...): <text>` for each entry a call left, and name the candidate
    the entries produced (and its parent) in `lineage.json`."""
    d = history_dir(run)
    done = []
    if candidate_id:
        note_lineage(run, entries or [], candidate=str(candidate_id),
                     **({"parent": str(parent_id)} if parent_id else {}))
    for e in entries or []:
        region, n = str(e.get("region") or ""), int(e.get("edit") or 0)
        f = d / f"{region}.md"
        if not region or n <= 0 or not f.is_file():
            continue
        with open(f, "a") as fh:
            fh.write(f"\neffect of edit {n}: {text}\n")
        done.append(f"{region}#{n}")
    return done


# Which candidate each history entry produced, and from which parent: `{"<region>#<edit>": {"parent": id,
# "candidate": id}}`. The parent is known when the reply is filed (record_history), the candidate when its
# evaluation ends (note_effect). A history shared by the whole run showed a call its siblings' edits as if they
# were its own program's, and the free baselines re-submitted a sibling's edit onto the seed it had been made
# on, byte for byte (exp9 fp_alu_cmp_hf best_of_n r3: the first four candidates identical).
LINEAGE = "lineage.json"


def lineage_index(run) -> dict:
    try:
        d = json.loads((history_dir(run) / LINEAGE).read_text())
    except Exception:  # noqa: BLE001 -- no file is no entry attributed yet
        return {}
    return d if isinstance(d, dict) else {}


def note_lineage(run, entries: list, **fields) -> None:
    """Merge `fields` into the lineage row of each entry, under a file lock (evaluations run in parallel)."""
    import fcntl
    rows = [(str(e.get("region") or ""), int(e.get("edit") or 0)) for e in entries or []]
    rows = [(r, n) for r, n in rows if r and n > 0]
    if not rows:
        return
    d = history_dir(run)
    d.mkdir(parents=True, exist_ok=True)
    with open(d / ".lineage.lock", "a") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            cur = lineage_index(run)
            for r, n in rows:
                cur.setdefault(f"{r}#{n}", {}).update(fields)
            tmp = d / f".{LINEAGE}.{os.getpid()}.tmp"
            tmp.write_text(json.dumps(cur, indent=1, sort_keys=True))
            os.replace(tmp, d / LINEAGE)
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)


def ancestry(parent: Optional[dict], by_id: dict) -> set:
    """The ids of `parent` and of every ancestor of it in the archive."""
    out: set = set()
    cur = parent
    while cur is not None and cur.get("candidate_id") and cur["candidate_id"] not in out:
        out.add(cur["candidate_id"])
        cur = by_id.get(cur.get("parent_id") or "")
    return out


def lineage_on() -> bool:
    return os.environ.get("ADIR_HISTORY_LINEAGE", "1") != "0"


_EDIT_HEAD = re.compile(r"^## edit (\d+)\b")
_EFFECT_CANDIDATE = re.compile(r"^\(candidate (\w+)")


def lineage_history(member: str, text: str, lineage: set, index: dict) -> list:
    """[(edit number, entry text)] of one region's history file made by a candidate in `lineage`: the
    candidate from `lineage.json`, else the one the entry's `effect of edit N` line names. An entry no
    evaluation has claimed yet is no ancestor's."""
    effects = history_effects(text)
    out = []
    for k, e in enumerate(_history_entries(EFFECT_RE.sub("", text)), 1):
        m = _EDIT_HEAD.match(e)
        n = int(m.group(1)) if m else k
        cid = (index.get(f"{member}#{n}") or {}).get("candidate")
        if not cid and n in effects:
            em = _EFFECT_CANDIDATE.match(effects[n].split(": ", 1)[-1])
            cid = em.group(1) if em else None
        if cid and cid in lineage:
            out.append((n, e))
    return out


def render_history(entries: list, effects: dict) -> str:
    """A history file of `entries` alone, each followed by its effect line."""
    parts = []
    for n, e in entries:
        parts.append("\n" + e.rstrip() + "\n" + (f"\n{effects[n]}\n" if n in effects else ""))
    return "".join(parts)


# The choice this asks for is the point of keeping histories at all, and it has to be
# asked whether or not the listing above it is rendered: with no listing the agent still
# has the directory and its file tools, and this is what tells it to look. The text is
# fixed, and it sits in the last section of the prompt (SKELETON_USER ends with
# `backend`), so it invalidates no cached prefix before it.
HISTORY_CHOICE = (
    "Decide for yourself whether to keep optimizing along one of these histories -- "
    "a region whose entries show steady gains, or one whose last attempt failed for a "
    "reason you can now avoid -- or to leave them and change a region nothing has "
    "touched yet. Say which you chose in one clause.")


def _history_notes(inst: Instance, run, parent, by_id, lineage: Optional[set] = None) -> list:
    """The prompt's view of what has been done to each member so far:
    one pointer line per member, then the newest few entries in brief.

    The entries themselves are not inlined -- a history that grows with
    the search would push the prompt up with it, and the agent has file
    tools and the directory. What it gets here is enough to decide where
    to work: which regions carry a long history of small wins, which have
    never been touched, and what the last few attempts on each bought.
    `lineage` (see call_workspace) limits the entries to the parent's
    ancestors'; None shows every entry of the run.
    """
    d = history_dir(run)
    if not d.is_dir():
        return []
    n = int(((inst.search.get("history") or {}).get("entries") or HISTORY_ENTRIES))
    files = sorted(d.glob("*.md"))
    if not files:
        return []
    hidden = retracted_entries(run)
    index = lineage_index(run) if lineage is not None else {}
    lines = ["### What has been done to each region so far", ""]
    touched = set()
    for f in files:
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        effects = history_effects(text)
        member = f.stem
        if lineage is None:
            entries = list(enumerate(_history_entries(EFFECT_RE.sub("", text)), 1))
        else:
            entries = lineage_history(member, text, lineage, index)
            if not entries:
                continue
        # an entry a `rollback` node retracted is not shown: the edit did not survive, and a
        # round that read it as something tried would be reading a change that never stood
        drop = set(hidden.get(member) or [])
        if drop:
            entries = [(k, e) for k, e in entries if k not in drop]
        touched.add(member)
        lines.append(f"* `{member}` ({len(entries)} edits, `history/{member}.md`)")
        for k, e in reversed(entries[-n:]):
            head = next((ln for ln in e.splitlines() if ln.startswith("## ")), "").lstrip("# ").strip()
            why = next((ln for ln in e.splitlines() if ln.lower().startswith("why:")), "").strip()
            eff = effects[k].split(": ", 1)[-1] if k in effects else "effect: not yet measured"
            lines.append(f"    * {head} -- {why[:160] or 'no reason recorded'} -- {eff[:160]}")
    try:                                   # the seed artifact names the members
        seeds = inst.seed_artifacts()
        all_members = list(seeds[0].members) if seeds and seeds[0].is_family else []
    except Exception:                      # noqa: BLE001 -- a missing list only costs the hint
        all_members = []
    untouched = [m for m in all_members if m not in touched]
    if len(lines) == 2 and not untouched:
        return []
    if untouched:
        lines += ["", f"Regions no edit has touched yet: {', '.join(untouched)}."]
    return lines


def fence_lang(inst: Instance) -> str:
    seeds = inst.seed_artifacts()
    lang = seeds[0].language if seeds else "text"
    return {"yosys_script": "text", "chisel": "scala"}.get(lang, lang)


# ------------------------------------------------------------- the backend's metrics

# What of a program's metrics the backend's own sections may show: the score, feasibility, the goal and the
# objectives it is computed from, and conformance. SkyDiscover prints every metric the evaluator returned --
# the declaration's resolved values (`declaration.decl.core.*`, what omit_vars keeps from the baselines), the
# fault campaign's and the synthesis runs' internals -- which put knowledge the method is not given into the
# free baselines' prompts (exp9 best_of_n, beam_search).
METRICS_SHOWN = ("combined_score", "feasible", "conformance.pass")
_METRICS_LINE = re.compile(r"^(\s*[-*]?\s*Metrics:\s*)(\S.*)$", re.M)
_METRIC_ITEM = re.compile(r"^([\w.\[\]/-]+):\s")
_METRIC_BULLET = re.compile(r"^\s*[-*]\s*([\w\[\]/-]+\.[\w.\[\]/-]+):\s.*$")


def metric_shown(inst: Instance, key: str) -> bool:
    if key in METRICS_SHOWN or key.startswith("goal."):
        return True
    try:
        objectives = {r for r in inst.goal.refs if not r.startswith("seed.")}
    except Exception:  # noqa: BLE001
        objectives = set()
    return key in objectives


def filter_metrics(inst: Instance, text: str) -> str:
    """The backend's text with every metric outside `metric_shown` dropped: from its `Metrics: k: v, ...`
    lines, and the `- node.key: v` lines of its metric lists."""
    def one_line(m):
        items = re.split(r",\s+(?=[\w.\[\]/-]+:\s)", m.group(2))
        kept = [it for it in items if (lambda km: km is not None and metric_shown(inst, km.group(1)))(_METRIC_ITEM.match(it))]
        return m.group(1) + (", ".join(kept) if kept else "(no goal metric)")
    text = _METRICS_LINE.sub(one_line, text or "")
    roots = set(getattr(inst, "nodes", {}) or {}) | {"declaration", "decl"}
    out = []
    for line in text.splitlines():
        b = _METRIC_BULLET.match(line)
        if b and b.group(1).split(".")[0] in roots and not metric_shown(inst, b.group(1)):
            continue
        out.append(line)
    return "\n".join(out)


# ------------------------------------------------------------- the composition

def compose(inst: Instance, run: Path, backend_user: str, rng: random.Random, archive: Optional[Archive] = None,
            ask=None, log=None) -> tuple:
    """(system, user, sidecar) for one solution-model call. `ask(role,
    system, user)` reaches another model role for instruction
    proposals."""
    run = Path(run)
    archive = archive or inst.archive(run)
    parsed = parse_backend(backend_user)
    by_id = {r["candidate_id"]: r for r in archive.records()}
    parent = by_id.get(parsed["parent_id"] or "")
    if parsed["parent_id"] and parent is None and log is not None:
        log(f"parent {parsed['parent_id']} is not in the archive; the prompt carries no current program")
    cfg = choose_config(inst, archive, rng)
    if ask is not None:
        maybe_propose(inst, run, archive, ask, log)
    instruction = choose_instruction(inst, run, archive, rng)
    ext, lang = program_ext(inst), fence_lang(inst)
    U: dict = {k: [] for k in SKELETON_USER}
    n = int(cfg["context_programs"])
    ctx_ids = parsed["inspiration_ids"][:n]
    # the histories of this parent's own lineage: a sibling's edit is not in this program
    lineage = ancestry(parent, by_id) if lineage_on() else None
    workspace = call_workspace(inst, run, parent["candidate_id"] if parent else "solution", parent, ctx_ids, ext,
                               lineage=lineage)
    # the round's files: what the call's directory holds beyond the program, one index line each; the
    # prompt carries the index and the agent reads what the change needs (design section 7.7)
    files: list = []
    cur = ["## Current program", ""]
    text = parsed["parent_text"]
    path = None
    if parent:
        cur += _metrics_lines(parent)[:1] + [""]
        files.append(write_context(workspace, "parent", "\n".join(
            ["# The parent", ""] + (["Declarations:", "", "```", _block(parent, max_lines=100000), "```", ""]
                                     if declares(inst) else [])
            + _metrics_lines(parent)),
            "the parent: " + ("its declaration block, " if declares(inst) else "")
            + "its metrics per node and its unsatisfied constraints"))
        p = program_path(run, parent["candidate_id"], ext)
        if p.is_file():
            text = p.read_text()
            path = workspace / f"program{ext}"
    # the names a HISTORY block may carry: the same mutable regions the `Current program`
    # section lists, so the name the agent writes has a referent it can see in the file
    hist_names = regions_of_program(inst, text) if text else []
    focus_region, focus_vars = choose_focus(inst, parent, text, cfg, rng)
    # the tactic follows the operator and the focus: under `local` a tactic that
    # proposes declaration values is out, under a focus it addresses that region
    from .prompts import choose_tactic
    tactic_id, tactic = choose_tactic(inst, archive, parent, rng, operator=cfg["operator"],
                                      focus_vars=focus_vars)
    # every agent reads files: the current program is named by its file unless `show: full` asks for the text
    if text and cfg["show"] != "full" and path is not None:
        spans = region_spans(inst, text)
        shown = [f"`{n}` (lines {lo}-{hi})" for n, lo, hi in spans[:40]]
        cur += [f"The program is the file `program{ext}` ({text.count(chr(10)) + 1} lines"
                + (f"; mutable regions: {', '.join(shown)}"
                   + (f", ... {len(spans) - 40} more" if len(spans) > 40 else "") if spans else "")
                + "). Read it with your file tools, the region in focus as a slice by its lines; "
                "a SEARCH block must match its text verbatim.", ""]
    elif text:
        cur += ["The program:", "", _fence(lang, text), ""]
    if focus_region:
        spans = {n: (lo, hi) for n, lo, hi in region_spans(inst, text or "")}
        span = spans.get(focus_region)
        cur += [f"The region in focus is `{focus_region}`" + (f", lines {span[0]}-{span[1]} of the file" if span else "") + ".", ""]
    if (workspace / "members").is_dir():
        k = sum(1 for _ in (workspace / "members").iterdir())
        files.append(f"* `members/` ({k} files): the program's members, one file per structure with the same text; "
                     f"edit through `program{ext}`")
    if (workspace / "history").is_dir():
        k = sum(1 for _ in (workspace / "history").glob("*.md"))
        files.append(f"* `history/` ({k} file{'s' if k != 1 else ''}): what earlier rounds changed in each region and why, "
                     "each edit followed, once it was evaluated, by an `effect of edit N` line with what it measured")
    if cfg["show_plan_table"]:
        files += _sources(inst, archive, parent, static=False, focus=focus_region, workspace=workspace)
    if parent:
        fb = _feedback(parent, cfg["feedback_depth"], workspace)
        if cfg["feedback_depth"] == "files":
            files += fb
        elif fb:
            cur += ["Feedback of its evaluation:", ""] + fb + [""]
    for cid in ctx_ids:
        r = by_id.get(cid)
        if not r:
            continue
        p = program_path(run, cid, ext)
        has_file = (workspace / "context" / f"{cid}{ext}").is_file()
        files.append(write_context(workspace, cid, "\n".join(
            [f"# Context program {cid}", ""] + (["Declarations:", "", "```", _block(r, max_lines=100000), "```", ""]
                                                if declares(inst) else [])
            + _metrics_lines(r)),
            f"another evaluated candidate for contrast, `{cid}`: " + ("its declaration block and metrics" if declares(inst) else "its metrics")
            + (f"; its program is `context/{cid}{ext}`" if has_file else "")))
        if cfg["show"] == "full" and p.is_file():
            cur += [f"Context program {cid}:", "", _fence(lang, p.read_text()), ""]
    cur += [f"This call's directory is `{workspace}`; the paths below and those in the system text are relative "
            "to it. This round's files:", ""] + files + [""]
    U["current"] = cur
    if parsed["attempts"] and "No previous attempts" not in parsed["attempts"]:
        U["history"] = ["## History", "", filter_metrics(inst, parsed["attempts"]), ""]
    U["operator"] = operator_section(inst, cfg["operator"], parent, cfg, rng, focus_region, focus_vars)
    U["ambition"] = ambition_section(str(cfg.get("ambition", "moderate")), plain=not declares(inst))
    if tactic:
        U["tactic"] = ["## Tactic", "", tactic, ""]
    if instruction:
        U["guidance"] = ["## Guidance", "", instruction["text"], ""]
    notes = []
    if parsed["failed"]:
        notes += [_demote(filter_metrics(inst, parsed["failed"])), ""]
    if parsed["backend"]:
        notes += [_demote(filter_metrics(inst, parsed["backend"])), ""]
    # The per-region listing is opt-in: it grows with the search and is the part that
    # costs prompt. The choice it asks for is not, and is appended below whatever the
    # setting, so the agent is always told to decide where to work and to say so.
    if os.environ.get("ADIR_HISTORY_NOTES") == "1":
        notes += _history_notes(inst, run, parent, by_id, lineage)
    notes += ([] if (notes and notes[-1] == "") else [""]) + [HISTORY_CHOICE, ""]
    if notes:
        U["backend"] = ["## Notes from the search", ""] + notes
    if cfg["knowledge_depth"] in ("index", "cards") and knowledge_path(inst):
        kp = knowledge_path(inst)
        files = sorted(kp.rglob("*.md"), key=card_rank(inst, parent, focus_vars))
        if cfg["knowledge_depth"] == "cards":
            U["backend"] += _cards(inst, kp, files, parent, focus_vars)
        else:
            # the cards nearest the round (card_rank: the focus region's variables, the parent's declared values,
            # the members of the searched variables) and the count of the rest; the agent reads what it needs
            shown = files[:INDEX_CARDS]
            U["backend"] += (["## Knowledge cards", "", f"Under `{workspace / 'knowledge'}`, the {len(shown)} nearest this round"
                              + (f" ({len(files) - len(shown)} further cards under the same directory, by family name):" if len(files) > len(shown) else ":")]
                             + [f"* `{f.relative_to(kp)}`" for f in shown] + [""])
    diff = bool(inst.search.get("diff_mode", True))
    if diff:
        U["response"] = ["## Response", "",
                         "State the reasoning in one short paragraph, then the change as SEARCH/REPLACE "
                         "blocks, each in exactly this form; every SEARCH block must match the current "
                         "program verbatim, whitespace included:", "",
                         "<<<<<<< SEARCH", "(lines copied from the current program)", "=======",
                         "(the replacement lines)", ">>>>>>> REPLACE", "",
                         "Then one note per mutable region you changed, which is what a later "
                         "round reads instead of the diff: the replaced lines in full, the lines "
                         "that replaced them in full, and why. Abbreviate neither side. Say in the "
                         "reason what you expected to gain, so a round that finds it did not work "
                         "knows what was already ruled out. The name after HISTORY is the region's "
                         + _history_names_hint(hist_names, (workspace / "regions.md").is_file())
                         + ".", "",
                         f"<<<<<<< HISTORY {hist_names[0] if hist_names else '<region name>'}",
                         "replaced:", "(the lines as they were)",
                         "with:", "(the lines as they now are)",
                         "why: (what this changes and what you expect from it)",
                         ">>>>>>> HISTORY", ""]
    else:
        U["response"] = ["## Response", "",
                         "State the reasoning in one short paragraph, then the complete program (the "
                         "markers, the member markers and the declaration block included) in one "
                         f"fenced block:", "", f"```{lang}", "(the complete program)", "```", ""]
    user = "\n".join(line for k in SKELETON_USER for line in U[k])
    from .confine import with_submission_note
    system = with_submission_note(system_text(inst, _seed_records(archive), archive, cfg, workspace=workspace))
    side = {"prompt_config": {**cfg, "tactic_id": tactic_id, "instruction_id": instruction["id"] if instruction else None,
                              "focus": focus_region},
            "tactic_id": tactic_id, "instruction_id": instruction["id"] if instruction else None,
            "parent_id": parent["candidate_id"] if parent else parsed["parent_id"], "time": time.time(),
            "workspace": str(workspace), "regions": list(hist_names)}
    if (inst.search.get("prompts") or {}).get("log", True):
        d = run / "prompts"
        d.mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        f = d / f"{stamp}_solution_{side['parent_id']}.md"
        f.write_text(f"<!-- prompt_config {json.dumps(side['prompt_config'])} -->\n\n# System\n\n{system}\n\n# User\n\n{user}\n")
        side["prompt_file"] = str(f)
    return system, user, side


def card_rank(inst: Instance, parent: Optional[dict], focus_vars: Optional[list] = None):
    """A sort key over card files: the members of the region in focus's
    variables first, then the parent's declared values, then the members
    of every searched domain, then the rest."""
    decl = ((parent or {}).get("declarations") or {}).get("vars") or {}
    focus = set()
    for n in focus_vars or []:
        b = inst.bindings.get(n)
        if b is not None and b.time == "search" and b.domain.finite() and len(b.domain.members()) <= 64:
            focus |= {str(m).lower() for m in b.domain.members()}
    declared = {str(v).lower() for v in decl.values()}
    searched = set()
    for b in inst.bindings.values():
        if b.time == "search" and b.domain.finite() and len(b.domain.members()) <= 64:
            searched |= {str(m).lower() for m in b.domain.members()}

    def rank(f: Path):
        stem = f.stem.lower()
        return (0 if stem in focus else 1 if stem in declared else 2 if stem in searched else 3,
                len(f.parts), str(f))
    return rank


def _cards(inst: Instance, kp: Path, files: list, parent: Optional[dict],
           focus_vars: Optional[list] = None) -> list:
    """The knowledge cards inlined, ranked by `card_rank`, up to
    CARDS_MAX_CHARS."""
    rank = card_rank(inst, parent, focus_vars)
    L = ["## Knowledge cards", ""]
    used = 0
    shown = 0
    for f in sorted(files, key=rank):
        try:
            text = f.read_text(errors="replace").strip()
        except OSError:
            continue
        if used + len(text) > CARDS_MAX_CHARS:
            if shown == 0:
                text = text[:CARDS_MAX_CHARS]
            else:
                continue
        L += [f"### {f.relative_to(kp)}", "", text, ""]
        used += len(text)
        shown += 1
        if used >= CARDS_MAX_CHARS:
            break
    if shown < len(files):
        L.append(f"({len(files) - shown} further cards under `{kp}` are not shown)")
        L.append("")
    return L


def _seed_records(archive: Archive) -> list:
    return [r for r in archive.records() if r.get("is_seed")]


def sample_user(inst: Instance, run: Path) -> str:
    """A composed user message for the first seed, written by `adir
    seeds` as prompt_sample.md so the composition can be inspected."""
    archive = inst.archive(run)
    seeds = _seed_records(archive)
    if not seeds:
        return ""
    first = seeds[0]
    others = seeds[1:]
    fake = (f"{MARK_CURRENT}\ncandidate_id: {first['candidate_id']}\n{MARK_INSPIRATIONS}\n"
            + "\n".join(f"candidate_id: {r['candidate_id']}" for r in others)
            + f"\n{MARK_ATTEMPTS}\nNo previous attempts yet.\n{MARK_END_BACKEND}\n")
    _, user, side = compose(inst, run, fake, random.Random(0), archive)
    return f"<!-- prompt_config {json.dumps(side['prompt_config'])} -->\n\n" + user


def skeleton_hash() -> str:
    import hashlib
    src = Path(__file__).read_text()
    return hashlib.sha256((COMPOSER_VERSION + src).encode()).hexdigest()[:16]
