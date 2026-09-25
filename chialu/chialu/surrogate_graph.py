"""The whole design as a graph: the input of a GNN surrogate of whole-ALU PPA.

    python -m chialu.surrogate_graph space <target.numeric.yaml>... --out space.json
    python -m chialu.surrogate_graph sample <target.numeric.yaml> --n 300 --out rows.jsonl [--jobs 8]
    python -m chialu.surrogate_graph check <dataset.jsonl>... --space space.json [--jobs 24] [--limit N]
    python -m chialu.surrogate_graph export <dataset.jsonl> --space space.json --out graphs.pkl [--jobs 24]

The XGBoost surrogate (chialu.surrogate_features) flattens a design into
fixed columns: one row of the synthesis database per structure id, the
sharing plan's tokens, and a one-hot of `core.*` and `x_form`. Two things
are lost on the way. Everything outside that one-hot is dropped silently
(an int design's four `check.*` checker variables are in no column), and
the composition is gone: which structure a nested choice configures,
which structures one physical unit realizes after sharing, and which
units stand in series on a mode's path. Near the Pareto front the
designs differ in exactly that composition, so a GNN over the design's
own structure is tried instead. The hard requirement is completeness:
every variable a design declares is one node of its graph, every
structure of the manifest and every unit of the plan is a node, and
`check` proves it row by row rather than trusting it.

The graph (`design_graph`) has three levels, every edge directed the
way information flows toward the output, so one topological sweep (or a
directed max-aggregation) reads a design bottom-up:

1. the configuration tree: one node per declared variable. A `.family`
   variable is a `slot` node (the family chosen there), every other one a
   `choice` node; a choice points at the slot whose family declares it
   and a nested slot at its parent slot (the parent is the variable the
   declaration's `when` names, from the declared space in `space.json`;
   a name prefix rule only where the space does not know the variable,
   reported by `check`). A root slot `core.<slot>.<index>.family`
   configures every manifest structure of that slot and index (the lanes
   of a mode share their declaration), `check.<rule>.family` its checker
   node, a unit-level component (`core.subword.*`) every unit and the
   top, and a global choice (`x_form`) every mode and the top. Nodes
   carry vocabulary ids of the variable's generic path (the mode index
   replaced by `*`, so the same choice in every mode shares parameters),
   of its last name, and of `name=value`; a numeric value also carries
   its position in the declared range. The vocabularies are built over
   the whole declared space (`space`), not over the values seen.
2. the database: every structure node carries the row
   `synthdb.estimate_structure` prices for its own family and pins at its
   width (and float format), every nested slot whose family belongs to a
   database kind the row of that family and its subtree's pins at the
   structure's width (a proxy, flagged: a nested slot's own width is the
   generator's business), the checker the `checker` row, each with
   flags for a missing row and the count of unmodeled moves. The database
   is `synthdb.db_dir`, which follows `CHIALU_SYNTH_DIR`.
3. the datapath: one `unit` node per physical unit after sharing,
   partitioned exactly as `chialu.eda.estimate` partitions it (the
   plan's groups, the fused FMA banks, the int/float adder bank, a
   separate-family fp_fma dropped), carrying the estimate's own rows of
   that unit (so the node holds what the numeric stage priced). Each
   structure points at the unit that realizes it (`realized_by`), a float
   add/multiply a fused FMA absorbs at that FMA (`absorbed_by`), an inline
   structure at its mode. Per mode, the path edges follow the estimate's
   composition: unpackers -> the parallel op units -> rounders -> the
   mode node -> the top, so the sum along a chain of maxima is the
   estimate's longest mode path. The sharing scheme's tokens, groups and
   union geometry (plan_features) are graph-level features and the
   group geometry sits on each shared unit as well; the plan's
   `structures` entries (family and pins) are flags on the variable nodes
   they repeat, and an entry that repeats no variable becomes a `pin`
   node, so a pin is never dropped either.

Graph-level features: the scheme's rule per axis, SHR/KIND/GEO of
plan_features, and the old estimate's area, delay and coverage (`est_*`,
flagged as the XGBoost input's prior, optional for a model).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPACE_VERSION = 1

NODE_TYPES = ("top", "mode", "unit", "structure", "slot", "choice", "checker", "pin")
EDGE_TYPES = ("choice_of", "slot_of", "configures", "component_of", "global_of", "pins", "realized_by",
              "absorbed_by", "computed_by", "inline_in", "path", "drives_mode", "mode_out", "checks")
UNIT_SPECIALS = ("single", "pair", "group", "int_fp_adder_bank", "fma_bank")
# the categorical columns of a node (a vocabulary id each, 0 = none or unknown) and the numeric ones
CAT_FIELDS = ("node_type", "gpath", "name", "value", "kind", "family", "format", "db_kind", "special")
NUM_FIELDS = ("num", "is_num", "bval", "is_bool", "depth", "width", "mode", "lane", "n_ops", "library", "inline",
              "declared", "plan_entry", "plan_match", "pinned", "dropped", "absorbed", "canonical", "n_members", "n_modes",
              "n_lanes", "n_formats", "sum_over_max_w", "shared", "count", "glue", "context",
              "area", "delay", "db_row", "db_missing", "db_unmodeled", "db_width_proxy", "db_interpolated", "n_rows")
LOG_FIELDS = ("area", "delay")          # taken as log1p in the arrays: the rows span three decades


# ------------------------------------------------------------------ names

_CORE_INDEX = re.compile(r"^m\d+$")


def generic(name: str) -> tuple:
    """(generic path, position of the index, the index) of a variable name: the per-mode index of
    `core.<slot>.<index>.*` (`m0`, `m1`, ...) and the rule of `check.<rule>.*` replaced by `*`, so the
    same choice in every mode (and every rule) is one vocabulary entry."""
    parts = str(name).split(".")
    if parts[0] == "core" and len(parts) >= 4 and _CORE_INDEX.match(parts[2]):
        return ".".join(parts[:2] + ["*"] + parts[3:]), 2, parts[2]
    if parts[0] == "check" and len(parts) >= 3:
        return ".".join(parts[:1] + ["*"] + parts[2:]), 1, parts[1]
    return str(name), None, None


def instantiate(gpath: str, pos, index) -> str:
    parts = gpath.split(".")
    if pos is not None and len(parts) > pos and parts[pos] == "*":
        parts[pos] = index
    return ".".join(parts)


def value_token(name: str, v) -> str:
    """`<last name>=<value>`: the same family or choice value shares its id at every position."""
    return f"{name.rsplit('.', 1)[-1]}={json.dumps(v, sort_keys=True, default=str)}"


def scheme_tokens(name: str) -> dict:
    """{axis: rule} of a sharing scheme's name (`add-none_mul-all_log-per_lane_sw-pcc`). A rule may hold
    an underscore itself (per_lane, per_mode), so the name splits only before `<axis>-`;
    surrogate_features.plan_tokens splits at every underscore and reads `log-per_lane` as `log: per`."""
    out = {}
    for tok in re.split(r"_(?=[a-z]+-)", str(name or "")):
        if "-" in tok:
            k, v = tok.split("-", 1)
            out[k] = v
    return out


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# ------------------------------------------------------------------ the declared space and its vocabularies

def numeric_instance(path):
    """The run file's variables bound without the rest of the load (tests/test_numeric_space does the
    same): 1-5 s where `adir.instance.load` takes 30-110 s, and the bindings and the template are all a
    vocabulary and a manifest need."""
    import yaml
    from adir.instance import Instance, _bind_variables
    from adir.registry import get_template
    import chialu.priors  # noqa: F401  the templates and priors the run files name
    inst = Instance()
    inst.path = Path(path).resolve()
    inst.base_dir = inst.path.parent
    inst.raw = yaml.safe_load(inst.path.read_text())["adir"]
    inst.search = inst.raw["search"]
    inst.template = get_template(inst.raw["module"])
    _bind_variables(inst, inst.raw["variables"])
    return inst


def target_name(numeric: Path) -> str:
    return Path(numeric).name.split(".")[0]


def db_kinds(pdk: str = "nangate45") -> list:
    """The kinds the database holds rows of (its files and split directories)."""
    from chialu import synthdb
    d = synthdb.db_dir(pdk)
    if not d.is_dir():
        return []
    return sorted({p.stem for p in d.glob("*.jsonl")} | {p.name for p in d.iterdir() if p.is_dir()})


_FAM_KINDS: dict = {}


def family_kinds(pdk: str = "nangate45") -> dict:
    """{family name: [database kinds whose families include it]}: a nested slot is priced as the kind
    that owns its family."""
    if pdk not in _FAM_KINDS:
        from chialu import synthdb
        out: dict = {}
        for k in db_kinds(pdk):
            try:
                fams = synthdb.families_of(k)
            except Exception:  # noqa: BLE001 - a kind without a space has no families to map
                fams = []
            for f in fams:
                out.setdefault(f.name, []).append(k)
        _FAM_KINDS[pdk] = out
    return _FAM_KINDS[pdk]


def build_space(numeric_files: list, pdk: str = "nangate45", level: str = "natural", db_families: bool = True) -> dict:
    """The declared space of one or more targets and the vocabularies over it (every declared member,
    whether or not a sample drew it, and every family of every database kind), with each target's spec,
    estimate inputs and scheme names, so a graph is built from `space.json` and a dataset row alone."""
    from chialu import synthdb
    from chialu.modules.generators import spec_of
    from chialu.surrogate_features import KINDS, RULES, TOKENS
    from chialu.surrogate_seeds import estimate_inputs, schemes_of
    from chialu.targets.rtl.alu_seed import structure_manifest
    targets, vars_, conflicts = {}, {}, []
    formats, kinds = set(), set(KINDS) | {"checker"}
    rules = list(RULES)
    for nf in numeric_files:
        nf = Path(nf).resolve()
        inst = numeric_instance(nf)
        ctx = inst.ctx()
        spec = spec_of(ctx)
        manifest = structure_manifest(spec)
        try:
            schemes = [n for n, _p in schemes_of(inst, ctx, level)[0]]
        except Exception as e:  # noqa: BLE001 - the scheme names only widen the rule vocabulary
            schemes = []
            conflicts.append(f"{nf.name}: schemes: {type(e).__name__}: {str(e)[:120]}")
        for s in schemes:
            for _t, r in scheme_tokens(s).items():
                if r not in rules:
                    rules.append(r)
        for s in manifest:
            kinds.add(s.kind)
            if s.format:
                formats.add(str(s.format))
        for m in spec.get("modes") or []:
            formats.add(str(m.get("format")))
        n_search = 0
        for v in inst.variable_order():
            b = inst.bindings.get(v.name)
            if b is None or b.time != "search":
                continue
            n_search += 1
            gp, _pos, _idx = generic(v.name)
            # a parent bound fixed (`core.family`: unit_per_class) is the target's, in no declaration:
            # the variable is a root of the declared tree
            pb = inst.bindings.get(v.when[0]) if v.when is not None else None
            parent = generic(v.when[0])[0] if pb is not None and pb.time == "search" else None
            members = list(b.domain.members()) if b.domain.finite() else []
            e = vars_.setdefault(gp, {"parent": parent, "members": [], "targets": []})
            if pb is not None and pb.time != "search":
                e["fixed_parent"] = [v.when[0], pb.time, getattr(pb, "value", None)]
            if e["parent"] != parent:
                conflicts.append(f"{gp}: parent {e['parent']} vs {parent} ({nf.name})")
            seen = {json.dumps(m, sort_keys=True, default=str) for m in e["members"]}
            e["members"] += [m for m in members if json.dumps(m, sort_keys=True, default=str) not in seen]
            if not b.domain.finite():
                e["continuous"] = True
            if target_name(nf) not in e["targets"]:
                e["targets"].append(target_name(nf))
        # the search run file beside it realizes the points: scheme_repair writes members of its domains the
        # numeric file narrows away (fp_fma `sharing=shared_across_formats` under a shared-FMA scheme), so
        # its members of the same variables belong to the vocabulary too
        rf = nf.with_name(nf.name.replace(".numeric", ""))
        if rf != nf and rf.is_file():
            rinst = numeric_instance(rf)
            for v in rinst.variable_order():
                gp = generic(v.name)[0]
                b = rinst.bindings.get(v.name)
                if gp not in vars_ or b is None:
                    continue
                if b.time == "search" and b.domain.finite():
                    extra = list(b.domain.members())
                elif b.time == "fixed":
                    extra = [b.value]
                else:
                    continue
                e = vars_[gp]
                seen = {json.dumps(m, sort_keys=True, default=str) for m in e["members"]}
                new = [m for m in extra if json.dumps(m, sort_keys=True, default=str) not in seen]
                if new:
                    e["members"] += new
                    e.setdefault("realized_only", []).extend(new)
        targets[target_name(nf)] = {"numeric": str(nf), "spec": spec, "est": estimate_inputs(nf),
                                    "schemes": schemes, "searched_variables": n_search}
    for e in vars_.values():
        nums = [m for m in e["members"] if _is_num(m)]
        e["range"] = [min(nums), max(nums)] if nums and len(nums) == len(e["members"]) else None
    tokens, names = set(), set()
    for gp, e in vars_.items():
        names.add(gp.rsplit(".", 1)[-1])
        for m in e["members"]:
            tokens.add(value_token(gp, m))
    dbk = db_kinds(pdk)
    kinds |= set(dbk)
    for k in (dbk if db_families else ()):     # the family library's load is most of this function's time
        try:
            for f in synthdb.families_of(k):
                tokens.add(value_token("family", f.name))
        except Exception:  # noqa: BLE001
            pass
    vocab = {"node_type": list(NODE_TYPES), "edge_type": list(EDGE_TYPES), "special": list(UNIT_SPECIALS),
             "gpath": sorted(vars_), "name": sorted(names), "value": sorted(tokens), "kind": sorted(kinds),
             "db_kind": sorted(dbk), "format": sorted(formats), "scheme_token": list(TOKENS), "scheme_rule": rules}
    vocab["family"] = sorted(t for t in tokens if t.startswith("family="))     # informative: ids are "value"'s
    return {"version": SPACE_VERSION, "pdk": pdk, "targets": targets, "vars": vars_, "vocab": vocab,
            "conflicts": conflicts, "note": "ids are list positions + 1; 0 is none or unknown"}


class Space:
    """space.json with its lookups (vocabulary ids start at 1; 0 is none or unknown)."""

    def __init__(self, d: dict):
        self.d = d
        self.vars = d["vars"]
        self.vocab = d["vocab"]
        self.ids = {k: {t: i + 1 for i, t in enumerate(v)} for k, v in self.vocab.items()}

    @classmethod
    def load(cls, path) -> "Space":
        return cls(json.loads(Path(path).read_text()))

    def id(self, field: str, token) -> int:
        if token is None:
            return 0
        return self.ids.get(field, {}).get(str(token), 0)

    def target(self, name: str) -> dict:
        return self.d["targets"][name]

    def target_of_path(self, path) -> str | None:
        """The target whose name the dataset path carries (the longest match: fp_alu_cmp_hf, not fp_alu_cmp)."""
        s = str(path)
        hits = [t for t in self.d["targets"] if re.search(rf"(^|[/._]){re.escape(t)}([/.]|$)", s)]
        return max(hits, key=len) if hits else None


# ------------------------------------------------------------------ the database, cached

_ROWS: dict = {}
_EST: dict = {}


@contextmanager
def cached_db():
    """`synthdb.rows_of` and `synthdb.estimate_structure` memoized for the duration: uncached, every
    lookup re-reads and re-parses the kind's whole file (1-3 s per design, 90% of it json decoding),
    and a design repeats most of its lookups under another design's name. `eda.estimate` calls both
    through the module, so it is served from the same cache. The database is read once per process;
    a rebuild written meanwhile is not seen until the next process."""
    from chialu import synthdb
    rows_of, est = synthdb.rows_of, synthdb.estimate_structure
    if getattr(rows_of, "_graph_cached", False):
        yield
        return

    def rows_cached(pdk_name, kind, family=None, effort=None, flow=True):
        k = (str(synthdb.db_dir(pdk_name)), pdk_name, kind, family, effort, flow)
        if k not in _ROWS:
            _ROWS[k] = rows_of(pdk_name, kind, family, effort, flow)
        return _ROWS[k]

    def est_cached(pdk_name, kind, family, pins, width, effort="medium", fmt=None, geom=None):
        k = (str(synthdb.db_dir(pdk_name)), pdk_name, kind, str(family),
             json.dumps(pins or {}, sort_keys=True, default=str), int(width), effort, fmt, geom)
        if k not in _EST:
            _EST[k] = est(pdk_name, kind, family, pins, width, effort, fmt=fmt, geom=geom)
        r = _EST[k]
        return dict(r) if r else {}
    rows_cached._graph_cached = True
    synthdb.rows_of, synthdb.estimate_structure = rows_cached, est_cached
    try:
        yield
    finally:
        synthdb.rows_of, synthdb.estimate_structure = rows_of, est


def db_features(r: dict | None) -> dict:
    """The node attributes of one database estimate (`{}`: no row)."""
    if not r:
        return {"db_row": 0.0, "db_missing": 1.0}
    return {"db_row": 1.0, "db_missing": 0.0, "area": float(r.get("area_um2") or 0.0),
            "delay": float(r.get("delay_ps") or 0.0), "db_unmodeled": float(len(r.get("unmodeled") or [])),
            "db_interpolated": float(bool(r.get("interpolated")))}


# ------------------------------------------------------------------ the physical units (mirrors eda.estimate)

def physical_units(manifest, plan: dict | None, decl: dict) -> tuple:
    """([(unit name, [structures], special)], fused modes, {structure id: why it is in no unit}) of a
    design: the partition `chialu.eda.estimate` prices, step for step (the plan's groups, else one
    unit per slotted structure; a fused family's FMA banks per lane, taking its mode's float adders
    and multipliers; a separate-family fp_fma in no unit, its lane's adder and multiplier compute it).
    `decl` is the nested declaration after scheme_repair, as the estimate sees it. `check` asserts
    that every row and every missing unit the estimate reports is one of these units, so a change to
    the estimate that this copy misses fails loudly."""
    from chialu import synthdb
    from chialu.targets.rtl.structures import is_inline

    def declared(slot: str, index: str) -> dict:
        cur = decl.get(slot)
        for part in index.split("."):
            if not isinstance(cur, dict):
                return {}
            cur = cur.get(part)
        return cur if isinstance(cur, dict) else {}

    def family_of(s):
        d = declared(s.slot, s.index)
        family = d.get("family")
        if family is None:
            fams = synthdb.families_of(s.slot)
            family = fams[0] if fams else None
        return family, {k: v for k, v in d.items() if k != "family"}

    if plan:
        from chialu.plans import partition_of_plan
        units = [(u, [manifest.get(m) for m in members]) for u, members in partition_of_plan(manifest, plan)]
    else:
        units = [(s.id, [s]) for s in manifest]
    fused_modes = {s.mode for s in manifest if s.kind == "fp_fma" and
                   family_of(s)[0] not in (None, "separate_multiplier_and_adder")}
    fma_shared = [s for s in manifest if s.kind == "fp_fma" and s.mode in fused_modes
                  and family_of(s)[1].get("sharing") == "shared_across_formats"]
    why: dict = {}
    if fused_modes:
        shared_ids = {s.id for s in fma_shared}
        units = [(u, [s for s in sts if s is not None and s.id not in shared_ids and
                      not (s.mode in fused_modes and s.kind in ("fp_adder", "fp_multiplier"))])
                 for u, sts in units]
        units = [(u, sts) for u, sts in units if sts]
        for lane in sorted({s.lane for s in fma_shared}):
            units.append((f"fp_fma_bank_l{lane}", [s for s in fma_shared if s.lane == lane]))
    out = []
    banks = {u for u, _ in units if u.startswith("fp_fma_bank_l")}
    for unit, sts in units:
        sts = [s for s in sts if s is not None and s.slot and not is_inline(s) and s.library]
        for s in sts:
            if s.kind == "fp_fma" and str(family_of(s)[0]) == "separate_multiplier_and_adder":
                why[s.id] = "separate_fma"
        sts = [s for s in sts if not (s.kind == "fp_fma" and str(family_of(s)[0]) == "separate_multiplier_and_adder")]
        if not sts:
            continue
        kinds = {s.kind for s in sts}
        if unit in banks:
            special = "fma_bank"
        elif len(sts) == 1:
            special = "single"
        elif kinds in ({"adder", "comparator"}, {"adder", "logic"}):
            special = "pair"
        elif kinds == {"adder", "fp_adder"}:
            special = "int_fp_adder_bank"
        else:
            special = "group"
        out.append((unit, sts, special))
    placed = {s.id for _u, sts, _sp in out for s in sts}
    for s in manifest:
        if s.id in placed or s.id in why:
            continue
        if is_inline(s) or not s.slot or not s.library:
            why[s.id] = "inline"
        elif s.mode in fused_modes and s.kind in ("fp_adder", "fp_multiplier"):
            why[s.id] = "absorbed"
        else:
            why[s.id] = "unplaced"
    return out, fused_modes, why


# ------------------------------------------------------------------ the graph

class Graph:
    """A design as typed nodes (a dict of attributes each: `type`, `key`, the provenance `src`, and the
    fields of CAT_FIELDS / NUM_FIELDS it has) and typed directed edges (src, dst, type, mode); `var_node`
    maps every declared variable to its node. Plain python: `arrays` makes the numpy form, `to_pyg` a
    torch_geometric Data."""

    def __init__(self, target: str = ""):
        self.target = target
        self.nodes: list = []
        self.edges: list = []
        self.index: dict = {}
        self.var_node: dict = {}
        self.globals: dict = {}
        self.issues: list = []

    def add(self, type_: str, key: str, src: str, **attrs) -> int:
        if key in self.index:
            raise ValueError(f"duplicate node {key}")
        self.index[key] = len(self.nodes)
        self.nodes.append({"type": type_, "key": key, "src": src, **attrs})
        return self.index[key]

    def edge(self, s: int, d: int, type_: str, mode: int = -1, w: float = 0.0) -> None:
        """`w`: on a path edge, the source unit's delay in that mode where it stands (its rows serving the
        mode, times their context factor): the estimate's composition, per mode rather than the unit's max."""
        self.edges.append((s, d, type_, int(mode), float(w)))

    def of_type(self, t: str) -> list:
        return [i for i, n in enumerate(self.nodes) if n["type"] == t]

    def arrays(self, space: Space) -> dict:
        """{x_cat [N, len(CAT_FIELDS)] int64, x_num [N, len(NUM_FIELDS)] float32, edge_index [2, E] int64,
        edge_type [E], edge_mode [E], node_type [N], globals [G] float32, global_names}."""
        import numpy as np
        n = len(self.nodes)
        x_cat = np.zeros((n, len(CAT_FIELDS)), dtype=np.int64)
        x_num = np.zeros((n, len(NUM_FIELDS)), dtype=np.float32)
        for i, nd in enumerate(self.nodes):
            x_cat[i, 0] = space.id("node_type", nd["type"])
            for j, f in enumerate(CAT_FIELDS[1:], 1):
                vocab = "value" if f == "family" else f
                x_cat[i, j] = space.id(vocab, nd.get(f))
            for j, f in enumerate(NUM_FIELDS):
                v = nd.get(f)
                if v is None:
                    continue
                v = float(v)
                x_num[i, j] = math.log1p(max(0.0, v)) if f in LOG_FIELDS else (v / 64.0 if f == "width" else v)
        ei = np.array([[e[0] for e in self.edges], [e[1] for e in self.edges]], dtype=np.int64).reshape(2, -1)
        et = np.array([space.id("edge_type", e[2]) for e in self.edges], dtype=np.int64)
        em = np.array([e[3] for e in self.edges], dtype=np.int64)
        ew = np.array([math.log1p(max(0.0, e[4])) for e in self.edges], dtype=np.float32)
        gnames = global_names(space)
        g = np.array([float(self.globals.get(k, 0.0)) for k in gnames], dtype=np.float32)
        return {"x_cat": x_cat, "x_num": x_num, "edge_index": ei, "edge_type": et, "edge_mode": em, "edge_w": ew,
                "node_type": x_cat[:, 0].copy(), "globals": g, "global_names": gnames,
                "cat_fields": CAT_FIELDS, "num_fields": NUM_FIELDS}

    def to_pyg(self, space: Space, y=None):
        """A torch_geometric Data of `arrays` (torch imported here only)."""
        import torch
        from torch_geometric.data import Data
        a = self.arrays(space)
        d = Data(x_cat=torch.from_numpy(a["x_cat"]), x_num=torch.from_numpy(a["x_num"]),
                 edge_index=torch.from_numpy(a["edge_index"]), edge_type=torch.from_numpy(a["edge_type"]),
                 edge_mode=torch.from_numpy(a["edge_mode"]), edge_w=torch.from_numpy(a["edge_w"]), u=torch.from_numpy(a["globals"])[None, :])
        if y is not None:
            d.y = torch.tensor([y], dtype=torch.float32)
        return d


def global_names(space: Space) -> list:
    """The graph-level columns: the rule of each scheme axis (its id in `scheme_rule`), plan_features'
    SHR, KIND and GEO, the target's glue, and the old estimate (`est_*`, the XGBoost input's prior)."""
    from chialu.surrogate_features import KINDS
    out = [f"rule__{t}" for t in space.vocab["scheme_token"]]
    out += ["SHR__n_groups", "SHR__max_gsize", "SHR__sum_grouped", "SHR__mean_gsize", "SHR__frac_grouped"]
    out += [f"KIND__{k}_grouped" for k in KINDS]
    out += [f"GEO__{k}_{g}" for k in KINDS for g in ("sum_over_max_w", "fmtspan", "modespan", "lanespan", "gsize")]
    out += ["n_structures", "n_units", "n_modes", "n_dropped", "glue_top", "est_area", "est_delay", "est_coverage"]
    return out


class Context:
    """What every design of one target shares: the spec and its manifest, the estimate's inputs."""

    def __init__(self, space: Space | None, target: str, spec: dict | None = None, est: dict | None = None,
                 pdk: str = "nangate45", effort: str = "medium"):
        from chialu.targets.rtl.alu_seed import structure_manifest
        from chialu.surrogate_features import manifest_table
        self.space, self.target, self.pdk, self.effort = space, target, pdk, effort
        t = space.target(target) if space is not None and target in space.d["targets"] else {}
        self.spec = spec if spec is not None else t["spec"]
        self.est = est if est is not None else (t.get("est") or {})
        self.files = {"spec.json": json.dumps(self.spec)}
        self.manifest = structure_manifest(self.spec)
        self.table = manifest_table(self.manifest)
        self.by_index: dict = {}
        for s in self.manifest:
            if s.slot:
                self.by_index.setdefault(f"core.{s.slot}.{s.index}", []).append(s)
        self.glue = {}
        try:
            self.glue = json.loads(self.est.get("glue_json") or "{}") or {}
        except ValueError:
            pass
        try:
            self.context = {str(k): float(v) for k, v in json.loads(self.est.get("context_json") or "{}").items()}
        except (ValueError, TypeError, AttributeError):
            self.context = {}


