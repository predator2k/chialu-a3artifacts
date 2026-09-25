"""The structure manifest of a generated seed: the physical structures
a seed realizes, one per (mode, lane, op class), the structure KINDS the
emitters register, the slot of the core's architecture space each kind's
microarchitecture comes from, and the op -> kind table.

The emitters register each structure as they write it
(alu_mode.ModeEmitter.structure); the manifest lands in the seed's
declaration block as `STRUCTURE` lines (the chiALU line kind), one per
structure, with `group=<unit>` naming the shared datapath that realizes
it. `StructureManifest.parse` recovers a manifest from those lines.
"""
from __future__ import annotations

import fnmatch
import re
from dataclasses import asdict, dataclass

# kind -> the core architecture's component slot that holds its space
KIND_SLOT = {
    "adder": "adder",               # add sub adc sbb neg abs add_sat sub_sat
    "comparator": "comparator",     # min max cmp
    "multiplier": "multiplier",     # mul mul_wide mul_high mul_sat
    "divider": "divider",           # div quot rem mod
    "shifter": "shifter",           # shl shr_logical shr_arith rol ror
    "bitcount": "bitcount",         # popcount clz ctz
    "fp_adder": "fp_adder",         # fadd fsub
    "fp_comparator": "fp_comparator",   # fcmp fmin fmax
    "rounder": "rounder",           # a float mode's normalize-and-round stage (registered by the emitter)
    "unpacker": "unpacker",         # a float mode's operand decode (registered by the emitter)
    "fp_multiplier": "fp_multiplier",   # fmul
    "fp_fma": "fp_fma",             # a float mode's multiply-add organization: separate structures on the two
                                    # slots above, or one fused datapath for fadd, fsub and fmul (registered by the
                                    # emitter); fmadd fmsub fnmsub fnmadd
    "fp_divider": "fp_divider",     # fdiv fsqrt
    "posit_unit": "posit_unit",     # posit decode/encode of a posit mode
    "logic": "logic",               # and or xor not fabs fneg
    "converter": "converter",       # cvt(<scalar format>); a block target stays inline
    "quantizer": None,              # block re-quantization
}
KINDS = tuple(KIND_SLOT)
# the kinds the top realizes inline (a posit mode's decode and encode): they have
# a family space of their own but no unit module, so no sharing plan groups them
INLINE_KINDS = ("posit_unit",)


_LANE = re.compile(r"l\d+")


def structure_index(sid: str, kind: str) -> str:
    """The variable index of a structure id: the id without its kind and
    its lane part (`m1.l0.adder` -> `m1`, `m0.l2.converter.fp16` ->
    `m0.fp16`)."""
    return ".".join(p for p in sid.split(".") if p != kind and not _LANE.fullmatch(p))


def is_inline(s) -> bool:
    """A structure the top realizes inline, with no unit module of its
    own: a posit mode's decode and encode, or a conversion into a block
    format (several lanes into one block, the cvtblk modules)."""
    if s.kind in INLINE_KINDS:
        return True
    if s.kind == "converter":
        from chialu.verify.alu_ref import cvt_target
        from chialu.verify.formats import BlockFormat
        return any(isinstance(cvt_target(op), BlockFormat) for op in s.ops)
    return False

OP_KIND = {
    **{op: "adder" for op in ("add", "sub", "adc", "sbb", "neg", "abs",
                              "add_sat", "sub_sat")},
    **{op: "comparator" for op in ("min", "max", "cmp")},
    **{op: "multiplier" for op in ("mul", "mul_wide", "mul_high", "mul_sat")},
    **{op: "divider" for op in ("div", "quot", "rem", "mod")},
    **{op: "shifter" for op in ("shl", "shr_logical", "shr_arith", "rol", "ror")},
    **{op: "bitcount" for op in ("popcount", "clz", "ctz")},
    **{op: "logic" for op in ("and", "or", "xor", "not", "fabs", "fneg")},
    **{op: "fp_adder" for op in ("fadd", "fsub")},
    **{op: "fp_comparator" for op in ("fcmp", "fmin", "fmax")},
    "fmul": "fp_multiplier",
    **{op: "fp_divider" for op in ("fdiv", "fsqrt")},
    # the fused multiply-add ops: the mode's multiply-add organization computes them (a fused family, or the
    # separate multiplier then adder under fma_contract sequential)
    **{op: "fp_fma" for op in ("fmadd", "fmsub", "fnmsub", "fnmadd")},
}


def kind_of(op: str) -> str:
    if op.startswith("cvt("):
        return "converter"
    return OP_KIND[op]


