"""Artifacts (design section 5.1): what a candidate is made of, the
mutable set, member families, and the program a backend rewrites.

A seed artifact's program carries `EVOLVE-BLOCK-START`/`END` around the
regions the `evolve` list names, one `ADIR-MEMBER <name>` marker per
member of a family, and the declaration block at the top of the first
mutable region. `split_program` and `fixed_part` undo that at
evaluation time; `evolve_bounds` compares the fixed part of a candidate
with the seeds'."""
from __future__ import annotations

import fnmatch
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .declaration import comment_prefix, parse_block, render_block
from .errors import BindError
from .yamlfile import check_keys

ROLES = ("seed", "fixed", "baseline", "input")
KINDS = ("text", "repo")
SOURCES = ("generated", "file", "checkout")
ART_KEYS = ("role", "kind", "source", "file", "path", "base_rev", "language",
            "evolve", "members", "indexed_by", "declaration_member", "declaration_file")
EVOLVE_START = "EVOLVE-BLOCK-START"
EVOLVE_END = "EVOLVE-BLOCK-END"
MEMBER_MARK = "ADIR-MEMBER"


@dataclass
class Artifact:
    path: str
    role: str
    kind: str = "text"
    source: str = "generated"
    file: str = ""
    repo_path: str = ""
    base_rev: str = ""
    language: str = "text"
    evolve: list = field(default_factory=list)
    members: Optional[list] = None
    indexed_by: Optional[str] = None
    declaration_member: Optional[str] = None
    declaration_file: str = ".adir/declaration.txt"
    texts: dict = field(default_factory=dict)      # member ("" when none) -> text
    sha256: dict = field(default_factory=dict)

    @property
    def is_family(self) -> bool:
        return self.members is not None

    @property
    def text(self) -> str:
        if self.is_family:
            return "\n".join(self.texts[m] for m in self.members)
        return self.texts.get("", "")

    def prefix(self, extra=None) -> str:
        return comment_prefix(self.language, extra)


def parse_artifact(path: str, raw: dict, yaml_path: str) -> Artifact:
    p = f"artifacts.{path}"
    check_keys(raw, ART_KEYS, p)
    a = Artifact(path=path, role=raw.get("role", ""), kind=raw.get("kind", "text"),
                 source=raw.get("source", "generated"), file=str(raw.get("file", "") or ""),
                 repo_path=str(raw.get("path", "") or ""), base_rev=str(raw.get("base_rev", "") or ""),
                 language=str(raw.get("language", "text") or "text"),
                 evolve=list(raw.get("evolve") or []),
                 members=list(raw["members"]) if raw.get("members") is not None else None,
                 indexed_by=raw.get("indexed_by"),
                 declaration_member=raw.get("declaration_member"),
                 declaration_file=raw.get("declaration_file", ".adir/declaration.txt"))
    if a.role not in ROLES:
        raise BindError(p, f"role {a.role!r} (one of {ROLES})")
    if a.kind not in KINDS:
        raise BindError(p, f"kind {a.kind!r} (one of {KINDS})")
    if a.source not in SOURCES:
        raise BindError(p, f"source {a.source!r} (one of {SOURCES})")
    if a.source == "file" and not a.file:
        raise BindError(p, "source: file needs `file`")
    if a.source == "checkout" and not a.repo_path:
        raise BindError(p, "source: checkout needs `path`")
    if a.role == "seed" and a.kind == "text" and not a.evolve:
        raise BindError(p, "a seed artifact needs an `evolve` list (`['*']` for the whole text)")
    if a.members is not None and a.indexed_by is not None:
        raise BindError(p, "members or indexed_by, not both")
    return a


def resolve_file(file: str, yaml_dir: Path) -> Path:
    f = Path(file)
    if f.is_absolute():
        return f
    for root in (yaml_dir, Path.cwd()):
        if (root / f).is_file():
            return root / f
    return yaml_dir / f


def materialize(a: Artifact, template, ctx, yaml_dir: Path, index_sets: dict):
    """Fill `texts` from the generator, the file or the checkout."""
    if a.indexed_by is not None:
        if a.indexed_by not in index_sets:
            raise BindError(f"artifacts.{a.path}", f"indexed_by {a.indexed_by!r} is not an "
                                                   f"index set the elaboration provides "
                                                   f"(has: {sorted(index_sets)})")
        a.members = [str(x) for x in index_sets[a.indexed_by]]
    if a.source == "generated":
        gen = template.generators.get(a.path)
        if gen is None:
            raise BindError(f"artifacts.{a.path}", f"source: generated, but {template.name} "
                                                   f"registers no generator for {a.path!r} "
                                                   f"(has: {sorted(template.generators)})")
        out = gen(ctx)
        if a.is_family:
            if not isinstance(out, dict):
                raise BindError(f"artifacts.{a.path}", "the generator of a family must return "
                                                       "{member: text}")
            missing = [m for m in a.members if m not in out]
            if missing:
                raise BindError(f"artifacts.{a.path}", f"the generator wrote no text for {missing}")
            a.texts = {m: str(out[m]) for m in a.members}
        else:
            if isinstance(out, dict):
                raise BindError(f"artifacts.{a.path}", "the generator returned members for an "
                                                       "artifact without `members`")
            a.texts = {"": str(out)}
    elif a.source == "file":
        if a.is_family:
            texts = {}
            for m in a.members:
                f = resolve_file(a.file.replace("*", m), yaml_dir)
                if not f.is_file():
                    raise BindError(f"artifacts.{a.path}", f"no file {f} for member {m}")
                texts[m] = f.read_text()
            a.texts = texts
        else:
            f = resolve_file(a.file, yaml_dir)
            if not f.is_file():
                raise BindError(f"artifacts.{a.path}", f"no file {f}")
            a.texts = {"": f.read_text()}
    else:
        a.texts = {}
    a.sha256 = {m: hashlib.sha256(t.encode()).hexdigest() for m, t in a.texts.items()}