def _parent(name: str, vals: dict, space: Space | None) -> tuple:
    """(parent variable, how): the variable the declared `when` names ("declared"), else the enclosing
    slot by name ("prefix": a choice's longest prefix P with P.family declared, a slot's the next
    one out); (None, "root") for a variable no slot encloses."""
    gp, pos, idx = generic(name)
    if space is not None and gp in space.vars:
        p = space.vars[gp]["parent"]
        if p is None:
            return None, "root"
        pn = instantiate(p, pos, idx)
        if pn in vals:
            return pn, "declared"
        return pn, "declared_absent"
    parts = name.split(".")
    stop = len(parts) - 2 if name.endswith(".family") else len(parts) - 1
    for k in range(stop, 0, -1):
        cand = ".".join(parts[:k]) + ".family"
        if cand != name and cand in vals:
            return cand, "prefix"
    return None, "root"


def design_graph(ctx: Context, vals: dict, scheme: str, plan: dict | None, with_db: bool = True,
                 with_estimate: bool = True) -> Graph:
    """The graph of one design: `vals` the flat declaration (`core.*`, `check.*`, `x_form`, ... as the
    dataset stores it, after scheme_repair), `scheme` the sharing scheme's name, `plan` the realized
    plan (`structures`, `shared`, `components`, maybe `dropped`). See the module doc for the levels."""
    from adir.registry import underlying
    from chialu import eda, synthdb
    from chialu.eda import SERIES_KINDS, _float_format
    from chialu.surrogate_features import nest, plan_features, scheme_groups, scheme_repair
    from chialu.targets.rtl.structures import is_inline
    space = ctx.space
    g = Graph(ctx.target)
    plan = plan or {}
    vals = dict(vals or {})
    top = g.add("top", "top", "design")

    # ---- modes
    modes = sorted({s.mode for s in ctx.manifest})
    spec_modes = ctx.spec.get("modes") or []
    g_mode = {int(k): float(v) for k, v in (ctx.glue.get("mode") or {}).items()}
    mode_node = {}
    for m in modes:
        sm = spec_modes[m] if m < len(spec_modes) else {}
        sts = [s for s in ctx.manifest if s.mode == m]
        mode_node[m] = g.add("mode", f"mode:{m}", f"spec.modes[{m}]", mode=m, format=str(sm.get("format") or ""),
                             count=float(sm.get("count") or 0), width=max([int(s.width or 0) for s in sts] or [0]),
                             n_members=float(len(sts)), glue=g_mode.get(m, 0.0))
        g.edge(mode_node[m], top, "mode_out", m)

    # ---- structures
    groups = scheme_groups(plan)
    in_group = {sid for _g, ms in groups.items() if len(ms) >= 2 for sid in ms}
    pstruct = plan.get("structures") or {}
    snode = {}
    for s in ctx.manifest:
        root = f"core.{s.slot}.{s.index}" if s.slot else None
        fam = vals.get(f"{root}.family") if root else None
        attrs = dict(kind=s.kind, mode=s.mode, lane=s.lane, width=int(s.width or 0), format=str(s.format or ""),
                     n_ops=float(len(s.ops or ())), library=float(bool(s.library)), inline=float(is_inline(s)),
                     declared=float(fam is not None), shared=float(s.id in in_group),
                     plan_entry=float(s.id in pstruct))
        if fam is not None:
            attrs["family"] = value_token("family", fam)
        if s.id in pstruct:
            attrs["plan_match"] = float(pstruct[s.id].get("family") == fam)
        if with_db and fam is not None and s.slot and s.library and not is_inline(s):
            d = nest({k: v for k, v in vals.items() if k.startswith(root + ".")})
            for part in [s.slot] + str(s.index).split("."):
                d = d.get(part, {}) if isinstance(d, dict) else {}
            pins = {k: v for k, v in synthdb.flat_pins(d).items() if k != "family"}
            r = synthdb.estimate_structure(ctx.pdk, s.slot, str(fam), pins, int(s.width), ctx.effort,
                                           fmt=_float_format(s))
            attrs.update(db_features(r))
            attrs["db_kind"] = s.slot
        snode[s.id] = g.add("structure", f"struct:{s.id}", f"manifest:{s.id}", **attrs)

    # ---- units after sharing, as the estimate partitions them
    repaired = scheme_repair(vals, plan) if plan else dict(vals)
    decl = nest(repaired)
    units, fused_modes, why = physical_units(ctx.manifest, plan, decl)
    unode, unit_of = {}, {}
    table = ctx.table
    for u, sts, special in units:
        gfam = ((plan.get("shared") or {}).get(u) or {}).get("family")
        first = sts[0]
        ffam = gfam or vals.get(f"core.{first.slot}.{first.index}.family")
        ws = [int(s.width or 0) for s in sts]
        attrs = dict(kind=first.kind if special != "int_fp_adder_bank" else "adder", special=special,
                     n_members=float(len(sts)), n_modes=float(len({s.mode for s in sts})),
                     n_lanes=float(len({s.lane for s in sts})), n_formats=float(len({s.format for s in sts})),
                     width=max(ws or [0]), sum_over_max_w=float(sum(ws)) / max(1, max(ws or [0])),
                     shared=float(len(sts) > 1))
        if ffam is not None:
            attrs["family"] = value_token("family", ffam)
        c = ctx.context.get(f"{attrs['kind']}/{ffam}")
        if c is not None:
            attrs["context"] = c
        unode[u] = g.add("unit", f"unit:{u}", f"plan.shared.{u}" if u in (plan.get("shared") or {}) else
                         (f"fma_bank:{u}" if special == "fma_bank" else f"manifest:{u}"), **attrs)
        for s in sts:
            unit_of[s.id] = u
            g.edge(snode[s.id], unode[u], "realized_by", s.mode)

    # ---- the estimate's rows on the units (what the numeric stage priced)
    est, in_place = {}, {}
    if with_estimate:
        est = underlying(eda.estimate)(ctx.files, decl, ctx.pdk, ctx.effort, 1.0, 1.0,
                                       json.dumps(plan) if plan else "", ctx.est.get("glue_json") or "",
                                       ctx.est.get("context_json") or "")
        per_unit: dict = {}
        for r in est.get("rows") or []:
            u = r["id"] if r["id"] in unode else unit_of.get(r["id"])
            if u is None:
                g.issues.append(f"estimate row {r['id']} is no unit of the graph")
                continue
            per_unit.setdefault(u, []).append(r)
        missing_units = set()
        for m in est.get("missing") or []:
            u = str(m).split(": ", 1)[0]
            if u not in unode:
                g.issues.append(f"estimate missing unit {u} is no unit of the graph")
            missing_units.add(u)
        unmod: dict = {}
        for m in est.get("unmodeled") or []:
            k = str(m).split(": ", 1)[0]
            u = k if k in unode else unit_of.get(k)
            if u is not None:
                unmod[u] = unmod.get(u, 0) + 1
        for u, i in unode.items():
            rs = per_unit.get(u) or []
            nd = g.nodes[i]
            nd.update({"n_rows": float(len(rs)), "db_row": float(bool(rs)), "db_missing": float(u in missing_units or not rs),
                       "area": sum(float(r["area_um2"]) for r in rs), "delay": max([float(r["delay_ps"]) for r in rs] or [0.0]),
                       "db_unmodeled": float(unmod.get(u, 0))})
            if rs:
                nd["db_kind"] = rs[0]["kind"]
            for r in rs:
                f = ctx.context.get(f"{r['kind']}/{r['family']}", 1.0)
                for m in r.get("modes") or []:
                    in_place.setdefault(u, {})[int(m)] = max(in_place.get(u, {}).get(int(m), 0.0), float(r["delay_ps"]) * f)

    # ---- per-mode paths: unpackers -> parallel op units -> rounders -> mode (the estimate's composition)
    for m in modes:
        stages = {"unpacker": [], "parallel": [], "rounder": []}
        for u, sts, special in units:
            ks = {s.kind for s in sts if s.mode == m}
            if not ks:
                continue
            role = next((k for k in SERIES_KINDS if ks == {k}), "parallel")
            stages[role].append(unode[u])
        chain = [stages["unpacker"], stages["parallel"], stages["rounder"]]
        chain = [c for c in chain if c]
        key = {i: k for k, i in unode.items()}
        for a, b in zip(chain, chain[1:]):
            for x in a:
                for y in b:
                    g.edge(x, y, "path", m, in_place.get(key[x], {}).get(m, 0.0))
        if chain:
            for x in chain[-1]:
                g.edge(x, mode_node[m], "drives_mode", m, in_place.get(key[x], {}).get(m, 0.0))

    # ---- structures in no unit
    for sid, w in why.items():
        s = ctx.manifest.get(sid)
        i = snode[sid]
        g.nodes[i]["absorbed"] = float(w in ("absorbed", "separate_fma"))
        if w == "absorbed":
            host = next((u for u, sts, sp in units if any(x.kind == "fp_fma" and x.mode == s.mode and x.lane == s.lane
                                                          for x in sts)), None)
            if host is not None:
                g.edge(i, unode[host], "absorbed_by", s.mode)
            else:
                g.edge(i, mode_node[s.mode], "inline_in", s.mode)
                g.issues.append(f"{sid}: absorbed by a fused FMA, but no FMA unit serves mode {s.mode} lane {s.lane}")
        elif w == "separate_fma":
            hosts = [u for u, sts, sp in units if any(x.kind in ("fp_adder", "fp_multiplier") and x.mode == s.mode
                                                      and x.lane == s.lane for x in sts)]
            for u in hosts:
                g.edge(i, unode[u], "computed_by", s.mode)
            if not hosts:
                g.edge(i, mode_node[s.mode], "inline_in", s.mode)
        else:
            g.edge(i, mode_node[s.mode], "inline_in", s.mode)

    # ---- checkers
    # the checker's groups as the spec derives them (`check.groups`: name, (mode, op) pairs), and any rule
    # the declaration names beyond them
    chk = ctx.spec.get("check") or {}
    rule_spec = {r.get("name"): r for r in (chk.get("groups") or chk.get("rules") or []) if r.get("name")}
    rules = list(rule_spec)
    rules += sorted({k.split(".")[1] for k in vals if k.startswith("check.") and k.count(".") >= 2} - set(rules))
    cnode = {}
    wmax = max([int(s.width or 0) for s in ctx.manifest] or [0])
    for r in rules:
        rs = rule_spec.get(r) or {}
        fam = vals.get(f"check.{r}.family")
        pairs = rs.get("pairs") or []
        attrs = dict(kind="checker", n_modes=float(len({p[0] for p in pairs})), n_ops=float(len(pairs)),
                     n_formats=float(len(rs.get("formats") or [])), width=wmax, declared=float(fam is not None))
        if fam is not None:
            attrs["family"] = value_token("family", fam)
            if with_db:
                pre = f"check.{r}."
                pins = {}
                for k, v in vals.items():
                    if k.startswith(pre) and k != pre + "family":
                        rel = k[len(pre):]
                        rel = rel[len(fam) + 1:] if rel.startswith(fam + ".") else rel
                        pins[rel] = v
                attrs.update(db_features(synthdb.estimate_structure(ctx.pdk, "checker", str(fam), pins, wmax, ctx.effort)))
                attrs.update(db_kind="checker", db_width_proxy=1.0)
        cnode[r] = g.add("checker", f"checker:{r}", f"spec.check.rules[{r}]", **attrs)
        g.edge(cnode[r], top, "checks")

    # ---- the plan's entries: each one repeats a declared variable (a flag on its node) or is a pin node
    # of its own, never dropped. `plan_items` lists every plan leaf and how it is held; `completeness`
    # walks the plan independently and fails on a leaf that is not listed.
    pinned: dict = {}
    overridden = set()
    plan_items: dict = {}

    def hold(path: str, var: str | None, v, targets: list, mode: int = -1) -> None:
        """A plan value: a flag on `var` when the declaration holds the same value, else a pin node
        feeding `targets` (and `var` marked as overridden by the plan when the declaration differs)."""
        if var is not None and var in vals and vals[var] == v:
            pinned[var] = pinned.get(var, 0) + 1
            plan_items[path] = f"var:{var}"
            return
        if var is not None and var in vals:
            overridden.add(var)
        k = path.rsplit(".", 1)[-1]
        attrs = dict(gpath=generic(var)[0] if var else None, name=k, value=value_token(k, v), plan_match=0.0)
        if isinstance(v, bool):
            attrs.update(is_bool=1.0, bval=float(v))
        elif _is_num(v):
            attrs.update(is_num=1.0, num=float(v))
        pid = g.add("pin", f"pin:{path}", path, **attrs)
        for t in targets:
            g.edge(pid, t, "pins", mode)
        plan_items[path] = f"pin:{path}"

    def pin_items(entry: dict, prefix: str):
        """(leaf name, value) of an entry's `family` and `pin` (flattened; a pin may nest)."""
        out = []
        if entry.get("family") is not None:
            out.append(("family", entry["family"]))
        for k, v in synthdb.flat_pins(entry.get("pin") or {}).items():
            out.append((f"pin.{k}", v))
        return out

    for sid, entry in pstruct.items():
        s = ctx.manifest.get(sid)
        if s is None or not s.slot:
            continue
        root = f"core.{s.slot}.{s.index}"
        for k, v in pin_items(entry, ""):
            hold(f"plan.structures.{sid}.{k}", f"{root}.{k[len('pin.'):] if k.startswith('pin.') else k}", v,
                 [snode[sid]], s.mode)
    for gname, entry in (plan.get("shared") or {}).items():
        u = unode.get(gname)
        members = [m for m in (entry.get("members") or []) if ctx.manifest.get(m) is not None]
        owner = ctx.manifest.get(entry.get("canonical")) if entry.get("canonical") else None
        owner = owner or (ctx.manifest.get(members[0]) if members else None)
        if u is not None:
            plan_items[f"plan.shared.{gname}.members"] = f"unit:{gname}"
        if entry.get("canonical"):
            if f"struct:{entry['canonical']}" in g.index:
                g.nodes[g.index[f"struct:{entry['canonical']}"]]["canonical"] = 1.0
                plan_items[f"plan.shared.{gname}.canonical"] = f"struct:{entry['canonical']}"
        for k, v in pin_items(entry, ""):
            if k == "family" and u is not None:
                plan_items[f"plan.shared.{gname}.family"] = f"unit:{gname}"   # the unit's own family attribute
                continue
            var = f"core.{owner.slot}.{owner.index}.{k[len('pin.'):]}" if owner is not None and k.startswith("pin.") else None
            hold(f"plan.shared.{gname}.{k}", var, v, [u] if u is not None else [top])
    for comp, entry in (plan.get("components") or {}).items():
        # the scheme decides the component (sw-pcc / sw-rep): where the declaration's own value differs
        # (half of the int rows), the pin node carries the value that is built
        for k, v in pin_items(entry, ""):
            hold(f"plan.components.{comp}.{k}", f"core.{comp}.{k[len('pin.'):] if k.startswith('pin.') else k}", v,
                 list(unode.values()) + [top])
        for k, v in entry.items():
            if k not in ("family", "pin"):
                hold(f"plan.components.{comp}.{k}", f"core.{comp}.{k}", v, list(unode.values()) + [top])
    for k, v in (plan.get("options") or {}).items():
        hold(f"plan.options.{k}", k, v, list(mode_node.values()) + [top])
    dropped = set(plan.get("dropped") or [])
    for name, v in vals.items():
        gp, _pos, _idx = generic(name)
        is_fam = name.endswith(".family")
        attrs = dict(gpath=gp, name=name.rsplit(".", 1)[-1], value=value_token(name, v),
                     depth=float(name.count(".")), pinned=float(pinned.get(name, 0)), dropped=float(name in dropped),
                     plan_match=0.0 if name in overridden else 1.0)
        if isinstance(v, bool):
            attrs.update(is_bool=1.0, bval=float(v))
        elif _is_num(v):
            rng = (space.vars.get(gp) or {}).get("range") if space is not None else None
            lo, hi = (rng or [0, 0])
            attrs.update(is_num=1.0, num=(float(v) - lo) / (hi - lo) if hi > lo else 0.0)
        if is_fam:
            attrs["family"] = value_token("family", v)
        g.var_node[name] = g.add("slot" if is_fam else "choice", f"var:{name}", f"vals.{name}", **attrs)
    root_of: dict = {}
    for name, i in g.var_node.items():
        p, how = _parent(name, vals, space)
        if how == "declared_absent":
            g.issues.append(f"{name}: its declared parent {p} is not in the declaration")
            p, how = _parent(name, vals, None)
        if p is not None:
            g.edge(i, g.var_node[p], "slot_of" if name.endswith(".family") else "choice_of")
            continue
        root_of[name] = i
    for name, i in root_of.items():
        parts = name.split(".")
        prefix = ".".join(parts[:3])
        if parts[0] == "core" and prefix in ctx.by_index:
            for s in ctx.by_index[prefix]:
                g.edge(i, snode[s.id], "configures", s.mode)
        elif parts[0] == "check" and len(parts) >= 3 and parts[1] in cnode:
            g.edge(i, cnode[parts[1]], "configures")
        elif parts[0] == "core":                    # a unit-level component (core.subword): every unit and the top
            for u in unode.values():
                g.edge(i, u, "component_of")
            g.edge(i, top, "component_of")
        else:                                       # a global choice (x_form): every mode and the top
            for m, j in mode_node.items():
                g.edge(i, j, "global_of", m)
            g.edge(i, top, "global_of")

    # ---- the nested slots' database rows (at the structure's width: a proxy)
    if with_db:
        fk = family_kinds(ctx.pdk)
        for name, i in g.var_node.items():
            if not name.endswith(".family") or not name.startswith("core."):
                continue
            parts = name.split(".")
            prefix = ".".join(parts[:3])
            if name == prefix + ".family" or prefix not in ctx.by_index:
                continue                             # a root slot: the structure carries its row
            P = name[:-len(".family")]
            fam = vals[name]
            kinds = fk.get(str(fam)) or []
            st = ctx.by_index[prefix][0]
            if not kinds:
                g.nodes[i]["db_kind"] = None
                continue
            slot = parts[-2]
            kind = (st.kind if st.kind in kinds else
                    next((k for k in kinds if k in slot), None) or
                    ("adder" if "adder" in kinds and any(h in slot for h in ("adder", "cpa", "subtract")) else None) or
                    ("incrementer" if "incrementer" in kinds and "incr" in slot else None) or kinds[0])
            pins = {k[len(P) + 1:]: v for k, v in vals.items() if k.startswith(P + ".") and k != name}
            r = synthdb.estimate_structure(ctx.pdk, kind, str(fam), pins, int(st.width), ctx.effort,
                                           fmt=_float_format(st) if kind == st.kind else None)
            g.nodes[i].update(db_features(r))
            g.nodes[i].update(db_kind=kind, db_width_proxy=1.0, width=int(st.width))

    # ---- graph-level features
    pf = plan_features(scheme, plan, table)
    toks = scheme_tokens(scheme)
    for t in (space.vocab["scheme_token"] if space is not None else ()):
        g.globals[f"rule__{t}"] = float(space.id("scheme_rule", toks.get(t))) if t in toks else 0.0
    for k, v in pf.items():
        if k.startswith(("SHR__", "KIND__", "GEO__")):
            g.globals[k] = float(v)
    g.globals.update(n_structures=float(len(ctx.manifest)), n_units=float(len(units)), n_modes=float(len(modes)),
                     n_dropped=float(len(dropped)), glue_top=float(ctx.glue.get("top") or 0.0))
    if est:
        g.globals.update(est_area=float(est.get("raw_area_um2") or 0.0), est_delay=float(est.get("raw_delay_ps") or 0.0),
                         est_coverage=float(est.get("coverage") or 0.0))
    for u, i in unode.items():                     # the group's union geometry on the unit too (plan_features' GEO)
        if u in groups and len(groups[u]) >= 2:
            sts = [table[s] for s in groups[u] if s in table]
            g.nodes[i]["n_formats"] = float(len({s["format"] for s in sts}))
    for x in plan.get("dropped") or []:
        plan_items[f"plan.dropped.{x}"] = f"var:{x}" if x in g.var_node else "global:n_dropped"
    g.meta = {"scheme": scheme, "tokens": toks, "plan_items": plan_items, "units": {u: [s.id for s in sts] for u, sts, _sp in units},
              "why": why, "repair_drift": sorted(k for k in set(repaired) | set(vals) if repaired.get(k) != vals.get(k)),
              "estimate": {k: est.get(k) for k in ("ok", "area_um2", "delay_ps", "raw_delay_ps", "coverage", "missing")} if est else {}}
    return g


