"""Per-microarchitecture description registry (knowledge/arch).

One markdown file per architecture family, filed by domain:

    chialu/knowledge/arch/<domain>/<family>.md

The FAMILY NAME is the key tying three places together: the structural
definition in chialu/spaces (families, choices, slots — the machine
authority), this description file (the human/prompt text), and the yaml
`architectures:` spec that invokes the family. The md never defines
structure; it describes mechanism, trade-offs, and when the family
wins, and ends with a `## references` section of `handle -> citation`
lines whose handles resolve through the bibliography (and through
legacy/knowledge/pdf for the collected papers).

File shape:

    # <family>
    <description prose, first paragraph is the prompt summary>
    ## references
    handle -> Citation, "Title", venue, year

A card also carries a `## design choices` section: one `### <choice>`
table per design choice, one row per enum member, saying what the member
selects in the realization. `member_lint` requires every enum member to
be named by its family card or to carry a variant card of its own.

A card may also carry a `## realization` table, whose rows each state
one structural claim and the pattern the generated module's header must
match; `claim_lint` generates the module and checks it.

CLI:  python3 -m chialu.archdocs [--strict] [--members] [--gaps]
      lints coverage: families without a doc, docs naming no family,
      the enum members no card names, and the card claims the module
      headers do not meet.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

KNOWLEDGE = Path(__file__).resolve().parent / "knowledge"
ARCH_DIR = KNOWLEDGE / "arch"
PDF_DIR = Path(__file__).resolve().parents[1] / "legacy" / "knowledge" / "pdf"   # the collected papers, out of the agent's knowledge base

_REF_RE = re.compile(r"^(?:\*\s*)?([a-z0-9_]+)\s*->\s*(.+)$")


class FamilyDoc:
    def __init__(self, family, domain, path, body, references):
        self.family = family
        self.domain = domain
        self.path = path
        self.body = body                    # description prose
        self.references = references        # list[(handle, citation)]

    @property
    def summary(self):
        """First paragraph — what render_space inlines."""
        return self.body.split("\n\n")[0].strip()


def load_family_docs() -> dict:
    """family -> FamilyDoc for every knowledge/arch/*/*.md."""
    docs = {}
    if not ARCH_DIR.is_dir():
        return docs
    for p in sorted(ARCH_DIR.glob("*/*.md")):
        text = p.read_text()
        lines = text.splitlines()
        if not lines or not lines[0].startswith("# "):
            raise ValueError(f"{p}: first line must be '# <family>'")
        family = lines[0][2:].strip()
        if family != p.stem:
            raise ValueError(f"{p}: title {family!r} != filename stem")
        body_lines, refs, in_refs = [], [], False
        for ln in lines[1:]:
            if ln.strip().lower() == "## references":
                in_refs = True
                continue
            if in_refs:
                m = _REF_RE.match(ln.strip())
                if m:
                    refs.append((m.group(1), m.group(2)))
            else:
                body_lines.append(ln)
        docs[family] = FamilyDoc(family, p.parent.name, p,
                                 "\n".join(body_lines).strip(), refs)
    return docs


class VariantDoc:
    """A named microarchitecture inside a family: a pin into the
    family's design choices plus its own description.

        chialu/knowledge/arch/<domain>/<family>/<variant>.md

        ---
        family: parallel_prefix
        pin: {topology: kogge_stone}
        ---
        # kogge_stone
        <prose; first paragraph is the prompt summary>
        ## references
        handle -> citation
    """

    def __init__(self, name, family, pin, domain, path, body, references):
        self.name = name
        self.family = family
        self.pin = pin                      # {choice: value}
        self.domain = domain
        self.path = path
        self.body = body
        self.references = references

    @property
    def qualified(self):
        return f"{self.family}/{self.name}"

    @property
    def summary(self):
        return self.body.split("\n\n")[0].strip()

    def spec(self) -> dict:
        """The §9.5 select() spec this variant names."""
        return {"family": self.family, "pin": dict(self.pin)}