# kind -> the kind whose datapath can also realize it: a float kind's
# significand arithmetic is its integer counterpart's (with alignment and
# normalization around it), a comparator is a subtractor with the sum path
# stripped, so min/max/cmp can live in the adder. One physical structure may
# hold members along one chain; the merged structure takes the deepest kind
# that is an ancestor of every member (group_kind).
KIND_PARENT = {"fp_adder": "adder", "fp_multiplier": "multiplier",
               "fp_divider": "divider", "comparator": "adder",
               "fp_comparator": "comparator", "logic": "adder"}
COMPATIBLE_KINDS = dict(KIND_PARENT)
FLOAT_OF = {"adder": "fp_adder", "multiplier": "fp_multiplier", "divider": "fp_divider"}
INT_OF = {v: k for k, v in FLOAT_OF.items()}


@dataclass
class Structure:
    id: str                 # m<mode>.l<lane>.<kind>[.<target>]
    kind: str
    slot: str | None        # the architecture-space slot, None when the
                            # kind carries no family
    mode: int = 0
    lane: int = 0
    ops: tuple = ()
    width: int = 0
    format: str = ""
    sv: str = ""            # the SV symbol realizing it (informative)
    target: str = ""        # a converter's target format
    group: str = ""         # the shared datapath (unit) that realizes it

    @property
    def library(self) -> bool:
        """Whether the structure carries a family of its own (variables under
        `core.<kind>.<index>.*`, a selection the seed must realize). Two
        slotted kinds do not for some structures: a float mode's rounder
        whose ops are conversions alone (the rounder unit hosts the
        converter family's modules, which round for themselves), and a
        converter into a posit format (the posit unit's encoder converts)
        or into a block format (the inline cvtblk module of the top scales
        and quantizes the lanes; the scalar converter families do not
        describe it).
        Computed from the structure's own fields, so a parsed manifest
        agrees with a generated one."""
        if self.kind == "rounder" and self.ops and all(op.startswith("cvt(") for op in self.ops):
            return False
        if self.kind == "converter" and self.target:
            from chialu.verify.formats import BlockFormat, PositFormat, parse_format
            try:
                return not isinstance(parse_format(self.target), (PositFormat, BlockFormat))
            except ValueError:
                return True
        return True

    @property
    def index(self) -> str:
        """The index of the structure's variables (`core.<kind>.<index>.family`):
        the id without its kind and its lane, since the lanes of one mode
        are replicas and share their decisions (`m1`, or `m1.<target>` for
        a converter)."""
        return structure_index(self.id, self.kind)

    def fields(self) -> list:
        parts = [self.id, f"kind={self.kind}", f"slot={self.slot or '-'}",
                 f"mode={self.mode}", f"lane={self.lane}", f"width={self.width}",
                 f"format={self.format or '-'}", f"ops={','.join(self.ops) or '-'}"]
        if self.target:
            parts.append(f"target={self.target}")
        if self.sv:
            parts.append(f"sv={self.sv}")
        if self.group:
            parts.append(f"group={self.group}")
        return parts

    def line(self) -> str:
        return "STRUCTURE " + " ".join(self.fields())

    def brief(self) -> str:
        t = f" -> {self.target}" if self.target else ""
        return (f"{self.id}: {self.kind}, mode {self.mode} lane {self.lane}, "
                f"{self.format}{t}, ops {', '.join(self.ops)}")


