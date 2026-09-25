"""A review node: a model reads every module a candidate declares a
family for and says whether the module's text realizes that family.
No gate can check a declaration against the text mechanically (the
seed realizes every family with the same behavioral text), so the
verdict is a node output the run file constrains (`review.agree >=
1.0`): a family declared but not implemented is then an infeasible
candidate rather than a label the archive learns from.

The node parses the candidate's own declaration block (its VAR lines)
and maps each `core.<kind>.<index>.family` departure to the modules the
STRUCTURE lines name for that index. It then writes a call directory
(`program.sv`, `members/`, `modules/<name>.sv` for the modules under
review, a copy of the knowledge base under `knowledge/`), hands the
agent that directory as its working directory and a prompt that is an
index of those files, and reads back one json verdict per module. The
agent reads what it needs with its own file tools, as the solution call
does; the prompt carries no RTL and no card text, so its length does not
grow with the design.

`chialu.review.claude`, `.codex` and `.opencode` are the same node under
the agent whose login the worker holds, and a run file picks the node,
the model and (for opencode) the provider. The agent runs through CHIA's
node when CHIA is importable, else through the CLI; either way editing,
the shell, the web and every path outside the call directory are denied.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from adir import node

REPO_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = REPO_ROOT / "chialu" / "knowledge"
_MODULE_RE = re.compile(r"^module\s+([A-Za-z_]\w*)\b.*?^endmodule\b", re.M | re.S)
_JSON_RE = re.compile(r"```(?:json)?\s*(\[.*?\])\s*```", re.S)
PER_CALL = 12         # modules judged per model call (the prompt is an index, so a call is cheap)
MAX_CALLS = 3         # the calls one review spends, so a candidate's review cost does not grow with
                      # the modules it declares: a wider candidate makes each call judge more modules

SYSTEM = """You review SystemVerilog against a microarchitecture declaration.

Each item names a module, the family the candidate declares for it and the family's
knowledge card. Decide whether the module's logic realizes that family: its structure
(the carry network, the recoding, the tree, the path split, ...) must be the family's,
not a behavioral operator (`a + b`, `a * b`) and not an instance of a reference module
the card would not call that family. A different but valid implementation of the same
family counts as realized. A module that instantiates a lane module, which in turn
instantiates a family library module, realizes the declared family when that library
module is the declared family's; follow the instantiation chain before judging, and read
the library module's own header, which names its family and its construction. A lane
module that only computes the op behaviorally does not realize a declared family.

The files are in your working directory; read them with your file tools. Judge the text
alone, and judge every item, including the ones whose chain you had to follow.

Answer with one json list in a fenced block, one object per item, in the order given:
[{"module": "<name>", "family": "<name>", "realized": true|false, "why": "<one sentence>"}]"""


def _declared_families(rtl_text: str) -> dict:
    """{`core.<slot>.<index>.family`: family} from the block's VAR lines.
    A structure standing at its slot's default family has no VAR line, so
    this mapping holds the candidate's departures alone; `_flat_families`
    reads the completed declaration."""
    from adir.declaration import parse_block
    d = parse_block(rtl_text)
    return {k: str(v) for k, v in d.vars.items() if k.startswith("core.") and k.endswith(".family")}


def _flat_families(declaration) -> dict:
    """{`core.<slot>.<index>.family`: family} from the completed
    declaration ADIR resolves for a candidate (`decl.core`), which carries
    every decision the block leaves out at its default. The value arrives
    as the nested mapping `{slot: {index: {choice: value}}}`."""
    if not isinstance(declaration, dict):
        return {}
    out = {}

    def walk(node, path):
        if not isinstance(node, dict):
            return
        for k, v in node.items():
            if k == "family" and not isinstance(v, dict):
                out["core." + ".".join(path + ["family"])] = str(v)
            else:
                walk(v, path + [str(k)])

    walk(declaration, [])
    return out


def _modules(rtl_text: str) -> dict:
    return {m.group(1): m.group(0) for m in _MODULE_RE.finditer(rtl_text)}


def _card_path(family: str, slot: str, knowledge: Path) -> str:
    """The family's card as a path under the knowledge root: the card in
    the slot's own domain where two domains share the name."""
    hits = sorted((knowledge / "arch").glob(f"*/{family}.md")) if (knowledge / "arch").is_dir() else []
    if not hits:
        return ""
    prefer = {"rounder": "round", "unpacker": "unpack"}.get(slot)
    for h in hits:
        if prefer and h.parent.name == prefer:
            return str(h.relative_to(knowledge))
    return str(hits[0].relative_to(knowledge))