def _split_front_matter(text: str):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    import yaml
    fm = yaml.safe_load(text[3:end]) or {}
    return fm, text[end + 4:].lstrip("\n")


def _parse_doc_body(text: str, path: Path):
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError(f"{path}: first line must be '# <name>'")
    name = lines[0][2:].strip()
    if name != path.stem:
        raise ValueError(f"{path}: title {name!r} != filename stem")
    body_lines, refs, in_refs = [], [], False
    for ln in lines[1:]:
        if ln.strip().lower() == "## references":
            in_refs = True
            continue
        if in_refs:
            m = _REF_RE.match(ln.strip())
            if m:
                refs.append((m.group(1), m.group(2)))
        else:
            body_lines.append(ln)
    return name, "\n".join(body_lines).strip(), refs


def load_variant_docs() -> dict:
    """qualified 'family/variant' -> VariantDoc for every
    knowledge/arch/*/*/*.md."""
    docs = {}
    if not ARCH_DIR.is_dir():
        return docs
    for p in sorted(ARCH_DIR.glob("*/*/*.md")):
        fm, body = _split_front_matter(p.read_text())
        family = fm.get("family") or p.parent.name
        if family != p.parent.name:
            raise ValueError(f"{p}: family {family!r} != folder "
                             f"{p.parent.name!r}")
        pin = fm.get("pin") or {}
        if not isinstance(pin, dict) or not pin:
            raise ValueError(f"{p}: front matter needs pin: {{choice: value}}")
        name, text, refs = _parse_doc_body(body, p)
        docs[f"{family}/{name}"] = VariantDoc(name, family, pin,
                                             p.parent.parent.name, p, text,
                                             refs)
    return docs


_VARIANTS = None


def variant_table() -> dict:
    """qualified and (where unique) bare variant names -> VariantDoc."""
    global _VARIANTS
    if _VARIANTS is None:
        docs = load_variant_docs()
        table = dict(docs)
        bare = {}
        for q, d in docs.items():
            bare.setdefault(d.name, []).append(d)
        for n, ds in bare.items():
            if len(ds) == 1 and n not in table:
                table[n] = ds[0]
        _VARIANTS = table
    return _VARIANTS


def resolve_variant(name: str) -> VariantDoc:
    t = variant_table()
    if name in t:
        return t[name]
    cands = sorted(q for q in t if "/" in q and q.endswith("/" + name))
    if cands:
        raise KeyError(f"variant {name!r} is ambiguous: {cands}; "
                       f"use family/variant")
    raise KeyError(f"no variant {name!r} (known: "
                   f"{sorted(q for q in t if '/' in q)[:12]}...)")


def variants_of(family: str) -> list:
    return sorted((d for q, d in variant_table().items()
                   if "/" in q and d.family == family),
                  key=lambda d: d.name)


_PDF_MAP = None


def pdf_map() -> dict:
    """handle -> pdf filename, from legacy/knowledge/pdf/handles.json (the
    persisted reconciliation of the collected corpus against the
    bibliography), plus handle-named files."""
    global _PDF_MAP
    if _PDF_MAP is None:
        import json
        m = {}
        idx = PDF_DIR / "handles.json"
        if idx.exists():
            m = {h: f for h, f in json.loads(idx.read_text()).items()
                 if (PDF_DIR / f).exists()}
        _PDF_MAP = m
    return _PDF_MAP


def pdf_available(handle: str) -> bool:
    return handle in pdf_map() or (PDF_DIR / f"{handle}.pdf").exists()


def pdf_path(handle: str):
    """Path to the paper's pdf, or None (the on_request serving hook)."""
    f = pdf_map().get(handle)
    if f:
        return PDF_DIR / f
    p = PDF_DIR / f"{handle}.pdf"
    return p if p.exists() else None


# ---- the enum members' coverage by the cards ---------------------------------------------------
#
# Every enum member of every family's design choices is named in the family's card, in a
# per-choice table or in the prose, or carries a variant card of its own. A member named
# nowhere in the knowledge path is a menu entry the agent reads as an identifier alone, so
# the lint reports it; item 6 of docs/work-plan.md records the decision.