class StructureManifest:
    """The structures of one artifact, in declaration order."""

    def __init__(self):
        self.items: list[Structure] = []
        self._by_id: dict[str, Structure] = {}

    def add(self, kind, mode: int = 0, lane: int = 0, ops=(), width: int = 0,
            fmt_name: str = "", sv: str = "", target: str = "") -> Structure:
        if isinstance(kind, Structure):
            return self._add(kind)
        if kind not in KIND_SLOT:
            raise ValueError(f"unknown structure kind {kind!r}")
        sid = f"m{mode}.l{lane}.{kind}" + (f".{target}" if target else "")
        return self._add(Structure(sid, kind, KIND_SLOT[kind], mode, lane,
                                   tuple(ops), width, fmt_name, sv, target))

    def _add(self, st: Structure) -> Structure:
        prev = self._by_id.get(st.id)
        if prev is not None:
            prev.ops = tuple(dict.fromkeys(tuple(prev.ops) + tuple(st.ops)))
            if st.sv and not prev.sv:
                prev.sv = st.sv
            if st.group and not prev.group:
                prev.group = st.group
            return prev
        self.items.append(st)
        self._by_id[st.id] = st
        return st

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)

    def __bool__(self):
        return bool(self.items)

    def get(self, sid: str) -> Structure | None:
        return self._by_id.get(sid)

    def ids(self) -> list[str]:
        return [s.id for s in self.items]

    def kinds(self) -> list[str]:
        return list(dict.fromkeys(s.kind for s in self.items))

    def group_kind(self, kinds) -> str:
        """The kind of one physical structure realizing members of
        `kinds`: the kind itself when there is one, else the deepest kind
        every member's compatibility chain contains."""
        kinds = sorted(set(kinds))
        if len(kinds) == 1:
            return kinds[0]
        if "fp_fma" in kinds and set(kinds) <= {"fp_adder", "fp_fma", "fp_multiplier"}:
            # a multiply-add: the fp_fma structure's datapath realizes the mode's fadd, fsub, fmul and fused ops,
            # and the adder and multiplier structures ride in its unit
            return "fp_fma"

        def chain(k):
            out = [k]
            while k in COMPATIBLE_KINDS and COMPATIBLE_KINDS[k] not in out:
                k = COMPATIBLE_KINDS[k]
                out.append(k)
            return out
        chains = [chain(k) for k in kinds]
        for cand in chains[0]:
            if all(cand in c for c in chains):
                return cand
        raise ValueError(f"members of several kinds {kinds} cannot be one "
                         f"physical structure (compatible chains: {COMPATIBLE_KINDS})")

    def select(self, pattern: str) -> list[Structure]:
        """Structures a selector names: a bare kind, an exact id, or a
        shell glob over ids."""
        if pattern in self._by_id:
            return [self._by_id[pattern]]
        if any(s.kind == pattern for s in self.items):
            return [s for s in self.items if s.kind == pattern]
        return [s for s in self.items if fnmatch.fnmatchcase(s.id, pattern)]

    def index_sets(self) -> dict:
        """`structures:<kind>` -> the indices of that kind's structures
        with a slot; the index sets the ALU template's variables expand
        over."""
        out: dict = {}
        for s in self.items:
            if s.slot and s.library and s.index not in out.setdefault(f"structures:{s.kind}", []):
                out[f"structures:{s.kind}"].append(s.index)
        return out

    def declaration_lines(self) -> list:
        """(kind, tokens) pairs for the declaration block."""
        return [("STRUCTURE", s.fields()) for s in self.items]

    def header_lines(self) -> list[str]:
        return ["// " + s.line() for s in self.items]

    def to_json(self) -> list[dict]:
        return [asdict(s) for s in self.items]

    @classmethod
    def from_json(cls, rows) -> "StructureManifest":
        m = cls()
        for r in rows:
            r = dict(r)
            r["ops"] = tuple(r.get("ops") or ())
            m._add(Structure(**r))
        return m

    @classmethod
    def from_fields(cls, entries) -> "StructureManifest":
        """From parsed STRUCTURE declaration entries ({_: [id], kind: ...})."""
        m = cls()
        for e in entries:
            m._add(structure_from_fields(e))
        return m

    @classmethod
    def parse(cls, text: str) -> "StructureManifest":
        """The manifest declared in a text's STRUCTURE lines (comment
        prefixes stripped)."""
        m = cls()
        for line in text.splitlines():
            s = line.strip().lstrip("/#- ").strip()
            if not s.startswith("STRUCTURE "):
                continue
            fields = s[len("STRUCTURE "):].split()
            if not fields:
                continue
            kv = dict(f.split("=", 1) for f in fields[1:] if "=" in f)
            m._add(structure_from_fields({"_": [fields[0]], **kv}))
        return m


def structure_from_fields(e: dict) -> Structure:
    sid = e["_"][0] if isinstance(e.get("_"), list) else str(e.get("_", ""))

    def s(k, default=""):
        v = e.get(k, default)
        return "" if v in ("-", None) else str(v)
    ops = e.get("ops", ())
    if isinstance(ops, str):
        ops = () if ops == "-" else tuple(ops.split(","))
    elif isinstance(ops, list):
        ops = tuple(str(o) for o in ops)
    slot = s("slot")
    return Structure(sid, s("kind"), slot or None, int(e.get("mode", 0) or 0),
                     int(e.get("lane", 0) or 0), tuple(ops), int(e.get("width", 0) or 0),
                     s("format"), s("sv"), s("target"), s("group"))


def strip_manifest_header(text: str) -> str:
    """A seed text without the manifest header lines the emitter writes
    at the top (they travel in the declaration block instead)."""
    out = []
    for line in text.splitlines(keepends=True):
        s = line.strip()
        if s.startswith("// STRUCTURE ") or s.startswith("// STRUCTURES:"):
            continue
        out.append(line)
    return "".join(out)