# ---------------------------------------------------------------- regions

_SV_MODULE = re.compile(r"^[ \t]*(?:module|package|interface)\s+([A-Za-z_]\w*)", re.M)
_SV_END = re.compile(r"^[ \t]*(?:endmodule|endpackage|endinterface)\b.*$", re.M)
_PY_DEF = re.compile(r"^([ \t]*)(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)", re.M)
_C_FUNC = re.compile(r"^(?![ \t])[^;{}#\n]*?\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*(?:const\s*)?\{", re.M)
_C_TYPE = re.compile(r"^(?:typedef\s+)?(?:struct|class|union|enum)\s+([A-Za-z_]\w*)\b[^;{]*\{", re.M)


def _brace_end(text: str, open_pos: int) -> int:
    depth, i, n = 0, open_pos, len(text)
    in_str = None
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == in_str:
                in_str = None
        elif c in "\"'":
            in_str = c
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                j = text.find("\n", i)
                return n if j < 0 else j + 1
        i += 1
    return n


def _line_start(text, pos):
    return text.rfind("\n", 0, pos) + 1


def find_regions(text: str, evolve: list, language: str, strict: bool = True) -> list:
    """(start, end, name) of every region an `evolve` entry names, in
    text order; `*` is the whole text. Under `strict` a named entry the
    text lacks, or no region at all, is an error; a member of a family
    is scanned without it (its regions may all lie in other members)."""
    if any(e == "*" for e in evolve):
        return [(0, len(text), "*")]
    regions = []
    for m in _SV_MODULE.finditer(text):
        name = m.group(1)
        if any(fnmatch.fnmatchcase(name, e) for e in evolve):
            end = _SV_END.search(text, m.end())
            regions.append((_line_start(text, m.start()),
                            len(text) if end is None else end.end() + 1, name))
    for m in _PY_DEF.finditer(text):
        name = m.group(2)
        if not any(fnmatch.fnmatchcase(name, e) for e in evolve):
            continue
        indent = len(m.group(1))
        pos = text.find("\n", m.end())
        end = len(text)
        while pos >= 0 and pos < len(text):
            nxt = text.find("\n", pos + 1)
            line = text[pos + 1: len(text) if nxt < 0 else nxt]
            if line.strip() and (len(line) - len(line.lstrip())) <= indent:
                end = pos + 1
                break
            pos = nxt
        regions.append((_line_start(text, m.start()), end, name))
    for rx, grp in ((_C_FUNC, 1), (_C_TYPE, 1)):
        for m in rx.finditer(text):
            name = m.group(grp)
            if any(fnmatch.fnmatchcase(name, e) for e in evolve):
                regions.append((_line_start(text, m.start()),
                                _brace_end(text, m.end() - 1), name))
    regions.sort()
    # drop regions nested in another region
    out = []
    for r in regions:
        if out and r[0] < out[-1][1]:
            if r[1] <= out[-1][1]:
                continue
            raise BindError("evolve", f"regions {out[-1][2]} and {r[2]} overlap")
        out.append(r)
    if not strict:
        return out
    found = {r[2] for r in out}
    missing = [e for e in evolve if "*" not in e and "?" not in e and e not in found]
    if missing:
        raise BindError("evolve", f"names {missing} not found in the artifact")
    if not out:
        raise BindError("evolve", f"no region matches {evolve}")
    return out


def mark_regions(text: str, regions: list, prefix: str, declaration: str | None) -> str:
    """The text with EVOLVE markers, the declaration block inserted at
    the top of the first region when the text has none."""
    p = f"{prefix} " if prefix else ""
    out, pos, first = [], 0, True
    for start, end, _name in regions:
        out.append(text[pos:start])
        out.append(f"{p}{EVOLVE_START}\n")
        if first and declaration and not parse_block(text).present:
            out.append(declaration)
        first = False
        out.append(text[start:end])
        if not text[start:end].endswith("\n"):
            out.append("\n")
        out.append(f"{p}{EVOLVE_END}\n")
        pos = end
    out.append(text[pos:])
    return "".join(out)