# (family|choice|member, reason): the members no card names on purpose. Each pattern is an
# fnmatch over "family|choice|member"; the reason states why the identifier stands alone.
MEMBER_ALLOWLIST = ()


def _family_table() -> dict:
    """family -> (domain, Family) over every space, the sub-slot spaces
    included (the domain is the one whose space opens the slot)."""
    from chialu.papers import _all_spaces
    out = {}

    def walk(domain, space):
        for a in space.candidates:
            out.setdefault(a.family, (domain, a))
            for sub in a.components.values():
                walk(domain, sub)
    for space in _all_spaces():
        for a in space.candidates:
            p = ARCH_DIR.glob(f"*/{a.family}.md")
            dom = next(p, None)
            walk(dom.parent.name if dom is not None else "?", space)
    return out


def _name_lines(path: Path, name: str) -> str:
    """`path:line` of the first line naming `name` as a word, or ''."""
    if not path or not path.is_file():
        return ""
    pat = re.compile(r"\b" + re.escape(name) + r"\b")
    for i, ln in enumerate(path.read_text().splitlines(), 1):
        if ln.strip().lower() == "## references":
            break
        if pat.search(ln):
            return f"{path.relative_to(KNOWLEDGE.parent.parent)}:{i}"
    return ""


def member_rows() -> list:
    """One row per (family, choice, enum member): how the knowledge path
    describes it. `status` is `variant` (a variant card pins it), `card`
    (the family card names it), `number` (a numeric member, which the
    choice's range describes), or `undescribed`."""
    from adir.domains import Enum
    fams = _family_table()
    docs = load_family_docs()
    vdocs = load_variant_docs()
    pinned = {}
    for q, v in vdocs.items():
        for k, val in v.pin.items():
            pinned.setdefault((v.family, k, str(val)), v)
    rows = []
    for fam, (domain, a) in sorted(fams.items()):
        doc = docs.get(fam)
        path = doc.path if doc else None
        for choice, dom in (a.design_choices or {}).items():
            if not isinstance(dom, Enum):
                continue
            for m in dom.members_:
                key = f"{fam}|{choice}|{m}"
                r = {"domain": domain, "family": fam, "choice": choice, "member": m,
                     "card": str(path.relative_to(KNOWLEDGE.parent.parent)) if path else ""}
                v = pinned.get((fam, choice, str(m)))
                if v is not None:
                    r.update(status="variant",
                             evidence=str(v.path.relative_to(KNOWLEDGE.parent.parent)))
                elif not isinstance(m, str):
                    r.update(status="number", evidence="")
                else:
                    ev = _name_lines(path, m)
                    r.update(status="card" if ev else "undescribed", evidence=ev)
                r["allowed"] = next((why for pat, why in MEMBER_ALLOWLIST
                                     if fnmatch.fnmatch(key, pat)), "")
                rows.append(r)
    return rows


def member_lint(rows=None) -> dict:
    """The member rows split by status; `findings` are the undescribed
    members no allowlist row covers."""
    rows = member_rows() if rows is None else rows
    by = {}
    for r in rows:
        by.setdefault(r["status"], []).append(r)
    findings = [r for r in by.get("undescribed", []) if not r["allowed"]]
    return {"rows": rows, "by_status": by, "findings": findings,
            "allowed": [r for r in by.get("undescribed", []) if r["allowed"]]}


# ---- the cards' structural claims against the realizations --------------------------------------
#
# A card may carry a `## realization` table whose rows each state one structural claim and the
# pattern the generated module's header must match:
#
#     ## realization
#
#     | claim | pins | the module header matches |
#     | --- | --- | --- |
#     | the lines are sized to the exponent range | alignment_strategy=exponent_sorted_realignment_lines | `realignment lines: \d+ lines of \d+ bits` |
#
# `claim_lint` generates each row's module through the coverage tool's realizer and matches the
# pattern against the module's leading comment. The check is of the header's own words: it catches
# a realization whose header contradicts the card (a technique's point dropped, a width raised to
# the frame), and it does not prove the netlist below the header. What proves that a member changes
# the netlist is `chialu.targets.rtl.families.coverage`.