def path_delay(g: Graph) -> float:
    """The longest mode path the graph's path edges spell (each edge weighs its source unit's delay in
    that mode; the mode's and the top's glue added): the estimate's raw delay when the datapath level
    follows its composition, which `check` counts."""
    glue_top = float(g.globals.get("glue_top", 0.0))
    best = 0.0
    for m_i in g.of_type("mode"):
        m = g.nodes[m_i]["mode"]
        into: dict = {}
        for s_, d_, t, mm, w in g.edges:
            if mm == m and t in ("path", "drives_mode"):
                into.setdefault(d_, []).append((s_, w))
        memo: dict = {}

        def arrive(x):
            if x not in memo:
                memo[x] = max([arrive(s_) + w for s_, w in into.get(x, [])] or [0.0])
            return memo[x]
        if into.get(m_i):
            best = max(best, arrive(m_i) + float(g.nodes[m_i].get("glue") or 0.0) + glue_top)
    return best


# ------------------------------------------------------------------ the completeness check

PLAN_PROSE = ("why", "reduced_after")


def plan_leaves(plan: dict | None) -> list:
    """Every leaf of a plan as a dotted path (`plan.structures.<sid>.pin.<k>`, `plan.shared.<g>.members`,
    `plan.dropped.<var>`, ...), walked without knowing the schema, so a field the builder does not know
    shows up as unencoded; the prose fields (PLAN_PROSE) alone are left out."""
    out = []

    def walk(d, path):
        if isinstance(d, dict):
            for k, v in d.items():
                if k in PLAN_PROSE:
                    continue
                walk(v, f"{path}.{k}")
        elif path == "plan.dropped" and isinstance(d, list):
            out.extend(f"plan.dropped.{x}" for x in d)
        else:
            out.append(path)
    walk(plan or {}, "plan")
    return out


