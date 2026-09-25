"""The declaration block (design section 5.2 and 5.3): every seed and
every candidate carries, in the artifact's comment syntax, a block

    // ADIR-DECL v1
    // VAR core.adder.family=parallel_prefix
    // STRUCTURE m1.l0.adder kind=adder ...      (a domain line)
    // ADIR-END

`VAR` is ADIR's line; every other kind is the domain's, registered as a
LineKind. The check is the node `adir.declaration`, always first."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import yaml

from .errors import BindError
from .variables import ABSENT, _pick, binding_lookup, default_under, member_exclusions

MARK_START = "ADIR-DECL v1"
MARK_END = "ADIR-END"
COMMENT = {
    "c": "//", "cpp": "//", "c++": "//", "systemverilog": "//", "verilog": "//",
    "sv": "//", "chisel": "//", "scala": "//", "java": "//", "rust": "//",
    "go": "//", "javascript": "//", "typescript": "//",
    "python": "#", "yaml": "#", "yosys_script": "#", "tcl": "#", "sh": "#",
    "bash": "#", "ruby": "#", "make": "#", "toml": "#",
    "vhdl": "--", "lua": "--", "sql": "--", "text": "",
}
_PREFIX = re.compile(r"^\s*(//|#|--|\*|;)?\s?")


def comment_prefix(language: str, extra: dict | None = None) -> str:
    if extra and language in extra:
        return extra[language]
    if language in COMMENT:
        return COMMENT[language]
    raise BindError("language", f"no comment syntax for {language!r}; register one "
                                f"in the template's comment_syntax")


@dataclass
class Declaration:
    vars: dict = field(default_factory=dict)       # VAR name -> value
    lines: list = field(default_factory=list)      # (kind, tokens) for domain lines
    raw: list = field(default_factory=list)
    present: bool = False


_INT = re.compile(r"^-?\d+$")
_FLOAT = re.compile(r"^-?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")


def value_from_text(s: str):
    """A declared value: an int or float by a strict spelling (no
    underscores, no octal), true/false, a flow list or mapping, else the
    text itself."""
    s = s.strip()
    if _INT.match(s):
        return int(s)
    if _FLOAT.match(s):
        return float(s)
    if s in ("true", "false"):
        return s == "true"
    if s[:1] in ("[", "{"):
        try:
            return yaml.safe_load(s)
        except yaml.YAMLError:
            return s
    return s


def value_to_text(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return v
    return yaml.safe_dump(v, default_flow_style=True).strip()


def parse_block(text: str) -> Declaration:
    """The first block in `text`; `present` is false when there is none."""
    d = Declaration()
    inside = False
    for line in text.splitlines():
        body = _PREFIX.sub("", line, count=1).rstrip()
        if not inside:
            if body.strip() == MARK_START:
                inside = True
                d.present = True
            continue
        if body.strip() == MARK_END:
            break
        if not body.strip():
            continue
        d.raw.append(body)
        tokens = body.split()
        kind, rest = tokens[0], tokens[1:]
        if kind == "VAR":
            spec = " ".join(rest)
            if "=" not in spec:
                raise BindError("declaration", f"VAR line without '=': {body!r}")
            name, value = spec.split("=", 1)
            d.vars[name.strip()] = value_from_text(value)
        else:
            d.lines.append((kind, rest))
    else:
        if inside:
            raise BindError("declaration", f"no {MARK_END} line")
    return d


def render_block(vars: dict, lines: list, prefix: str) -> str:
    p = f"{prefix} " if prefix else ""
    out = [f"{p}{MARK_START}"]
    for name, value in vars.items():
        out.append(f"{p}VAR {name}={value_to_text(value)}")
    for kind, tokens in lines:
        if isinstance(tokens, str):
            out.append(f"{p}{kind} {tokens}".rstrip())
        else:
            out.append(f"{p}{kind} {' '.join(str(t) for t in tokens)}".rstrip())
    out.append(f"{p}{MARK_END}")
    return "\n".join(out) + "\n"


def parse_fields(tokens: list) -> dict:
    """`k=v` tokens as a dict, bare tokens under `_` in order; a value
    with commas is a list."""
    out, bare = {}, []
    for t in tokens:
        if "=" in t:
            k, v = t.split("=", 1)
            out[k] = [value_from_text(x) for x in v.split(",")] if "," in v else value_from_text(v)
        else:
            bare.append(t)
    if bare:
        out["_"] = bare
    return out


def check_declaration(instance, decl: Declaration, ctx) -> dict:
    """The outputs of `adir.declaration`: `ok`, `detail`, and one
    `decl.<name>` per VAR plus one `decl.<KIND>` list per domain line
    kind. `ctx` is what the domain checks receive."""
    problems = []
    outputs: dict[str, Any] = {}
    if not decl.present:
        return {"ok": False, "detail": f"no {MARK_START} block"}
    hook = getattr(instance.template, "normalize_declaration", None)
    if hook is not None:
        # the domain completes the block by its own rules (a group's members
        # share what any member declares) before the variables are checked
        try:
            decl = hook(ctx, decl) or decl
        except Exception as e:  # noqa: BLE001
            problems.append(f"normalize_declaration: {e}")
    bindings = instance.bindings
    if hasattr(bindings, "activate"):
        bindings.activate(dict(decl.vars))     # the block's variables and the children its values open
    order = instance.variable_order()
    values = {}
    active_names = set()
    defaulted = []
    defaulted_under = {}
    # a member condition reads its sibling's value: fixed or runtime from the binding, a searched one from
    # the values this pass decided (declared or defaulted; the order places a sibling first), absent otherwise
    lookup = binding_lookup(bindings, lambda n: values[n] if n in values else ABSENT)
    for var in order:
        b = bindings.get(var.name)
        if b is None:
            continue
        if var.when is not None:
            parent = var.when[0]
            pb = bindings.get(parent)
            if pb is None or parent not in active_names:
                active = False
            elif pb.time == "search":
                pv = values.get(parent)
                active = pv is not None and var.condition_holds(pv)
            elif pb.time == "fixed":
                active = var.condition_holds(pb.value)
            else:
                active = any(var.condition_holds(m) for m in pb.members)
        else:
            active = True
        active = active and not var.inactive(lookup)
        if active:
            active_names.add(var.name)
        if b.time != "search":
            if b.time == 'fixed' and var.inactive(lookup):
                problems.append(f"fixed {var.name} declared, but inactive")
            if b.time == "fixed" and active and var.member_when:
                # a fixed member the block's other values exclude: the sibling to change is named
                why = _pick(member_exclusions(var, var.domain, lookup), b.value)
                if why:
                    problems.append(f"fixed {var.name}={b.value!r}: {why}")
            values[var.name] = b.value if b.time == "fixed" else b.members
            continue
        if active:
            if var.name in decl.vars:
                v = decl.vars[var.name]
                if not b.domain.contains(v):
                    # a member a domain check removed carries its reason (the domain library's rule)
                    why = b.domain.exclusion_reason(v) or var.domain.exclusion_reason(v)
                    problems.append(f"VAR {var.name}={v!r} outside {b.domain.describe()}"
                                    + (f": {why}" if why else ""))
                    continue
                if var.member_when:
                    why = _pick(member_exclusions(var, b.domain, lookup), v)
                    if why:
                        problems.append(f"VAR {var.name}={v!r}: {why}")
                        continue
            else:
                # a decision the block leaves out stands at its default: the first member the block's
                # other values admit, which the output names where it is not the domain's first
                v = default_under(var, b.domain, lookup) if var.member_when else b.domain.default()
                if v is None:
                    problems.append(f"missing VAR {var.name} ({b.domain.describe()} has no default)")
                    continue
                defaulted.append(var.name)
                if var.member_when and v != b.domain.default():
                    sib = (_pick(var.member_when, b.domain.default()) or ("", (), ""))[0]
                    defaulted_under[var.name] = {"default": v, "sibling": sib, "value": lookup(sib)[1]}
            values[var.name] = v
            outputs[f"decl.{var.name}"] = v
        elif var.name in decl.vars:
            problems.append(f"VAR {var.name} declared, but inactive")
    searched = {v.name for v in order if bindings.get(v.name) and bindings[v.name].time == "search"}
    for name in decl.vars:
        if name not in searched:
            problems.append(f"VAR {name} is not a searched variable")
    by_kind: dict[str, list] = {}
    for kind, tokens in decl.lines:
        lk = instance.template.line_kind(kind)
        if lk is None:
            problems.append(f"unknown line kind {kind!r}")
            continue
        try:
            by_kind.setdefault(kind, []).append(lk.parse(tokens))
        except Exception as e:  # noqa: BLE001
            problems.append(f"{kind} line {' '.join(tokens)!r}: {e}")
    for kind, entries in by_kind.items():
        lk = instance.template.line_kind(kind)
        outputs[f"decl.{kind}"] = entries
        if lk.check is not None:
            try:
                ok, detail = lk.check(ctx, entries)
            except Exception as e:  # noqa: BLE001
                ok, detail = False, f"{kind} check raised {e!r}"
            if not ok:
                problems.append(f"{kind}: {detail}")
    outputs["ok"] = not problems
    outputs["defaulted"] = defaulted
    outputs["defaulted_under"] = defaulted_under
    moved = "".join(f"; {n} defaults to {d['default']!r} under {d['sibling']}={d['value']!r}"
                    for n, d in defaulted_under.items())
    outputs["detail"] = ("; ".join(problems) if problems
                         else f"declaration ok ({len(decl.vars)} declared, {len(defaulted)} at defaults{moved})")
    return outputs