def assemble_program(a: Artifact, texts: dict, declaration: str | None, extra_comment=None) -> str:
    """The program a backend rewrites: markers around the mutable
    regions of every member, a member marker per member."""
    prefix = a.prefix(extra_comment)
    if a.kind == "repo":
        raise BindError(f"artifacts.{a.path}", "a repo artifact has no single program text")
    decl_member = a.declaration_member or (a.members[0] if a.is_family else "")
    parts = []
    for member in (a.members if a.is_family else [""]):
        text = texts[member]
        regions = find_regions(text, a.evolve, a.language, strict=not a.is_family)
        marked = mark_regions(text, regions, prefix,
                              declaration if member == decl_member else None)
        if a.is_family:
            parts.append(f"{prefix} {MEMBER_MARK} {member}\n".lstrip() + marked)
        else:
            parts.append(marked)
    return "".join(parts)


def split_program(a: Artifact, program: str) -> dict:
    """member -> marked text."""
    if not a.is_family:
        return {"": program}
    rx = re.compile(rf"^.*{MEMBER_MARK} (\S+)[ \t]*$", re.M)
    marks = list(rx.finditer(program))
    if [m.group(1) for m in marks] != list(a.members):
        raise BindError("program", f"member markers {[m.group(1) for m in marks]} do not "
                                   f"match the members {a.members}")
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(program)
        out[m.group(1)] = program[m.end() + 1:end]
    return out


def regions_of(marked: str) -> list:
    """(fixed text before, region text) pairs plus the trailing fixed
    text, from a marked text."""
    lines = marked.splitlines(keepends=True)
    fixed, regions, cur, inside = [], [], [], False
    for line in lines:
        if EVOLVE_START in line:
            if inside:
                raise BindError("program", "nested EVOLVE-BLOCK-START")
            inside = True
            fixed.append("".join(cur))
            cur = []
            continue
        if EVOLVE_END in line:
            if not inside:
                raise BindError("program", "EVOLVE-BLOCK-END without START")
            inside = False
            regions.append("".join(cur))
            cur = []
            continue
        cur.append(line)
    if inside:
        raise BindError("program", "EVOLVE-BLOCK-START without END")
    fixed.append("".join(cur))
    return fixed, regions


def strip_markers(marked: str) -> str:
    return "".join(l for l in marked.splitlines(keepends=True)
                   if EVOLVE_START not in l and EVOLVE_END not in l
                   and MEMBER_MARK not in l)


def fixed_part(marked: str) -> str:
    fixed, _ = regions_of(marked)
    return "\x00".join(fixed)


def region_names(a: Artifact, marked: str) -> list:
    """The names of a marked program's regions, in order: the regions the
    `evolve` patterns mark (inside every member of a family), or, for a
    family without `evolve` patterns, its members, one region each."""
    if a.is_family and not a.evolve:
        return list(a.members)
    text = strip_markers(marked)
    return [name for _, _, name in find_regions(text, a.evolve, a.language)]


def swap_regions(a: Artifact, marked: str, other: str, keep: list) -> str:
    """`marked` with the body of every region named in `keep` taken from
    `other`, where both programs have that region; the markers, the
    fixed text and the declaration block of `marked` stay."""
    if not keep or (a.is_family and not a.evolve):
        return marked
    names_new = region_names(a, marked)
    names_old = region_names(a, other)
    _, bodies_old = regions_of(other)
    old_by_name = {n: b for n, b in zip(names_old, bodies_old)}
    out, idx, inside, cur = [], 0, False, []
    for line in marked.splitlines(keepends=True):
        if EVOLVE_START in line:
            inside, cur = True, []
            out.append(line)
            continue
        if EVOLVE_END in line:
            name = names_new[idx] if idx < len(names_new) else None
            idx += 1
            body = "".join(cur)
            if name in keep and name in old_by_name:
                old = old_by_name[name]
                # the declaration block belongs to the new program: keep its lines
                if idx == 1 and MARK_START_LINE(body):
                    head = body[:body.index("\n", body.index(_DECL_END)) + 1]
                    old = head + _strip_decl(old)
                body = old
            out.append(body)
            out.append(line)
            inside = False
            continue
        if inside:
            cur.append(line)
        else:
            out.append(line)
    return "".join(out)


_DECL_END = "ADIR-END"


def MARK_START_LINE(body: str) -> bool:
    return "ADIR-DECL v1" in body and _DECL_END in body


def _strip_decl(body: str) -> str:
    if not MARK_START_LINE(body):
        return body
    return body[body.index("\n", body.index(_DECL_END)) + 1:]


def touched_members(a: Artifact, program: str, parent_program: str) -> list:
    if not a.is_family:
        return [] if program == parent_program else [""]
    cur, par = split_program(a, program), split_program(a, parent_program)
    return [m for m in a.members if cur.get(m) != par.get(m)]