def completeness(g: Graph, ctx: Context, vals: dict, plan: dict | None) -> list:
    """Every way the graph could fail to hold the whole design, as messages (empty: complete):
    a declared variable without its node (or with two), a variable node without its variable, a node
    without provenance, a structure, plan group or unit missing, a plan pin not encoded, an estimate
    row outside the units, a node that reaches no output, a categorical value outside the space."""
    out = []
    plan = plan or {}
    var_nodes = [n for n in g.nodes if n["type"] in ("slot", "choice")]
    names = [n["key"][len("var:"):] for n in var_nodes]
    dup = {x for x in names if names.count(x) > 1}
    if dup:
        out.append(f"variables with more than one node: {sorted(dup)[:5]}")
    if set(names) != set(vals):
        out += [f"variable dropped: {v}" for v in sorted(set(vals) - set(names))]
        out += [f"variable node without a variable: {v}" for v in sorted(set(names) - set(vals))]
    for n in g.nodes:
        if not n.get("src"):
            out.append(f"node without a source: {n['key']}")
    for s in ctx.manifest:
        if f"struct:{s.id}" not in g.index:
            out.append(f"structure missing: {s.id}")
    for u in g.meta["units"]:
        if f"unit:{u}" not in g.index:
            out.append(f"unit missing: {u}")
    items = g.meta.get("plan_items") or {}
    for path in plan_leaves(plan):
        how = items.get(path)
        if how is None:
            out.append(f"plan entry not encoded: {path}")
            continue
        kind, _, ref = how.partition(":")
        if kind == "var":
            if ref not in g.var_node or g.nodes[g.var_node[ref]].get("pinned", 0) < 1:
                out.append(f"plan entry {path}: its variable {ref} carries no plan flag")
        elif kind in ("pin", "unit", "struct") and how not in g.index:
            out.append(f"plan entry {path}: node {how} missing")
    out += [f"graph: {x}" for x in g.issues]
    # every node reaches the top along the directed edges
    succ: dict = {}
    for s_, d_, _t, _m, _w in g.edges:
        succ.setdefault(s_, []).append(d_)
    top = g.index["top"]
    reach = {top}
    pred: dict = {}
    for s_, d_, _t, _m, _w in g.edges:
        pred.setdefault(d_, []).append(s_)
    stack = [top]
    while stack:
        x = stack.pop()
        for p in pred.get(x, []):
            if p not in reach:
                reach.add(p)
                stack.append(p)
    lost = [g.nodes[i]["key"] for i in range(len(g.nodes)) if i not in reach]
    if lost:
        out.append(f"{len(lost)} nodes reach no output: {lost[:5]}")
    if ctx.space is not None:
        sp = ctx.space
        for n in g.nodes:
            if n["type"] in ("slot", "choice"):
                if sp.id("gpath", n.get("gpath")) == 0:
                    out.append(f"variable outside the declared space: {n['key']}")
                if sp.id("value", n.get("value")) == 0:
                    out.append(f"value outside the declared space: {n['key']} {n.get('value')}")
            if n.get("family") is not None and sp.id("value", n["family"]) == 0:
                out.append(f"family outside the vocabulary: {n['key']} {n['family']}")
            for f in ("kind", "format", "special", "db_kind"):
                if n.get(f) and sp.id(f, n[f]) == 0:
                    out.append(f"{f} outside the vocabulary: {n['key']} {n[f]}")
        for t, r in g.meta["tokens"].items():
            if sp.id("scheme_rule", r) == 0 or t not in sp.vocab["scheme_token"]:
                out.append(f"scheme token outside the vocabulary: {t}-{r}")
    return out