def _items(rtl_text: str, structures, knowledge: Path, declaration=None) -> list:
    """[(module, family, card path)] for every declared family, one entry
    per (module, family). `declaration` is the candidate's completed
    declaration (`decl.core`): with it a structure standing at its slot's
    default family is reviewed like any other, and without it the review
    sees the block's VAR lines alone and judges the departures."""
    from chialu.targets.rtl.structures import structure_index
    declared = dict(_flat_families(declaration))
    declared.update(_declared_families(rtl_text))   # a VAR line wins over the resolved value
    if not declared:
        return []
    mods = _modules(rtl_text)
    out, seen = [], set()
    for e in structures or []:
        sid = e["_"][0] if isinstance(e.get("_"), list) else str(e.get("id", ""))
        kind = str(e.get("kind", ""))
        slot = str(e.get("slot") or kind)
        sv = e.get("sv")
        if not sv or slot in ("-", ""):
            continue
        fam = declared.get(f"core.{slot}.{structure_index(sid, kind)}.family")
        if fam is None or (sv, fam) in seen or sv not in mods:
            continue
        seen.add((sv, fam))
        out.append((sv, fam, _card_path(fam, slot, knowledge)))
    return out


def _workspace(root: Path, rtl_text: str, members, items: list, knowledge: Path) -> Path:
    """The call's directory: the whole candidate as `program.sv`, its
    members one file each where the candidate is a family, the module of
    each item cut out as `modules/<name>.sv`, and a copy of the knowledge
    base. Copies rather than links, so every path the agent can read is
    this call's own."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "program.sv").write_text(rtl_text)
    if isinstance(members, dict) and members:
        d = root / "members"
        d.mkdir(exist_ok=True)
        for name, text in members.items():
            (d / (re.sub(r"[^\w.-]+", "_", str(name)) + ".sv")).write_text(
                text if isinstance(text, str) else str(text))
    mods = _modules(rtl_text)
    d = root / "modules"
    d.mkdir(exist_ok=True)
    for sv, _fam, _card in items:
        if sv in mods:
            (d / f"{sv}.sv").write_text(mods[sv])
    if knowledge.is_dir() and not (root / "knowledge").exists():
        shutil.copytree(knowledge, root / "knowledge", ignore=shutil.ignore_patterns(".*", "__pycache__"))
    return root


def _prompt(items: list, ws: Path, rtl_text: str) -> str:
    """The index of the call's files: one line per item, with no RTL and no
    card text, so the prompt's length does not grow with the design."""
    mods = _modules(rtl_text)
    L = [f"The working directory holds `program.sv` (the whole candidate, {rtl_text.count(chr(10)) + 1} lines, "
         f"{len(mods)} modules), the module of each item as `modules/<name>.sv`"
         + (", the candidate's members one file each under `members/`" if (ws / "members").is_dir() else "")
         + ", and the knowledge base under `knowledge/`. Follow an instantiation by searching `program.sv` "
           "for `module <name>`; a library module's header names its family.", "",
         f"The {len(items)} item{'s' if len(items) != 1 else ''} to judge:", ""]
    for i, (sv, fam, card) in enumerate(items, 1):
        L.append(f"{i}. module `{sv}` (`modules/{sv}.sv`), declared family `{fam}`"
                 + (f", card `knowledge/{card}`" if card else ", no card for this family"))
    L += ["", "Answer with the json list alone, in that order."]
    return "\n".join(L)