_CLAIM_HEAD = re.compile(r"^\|\s*claim\s*\|", re.I)


def _header_of(text: str) -> str:
    """The module's leading comment: every `//` line before the first
    `module` keyword."""
    out = []
    for ln in text.splitlines():
        st = ln.strip()
        if st.startswith("module "):
            break
        if st.startswith("//"):
            out.append(st[2:].strip())
    return " ".join(out)


def _claim_table(doc) -> list:
    """[(claim, pins, pattern, line)] of a card's `## realization`
    table."""
    rows, in_sec, lineno = [], False, 0
    for i, ln in enumerate(doc.path.read_text().splitlines(), 1):
        st = ln.strip()
        if st.lower().startswith("## "):
            in_sec = st.lower() == "## realization"
            continue
        if not in_sec or not st.startswith("|"):
            continue
        cells = [c.strip() for c in st.strip("|").split("|")]
        if len(cells) != 3 or _CLAIM_HEAD.match(st) or set(cells[0]) <= set("- "):
            continue
        claim, pin_s, pat = cells
        pins = {}
        if pin_s and pin_s != "-":
            for part in pin_s.split(";"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    pins[k.strip()] = v.strip()
        rows.append((claim, pins, pat.strip().strip("`"), i))                # `kind=` names the parent
        lineno = i
    return rows


# the kind a card's domain names, where the space walk does not place the family
CLAIM_KIND = {"dot": "dot", "fp": "fp_adder", "adder": "adder", "mul": "multiplier", "div": "divider",
              "shift": "shifter", "round": "rounder", "sfu": "sfu", "checker": "checker",
              "decimal": "adder", "redundant": "adder", "approx": "adder", "unpack": "unpacker",
              "logic": "logic", "dsp": "posit_unit"}
_KIND_OF: dict = {}


def kind_of_family(family: str, domain: str = "") -> str:
    """The kind whose space opens a family, from the coverage tool's own
    space walk; the card's domain names it where the walk does not."""
    if not _KIND_OF:
        from chialu.targets.rtl.families import coverage as COV
        # a family's kind is the kind whose space opens it at the top level. A component slot
        # (`sub_adder`, `upper_adder`, `tile_adder`) names a place inside a family rather than a
        # kind, and no realizer answers to it, so the slots are walked in a second pass, only the
        # slots whose name is itself a root kind are recorded, and they fill in the families no
        # root opens. A family neither path reaches falls back to its card's domain.
        from_slot: dict = {}
        roots = set(COV.roots())

        def walk(kind, space, top: bool):
            for a in space.candidates:
                if top or kind in roots:
                    (_KIND_OF if top else from_slot).setdefault(a.family, kind)
                for slot, sub in a.components.items():
                    walk(slot, sub, False)
        for kind, spaces in COV.roots().items():
            for space, _opener in spaces:
                walk(kind, space, True)
        for fam, kind in from_slot.items():
            _KIND_OF.setdefault(fam, kind)
    return _KIND_OF.get(family) or CLAIM_KIND.get(domain, domain)

# (family, reason): the claim rows whose module the realizer cannot build here
CLAIM_ALLOWLIST = ()


def claim_rows(kind_of=None) -> list:
    """One row per card claim: the module generated, its header, and
    whether the claim's pattern matches."""
    from chialu.targets.rtl.families import coverage as COV
    docs = load_family_docs()
    out = []
    for fam, doc in sorted(docs.items()):
        for claim, pins, pat, line in _claim_table(doc):
            pins = dict(pins)
            # `kind=` and `family=` name the parent a slot family is realized inside
            kind = pins.pop("kind", None) or (kind_of or {}).get(fam) or kind_of_family(fam, doc.domain)
            built = pins.pop("family", None) or fam
            r = {"family": fam, "domain": doc.domain, "kind": kind, "built": built, "claim": claim,
                 "pins": pins, "pattern": pat,
                 "where": f"{doc.path.relative_to(KNOWLEDGE.parent.parent)}:{line}"}
            try:
                got = COV.realize(kind, built, dict(pins))
            except Exception as e:                              # noqa: BLE001 - the generator's own reason
                r.update(status="ungenerated", detail=f"{type(e).__name__}: {str(e)[:120]}", header="")
                out.append(r)
                continue
            if got is None:
                r.update(status="ungenerated", detail=f"the kind {kind!r} has no realizer", header="")
                out.append(r)
                continue
            head = _header_of(got[1])
            r["header"] = head[:400]
            r["module"] = got[0]
            try:
                ok = re.search(pat, head) is not None
            except re.error as e:
                r.update(status="bad_pattern", detail=str(e))
                out.append(r)
                continue
            r.update(status="ok" if ok else "mismatch", detail="" if ok else "the header does not match")
            out.append(r)
    for r in out:
        r["allowed"] = next((why for p, why in CLAIM_ALLOWLIST
                             if fnmatch.fnmatch(f"{r['family']}|{r['claim']}", p)), "")
    return out


def claim_lint(rows=None) -> dict:
    """The claim rows split by status; `findings` are the mismatched,
    ungenerated or malformed rows no allowlist row covers."""
    rows = claim_rows() if rows is None else rows
    by = {}
    for r in rows:
        by.setdefault(r["status"], []).append(r)
    findings = [r for r in rows if r["status"] != "ok" and not r["allowed"]]
    docs = load_family_docs()
    claimed = {r["family"] for r in rows}
    return {"rows": rows, "by_status": by, "findings": findings,
            "with_claims": len(claimed), "without_claims": sorted(set(docs) - claimed)}


# ---- the corpus's gap reviews -------------------------------------------------------------------
#
# `legacy/knowledge/extract/gaps/<family>.md` holds the review a card writer left for the space:
# the choices, values and ranges the notes suggested the family should carry. `gap_triage` places
# every review in one state and every open proposal in one class, so the reviews are closed against
# the record rather than read one at a time. The classifier reads the proposed choice's NAME; a name
# it cannot place falls to `structural`, which is the set a person reviews against the standing rule
# of docs/deferred-families.md. docs/knowledge-gaps.md records the decision per state.

GAP_DIR = KNOWLEDGE.parent.parent / "legacy" / "knowledge" / "extract" / "gaps"

_GAP_PROP = re.compile(r"`([a-z0-9_]+)(?:\.[a-z0-9_]+)?\s*:")
_GAP_PROP2 = re.compile(r"choices?\s+`([a-z0-9_]+)`")

# the classes the standing rule excludes: a proposal whose name places it here selects no structure
# of a single-cycle binary unit, so the review closes without a space change
GAP_CLASSES = (
    ("circuit", re.compile(r"logic_style|circuit_style|circuit_mapping|transistor|gate_substitution|"
                           r"_gate_type|circuit_type|cell_|_cell$|layout|wire_|drive|buffer|technology|"
                           r"voltage|power_gat|device_mapping|physical_malleability|gate_delay_model|"
                           r"input_pin_assignment")),
    ("sequential", re.compile(r"clock|pipelin|double_pumped|stage_count|latency|iteration_count|"
                              r"control_placement|schedule|microarchitecture_organization|sequential|"
                              r"passes_|reuse_cycles|throughput|recurrence_copies|digit_iteration_sharing")),
    ("interface", re.compile(r"support$|_support|interface|port|context|operand_source|integration|"
                             r"instruction|isa_|exception|flag_|rounding_mode|format_|precision_support|"
                             r"^operation$|^operation_set$|checker_input_configuration")),
    ("method", re.compile(r"objective|optimization|solution_multiplicity|search|profile|policy|metrics|"
                          r"calibration|training|synthesis|constraint|accuracy_level|estimator|"
                          r"gate_delay_model")),
)


def gap_class(name: str) -> str:
    for label, pat in GAP_CLASSES:
        if pat.search(name):
            return label
    return "structural"


def gap_triage() -> dict:
    """Every gap review in one state: `left_space` (the family is
    deferred), `no_module` (the family has no realization of its own),
    `applied` (the space carries every proposal) or `open`. An open
    review's proposals are counted per class."""
    from chialu.targets.rtl import families as FAM
    docs = load_family_docs()
    fams = _family_table()
    rows = []
    if not GAP_DIR.is_dir():
        return {"rows": rows, "states": {}, "classes": {}}
    for p in sorted(GAP_DIR.glob("*.md")):
        fam = p.stem
        a = fams.get(fam)
        bullets = [l for l in p.read_text().splitlines() if l.strip().startswith("* ")]
        props = set()
        for b in bullets:
            props |= set(_GAP_PROP.findall(b)) | set(_GAP_PROP2.findall(b))
        have = (set(a[1].design_choices or {}) | set(a[1].components or {})) if a else set()
        kind = kind_of_family(fam, docs[fam].domain if fam in docs else "") if a else ""
        realized = bool(a) and bool(FAM.has_module(kind, fam))
        open_ = sorted(props - have)
        state = ("left_space" if a is None else
                 "no_module" if not realized else
                 "applied" if not open_ else "open")
        rows.append({"family": fam, "kind": kind, "state": state, "bullets": len(bullets),
                     "proposed": sorted(props), "covered": sorted(props & have), "open": open_,
                     "classes": {n: gap_class(n) for n in open_},
                     "where": str(p.relative_to(KNOWLEDGE.parent.parent))})
    states: dict = {}
    classes: dict = {}
    for r in rows:
        states[r["state"]] = states.get(r["state"], 0) + 1
        if r["state"] != "open":                 # a review that closes on its state has no open proposal
            continue
        for _n, c in r["classes"].items():
            classes[c] = classes.get(c, 0) + 1
    return {"rows": rows, "states": states, "classes": classes}


def _all_families() -> dict:
    """family -> domain hint, from every registered space, INCLUDING
    the families reachable only through component slots (reduction
    trees, digit-selection tables, alignment shifters, ...): a slot
    family is a microarchitecture like any other and needs its doc."""
    from chialu.papers import _all_spaces
    fams = {}

    def walk(space):
        for a in space.candidates:
            fams.setdefault(a.family, set())
            for sub in a.components.values():
                walk(sub)
    for space in _all_spaces():
        walk(space)
    return fams


def lint(docs=None):
    docs = docs if docs is not None else load_family_docs()
    fams = _all_families()
    missing = sorted(set(fams) - set(docs))
    orphans = sorted(set(docs) - set(fams))
    bad_refs = []
    from chialu.papers import PaperDB
    from chialu.papers import PAPER_DB
    for d in docs.values():
        for h, _c in d.references:
            if h not in PAPER_DB.papers:
                bad_refs.append(f"{d.path.name}: unknown handle {h}")
    # variants: pin must name a real choice/value of a real family
    bad_variants = []
    arch_of = {}
    from chialu.papers import _all_spaces

    def walk_arch(space):
        for a in space.candidates:
            arch_of.setdefault(a.family, a)
            for sub in a.components.values():
                walk_arch(sub)
    for space in _all_spaces():
        walk_arch(space)
    try:
        vdocs = load_variant_docs()
    except ValueError as e:
        vdocs = {}
        bad_variants.append(str(e))
    for q, v in vdocs.items():
        a = arch_of.get(v.family)
        if a is None:
            bad_variants.append(f"{q}: no such family")
            continue
        for k, val in v.pin.items():
            if k not in a.design_choices:
                bad_variants.append(f"{q}: no choice {k!r} in {v.family}")
            elif not a.design_choices[k].contains(val):
                bad_variants.append(f"{q}: {k}={val!r} outside "
                                    f"{a.design_choices[k].describe()}")
        if v.family not in docs:
            bad_variants.append(f"{q}: family has no doc of its own")
        for h, _c in v.references:
            if h not in PAPER_DB.papers:
                bad_refs.append(f"{q}: unknown handle {h}")
    # a family name two domains share (rounder and unpacker both have a
    # shared_per_lane): legitimate under different kinds, but a card lookup
    # by bare name is ambiguous, so the prompt sources resolve it by the slot
    by_name: dict = {}
    for p in sorted(ARCH_DIR.glob("*/*.md")):
        by_name.setdefault(p.stem, []).append(p.parent.name)
    shared = {n: ds for n, ds in by_name.items() if len(ds) > 1}
    return {"families": len(fams), "documented": len(docs),
            "missing": missing, "orphans": orphans, "bad_refs": bad_refs,
            "variants": len(vdocs), "bad_variants": bad_variants,
            "shared_names": shared}


def main():
    import sys
    strict = "--strict" in sys.argv
    verbose = "--members" in sys.argv
    if "--gaps" in sys.argv:
        t = gap_triage()
        print(f"[archdocs] {len(t['rows'])} gap reviews: " +
              ", ".join(f"{n} {k}" for k, n in sorted(t["states"].items())))
        print("[archdocs] the open reviews' proposals: " +
              ", ".join(f"{n} {k}" for k, n in sorted(t["classes"].items())))
        for r in sorted((x for x in t["rows"] if x["state"] == "open"), key=lambda r: (r["kind"], r["family"])):
            st = [n for n in r["open"] if r["classes"][n] == "structural"]
            print(f"  {r['family']:36s} {r['kind']:14s} {len(st):3d} structural, "
                  f"{len(r['open']) - len(st)} excluded  ({r['where']})")
        return 0
    r = lint()
    print(f"[archdocs] {r['documented']} docs for {r['families']} "
          f"families; {len(r['missing'])} undocumented; "
          f"{r['variants']} variant docs")
    mr = member_lint()
    n = {k: len(v) for k, v in mr["by_status"].items()}
    print(f"[archdocs] enum members: {n.get('card', 0)} named by a family card, "
          f"{n.get('variant', 0)} with a variant card, {n.get('number', 0)} numeric, "
          f"{len(mr['findings'])} undescribed, {len(mr['allowed'])} allowed")
    for f in mr["findings"] if verbose or len(mr["findings"]) <= 40 else mr["findings"][:40]:
        print(f"  UNDESCRIBED MEMBER: {f['family']}.{f['choice']} = {f['member']}  ({f['card'] or 'no card'})")
    if len(mr["findings"]) > 40 and not verbose:
        print(f"  ... {len(mr['findings']) - 40} more (--members lists them)")
    cr = claim_lint()
    print(f"[archdocs] card claims: {len(cr['by_status'].get('ok', []))} met by the module header, "
          f"{len(cr['findings'])} unmet, over {cr['with_claims']} families "
          f"({len(cr['without_claims'])} cards state none)")
    for f in cr["findings"]:
        print(f"  UNMET CLAIM: {f['family']} ({f['where']}): {f['detail']}")
        print(f"      claim:   {f['claim']}")
        print(f"      pattern: {f['pattern']}")
        if f["header"]:
            print(f"      header:  {f['header'][:200]}")
    for o in r["orphans"]:
        print(f"  ORPHAN doc (no such family): {o}")
    for n, ds in r["shared_names"].items():
        print(f"  SHARED NAME: {n} in {', '.join(ds)} (resolved by the slot in the prompt)")
    for b in r["bad_refs"]:
        print(f"  BAD REF: {b}")
    for b in r["bad_variants"]:
        print(f"  BAD VARIANT: {b}")
    if strict and r["missing"]:
        for m in r["missing"]:
            print(f"  missing doc: {m}")
    fail = (r["orphans"] or r["bad_refs"] or r["bad_variants"]
            or mr["findings"] or cr["findings"] or (strict and r["missing"]))
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