# ------------------------------------------------------------------ the dataset in workers

_W: dict = {}


def _init(space_path: str, target: str):
    _W["space"] = Space.load(space_path)
    _W["ctx"] = Context(_W["space"], target)


def _one(row: dict) -> dict:
    ctx = _W["ctx"]
    t0 = time.time()
    try:
        with cached_db():
            g = design_graph(ctx, row["vals"], row.get("scheme") or "", row.get("plan"))
        dt = time.time() - t0
        issues = completeness(g, ctx, row["vals"], row.get("plan"))
    except Exception as e:  # noqa: BLE001 - a row the builder cannot take is a failure, reported
        import traceback
        return {"name": row.get("name"), "issues": [f"exception: {type(e).__name__}: {e}",
                                                     traceback.format_exc()[-800:]], "seconds": time.time() - t0}
    types = {t: 0 for t in NODE_TYPES}
    for n in g.nodes:
        types[n["type"]] += 1
    out = {"name": row.get("name"), "issues": issues, "seconds": dt, "nodes": len(g.nodes), "edges": len(g.edges),
           "vars": len(row["vals"]), "types": types, "drift": len(g.meta["repair_drift"]),
           "prefix_parents": sum(1 for x in g.issues if "declared parent" in x),
           "path_vs_estimate": abs(path_delay(g) - float((g.meta.get("estimate") or {}).get("raw_delay_ps") or 0.0))}
    if _W.get("export"):
        a = g.arrays(_W["space"])
        a.update(name=row.get("name"), area_um2=row.get("area_um2"), delay_ps=row.get("delay_ps"),
                 scheme=row.get("scheme"), node_keys=[n["key"] for n in g.nodes])
        out["arrays"] = a
    return out