import threading
_CALLS = threading.local()   # the review's model calls: wall time, outcome, tokens and cost, one row per call


def _calls() -> list:
    if not hasattr(_CALLS, "rows"):
        _CALLS.rows = []
    return _CALLS.rows


def _ask(agent: str, model: str, system: str, user: str, timeout_s: int, provider: str = "",
         small_model: str = "", work_dir: str = "", effort: str = "", max_output_tokens: int = 0) -> str:
    """The model's reply, with the call's directory as its working
    directory and its file tools: through CHIA's agent node when
    importable, else the CLI. Editing, the shell, the web and every path
    outside the directory are denied."""
    try:
        from adir.backends.skydiscover import AgentLLM
        spec = {"agent": agent, "model": model, "timeout_s": timeout_s, "retries": 1}   # one attempt a call
        if effort:
            spec["effort"] = effort           # opencode: --variant; claude: --effort; codex: reasoning_effort
        if max_output_tokens:
            spec["max_output_tokens"] = max_output_tokens   # opencode's per-call output cap, reasoning included
        if agent == "opencode":
            spec.update({k: v for k, v in (("provider", provider), ("small_model", small_model)) if v})
        llm = AgentLLM(spec, None, getattr(_CALLS, "run", None), "review")
        llm._cls()                       # raises without CHIA
    except (ImportError, RuntimeError):
        llm = None
    if llm is not None:
        # a failed call raises to the review, which reads it as no verdict; it is not repeated through the
        # CLI below, which would be a second attempt no budget counts
        try:
            return llm._call(system, user, work_dir or None)
        finally:
            if getattr(llm, "last_call", None) is not None:
                _calls().append(llm.last_call)
    if agent == "opencode":
        # the CLI takes opencode's provider/model id; its own title and summary calls stay on the small model.
        # The permissions go in beside them: without them `external_directory` defaults to a question nobody
        # answers in a non-interactive run, and the agent now has a working directory and its file tools.
        import os
        from adir.backends.skydiscover import opencode_model, set_opencode_env
        spec = {"model": model, "provider": provider or None, "small_model": small_model or None,
                "max_output_tokens": max_output_tokens or None}
        model = opencode_model(spec)
        set_opencode_env(spec)
        try:
            cfg = json.loads(os.environ.get("OPENCODE_CONFIG_CONTENT") or "{}")
        except ValueError:
            cfg = {}
        cfg["permission"] = {"edit": "deny", "bash": "deny", "webfetch": "deny",
                             "external_directory": "deny", "doom_loop": "deny"}
        os.environ["OPENCODE_CONFIG_CONTENT"] = json.dumps(cfg, sort_keys=True)
    with tempfile.TemporaryDirectory() as td:
        cwd = work_dir or td
        stdin_text = None
        if agent == "claude":
            cmd = ["claude", "-p", "--output-format", "text", "--model", model,
                   "--disallowedTools", "Bash,Edit,Write,MultiEdit,NotebookEdit,WebFetch,WebSearch,Task,Agent",
                   "--add-dir", cwd, "--append-system-prompt", system]
            if effort:
                cmd += ["--effort", effort]
            stdin_text = user                     # the prompt on stdin: no argument-length limit
        elif agent == "codex":
            out = Path(td) / "last.md"
            cmd = ["codex", "exec", "-m", model, "--sandbox", "read-only", "-C", cwd,
                   "--output-last-message", str(out), "-"]
            stdin_text = f"{system}\n\n{user}"
        elif agent == "opencode":
            cmd = ["opencode", "run", "--model", model, "--dir", cwd]
            if effort:
                cmd += ["--variant", effort]      # opencode's name for the provider's reasoning effort
            cmd += [f"{system}\n\n{user}"]
        else:
            raise ValueError(f"agent {agent!r}: one of claude, codex, opencode")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, cwd=cwd,
                           input=stdin_text, **({} if stdin_text is not None else {"stdin": subprocess.DEVNULL}))
        if agent == "codex" and (Path(td) / "last.md").is_file():
            return (Path(td) / "last.md").read_text()
        if r.returncode != 0 and not r.stdout.strip():
            raise RuntimeError(f"{agent} exited {r.returncode}: {(r.stderr or '')[-800:]}")
        return r.stdout


