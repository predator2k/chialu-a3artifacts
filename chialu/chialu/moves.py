"""The move library: word- and bit-level rewrites the level-2
micro-optimizer may propose (knowledge/moves/<id>.md).

Each file carries YAML front matter (id, tier, applies_to, preserves,
check, effect, sources) and three prose fields (pattern, rewrite,
when). `applies_to` names domains (adder, mul, div, fp, dot, shift,
checker, sfu, decimal, redundant, approx, dsp, alu) or families;
`render_menu(families, domains)` returns the entries that apply,
formatted for the prompt.

CLI:  python3 -m chialu.moves            lint + counts
      python3 -m chialu.moves <family>   the menu for one family
"""

from __future__ import annotations

import re
from pathlib import Path

from chialu.archdocs import KNOWLEDGE, _split_front_matter

MOVES_DIR = KNOWLEDGE / "moves"
DOMAINS = {"adder", "mul", "div", "fp", "dot", "shift", "checker", "sfu",
           "decimal", "redundant", "approx", "dsp", "alu"}
TIERS = {"bit", "word", "structural"}
PRESERVES = {"bit_exact", "error_bounded", "latency_neutral"}
CHECKS = {"tb", "cec", "error_budget"}


class Move:
    def __init__(self, meta: dict, title: str, fields: dict, path: Path):
        self.id = meta["id"]
        self.tier = meta.get("tier", "word")
        self.applies_to = list(meta.get("applies_to") or [])
        self.preserves = meta.get("preserves", "bit_exact")
        self.check = meta.get("check", "tb")
        self.effect = meta.get("effect", "")
        self.sources = list(meta.get("sources") or [])
        self.title = title
        self.pattern = fields.get("pattern", "")
        self.rewrite = fields.get("rewrite", "")
        self.when = fields.get("when", "")
        self.path = path

    def applies(self, families: set, domains: set) -> bool:
        return any(a in families or a in domains for a in self.applies_to)

    def render(self) -> str:
        return (f"* {self.id} [{self.tier}; preserves {self.preserves}; "
                f"check {self.check}; effect {self.effect}]: {self.title}\n"
                f"    pattern: {self.pattern}\n"
                f"    rewrite: {self.rewrite}\n"
                f"    when: {self.when}")


_FIELD_RE = re.compile(r"^(pattern|rewrite|when):\s*(.*)$", re.M | re.S)


def load_moves(moves_dir=None) -> dict:
    d = Path(moves_dir) if moves_dir else MOVES_DIR
    out = {}
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.md")):
        if p.name == "README.md":
            continue
        meta, body = _split_front_matter(p.read_text())
        if "id" not in meta:
            raise ValueError(f"{p}: front matter needs id:")
        lines = body.splitlines()
        title = lines[0][2:].strip() if lines and lines[0].startswith("# ") \
            else meta["id"]
        fields = {}
        for block in body.split("\n\n"):
            m = re.match(r"^(pattern|rewrite|when):\s*(.*)$", block.strip(),
                         re.S)
            if m:
                fields[m.group(1)] = " ".join(m.group(2).split())
        out[meta["id"]] = Move(meta, title, fields, p)
    return out


def render_menu(families, domains=(), moves=None, limit: int = 40) -> str:
    """The prompt block: every move that applies to one of the families
    or domains, tier order bit < word < structural."""
    moves = moves if moves is not None else load_moves()
    fam, dom = set(families), set(domains)
    order = {"bit": 0, "word": 1, "structural": 2}
    sel = sorted((m for m in moves.values() if m.applies(fam, dom)),
                 key=lambda m: (order.get(m.tier, 9), m.id))
    return "\n".join(m.render() for m in sel[:limit]) or "none"


def lint(moves=None) -> dict:
    from chialu.archdocs import _all_families
    from chialu.papers import PAPER_DB
    moves = moves if moves is not None else load_moves()
    fams = set(_all_families())
    problems = []
    for m in moves.values():
        if m.tier not in TIERS:
            problems.append(f"{m.id}: tier {m.tier!r}")
        if m.preserves not in PRESERVES:
            problems.append(f"{m.id}: preserves {m.preserves!r}")
        if m.check not in CHECKS:
            problems.append(f"{m.id}: check {m.check!r}")
        for a in m.applies_to:
            if a not in DOMAINS and a not in fams:
                problems.append(f"{m.id}: applies_to {a!r} is neither a "
                                f"domain nor a family")
        for h in m.sources:
            if h not in PAPER_DB.papers:
                problems.append(f"{m.id}: unknown source handle {h}")
        if not (m.pattern and m.rewrite):
            problems.append(f"{m.id}: pattern/rewrite missing")
    return {"moves": len(moves), "problems": problems}


def main(argv=None):
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        from chialu.extract import family_domains
        fd = family_domains()
        fams = set(argv)
        doms = {fd[f][0] for f in fams if f in fd}
        print(render_menu(fams, doms))
        return 0
    r = lint()
    print(f"[moves] {r['moves']} moves; {len(r['problems'])} problems")
    for p in r["problems"]:
        print("  " + p)
    return 1 if r["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