def _rows(paths: list, limit: int | None) -> list:
    rows = []
    for p in paths:
        for line in Path(p).read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("vals") is None or r.get("rejected"):
                continue                     # a point the seed refused is no design
            rows.append(r)
            if limit and len(rows) >= limit:
                return rows
    return rows


def _pool_map(rows: list, space_path: str, target: str, jobs: int, export: bool = False) -> list:
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor
    _W["export"] = export
    if jobs <= 1:
        _init(space_path, target)
        return [_one(r) for r in rows]
    with ProcessPoolExecutor(max_workers=jobs, mp_context=mp.get_context("fork"), initializer=_init,
                             initargs=(space_path, target)) as ex:
        return list(ex.map(_one, rows, chunksize=max(1, len(rows) // (jobs * 8))))


def _stats(xs: list) -> str:
    import statistics
    return f"{min(xs)}/{statistics.median(xs):g}/{max(xs)}" if xs else "-"


def cmd_check(a) -> int:
    space = Space.load(a.space)
    bad_total = 0
    report = {}
    for p in a.dataset:
        target = a.target or space.target_of_path(p)
        if target is None:
            print(f"{p}: no target of {sorted(space.d['targets'])} in the path; give --target", file=sys.stderr)
            return 2
        rows = _rows([p], a.limit)
        t0 = time.time()
        res = _pool_map(rows, a.space, target, a.jobs)
        bad = [r for r in res if r["issues"]]
        bad_total += len(bad)
        ok = [r for r in res if not any(i.startswith("exception") for i in r["issues"])]
        types: dict = {}
        for r in ok:
            for k, v in r["types"].items():
                types.setdefault(k, []).append(v)
        rep = {"target": target, "rows": len(res), "complete": len(res) - len(bad),
               "nodes": _stats([r["nodes"] for r in ok]), "edges": _stats([r["edges"] for r in ok]),
               "vars": _stats([r["vars"] for r in ok]),
               "per_type": {k: _stats(v) for k, v in sorted(types.items())},
               "seconds_per_design": _stats([round(r["seconds"], 3) for r in ok]),
               "wall_s": round(time.time() - t0, 1), "jobs": a.jobs,
               "rows_with_repair_drift": sum(1 for r in ok if r["drift"]),
               "path_delay_equals_estimate": f"{sum(1 for r in ok if r['path_vs_estimate'] < 0.5)}/{len(ok)}",
               "path_delay_max_abs_diff_ps": round(max([r["path_vs_estimate"] for r in ok] or [0.0]), 1)}
        report[str(p)] = rep
        print(json.dumps(rep, indent=1))
        from collections import Counter
        kinds = Counter(re.sub(r"[:\s].*", "", i) for r in bad for i in r["issues"])
        if bad:
            print(f"FAIL {target}: {len(bad)} of {len(res)} rows incomplete; issue kinds {dict(kinds)}", file=sys.stderr)
            for r in bad[:a.show]:
                print(f"  {r['name']}: " + " | ".join(r["issues"][:6]), file=sys.stderr)
        else:
            print(f"OK {target}: {len(res)} of {len(res)} rows complete")
    if a.out:
        Path(a.out).write_text(json.dumps(report, indent=1))
    return 1 if bad_total else 0


def cmd_export(a) -> int:
    import pickle
    space = Space.load(a.space)
    target = a.target or space.target_of_path(a.dataset[0])
    rows = [r for r in _rows(a.dataset, a.limit) if a.all or (r.get("area_um2") and r.get("delay_ps"))]
    res = _pool_map(rows, a.space, target, a.jobs, export=True)
    bad = [r for r in res if r["issues"]]
    with open(a.out, "wb") as f:
        pickle.dump({"space": a.space, "target": target, "graphs": [r["arrays"] for r in res if "arrays" in r]}, f)
    print(f"{len(res)} graphs to {a.out}; {len(bad)} incomplete")
    return 1 if bad else 0


def cmd_space(a) -> int:
    t0 = time.time()
    sp = build_space(a.numeric, a.pdk)
    Path(a.out).write_text(json.dumps(sp, default=str))
    print(json.dumps({"out": a.out, "seconds": round(time.time() - t0, 1),
                      "targets": {t: v["searched_variables"] for t, v in sp["targets"].items()},
                      "vocab": {k: len(v) for k, v in sp["vocab"].items()}, "conflicts": sp["conflicts"][:10]}, indent=1))
    return 0


_S: dict = {}


def _sample_one(i: int) -> dict:
    """One random declaration under a random scheme, repaired and realized as the surrogate's sampler
    does (surrogate_seeds.Stage.draw and _render, without the rendering check)."""
    import random
    from adir.backends.numeric import sample_declaration
    from chialu.front_seeds import realize
    from chialu.surrogate_features import scheme_repair
    rng = random.Random(_S["seed"] * 1000003 + i)
    num, inst, ctx, manifest, schemes = _S["num"], _S["inst"], _S["ctx"], _S["manifest"], _S["schemes"]
    vals = sample_declaration(num, rng)
    name, plan_s = rng.choice(schemes)
    vals = scheme_repair(vals, plan_s)
    row = {"name": f"g{i:05d}", "scheme": name, "vals": vals, "source": "graph_sample"}
    try:
        plan, err = realize(inst, ctx, manifest, {"declarations": {"vars": vals}}, row["name"], 0, plan_s)
    except Exception as e:  # noqa: BLE001
        plan, err = None, f"{type(e).__name__}: {str(e)[:200]}"
    row["plan"] = plan
    if plan is None:
        row["rejected"] = err
    return row


def sample_rows(numeric, n: int, seed: int = 0, level: str = "natural", jobs: int = 1) -> list:
    """`n` random declarations of a target under random schemes, repaired and realized (`_sample_one`)."""
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor
    from chialu.surrogate_seeds import schemes_of
    # declarations from the numeric run file, schemes and realization from the search run file beside it
    # (as the surrogate's stage and tests/test_numeric_space do: the numeric file narrows fp_fma's
    # `sharing` to dedicated_per_mode, so its own template refuses every shared-FMA scheme)
    num = numeric_instance(numeric)
    inst = numeric_instance(Path(numeric).with_name(Path(numeric).name.replace(".numeric", "")))
    ctx = inst.ctx()
    schemes, manifest = schemes_of(inst, ctx, level)
    _S.update(num=num, inst=inst, ctx=ctx, manifest=manifest, schemes=schemes, seed=seed)
    if jobs <= 1:
        return [_sample_one(i) for i in range(n)]
    with ProcessPoolExecutor(max_workers=jobs, mp_context=mp.get_context("fork")) as ex:
        return list(ex.map(_sample_one, range(n), chunksize=4))


def cmd_sample(a) -> int:
    """Random declarations of a target that has no dataset, to exercise the builder on its space."""
    t0 = time.time()
    rows = sample_rows(a.numeric, a.n, a.seed, a.level, a.jobs)
    with open(a.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    rej = sum(1 for r in rows if r.get("rejected"))
    print(f"{len(rows)} declarations of {Path(a.numeric).name} ({len(_S['schemes'])} schemes) to {a.out}, "
          f"{rej} the seed refused (kept, plan None), {time.time() - t0:.0f}s")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("space", help="the declared space and vocabularies of one or more targets")
    s.add_argument("numeric", nargs="+")
    s.add_argument("--out", required=True)
    s.add_argument("--pdk", default="nangate45")
    c = sub.add_parser("check", help="build every row's graph and prove it complete")
    c.add_argument("dataset", nargs="+")
    c.add_argument("--space", required=True)
    c.add_argument("--target")
    c.add_argument("--jobs", type=int, default=24)
    c.add_argument("--limit", type=int)
    c.add_argument("--show", type=int, default=10)
    c.add_argument("--out")
    e = sub.add_parser("export", help="the numpy arrays of every measured row's graph, pickled")
    e.add_argument("dataset", nargs="+")
    e.add_argument("--space", required=True)
    e.add_argument("--target")
    e.add_argument("--out", required=True)
    e.add_argument("--jobs", type=int, default=24)
    e.add_argument("--limit", type=int)
    e.add_argument("--all", action="store_true", help="rows without a measurement too")
    m = sub.add_parser("sample", help="random declarations of a target without a dataset")
    m.add_argument("numeric")
    m.add_argument("--n", type=int, default=300)
    m.add_argument("--seed", type=int, default=0)
    m.add_argument("--level", default="natural")
    m.add_argument("--jobs", type=int, default=8)
    m.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"space": cmd_space, "check": cmd_check, "export": cmd_export, "sample": cmd_sample}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