_ROW_RE = re.compile(r'"module"\s*:\s*"([^"]+)"[^{}]*?"realized"\s*:\s*(true|false)(?:[^{}]*?"why"\s*:\s*"((?:[^"\\]|\\.)*)")?',
                     re.S)


def _rows(text: str) -> list:
    """The verdict rows of a reply: its JSON array, or, when the array
    does not parse (a model's unescaped quote inside a `why`), every
    object whose module and verdict a pattern recovers."""
    try:
        rows = json.loads(text)
        return rows if isinstance(rows, list) else []
    except json.JSONDecodeError:
        return [{"module": m.group(1), "realized": m.group(2) == "true", "why": (m.group(3) or "").replace('\\"', '"')}
                for m in _ROW_RE.finditer(text)]


def _verdict_of(row) -> bool | None:
    """The row's `realized` field as a verdict: a JSON boolean, or the two
    spellings a model writes instead of one. Anything else is no verdict,
    so a row of `"realized": "maybe"` does not score as realized."""
    if not isinstance(row, dict):
        return None
    v = row.get("realized")
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and v.strip().lower() in ("true", "false"):
        return v.strip().lower() == "true"
    return None


def _parse(reply: str, items: list) -> list:
    """One verdict per item, matched by module name. A row naming no item
    is dropped, an item no row names has no verdict, and an item whose
    verdict is not a boolean has no verdict. An item without a verdict is
    not realized, so a reply that echoes the format template or answers
    about other modules fails the review rather than passing it."""
    m = _JSON_RE.search(reply)
    text = m.group(1) if m else reply[reply.find("["): reply.rfind("]") + 1]
    rows = _rows(text)
    if not rows:
        raise ValueError(f"no verdict rows in the reply ({len(reply)} characters)")
    by_module = {}
    for r in rows:
        if isinstance(r, dict) and isinstance(r.get("module"), str):
            by_module.setdefault(r["module"], r)
    if not any(sv in by_module for sv, _f, _c in items):
        raise ValueError(f"no verdict row names an item under review ({len(rows)} rows, "
                         f"first: {sorted(by_module)[:3]})")
    out = []
    for sv, fam, _card in items:
        row = by_module.get(sv)
        verdict = _verdict_of(row)
        why = str(row.get("why", ""))[:300] if isinstance(row, dict) else ""
        if verdict is None:
            why = ("the reply names no verdict for this module" if row is None
                   else f"the reply's verdict is not a boolean ({row.get('realized')!r})")
        out.append({"module": sv, "family": fam, "realized": verdict is True,
                    "verdict": verdict, "why": why})
    return out


def review(rtl_text: str, structures, agent: str, model: str, knowledge_dir: str = "",
           timeout_s: int = 900, provider: str = "", small_model: str = "", only=None,
           work_dir: str = "", effort: str = "", declaration=None, max_calls: int = MAX_CALLS,
           max_output_tokens: int = 0) -> dict:
    """`only` (ADIR's `candidate.touched`): the members whose text the
    candidate wrote itself; the review judges those modules alone, since a
    unit the library re-rendered realizes its declaration by construction.
    None judges every declared family (a seed, or a run file without the
    input); an empty list judges nothing. `work_dir` keeps the call
    directories under a path of the run's instead of a temporary one.
    `declaration` is the candidate's completed declaration (`decl.core`),
    which carries the structures standing at their slot's default family;
    without it the review judges the block's VAR lines alone. `max_calls`
    bounds the model calls one review spends, so the cost a candidate adds
    to the run's budget is a constant rather than a count of its modules."""
    from chialu.eda import rtl_of
    members = rtl_text if isinstance(rtl_text, dict) else None
    rtl_text = rtl_of(rtl_text)            # a multi-file seed arrives as its member dictionary
    _CALLS.rows = []
    # the run the calls belong to, when the run file routes them into its agent directory
    # (`work_dir: run.agent_dir`): each call is then a line of the run's llm_calls.jsonl as well
    # (adir.confine keeps a run's agent directory outside its git repository and names the run in `RUN`)
    from adir.confine import run_of_agent_dir
    _CALLS.run = run_of_agent_dir(work_dir) if work_dir else None
    t0 = time.time()
    knowledge = Path(knowledge_dir) if knowledge_dir else KNOWLEDGE
    try:
        items = _items(rtl_text, structures, knowledge, declaration)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "agree": 0.0, "reviewed": 0, "verdicts": [], "prompt": "",
                "detail": f"review: {type(e).__name__}: {e}", "seconds": round(time.time() - t0, 1), "llm_calls": list(_calls())}
    if only is not None:
        touched = {str(m) for m in (only or [])}
        items = [it for it in items if any(it[0] == m or it[0].endswith("_u_" + m) for m in touched)]
        if not items:
            return {"ok": True, "agree": 1.0, "dissent": 0, "reviewed": 0, "unreviewed": True,
                    "verdicts": [], "prompt": "",
                    "detail": "no edited module with a declared family to judge"
                              + (f" (edited: {', '.join(sorted(touched))})" if touched else " (no member edited)"),
                    "seconds": round(time.time() - t0, 1), "llm_calls": list(_calls())}
    if not items:
        return {"ok": True, "agree": 1.0, "dissent": 0, "reviewed": 0, "unreviewed": True,
                "verdicts": [], "prompt": "",
                "detail": "no declared family to judge", "seconds": round(time.time() - t0, 1), "llm_calls": list(_calls())}
    tmp = None
    if work_dir:
        stamp = time.strftime("review-%Y%m%d-%H%M%S-") + f"{abs(hash(rtl_text)) % 0x1000000:06x}"
        root = Path(work_dir) / stamp
    else:
        tmp = tempfile.TemporaryDirectory(prefix="chialu_review_")
        root = Path(tmp.name)
    verdicts, user = [], ""
    try:
        ws = _workspace(root, rtl_text, members, items, knowledge)
        per_call = max(PER_CALL, -(-len(items) // max(1, max_calls)))
        for i in range(0, len(items), per_call):
            chunk = items[i:i + per_call]
            user = _prompt(chunk, ws, rtl_text)
            try:
                reply = _ask(agent, model, SYSTEM, user, timeout_s, provider, small_model, str(ws), effort,
                             max_output_tokens)
                try:
                    verdicts += _parse(reply, chunk)
                except ValueError:
                    # a reply without recoverable rows is asked once more, with the format restated
                    reply = _ask(agent, model, SYSTEM, user + "\n\nThe previous reply held no valid JSON array; "
                                 "answer with the JSON array alone, every string escaped.", timeout_s,
                                 provider, small_model, str(ws), effort, max_output_tokens)
                    verdicts += _parse(reply, chunk)
            except Exception as e:  # noqa: BLE001
                # A call that fails says nothing about the candidate, so it must not read as a
                # verdict against it: `agree: 0.0` here discarded a candidate that passed every
                # hard gate and was the best design any model produced, because the provider
                # refused the request's shape. The dissent count stays at the modules actually
                # judged wrong, which is what the constraint reads, and `unreviewed` records
                # that the judgement is missing rather than favourable.
                return {"ok": False, "agree": None, "dissent": sum(1 for v in verdicts
                                                                  if _verdict_of(v) is False),
                        "reviewed": len(verdicts), "unreviewed": True, "verdicts": verdicts,
                        "prompt": user,
                        "detail": f"review call failed: {type(e).__name__}: {str(e)[:300]}",
                        "seconds": round(time.time() - t0, 1), "llm_calls": list(_calls())}
    finally:
        if tmp is not None:
            tmp.cleanup()
    n_ok = sum(1 for v in verdicts if v["realized"])
    n_silent = sum(1 for v in verdicts if v.get("verdict") is None)
    detail = "; ".join(f"{v['module']}: {v['family']} "
                       + ("no verdict" if v.get("verdict") is None
                          else ("realized" if v["realized"] else "NOT realized"))
                       + f" ({v['why']})" for v in verdicts)
    if n_silent:
        detail = f"{n_silent} of {len(verdicts)} modules got no verdict; " + detail
    # `dissent` is the number of modules the review judged not to realize their declared family.
    # The constraint reads this rather than the ratio: a candidate that rewrites a region often
    # lands on a structure the declaration no longer names, and a count tolerates one such module
    # the same way whether the candidate declares two structures or twelve, which a ratio does not.
    return {"ok": n_ok == len(verdicts), "agree": round(n_ok / len(verdicts), 4) if verdicts else 1.0,
            "dissent": len(verdicts) - n_ok, "unreviewed": not verdicts,
            "reviewed": len(verdicts), "verdicts": verdicts, "prompt": user,
            "detail": detail[:4000], "seconds": round(time.time() - t0, 1), "llm_calls": list(_calls())}


OUTPUTS = ["ok", "agree", "dissent", "unreviewed", "reviewed", "verdicts", "prompt",
           "detail", "seconds", "llm_calls"]


@node(outputs=OUTPUTS, resources={"claude_creds": 1})
def claude(rtl_text: str, structures, model: str = "claude-opus-5", knowledge_dir: str = "",
           timeout_s: int = 900, only=None, work_dir: str = "", declaration=None,
           max_calls: int = MAX_CALLS) -> dict:
    """The review under the claude agent; the run file names the model,
    and `only` is its `candidate.touched`."""
    return review(rtl_text, structures, "claude", model, knowledge_dir, timeout_s,
                  only=only, work_dir=work_dir, declaration=declaration, max_calls=max_calls)


@node(outputs=OUTPUTS, resources={"codex_creds": 1})
def codex(rtl_text: str, structures, model: str = "gpt-5.6-sol", knowledge_dir: str = "",
          timeout_s: int = 900, only=None, work_dir: str = "", declaration=None,
          max_calls: int = MAX_CALLS) -> dict:
    """The review under the codex agent; the run file names the model,
    and `only` is its `candidate.touched`."""
    return review(rtl_text, structures, "codex", model, knowledge_dir, timeout_s,
                  only=only, work_dir=work_dir, declaration=declaration, max_calls=max_calls)


@node(outputs=OUTPUTS, resources={"opencode_creds": 1})
def opencode(rtl_text: str, structures, model: str = "gemini-3.1-pro-preview", provider: str = "google-vertex",
             small_model: str = "", knowledge_dir: str = "", timeout_s: int = 900, only=None,
             work_dir: str = "", effort: str = "", declaration=None,
             max_calls: int = MAX_CALLS, max_output_tokens: int = 0) -> dict:
    """The review under the opencode agent: `provider` and `model` are
    opencode's provider id and the provider's model id (one setting more
    than the claude and codex nodes take); `small_model` is the model of
    opencode's own title and summary calls, the review's model by
    default; `only` is the run file's `candidate.touched`."""
    return review(rtl_text, structures, "opencode", model, knowledge_dir, timeout_s, provider, small_model,
                  only=only, work_dir=work_dir, declaration=declaration, effort=effort, max_calls=max_calls,
                  max_output_tokens=max_output_tokens)
