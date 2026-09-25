"""chiALU's CHIA nodes: lint, the verify-layer gates (conformance,
fault harness), yosys equivalence, yosys statistics, and yosys/ABC
synthesis on a PDK descriptor. Every input arrives as text or a dict
and every output is a dict, so a node runs unchanged on a ray worker or
in ADIR's local executor. `adir.node` documents the outputs and wraps
each function as a `@ChiaFunction` when CHIA is importable."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from adir import node

REPO_ROOT = Path(__file__).resolve().parents[1]
# The `eda` pool counts what a task really occupies rather than the task itself, since Ray sees
# neither the processes a tool forks nor the memory it holds. Measured on the host (23 GB, 2026-09-17):
# one synthesis of the vec_dot_acc seed (540 KB, 195k cells) peaks at 8.78 GB, fp_alu_cmp at 1.24 GB
# and int_subword_alu at 0.11 GB. A pool of 8 with a weight of 1 would admit eight of the first and
# run the machine out of memory, so a synthesis reserves a quarter of the pool and at most four run
# at once. CHIALU_EDA_SYNTH_WEIGHT tunes it for a larger machine.
SYNTH_WORKERS = max(1, int(os.environ.get("CHIALU_SYNTH_JOBS", "1")))
EDA_RESOURCE = max(float(SYNTH_WORKERS), float(os.environ.get("CHIALU_EDA_SYNTH_WEIGHT", "2")))
# A simulation node builds a Verilator model, and that build runs CHIALU_VERILATOR_JOBS compilers
# inside the one task, which Ray cannot see. The node therefore reserves that many slots, so the
# pool counts processes rather than tasks: `eda: 8` with four jobs admits two builds, eight
# compilers.
SIM_RESOURCE = float(os.environ.get("CHIALU_VERILATOR_JOBS", "4"))


def _die_with_parent():
    """preexec_fn for the EDA subprocesses on Linux: the child gets
    SIGKILL when its worker dies."""
    if sys.platform.startswith("linux"):
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.prctl(1, 9)
        except Exception:  # noqa: BLE001
            pass


_MODULE_EDGE_RE = re.compile(r"^\s*(?:module|package|interface)\b|^\s*end(?:module|package|interface)\b", re.M)


def largest_module_bytes(rtl_text: str) -> int:
    """The byte length of the largest module (or package) of a text, by
    its header and end lines."""
    best, start = 0, None
    for m in _MODULE_EDGE_RE.finditer(rtl_text):
        if m.group(0).lstrip().startswith("end"):
            if start is not None:
                best = max(best, m.end() - start)
                start = None
        else:
            start = m.start()
    return best


# The yosys frontend is yosys-slang (`read_slang`, which yosys 0.68+36 carries built in), and it
# reads the generated SystemVerilog as written. The frontend is part of the flow, so it enters the
# database's tool hash.
FRONTEND = "slang"


def frontend_source(rtl_text: str, td: str, name: str = "cand"):
    """(path, error) of the file the yosys frontend reads, which is the
    SystemVerilog itself."""
    src = Path(td) / f"{name}.sv"
    src.write_text(rtl_text)
    return src, ""


def frontend_read(path, top: str = "", hierarchy: bool = False) -> str:
    """The yosys command that reads `path`. `top` narrows the
    elaboration to one module, which is what `synth_unit` needs to map
    each unit alone. `hierarchy` keeps the instance tree, which the
    frontend otherwise elaborates away into a single module.

    The flow does not use it: keeping the hierarchy changes the netlist
    `synth -flatten` then produces, and with it the metric (measured on
    the host, int_subword_alu: area 5734.4 -> 5799.1 um2, ABC delay
    2248.3 -> 2239.6 ps), which would make a new measurement
    incomparable with the database and with everything measured before.
    chialu.synthreport asks for it in a second pass of its own, because
    its attribution needs the instance tree the metric's pass discards."""
    opts = (" --top " + top if top else "") + (" --best-effort-hierarchy" if hierarchy else "")
    return f"read_slang{opts} {path}\n"


def _pdk(pdk) -> dict:
    if isinstance(pdk, dict):
        return pdk
    import pdk as pdk_pkg
    return pdk_pkg.resolve(str(pdk))


def liberty_files(pdk: dict) -> list:
    """Liberty paths on the EDA node for a PDK descriptor: the copy under
    pdk/lib when present, else ~/pdk/<file>, fetched from the
    descriptor's url on first use (gunzipped when the url ends in .gz)."""
    import gzip
    import urllib.request
    out = []
    for lib in pdk.get("liberty") or []:
        rel = (lib.get("path") or lib.get("file")) if isinstance(lib, dict) else str(lib)
        url = lib.get("url") if isinstance(lib, dict) else None
        local = Path(rel) if Path(rel).is_absolute() else REPO_ROOT / rel
        if local.is_file():
            out.append(str(local))
            continue
        home = Path.home() / "pdk" / Path(rel).name
        if not home.is_file() and url:
            home.parent.mkdir(parents=True, exist_ok=True)
            data = urllib.request.urlopen(url, timeout=120).read()
            if url.endswith(".gz"):
                data = gzip.decompress(data)
            home.write_bytes(data)
        out.append(str(home))
    return out


def flow_id(kwargs: dict) -> str:
    """The flow one synthesis runs under, as a string the node cache folds
    into its key: the liberty files, the resolved ABC script and the tool
    versions. A node's keyword arguments name the PDK by its name alone,
    so without this a changed liberty or an upgraded yosys serves the old
    measurement for the same text."""
    from chialu import synthdb
    pdk = _pdk(kwargs.get("pdk") or "nangate45")
    effort = str(kwargs.get("effort") or "medium")
    from chialu.synth_records import VERSION, seeds_for
    seeds = seeds_for(kwargs.get("repeats", 5), kwargs.get("seeds"))
    return f"{VERSION}|{seeds}|{synthdb.liberty_hash(pdk)}|{synthdb.tool_hash(pdk)}|{abc_script_for(pdk, effort, 0)}"


def tool_flow_id(kwargs: dict) -> str:
    """The flow a yosys or simulator node runs under: the tool versions
    alone, since those nodes name no PDK."""
    from chialu import synthdb
    return synthdb.tool_hash()


# ----------------------------------------------------------------- lint

# A candidate is one self-contained text: every evaluator reads it alone, with no user include path.
# A text that reaches a file outside itself (an `include of a sibling run's program, a $readmem of
# a table) would be measured on that file's design, so it is rejected before any tool runs.
_EXT_DIRECTIVE_RE = re.compile(r"`\s*include\b[^\n]*")
_EXT_TASK_RE = re.compile(r"\$(readmemh|readmemb|writememh|writememb|fopen|fread|fscanf|fgets|system)\b")
_EXT_STRING_RE = re.compile(r'"((?:[^"\\\n]|\\.)*)"')


def _strip_comments(text: str) -> str:
    """The text without // and /* */ comments (string literals kept, so a
    `//` inside a string does not cut it)."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"' and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            out.append(" ")
            i = n if j < 0 else j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def external_refs(rtl_text) -> list:
    """The references of a candidate text to anything outside itself: an
    `include (in any form, comments aside), a file system task ($readmem*,
    $fopen, ...), and a string literal naming an absolute path, a `../`
    path or a run directory. Empty for a self-contained text."""
    text = _strip_comments(rtl_of(rtl_text) or "")
    found = [f"`include: {m.group(0).strip()[:160]}" for m in _EXT_DIRECTIVE_RE.finditer(text)]
    found += [f"file system task ${m.group(1)}" for m in _EXT_TASK_RE.finditer(text)]
    for m in _EXT_STRING_RE.finditer(text):
        s = m.group(1)
        if s.startswith("/") or s.startswith("~/"):
            found.append(f"absolute path \"{s[:160]}\"")
        elif "../" in s or "..\\" in s:
            found.append(f"relative path \"{s[:160]}\"")
        elif re.search(r"(^|/)run/", s):
            found.append(f"run directory \"{s[:160]}\"")
    return found


def _external_ref_failure(rtl_text, t0: float, key: str = "ok"):
    """The failed result of a node for a candidate with external references, else None."""
    refs = external_refs(rtl_text)
    if not refs:
        return None
    return {key: False, "detail": "external reference: " + "; ".join(refs[:8]),
            "seconds": round(time.time() - t0, 1)}


@node(cache_id=tool_flow_id, outputs=["ok", "detail", "seconds"], resources={"eda": 0.1})
def lint(rtl_text: str) -> dict:
    """A yosys read with hierarchy check, then the structural
    checks: the text parses, elaborates, and carries no latch, no driver
    conflict and no undriven or unused bit that `check` reports. `check
    -assert` stops on a multiply driven or undriven wire, and the two
    `select -assert-none` lines stop on an inferred latch, which is a
    sequential element in a combinational unit. A candidate that passes
    the parse and fails one of these used to reach the gates as ok."""
    rtl_text = rtl_of(rtl_text)
    t0 = time.time()
    bad = _external_ref_failure(rtl_text, t0)
    if bad is not None:
        return bad
    with tempfile.TemporaryDirectory() as td:
        rtl, err = frontend_source(rtl_text, td)
        if rtl is None:
            return {"ok": False, "detail": f"{FRONTEND}: {err}", "seconds": round(time.time() - t0, 1)}
        ys = Path(td) / "lint.ys"
        ys.write_text(frontend_read(rtl) + "hierarchy -check -auto-top\nproc\n"
                      "check -assert\n"
                      "select -assert-none t:$dlatch\n"
                      "select -assert-none t:$_DLATCH_*\n")
        try:
            r = subprocess.run(["yosys", "-q", str(ys)], capture_output=True, text=True,
                               timeout=300, preexec_fn=_die_with_parent)
        except subprocess.TimeoutExpired:
            return {"ok": False, "detail": "yosys lint timeout", "seconds": round(time.time() - t0, 1)}
    return {"ok": r.returncode == 0, "detail": "" if r.returncode == 0 else (r.stderr or r.stdout)[-2000:],
            "seconds": round(time.time() - t0, 1)}


# ----------------------------------------------------------- simulation

# the structure kinds a data path crosses in series in a float mode (the parallel op units stand between them)
SERIES_KINDS = ("unpacker", "rounder")


def _float_format(s) -> str | None:
    """The float format a structure of a float kind is built for (a block
    mode's element format stands for it), else None: fp16 and bf16 are
    both 16 bits and share no geometry, so a float row is looked up by
    its format rather than by its width."""
    from chialu.synthdb import FP_DB_KINDS
    from chialu.verify.formats import BlockFormat, FloatFormat, parse_format
    if (getattr(s, "slot", None) or getattr(s, "kind", None)) not in FP_DB_KINDS:
        return None
    try:
        fmt = parse_format(str(getattr(s, "format", "") or ""))
    except ValueError:
        return None
    if isinstance(fmt, BlockFormat):
        fmt = fmt.elem
    return fmt.name if isinstance(fmt, FloatFormat) else None


@node(outputs=["ok", "area_um2", "delay_ps", "raw_area_um2", "raw_delay_ps", "coverage", "structures", "missing", "rows",
               "unmodeled", "detail", "seconds"],
      resources={"eda": 0.05})
def estimate(files: dict, decl: dict, pdk: str = "nangate45", effort: str = "medium",
             area_scale: float = 1.0, delay_scale: float = 1.0, plan_json: str = "",
             glue_json: str = "", context_json: str = "") -> dict:
    """The synthesis database's estimate of a declaration (the numeric
    stage of the search, docs/demo-plan.md): per structure of the
    unit's manifest the row of its declared family and pins at its
    width (synthdb.estimate_structure), the area summed over the
    structures (one unit per structure: the plan of a declaration-only
    candidate), the delay the longest mode path (the series kinds of
    the mode summed, plus the slowest op unit, plus the glue the top
    adds around them). `glue_json` carries that glue as `{"mode":
    {mode: ps}, "top": ps}`, measured once per target by chialu.profile
    on the baseline seed (the pipeline's calibrate stage): the rows are
    modules synthesized alone, so the OR of a mode's unit buses, the
    mode mux and the flag map are in no row. They belong to the unit
    rather than to a candidate, so they enter as an addition instead of
    being left to `delay_scale`, which would stretch a candidate far
    faster than the baseline by the same factor. `context_json` carries
    `{"<kind>/<family>": factor}` from the same profile
    (chialu.profile.context_factors): the delay a unit of that kind and
    family adds where it stands, over the wires its driver reads,
    against the same module synthesized alone, which is what its row
    is. A unit that overlaps its producer costs less in place than its
    row says, and one factor for the whole design (`delay_scale`)
    cannot tell one kind from another; a row of a (kind, family) the
    profile did not see is taken at its own delay. `coverage` is the
    fraction of structures with a row; a structure without one counts
    zero and is listed in `missing`. `area_scale` and `delay_scale`
    multiply the sums (the pipeline's calibrate stage fits them on the
    baseline seed, measured against this estimate: the database's rows
    are modules synthesized alone, at their own timing target); the
    unscaled sums are `raw_area_um2` and `raw_delay_ps`. `plan_json` is
    a sharing plan (chialu.plans.PLAN_DOC) as JSON: its shared groups
    are estimated as one unit each (a lane-partitioned adder, a twin
    multiplier or a gate row at the bus width under the group's family
    or the first member's, a rounder or unpacker at the widest format;
    an adder with its comparator or its gates as the members' rows),
    so the numeric stage ranks declarations under one sharing scheme."""
    from chialu import synthdb
    from chialu.targets.rtl.alu_seed import structure_manifest
    from chialu.targets.rtl.structures import is_inline
    t0 = time.time()
    spec = _spec_of(files)
    if spec.get("unit") != "alu":
        return {"ok": False, "detail": "the estimate covers the ALU template", "seconds": round(time.time() - t0, 1)}
    try:
        manifest = structure_manifest(spec)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": f"manifest: {type(e).__name__}: {str(e)[:200]}", "seconds": round(time.time() - t0, 1)}
    decl = decl if isinstance(decl, dict) else {}

    def declared(slot: str, index: str) -> dict:
        cur = decl.get(slot)
        for part in index.split("."):
            if not isinstance(cur, dict):
                return {}
            cur = cur.get(part)
        return cur if isinstance(cur, dict) else {}

    def family_of(s, group_family=None):
        d = declared(s.slot, s.index)
        family = group_family or d.get("family")
        if family is None:                            # an undeclared family stands at its domain's default
            fams = synthdb.families_of(s.slot)
            family = fams[0] if fams else None
        return family, {k: v for k, v in d.items() if k != "family"}

    units = None
    if plan_json:
        from chialu.plans import partition_of_plan
        plan = json.loads(plan_json) if isinstance(plan_json, str) else dict(plan_json)
        from chialu.surrogate_features import decl_vars, nest, scheme_repair
        decl = nest(scheme_repair(decl_vars(decl), plan))
        try:
            units = [(u, [manifest.get(m) for m in members]) for u, members in partition_of_plan(manifest, plan)]
        except ValueError as e:
            return {"ok": False, "detail": f"plan: {e}", "seconds": round(time.time() - t0, 1)}
        group_family = {u: (plan.get("shared") or {}).get(u, {}).get("family") for u, _ in units}
    else:
        units = [(s.id, [s]) for s in manifest]
        group_family = {}

    # A fused family owns its mode's add/multiply slots. Its mode-selected
    # sharing is expressed by pins rather than mixed-kind STRUCTURE groups.
    # Price the same physical FMA banks the renderer builds, once per lane.
    fused_modes = {s.mode for s in manifest if s.kind == "fp_fma" and
                   family_of(s)[0] not in (None, "separate_multiplier_and_adder")}
    fma_shared = [s for s in manifest if s.kind == "fp_fma" and s.mode in fused_modes
                  and family_of(s)[1].get("sharing") == "shared_across_formats"]
    if fused_modes:
        shared_ids = {s.id for s in fma_shared}
        units = [(u, [s for s in sts if s.id not in shared_ids and
                      not (s.mode in fused_modes and s.kind in ("fp_adder", "fp_multiplier"))])
                 for u, sts in units]
        units = [(u, sts) for u, sts in units if sts]
        for lane in sorted({s.lane for s in fma_shared}):
            units.append((f"fp_fma_bank_l{lane}", [s for s in fma_shared if s.lane == lane]))

    def bus_width(sts) -> int:
        return max(sum(int(x.width) for x in sts if x.mode == m) for m in {x.mode for x in sts})


    context, bad_context = {}, False
    if context_json:
        try:
            context = {str(k): float(v) for k, v in
                       (json.loads(context_json) if isinstance(context_json, str) else dict(context_json)).items()}
        except (ValueError, TypeError, AttributeError):
            bad_context = True

    def add(sid, est, modes, kind, family=None):
        """One unit's area once, its delay in every mode it serves, at
        the factor its (kind, family) costs in place."""
        nonlocal total_area
        total_area += est["area_um2"]
        # The per-unit rows are kept, not only their sum. Summing them here bakes in a composition
        # -- area added up, delay the longest mode path -- and measurement says that composition is
        # exactly what is wrong: with no sharing the sum over-estimates by about 1.7x because
        # synthesis optimizes across the units anyway, and with full sharing it under-estimates by
        # about 1.8x because one unit serving three formats carries the union geometry and its mode
        # muxes. A caller that wants to learn the composition rather than correct it afterwards
        # needs the parts, and they cost nothing extra: every one was already looked up.
        rows.append({"id": sid, "kind": kind, "family": str(getattr(family, "name", family)),
                     "area_um2": round(float(est["area_um2"]), 2),
                     "delay_ps": round(float(est["delay_ps"]), 2),
                     "modes": sorted(int(m) for m in modes)})
        unmodeled.extend(f"{sid}: {u}" for u in est["unmodeled"])
        key = f"{kind}/{getattr(family, 'name', family)}"
        f = context.get(key)
        if f is None:
            uncontexted.add(key)
        delay = est["delay_ps"] * (1.0 if f is None else f)
        for mode in modes:
            m = per_mode.setdefault(mode, {"series": {}, "parallel": 0.0})
            if kind in SERIES_KINDS:
                m["series"][kind] = max(m["series"].get(kind, 0.0), delay)
            else:
                m["parallel"] = max(m["parallel"], delay)

    total_area, per_mode, n, missing, unmodeled = 0.0, {}, 0, [], []
    rows: list = []
    uncontexted: set = set()

    # A float kind's structures grouped across two formats or more are one datapath per lane position, and a
    # rounder or unpacker declared shared_across_formats one per lane: the seed then widens every float mode
    # of the unit to one geometry, so every float row is read at that geometry rather than at the format's own.
    from chialu.targets.rtl.families.partition import FP_SHARE_KINDS, is_float_structure
    shared_float = len({s.mode for s in fma_shared}) > 1 or any(
        len(sts) >= 2 and {s.kind for s in sts} in FP_SHARE_KINDS and all(is_float_structure(s) for s in sts)
        and len({s.format for s in sts}) >= 2 for _u, sts in
        [(u, [s for s in ss if s is not None]) for u, ss in units]) or any(
        s.kind in ("rounder", "unpacker") and family_of(s)[0] == "shared_across_formats" for s in manifest if s.slot)
    geom_tag = None
    if shared_float:
        from chialu.targets.rtl.alu_seed import union_geometry
        try:
            g = union_geometry(spec, {f"core.{s.slot}.{s.index}": family_of(s) for s in manifest if s.slot})
            geom_tag = g.tag() if g is not None else None
        except Exception as e:  # noqa: BLE001 - a spec the geometry refuses is priced at the formats' own
            unmodeled.append(f"union geometry: {type(e).__name__}: {str(e)[:80]}")

    def geom_of(s):
        return geom_tag if _float_format(s) else None

    for unit, sts in units:
        sts = [s for s in sts if s is not None and s.slot and not is_inline(s) and s.library]
        # An fp_fma declared separate_multiplier_and_adder is no module of its own: its lane's fp_adder and
        # fp_multiplier compute it and are priced as themselves (partition.fuse_multiply_add takes it out of
        # every group). Counted, it stood as a structure the database lacks -- four of fp_alu_cmp's nine units
        # under its fmt-all plan, coverage 0.56 against the numeric stage's 0.8, so that stage ranked almost
        # no point and its front was the baseline alone.
        sts = [s for s in sts if not (s.kind == "fp_fma" and str(family_of(s)[0]) == "separate_multiplier_and_adder")]
        if not sts:
            continue
        n += 1
        kinds = {s.kind for s in sts}
        if len(sts) == 1 or kinds in ({"adder", "comparator"}, {"adder", "logic"}):
            # one structure, or a pair the seed builds from both members' logic: the members' own rows; a unit
            # is missing once, when no member has a row
            found = False
            for s in sts:
                family, pins = family_of(s)
                est = synthdb.estimate_structure(pdk, s.slot, str(family), pins, int(s.width), effort,
                                                 fmt=_float_format(s), geom=geom_of(s)) if family else {}
                if not est:
                    unmodeled.append(f"{s.id}: no row for {family}@{s.width}")
                    continue
                found = True
                add(s.id, est, (s.mode,), s.kind, family)
            if not found:
                missing.append(f"{unit}: " + ", ".join(f"{s.id}@{s.width}" for s in sts))
            continue
        if kinds == {"adder", "fp_adder"}:
            # the integer adders' bank widened to the float significand add: the bank's row at the significand width
            # (a multiple of the finest lane) under the first integer adder's family, plus each float adder's row
            # less the row of its own significand adder, which the bank replaces
            ints = [s for s in sts if s.kind == "adder"]
            fps = [s for s in sts if s.kind == "fp_adder"]
            fam, pins = family_of(ints[0], group_family.get(unit))
            fine = min(int(s.width) for s in ints)
            iw = max(int(s.width) for s in fps)          # the fp_adder row's width is the significand add's
            w_sh = ((max(bus_width(ints), iw + 1) + fine - 1) // fine) * fine
            est = synthdb.estimate_structure(pdk, "adder", str(fam), pins, w_sh, effort) if fam else {}
            if not est:
                missing.append(f"{unit}: {fam}@{w_sh}")
                continue
            add(unit, est, sorted({s.mode for s in sts}), "adder", fam)
            for f in fps:
                ffam, fpins = family_of(f)
                fest = synthdb.estimate_structure(pdk, f.slot, str(ffam), fpins, int(f.width), effort,
                                                  fmt=_float_format(f), geom=geom_of(f)) if ffam else {}
                if not fest:
                    unmodeled.append(f"{f.id}: no row for {ffam}@{f.width}")
                    continue
                sig = {k[len("sig_adder."):]: v for k, v in fpins.items() if str(k).startswith("sig_adder.")} \
                    if any(str(k).startswith("sig_adder.") for k in fpins) else fpins.get("sig_adder", {})
                sfam = (sig or {}).get("family") or (synthdb.families_of("adder") or [None])[0]
                sfam = getattr(sfam, "name", sfam)
                sest = synthdb.estimate_structure(pdk, "adder", str(sfam), {k: v for k, v in (sig or {}).items() if k != "family"},
                                                  int(f.width), effort) if sfam else {}
                fest = dict(fest)
                if sest:
                    fest["area_um2"] = max(0.0, fest["area_um2"] - sest["area_um2"])
                else:
                    unmodeled.append(f"{f.id}: its own significand adder ({sfam}) not subtracted")
                add(f.id, fest, (f.mode,), f.kind, ffam)
            unmodeled.append(f"{unit}: the operand muxes of the shared significand add")
            continue
        # a shared group: one unit at the bus width (or the widest member) under the group's family or the first
        # member's, its delay counted in every mode it serves
        first = sts[0]
        family, pins = family_of(first, group_family.get(unit))
        width = bus_width(sts) if kinds <= {"adder", "multiplier", "logic"} else max(int(s.width) for s in sts)
        est = synthdb.estimate_structure(pdk, first.slot, str(family), pins, width, effort,
                                         fmt=_float_format(first), geom=geom_of(first)) if family else {}
        if not est and family and kinds <= {"multiplier", "rounder", "unpacker"}:
            # no row for the sharing family at this width: the widest member's own family stands in
            family, pins = family_of(first)
            est = synthdb.estimate_structure(pdk, first.slot, str(family), pins, width, effort,
                                             fmt=_float_format(first), geom=geom_of(first)) if family else {}
            if est:
                unmodeled.append(f"{unit}: shared as {group_family.get(unit)}, estimated as {family}")
        if not est:
            missing.append(f"{unit}: {family}@{width}")
            continue
        add(unit, est, sorted({s.mode for s in sts}), first.kind, family)
        if first.kind == "adder":
            unmodeled.append(f"{unit}: lane-boundary carry gates of the partitioned adder")
    glue = {}
    if glue_json:
        try:
            glue = json.loads(glue_json) if isinstance(glue_json, str) else dict(glue_json)
        except (ValueError, TypeError):
            unmodeled.append(f"glue_json: not a measurement ({str(glue_json)[:40]})")
    g_mode = {int(k): float(v) for k, v in (glue.get("mode") or {}).items()}
    g_top = float(glue.get("top") or 0.0)
    delay = max((sum(m["series"].values()) + m["parallel"] + g_mode.get(mode, 0.0) + g_top
                 for mode, m in per_mode.items()), default=0.0)
    coverage = (n - len(missing)) / n if n else 0.0
    ka, kd = float(area_scale or 1.0), float(delay_scale or 1.0)
    scaled = f"; scaled by {ka:.3f} (area) and {kd:.3f} (delay)" if (ka, kd) != (1.0, 1.0) else ""
    if glue:
        scaled = (f"; glue {g_top:.0f} ps at the top and up to {max(g_mode.values(), default=0.0):.0f} ps "
                  f"per mode") + scaled
    elif per_mode:
        unmodeled.append("the top's glue (the OR of the units, the mode mux, the flags): no profile")
    if bad_context:
        unmodeled.insert(0, f"context_json: not a measurement ({str(context_json)[:40]})")
    if context:
        scaled = f"; {len(context)} context factors" + scaled
        if uncontexted:
            unmodeled.insert(0, f"{len(uncontexted)} without a context factor, priced at their rows: "
                             + ", ".join(sorted(uncontexted)[:8]))
    elif per_mode:
        unmodeled.append("the context of the rows (a unit's delay where it stands): no profile")
    return {"ok": n > 0 and coverage > 0, "area_um2": round(total_area * ka, 1), "delay_ps": round(delay * kd, 1),
            "raw_area_um2": round(total_area, 1), "raw_delay_ps": round(delay, 1),
            "coverage": round(coverage, 3), "structures": n, "missing": missing[:40], "unmodeled": unmodeled[:40],
            "rows": rows,
            "detail": f"{n - len(missing)} of {n} structures from the database" + (f"; {len(unmodeled)} pins unmodeled" if unmodeled else "") + scaled,
            "seconds": round(time.time() - t0, 1)}


_SURROGATE_CACHE: dict = {}


def _surrogate_parts(files: dict, model: str) -> tuple:
    """(bundle, structure table) of a surrogate model file and a spec, cached
    by the file's path and mtime and the spec's text."""
    import pickle
    p = Path(model)
    mkey = (str(p), p.stat().st_mtime)
    skey = hashlib.sha256(str(files.get("spec.json", "")).encode()).hexdigest()
    if _SURROGATE_CACHE.get("model_key") != mkey:
        with p.open("rb") as f:
            _SURROGATE_CACHE["bundle"] = pickle.load(f)
        for m in _SURROGATE_CACHE["bundle"]["models"].values():
            m.set_params(n_jobs=1)                     # one prediction at a time, beside other searches
        _SURROGATE_CACHE["model_key"] = mkey
    if _SURROGATE_CACHE.get("spec_key") != skey:
        from chialu.surrogate_features import manifest_table
        from chialu.targets import derive
        _SURROGATE_CACHE["table"] = manifest_table(derive.seed_alu_text(_spec_of(files), None).structures)
        _SURROGATE_CACHE["spec_key"] = skey
    return _SURROGATE_CACHE["bundle"], _SURROGATE_CACHE["table"]


@node(outputs=["ok", "area_um2", "delay_ps", "est_area_um2", "est_delay_ps", "known", "detail", "seconds"],
      resources={"eda": 0.01})
def surrogate(files: dict, decl: dict, model: str, plan_json: str = "", scheme: str = "unshared",
              pdk: str = "nangate45", effort: str = "medium", glue_json: str = "", context_json: str = "",
              x_form: str = "exact", full_decl: dict | None = None) -> dict:
    """The whole-unit surrogate's area and delay of a declaration: the
    XGBoost/GNN model chialu.surrogate_seeds fits on this target's own
    whole-unit syntheses (at the search run's clock and mapping), over
    `rows + plan + one-hot` (chialu.surrogate_features) of the declaration
    under the sharing scheme `plan_json` (named `scheme`): the estimate's
    own sum and rows, the scheme's groups and geometry, and every declared
    variable. `known` is the fraction of the declaration's one-hot columns
    the model was trained with (null for GNN). Graph inference also consumes
    `full_decl`, the declaration node output, because decl.core drops check.*."""
    t0 = time.time()
    try:
        from chialu.surrogate_features import decl_vars, features, scheme_repair
        from chialu.surrogate_seeds import predict, scheme_trained
        bundle, table = _surrogate_parts(files, model)
        if not scheme_trained(bundle, scheme):
            # the model never saw this sharing scheme (or too rarely): no prediction rather than an extrapolation
            return {"ok": False, "detail": f"scheme {scheme!r} not in the model's training set "
                    f"({(bundle.get('schemes') or {}).get(scheme, 0)} rows < {bundle.get('min_per_scheme')})",
                    "seconds": round(time.time() - t0, 3)}
        plan = json.loads(plan_json) if plan_json else None
        vals = scheme_repair(decl_vars(decl if isinstance(decl, dict) else {}), plan)
        if bundle.get("model_type", "xgboost") == "gnn":
            from chialu.surrogate_gnn import bound_vars
            if full_decl is None:
                raise ValueError("GNN requires full_decl from the declaration node (including check.*)")
            vals = scheme_repair(bound_vars(full_decl), plan)
        vals["x_form"] = x_form
        f = features(files, vals, scheme, plan, table,
                     {"pdk": pdk, "effort": effort, "glue_json": glue_json, "context_json": context_json})
        graphs = None
        if bundle.get("model_type", "xgboost") == "gnn":
            from chialu.surrogate_gnn import graph_input
            graphs = [graph_input(bundle["graph_space"], files, vals, scheme, plan,
                                  {"pdk": pdk, "effort": effort, "glue_json": glue_json, "context_json": context_json})]
        p = predict(bundle, [f], graphs=graphs)
        names = set(bundle.get("names", []))
        oh = [k for k in f if k.startswith("OH__")]
        return {"ok": True, "area_um2": round(float(p["area_um2"][0]), 2), "delay_ps": round(float(p["delay_ps"][0]), 2),
                "est_area_um2": f.get("EST__area"), "est_delay_ps": f.get("EST__delay"),
                "known": (round(sum(1 for k in oh if k in names) / max(1, len(oh)), 3)
                          if graphs is None else None), "detail": "",
                "seconds": round(time.time() - t0, 3)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": f"{type(e).__name__}: {str(e)[:200]}", "seconds": round(time.time() - t0, 3)}


def rtl_of(rtl) -> str:
    """The RTL text of a candidate: a text, or the member dictionary of a
    multi-file seed (ADIR hands `candidate.core` of a family artifact as
    {member: text} in member order), joined in that order."""
    if isinstance(rtl, dict):
        return "\n".join(str(t) for t in rtl.values())
    return "" if rtl is None else str(rtl)


def _declared_rule_members(rtl_text: str) -> list:
    """The VAR values of the candidate's declaration block that a
    behavior rule or a conditional family governs, or [] (no block, or
    none)."""
    try:
        from adir.declaration import parse_block
        from chialu.behavior_rules import declared_rule_members
        d = parse_block(rtl_text)
        return declared_rule_members(d.vars) if d.present else []
    except Exception:  # noqa: BLE001 - a note on a failure never becomes a failure of its own
        return []


# the phases of the last _sim_bundle of this process: {"simulator", "compile_s", "run_s"} (the benchmark reads it)
LAST_SIM = {}
# the compiled models of the universal testbench, one per (simulator, design, checker, bench) content key: a
# candidate's conformance and fault campaigns run the same build (the fault build also holds the checker)
def _strip_build(root: Path, exe: Path) -> None:
    """Drop a cached build's compile intermediates (Verilator's precompiled headers alone are ~130 MB
    a build; the cache grew by ~90 GB in half an hour under Table A): a later hit runs the executable
    and reads nothing else, so the executable, the sources and the metadata stay."""
    keep = {exe.resolve()}
    for f in root.rglob("*"):
        if f.is_file() and f.resolve() not in keep and f.suffix in (".gch", ".o", ".a", ".d", ".cpp", ".h", ".mk", ".dat"):
            try:
                f.unlink()
            except OSError:
                pass


SIM_BUILD_CACHE_DIR = Path(os.environ.get("CHIALU_SIM_BUILD_CACHE") or (Path.home() / ".cache" / "chialu" / "sim_build"))
UNIVERSAL_TB = os.environ.get("CHIALU_UNIVERSAL_TB", "1") != "0"


def _universal_ports(spec: dict):
    """(ports, core_ins, chk_ins, chk_outs) of the universal testbench for a
    spec, or None where the unit's bench is clocked or table-driven (the
    SFU's slot tables), which keeps the per-campaign bench."""
    unit = spec.get("unit")
    if spec.get("latency_cycles") or spec.get("variable_latency_max"):
        return None
    if unit == "alu":
        from chialu.verify import alu_ref as A
        lay = A.alu_layout(A.normalize_spec(spec))
        core = [p.name for p in lay["core_in"]]
        extra = list(lay["chk_extra"])
        chk_outs = (["d"] if lay["d_w"] else []) + (["flags"] if lay["flags"] and spec.get("check_flags") else [])
        return list(lay["core_in"]) + extra + list(lay["core_out"]), core, core + [p.name for p in extra], chk_outs
    if unit == "vec_dot_acc":
        from chialu.verify import dot_ref as D
        lay = D.dot_layout(D.normalize_dot_spec(spec))
        core = [p.name for p in lay["core_in"]]
        extra = list(lay["chk_extra"])
        chk_outs = ["flags"] if (lay["flags"] and spec.get("check_flags")) else []
        return list(lay["core_in"]) + extra + list(lay["core_out"]), core, core + [p.name for p in extra], chk_outs
    if unit == "vec_sfu":
        from chialu.verify import sfu_ref as S
        lay = S.sfu_layout(S.normalize_sfu_spec(spec))
        if lay.get("slots"):
            return None
        core = [p.name for p in lay["core_in"]]
        return list(lay["core_in"]) + list(lay["core_out"]), core, core, []
    return None


def _candidate_build(rtl_text: str, checker_rtl: str | None, spec: dict, files: dict, simulator: str | None = None):
    """(build, meta) of a candidate's universal testbench: the design
    the checker where given and the bench compiled once under
    SIM_BUILD_CACHE_DIR by content key, or None where the unit keeps the
    per-campaign bench. meta carries the nets of the internal sites, the
    vector count and the campaign row bound the bench was sized for."""
    from chialu.verify import fault_sites, simulate as SIM, tb_gen
    if not UNIVERSAL_TB:
        return None, {}
    ports = _universal_ports(spec)
    if ports is None:
        return None, {}
    ports, core_ins, chk_ins, chk_outs = ports
    n_vectors = len(files.get("vectors.hex", "").split())
    if not n_vectors:
        return None, {}
    checked = bool(checker_rtl)
    sim = simulator or SIM.DEFAULT
    if sim not in SIM.SIMULATORS:
        raise ValueError(f"simulator {sim!r}: one of {SIM.SIMULATORS}")
    y_w = next((p.width for p in ports if p.direction == "out" and p.name == "y"), 1)
    n_masks = int(spec.get("n_random_masks", 2000))
    # the seam plan: clean + one bit per output bit + random; the grouped plan: per group the same plus the
    # internal corruptions (2 x n_masks at most) over at most every legal (mode, op) pair and a replica group
    groups = 1
    if checked and spec.get("unit") == "alu":
        try:
            from chialu.targets.rtl.alu_checker import check_groups
            gs, _u, _r = check_groups(spec)
            groups = len(gs) + 1
        except (ValueError, KeyError):
            groups = 2
    max_rows = max(512 + y_w + n_masks, groups * (128 + y_w + 2 * n_masks)) if checked else 0
    sim = SIM.choose(sim)
    nets = []
    if checked and spec.get("unit") == "alu":
        table = fault_sites.sites_by_pair(rtl_text, spec.get("dut_name", "alu_core"))
        seen = set()
        for key in sorted(table, key=str):
            for path, w in table[key]:
                if path not in seen:
                    seen.add(path)
                    nets.append((path, w))
    tb = tb_gen.emit_tb_universal(spec.get("dut_name", "alu_core"), ports, n_vectors,
                                  checker_name=spec.get("checker_name", "alu_checker") if checked else None,
                                  max_rows=max_rows, nets=nets, core_ins=core_ins, chk_ins=chk_ins, chk_outs=chk_outs)
    key = hashlib.sha256("\0".join([sim, rtl_text, checker_rtl or "", tb]).encode()).hexdigest()[:24]
    d = SIM_BUILD_CACHE_DIR / key
    meta = {"nets": nets, "n_vectors": n_vectors, "max_rows": max_rows, "key": key, "simulator": sim}
    if (d / "build.json").is_file():
        info = json.loads((d / "build.json").read_text())
        b = SIM.Build(sim, True, info["exe"], compile_s=0.0, cached=True,
                      sources=info.get("sources", ["design.v"] + (["extra.sv"] if checker_rtl else [])), tb="tb.sv", cwd=str(d))
        return b, meta
    tmp = SIM_BUILD_CACHE_DIR / f"{key}.build-{os.getpid()}"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    # Verilator reads the generated SystemVerilog directly (packages, imports, `return`, `foreach`
    # and the rest), so the simulation path converts nothing.
    (tmp / "design.sv").write_text(rtl_text)
    srcs = ["design.sv"]
    if checker_rtl:
        (tmp / "extra.sv").write_text(checker_rtl)
        srcs.append("extra.sv")
    (tmp / "tb.sv").write_text(tb)
    b = SIM.build(srcs, "tb.sv", tmp, sim, compile_timeout=900, preexec_fn=_die_with_parent)
    if not b.ok:
        shutil.rmtree(tmp, ignore_errors=True)
        return b, meta
    exe = str(d / Path(b.exe).relative_to(tmp))
    _strip_build(tmp, Path(b.exe))
    (tmp / "build.json").write_text(json.dumps({"exe": exe, "simulator": sim, "compile_s": round(b.compile_s, 2),
                                                "nets": nets, "n_vectors": n_vectors, "max_rows": max_rows, "sources": srcs}))
    try:
        os.replace(tmp, d)
    except OSError:
        shutil.rmtree(tmp, ignore_errors=True)        # another process won the race
    b.exe = exe
    b.cwd = str(d)
    return b, meta


def _run_campaign(b, files: dict, plusargs: list, dump: str, timeout_s: int):
    """(error_or_None, stdout, dump_text) of one campaign of a build: the
    bundle's files land in a scratch directory the run works in."""
    from chialu.verify import simulate as SIM
    with tempfile.TemporaryDirectory() as td:
        for name, text in files.items():
            if name.endswith((".hex",)):
                (Path(td) / name).write_text(text)
        res = SIM.run(b, td, plusargs + [f"+dump={dump}"], run_timeout=timeout_s, preexec_fn=_die_with_parent)
        p = Path(td) / dump
        if res.ok and not (p.is_file() and p.stat().st_size):
            # a Verilator model that ends at time 0 with no output and no dump (seen on the fault builds of some
            # seeds, while their conformance builds run) is a dead model rather than a passing
            # campaign, so it fails and names the reason.
            res.ok = False
            res.phase = res.phase or "sim"
            res.detail = "the Verilator model ended with no dump; the campaign produced no result"
        LAST_SIM.clear()
        LAST_SIM.update({"simulator": res.simulator, "compile_s": round(res.compile_s, 2), "run_s": round(res.run_s, 2),
                         "cached": b.cached, **({"note": res.note} if res.note else {})})
        if not res.ok:
            return ({"phase": res.phase, "pass": False, "detail": res.detail, "simulator": res.simulator}, res.stdout, "")
        p = Path(td) / dump
        return None, res.stdout, (p.read_text() if p.is_file() else "")


def _sim_bundle(rtl_text: str, files: dict, tb: str, extra_rtl: str, timeout_sim: int, simulator: str | None = None):
    """Write the candidate and its files to a scratch directory, compile and run
    under Verilator (chialu.verify.simulate).
    (error_or_None, stdout, dump_text)."""
    from chialu.verify import simulate as SIM
    t0 = time.time()
    with tempfile.TemporaryDirectory() as td:
        design = Path(td) / "design.sv"
        design.write_text(rtl_text)          # Verilator reads the SystemVerilog as generated
        for name, text in files.items():
            (Path(td) / name).write_text(text)
        srcs = [str(design)]
        if extra_rtl:
            (Path(td) / "extra.sv").write_text(extra_rtl)
            srcs.append(str(Path(td) / "extra.sv"))
        res = SIM.simulate(srcs, tb, td, simulator, compile_timeout=900, run_timeout=timeout_sim,
                           preexec_fn=_die_with_parent)
        LAST_SIM.clear()
        LAST_SIM.update({"simulator": res.simulator, "compile_s": round(res.compile_s, 2),
                         "run_s": round(res.run_s, 2), **({"note": res.note} if res.note else {})})
        if not res.ok:
            return ({"phase": res.phase, "pass": False, "detail": res.detail, "simulator": res.simulator,
                     "seconds": round(time.time() - t0, 1)}, res.stdout, "")
        dumps = sorted(Path(td).glob("*dump.hex"))
        dump = dumps[0].read_text() if dumps else ""
    return None, res.stdout, dump


def _spec_of(files: dict) -> dict:
    if "spec.json" not in files:
        raise ValueError("the verify files carry no spec.json")
    spec = json.loads(files["spec.json"])
    if "detect" in spec:
        spec["detect"] = {k: tuple(v) for k, v in spec["detect"].items()}
    return spec


@node(outputs=["pass", "detail", "mismatch_count", "first_mismatches", "cycles_per_frame",
               "max_ulp", "metrics", "seconds", "algorithm_pass", "budget_pass", "mathematical_metrics",
               "accuracy_mode", "budget_applied", "error_range", "error_range_complete"], resources={"eda": SIM_RESOURCE})
def conformance(rtl_text: str, files: dict, timeout_s: int = 1800) -> dict:
    """The conformance gate from the verify files (tb.sv, vectors.hex,
    expected.hex, spec.json): a bit-exact testbench prints CONFORMANCE
    PASS/FAIL; an accuracy-bounded unit dumps its results and the judge
    the spec's budget defines rules on the dump."""
    rtl_text = rtl_of(rtl_text)
    t0 = time.time()
    bad = _external_ref_failure(rtl_text, t0, "pass")
    if bad is not None:
        return bad
    b = None
    if "spec.json" in files:
        try:
            b, _meta = _candidate_build(rtl_text, None, _spec_of(files), files)
        except (ValueError, KeyError) as e:      # a spec the universal bench does not cover: the bundle's bench
            b = None
    if b is not None and not b.ok:
        return {"phase": b.phase, "pass": False, "detail": b.detail, "seconds": round(time.time() - t0, 1)}
    if b is not None:
        args = ["+campaign=0", "+vectors=vectors.hex", f"+n={len(files['vectors.hex'].split())}"]
        if "expected.hex" in files:
            args.append("+expected=expected.hex")
        err, out, dump = _run_campaign(b, files, args, "dump.hex", timeout_s)
    else:
        err, out, dump = _sim_bundle(rtl_text, files, "tb.sv", "", timeout_s)
    if err:
        err.setdefault("detail", "")
        err["seconds"] = round(time.time() - t0, 1)
        return err
    if "DUMP DONE" in out and "CONFORMANCE" not in out:
        spec = _spec_of(files)
        if spec.get("unit") == "vec_dot_acc" and spec.get("dot_contract") == "architecture":
            return {"pass": False, "phase": "verification_bundle", "algorithm_pass": False,
                    "detail": "architecture contracts require an exact expected.hex bundle; regenerate the verification files"}
        from chialu.verify.harness import build_verification
        with tempfile.TemporaryDirectory() as td:
            ver = build_verification(spec, Path(td))
            p = Path(td) / "dump.hex"
            p.write_text(dump)
            ok, viol, rep = ver.check(p)
        metrics = rep.summary() if hasattr(rep, "summary") else {}
        result = {"pass": bool(ok), "detail": "; ".join(viol) if viol else "accuracy within budget",
                "metrics": metrics, "max_ulp": metrics.get("max_ulp"),
                "seconds": round(time.time() - t0, 1)}
        if spec.get("unit") == "vec_sfu":
            from chialu.verify.sfu_range import result_of
            result.update(result_of(ver, rep))
            result["budget_pass"] = bool(ok) if result["budget_applied"] else None
            if not result["budget_applied"]:
                if ok:
                    result["detail"] = "complete implementation error range reported; user error target is not applied"
        return result
    ok = "CONFORMANCE PASS" in out
    mism = [l for l in out.splitlines() if "MISMATCH" in l][:10]
    m = re.search(r"CONFORMANCE FAIL (\d+) of", out)
    detail = "bit-exact against the reference" if ok else \
        f"{m.group(1) if m else '?'} vectors mismatch; the first ones:\n" + "\n".join("* " + l for l in mism)
    if not ok and "spec.json" in files:
        try:
            from chialu.verify.harness import build_verification
            spec = _spec_of(files)
            with tempfile.TemporaryDirectory() as td:
                ver = build_verification(spec, Path(td))
            detail = f"{m.group(1) if m else '?'} vectors mismatch; the first ones:\n" + \
                "\n".join("* " + ver.explain(l) for l in mism[:8])
        except Exception:  # noqa: BLE001
            pass
    cm = re.search(r"CYCLES_PER_FRAME (\d+)", out)
    result = {"pass": ok, "mismatch_count": 0 if ok else (int(m.group(1)) if m else -1),
            "first_mismatches": mism, "detail": detail,
            "cycles_per_frame": int(cm.group(1)) if cm else None,
            "seconds": round(time.time() - t0, 1)}
    if not ok:
        # a rule defect candidate (docs/behav_checker_plan.md, pitfall 1): the declaration names a member a
        # behavior rule or a conditional family governs, which the rules admitted under this contract; the
        # archive keeps these apart from ordinary failures (python3 -m chialu.behavior_rules defects)
        members = _declared_rule_members(rtl_text)
        result["rule_defect_candidate"] = bool(members)
        result["rule_members"] = members
        if members:
            result["detail"] += ("\nthe declaration names " + ", ".join(members) + ", which chialu.behavior_rules "
                                 "admitted under this contract: a failure of a library-rendered unit here is a rule "
                                 "or library defect rather than a candidate defect")
    spec = _spec_of(files) if "spec.json" in files else {}
    if spec.get("unit") == "vec_dot_acc" and spec.get("dot_contract") == "architecture":
        result.update(algorithm_pass=ok, budget_pass=None)
        if ok:
            from chialu.verify.architecture_accuracy import dot_accuracy
            from chialu.verify.harness import build_verification
            with tempfile.TemporaryDirectory() as td:
                accuracy = dot_accuracy(build_verification(spec, Path(td)))
            result.update(accuracy)
            result.update(metrics=accuracy["mathematical_metrics"], max_ulp=accuracy["mathematical_metrics"]["max_ulp"])
            if accuracy["budget_pass"] is False:
                result.update({"pass": False, "phase": "accuracy", "detail": "; ".join(accuracy["budget_violations"])})
            else:
                result["detail"] = "architecture bit-exact; " + ("mathematical budget satisfied" if accuracy["budget_pass"] else "mathematical error reported without an explicit budget")
            result["seconds"] = round(time.time() - t0, 1)
    return result


@node(outputs=["pass", "detail", "false_alarms", "single_bit_coverage", "alias_rate", "rates",
               "escape", "escape_max", "groups", "sites", "seconds"], resources={"eda": SIM_RESOURCE})
def fault(rtl_text: str, files: dict, checker_rtl: str, timeout_s: int = 1800, seed_sites: int = 0) -> dict:
    """The fault harness: the candidate core and the frozen checker under
    fault_tb.sv with masks.hex; the verdict (false alarms, single-bit
    coverage, alias rate) from the fault plan the spec rebuilds.

    `alias_rate` is the seam campaign's `random_alias`, an XOR mask on
    `y_core` before the checker, so for a conformant core it depends on
    the vector, the mask and the checker declaration rather than on the
    candidate's own logic. It gates the checker declaration. The number
    that does depend on the datapath is the grouped campaign's `escape`,
    the fraction of one-bit corruptions of a unit's internal nets the
    checker misses; `escape` is that rate per group and `escape_max` its
    worst group, which a run file constrains. The gate fails when the
    candidate exposes no injection site, or sites for fewer than half the
    checked pairs (`site_violations`), or, with `seed_sites` (the seed's
    `fault.sites`, optional), fewer than half the seed's sites."""
    rtl_text = rtl_of(rtl_text)
    t0 = time.time()
    # fault runs beside lint, not after it: a candidate that reaches outside its text ($system,
    # `include, $readmem) must not reach the simulator here either
    bad = _external_ref_failure(rtl_text, t0, "pass")
    if bad is not None:
        return bad
    spec = _spec_of(files)
    b = None
    try:
        b, meta = _candidate_build(rtl_text, checker_rtl, spec, files)
    except (ValueError, KeyError):
        b, meta = None, {}
    if b is not None and not b.ok:
        return {"phase": b.phase, "pass": False, "detail": b.detail, "seconds": round(time.time() - t0, 1)}
    if not files.get("masks.hex", "").split():
        # the bundle of an unchecked spec carries no fault plan and no fault bench; the run file of
        # such a target does not bind this node, and a direct call says so rather than reporting a
        # bench that read no masks and dumped nothing
        return {"pass": False, "detail": "the verify bundle carries no masks.hex: the spec declares no "
                                         "checker, so there is no fault campaign to run",
                "seconds": round(time.time() - t0, 1)}
    if b is not None:
        n_masks_file = len(files.get("masks.hex", "").split())
        args = ["+campaign=1", "+vectors=vectors.hex", "+masks=masks.hex",
                f"+n={len(files['vectors.hex'].split())}", f"+m={n_masks_file}"]
        err, out, dump = _run_campaign(b, files, args, "fault_dump.hex", timeout_s)
    else:
        err, out, dump = _sim_bundle(rtl_text, files, "fault_tb.sv", checker_rtl, timeout_s)
    if err:
        err.setdefault("detail", "")
        err["seconds"] = round(time.time() - t0, 1)
        return err
    if not dump:
        return {"pass": False, "detail": "no fault dump", "seconds": round(time.time() - t0, 1)}
    from chialu.verify.harness import build_fault_verification, build_verification
    with tempfile.TemporaryDirectory() as td:
        ver = build_verification(spec, Path(td))
        _plan, check = build_fault_verification(spec, ver, Path(td),
                                                n_random_masks=spec.get("n_random_masks", 2000))
        p = Path(td) / "fault_dump.hex"
        p.write_text(dump)
        ok, viol, rep = check(p)
    rates = rep.summary() if hasattr(rep, "summary") else {}
    out = {"pass": bool(ok), "detail": "; ".join(viol) if viol else "checker verdict ok",
           "false_alarms": rates.get("false_alarms"),
           "single_bit_coverage": rates.get("single_bit_coverage"),
           "alias_rate": rates.get("random_alias"), "rates": rates,
           "seconds": round(time.time() - t0, 1)}
    if spec.get("unit") == "alu" and spec.get("checker_name"):
        grouped = fault_groups(rtl_text, files, checker_rtl, spec, timeout_s, build=(b, meta) if b is not None else None)
        out.update(grouped)
        esc = grouped.get("escape") or {}
        out["escape_max"] = max(esc.values()) if esc else 0.0
        if grouped.get("group_violations"):
            out["pass"] = False
            out["detail"] = (out["detail"] + "; " if viol else "") + "; ".join(grouped["group_violations"])
        elif not esc:
            # no escape rate was measured (the grouped campaign did not run): an empty maximum is no
            # evidence that the checker catches internal faults, so the gate does not pass on it
            out["pass"] = False
            out["detail"] = ((out["detail"] + "; " if viol else "") + "no internal-net escape rate measured: "
                             + str(grouped.get("groups_detail", "grouped campaign did not run"))[:600])
        if seed_sites:
            # `sites` is the plan's count, the same number the seed's `fault.sites` reports
            extra = site_violations({"sites": int(grouped.get("sites") or 0)}, int(seed_sites))
            extra = [v for v in extra if "seed" in v]
            if extra:
                out["pass"] = False
                out["detail"] = out["detail"] + "; " + "; ".join(extra)
        out["seconds"] = round(time.time() - t0, 1)
    return out


def fault_groups(rtl_text: str, files: dict, checker_rtl: str, spec: dict, timeout_s: int, build=None) -> dict:
    """The campaign per check rule group (docs/checker-spec-plan.md, "The
    fault campaign"): the masks partitioned by the vector's (mode, op)
    into the groups of the check table (the one-rule spelling has the
    group `all`, its replica pairs the group `replica`), each group's
    vectors under clean, one-bit and random seam masks (`output_alias`)
    and under one-bit corruptions of the internal nets its units declare
    (`escape`); each group gated by its rule's `detect`. Returns
    {"groups": {name: rates}, "escape": {name: rate}, "sites": n,
    "group_violations": [...]}, or {"groups_detail": reason} where the
    campaign could not run."""
    from chialu.verify import fault_sites, tb_gen
    from chialu.verify.faults import DetectBudget, FaultPlan, FaultReport
    from chialu.verify.harness import build_verification
    from chialu.verify import alu_ref as A
    from chialu.targets.rtl.alu_checker import check_groups
    try:
        groups, unchecked, _replica = check_groups(spec)
    except ValueError as e:
        return {"groups_detail": f"no groups: {e}"}
    with tempfile.TemporaryDirectory() as td:
        ver = build_verification(spec, Path(td))
    lay = A.alu_layout(A.normalize_spec(spec))
    y = next(p for p in lay["core_out"] if p.name == "y")
    y_w, out_w = y.width, sum(p.width for p in lay["core_out"])
    of_pair = {}
    for g in groups:
        for pr in g.coded:
            of_pair[pr] = g.name
        for pr in g.replica:
            of_pair[pr] = "replica"
    # both tables are keyed by the (mode, op) pair rather than flattened per group, so
    # `build_grouped` can spread a group's rows over its pairs and drive an internal site on a
    # vector the unit at that site serves. Flattening them put the whole group on one pair's
    # vectors and left 84% of the stuck rows forcing a site the driven op never reaches, which the
    # campaign then counted as no fault.
    vectors_by_group: dict = {}
    for i, m in enumerate(ver.meta):
        pair = (m["mode"], m["op"])
        name = of_pair.get(pair)
        if name is not None:
            vectors_by_group.setdefault(name, {}).setdefault(pair, []).append(i)
    if not vectors_by_group:
        return {"groups_detail": "no checked pair has a vector"}
    table = fault_sites.sites_by_pair(rtl_text, spec.get("dut_name", "alu_core"))
    sites_by_group = {}
    for g in groups:
        sites_by_group[g.name] = {pr: fault_sites.sites_for([pr], table) for pr in sorted(g.coded)}
    sites_by_group["replica"] = {pr: fault_sites.sites_for([pr], table)
                                 for pr in sorted({pr for g in groups for pr in g.replica})}
    checked = [pr for g in groups for pr in sorted(g.coded)]
    site_pairs = {"checked": len(checked), "with_sites": sum(1 for pr in checked if fault_sites.sites_for([pr], table)),
                  "sites": len({s for pr in checked for s in fault_sites.sites_for([pr], table)})}
    early = site_violations(site_pairs)
    if early:                                   # nothing to inject into: no campaign, and the gate fails
        return {"groups_detail": "; ".join(early), "sites": site_pairs["sites"], "group_violations": early,
                "site_pairs": site_pairs}
    n_masks = int(spec.get("n_random_masks", 2000))
    plan = FaultPlan.build_grouped(y_w, vectors_by_group, spec.get("seed", 1), n_masks,
                                   sites_by_group=sites_by_group, n_sites=n_masks)
    if build is not None and build[0] is not None and build[0].ok:
        b, meta = build
        if len(plan.rows) > meta.get("max_rows", 0):
            return {"groups_detail": f"grouped plan of {len(plan.rows)} rows exceeds the bench's {meta.get('max_rows')}"}
        words, pw = tb_gen.plan_words_universal(plan.rows, meta["nets"], plan.sites, len(ver.vecs), y_w)
        with tempfile.TemporaryDirectory() as td:
            tb_gen.write_hex(Path(td) / "fault_plan.hex", words, pw)
            plan_text = (Path(td) / "fault_plan.hex").read_text()
        err, _out, dump = _run_campaign(b, {"vectors.hex": files["vectors.hex"], "fault_plan.hex": plan_text},
                                        ["+campaign=2", "+vectors=vectors.hex", "+plan=fault_plan.hex",
                                         f"+n={len(ver.vecs)}", f"+m={len(plan.rows)}"], "fault_sites_dump.hex", timeout_s)
    else:
        words, pw = tb_gen.plan_words(plan.rows, plan.sites, len(ver.vecs), y_w)
        core_names = [p.name for p in lay["core_in"]]
        extra = list(lay["chk_extra"])
        ports = list(lay["core_in"]) + extra + list(lay["core_out"])
        chk_outs = (["d"] if lay["d_w"] else []) + (["flags"] if lay["flags"] and spec.get("check_flags") else [])
        tb = tb_gen.emit_fault_tb_sites(spec.get("dut_name", "alu_core"), spec["checker_name"], ports, len(ver.vecs),
                                        plan.rows, plan.sites, core_ins=core_names,
                                        chk_ins=core_names + [p.name for p in extra], chk_outs=chk_outs)
        with tempfile.TemporaryDirectory() as td:
            tb_gen.write_hex(Path(td) / "fault_plan.hex", words, pw)
            plan_text = (Path(td) / "fault_plan.hex").read_text()
        sim_files = {"vectors.hex": files["vectors.hex"], "fault_plan.hex": plan_text, "fault_sites_tb.sv": tb}
        err, _out, dump = _sim_bundle(rtl_text, sim_files, "fault_sites_tb.sv", checker_rtl, timeout_s)
    if err:
        return {"groups_detail": f"grouped campaign {err.get('phase')}: {str(err.get('detail', ''))[-600:]}", "sites": len(plan.sites) - 1}
    lines = dump.split()
    reports = {name: FaultReport() for name in plan.groups}
    expected_y = [(w >> (out_w - y_w)) & ((1 << y_w) - 1) for w in ver.expected]
    for row, ln in zip(plan.rows, lines):
        if not _is_hex_word(ln):
            continue
        val = int(ln, 16)
        alarm = (val >> y_w) & 1
        got = val & ((1 << y_w) - 1)
        rep = reports[row["group"]]
        if row["kind"] == "clean":
            rep.add_clean(alarm)
        elif row["kind"] == "stuck":
            if got == expected_y[row["vector"]]:
                rep.add_masked()
            else:
                rep.add_fault("stuck", row["site"], alarm)
        else:
            rep.add_fault(row["kind"], row["mask"], alarm)
    detect_of = {g.name: g.detect for g in groups}
    legacy = spec.get("detect") if not spec.get("check") else None
    violations, rates, escape = [], {}, {}
    for name, rep in reports.items():
        rates[name] = rep.summary()
        rates[name]["sites"] = len({r["site"] for r in plan.rows if r["group"] == name and r["kind"] == "stuck"})
        if rep.escape is not None:
            escape[name] = rep.escape
        if name == "replica":
            budget = DetectBudget([("false_alarms", "==", 0)])
        elif legacy is not None:
            budget = DetectBudget([(k, op, b) for k, (op, b) in legacy.items()])
        else:
            budget = DetectBudget.for_rule(detect_of.get(name), n_masks)
        ok, viol = budget.verdict(rep)
        if not ok:
            violations += [f"rule {name}: {v}" for v in viol]
    if len(lines) < len(plan.rows):
        violations.append(f"grouped fault dump has {len(lines)} of {len(plan.rows)} lines")
    violations += site_violations(site_pairs)
    return {"groups": rates, "escape": escape, "sites": len(plan.sites) - 1, "group_violations": violations,
            "site_pairs": site_pairs}


# The internal-net campaign measures the checker only where the candidate exposes the unit nets it
# corrupts. A candidate that flattens or renames its units away exposes none, its escape rate is then an
# empty maximum (0.0) and the gate used to pass; the audit of exp3 found every such case. The gate now
# fails when fewer than this fraction of the checked (mode, op) pairs have a site, or when no site is left.
MIN_SITE_PAIR_FRACTION = 0.5


def site_violations(site_pairs: dict, seed_sites: int = 0) -> list:
    """The violations of the injection-site floor: no site at all, fewer
    than MIN_SITE_PAIR_FRACTION of the checked pairs with a site, or,
    with the seed's site count, fewer than that fraction of its sites."""
    n, k, sites = site_pairs.get("checked", 0), site_pairs.get("with_sites", 0), site_pairs.get("sites", 0)
    out = []
    if n and sites == 0:
        out.append("fault sites: the candidate exposes 0 injection sites (flattened or renamed units); "
                   "the internal-net campaign cannot measure the checker")
    elif n and k < MIN_SITE_PAIR_FRACTION * n:
        out.append(f"fault sites: only {k} of {n} checked (mode, op) pairs have an injection site "
                   f"(< {MIN_SITE_PAIR_FRACTION:.0%})")
    if seed_sites and sites < MIN_SITE_PAIR_FRACTION * seed_sites:
        out.append(f"fault sites: {sites} injection sites, fewer than {MIN_SITE_PAIR_FRACTION:.0%} "
                   f"of the seed's {seed_sites}")
    return out


def _is_hex_word(s: str) -> bool:
    return bool(s) and all(c in "0123456789abcdefABCDEF" for c in s)


@node(outputs=["rtl_text", "manifest", "groups", "ok", "detail", "seconds"], resources={"eda": 0.1})
def checker_gen(files: dict, decl=None) -> dict:
    """The checker of a candidate under its declared check rules: the
    spec the verification files carry, with the candidate's `decl.check`
    mapping (the family, pins, comparator and slot choices per rule
    group) applied, regenerated through the checker generator. A
    generator that depends on a searched variable is a node rather than
    a bind-time artifact (ADIR design 3.7); `fault` reads `rtl_text`.
    Without a `check` table the frozen checker is returned unchanged."""
    t0 = time.time()
    spec = _spec_of(files)
    from chialu.modules.check_rules import apply_declaration
    from chialu.targets.rtl.alu_checker import alu_checker_sv, check_manifest
    if spec.get("unit") != "alu":
        return {"ok": False, "rtl_text": "", "manifest": [], "groups": 0,
                "detail": f"checker_gen: unit {spec.get('unit')!r} has no rule table", "seconds": round(time.time() - t0, 1)}
    try:
        if isinstance(decl, dict) and spec.get("check"):
            spec = apply_declaration(spec, decl)
        rtl, _protected = alu_checker_sv(spec, spec.get("checker_name", "alu_checker"))
        manifest = check_manifest(spec)
    except (ValueError, KeyError) as e:
        return {"ok": False, "rtl_text": "", "manifest": [], "groups": 0,
                "detail": f"checker_gen: {e}", "seconds": round(time.time() - t0, 1)}
    groups = spec.get("check", {}).get("groups") if spec.get("check") else None
    names = ", ".join(f"{g['name']}={g['family']}" for g in (groups or []))
    return {"ok": True, "rtl_text": rtl, "manifest": manifest, "groups": len(groups) if groups else 1,
            "detail": names or "the one-rule checker", "seconds": round(time.time() - t0, 1)}


@node(outputs=["pass", "detail", "seconds"], resources={"eda": EDA_RESOURCE})
def equiv_check(rtl_a: str, rtl_b: str, top: str, timeout_s: int = 300) -> dict:
    """Combinational equivalence of two realizations of `top` (yosys
    equiv_simple/equiv_induct). pass True/False, or None when
    the check timed out or could not decide."""
    t0 = time.time()
    with tempfile.TemporaryDirectory() as td:
        a, ea = frontend_source(rtl_a, td)
        if a is None:
            return {"pass": None, "detail": f"{FRONTEND}(a): {ea}", "seconds": round(time.time() - t0, 1)}
        tdb = Path(td) / "b"           # the source carries a fixed file name: one directory per side
        tdb.mkdir()
        b, eb = frontend_source(rtl_b, str(tdb))
        if b is None:
            return {"pass": None, "detail": f"{FRONTEND}(b): {eb}", "seconds": round(time.time() - t0, 1)}
        ys = Path(td) / "equiv.ys"
        ys.write_text(
            frontend_read(a, top) + f"prep -top {top}\nrename {top} gold\n"
            f"design -stash gold\n"
            + frontend_read(b, top) + f"prep -top {top}\nrename {top} gate\n"
            f"design -stash gate\n"
            f"design -copy-from gold -as gold gold\n"
            f"design -copy-from gate -as gate gate\n"
            f"equiv_make gold gate equiv\nhierarchy -top equiv\n"
            f"equiv_simple -seq 1\nequiv_induct -seq 1\n"
            f"equiv_status -assert\n")
        try:
            r = subprocess.run(["yosys", "-q", str(ys)], capture_output=True, text=True,
                               timeout=timeout_s, preexec_fn=_die_with_parent)
        except subprocess.TimeoutExpired:
            return {"pass": None, "detail": f"equiv timeout {timeout_s}s",
                    "seconds": round(time.time() - t0, 1)}
    ok = r.returncode == 0
    # yosys prints "Found N unproven $equiv cells", so the test is case-insensitive; an undecided
    # induction is `pass: None` and a counterexample is `pass: False`, which are different verdicts
    log = r.stdout + r.stderr
    unproven = re.search(r"\bunproven\b", log, re.I) is not None
    return {"pass": None if (not ok and unproven) else ok,
            "detail": ((("undecided: " if unproven else "") + (r.stderr or r.stdout)[-1500:])
                       if not ok else ""),
            "seconds": round(time.time() - t0, 1)}


def _cells(log: str):
    """The cell count of a yosys `stat` block, in the `Number of cells:
    N` form (yosys to 0.66) or the `N cells` form (yosys 0.68)."""
    # the last block: synth prints its own stat before the mapping, and the
    # mapped netlist's count is the one that stands
    ms = list(re.finditer(r"Number of cells:\s*(\d+)", log))
    if not ms:
        # yosys 0.68: `N cells`, or `N <area> cells` under a liberty stat
        ms = list(re.finditer(r"^\s*(\d+)\s+(?:[\d.]+(?:[eE][+-]?\d+)?\s+)?cells\s*$", log, re.M))
    return ms[-1] if ms else None


# ------------------------------------------------------------ synthesis

def abc_commands(script: str) -> str:
    """The ABC script file text for a descriptor's `abc.script`: the
    "+cmd,arg;cmd" form becomes one command per line; a text without the
    leading '+' is already a script."""
    if not script.startswith("+"):
        return script
    return "\n".join(c.replace(",", " ") for c in script[1:].split(";") if c) + "\n"


EFFORTS = ("low", "medium", "high")
# every effort optimizes the AIG before mapping; a mapping-only flow (the mapper alone
# on the hashed netlist) is not offered, since its area and delay reflect the RTL's
# syntax more than its logic
# `topo;stime` after the mapping prints the `Delay = <n> ps` line `abc_delay_ps` is
# read from; a script without it maps but reports no delay
#
# The mapper is `&nf`, the flow the synthesis database was built under and the one
# yosys's own `-liberty` default uses. `&nf -D` is inert in this ABC build (identical
# mappings at D = 1 and D = 1e6), so the delay target reaches the netlist through the
# buffering tail alone. `buffer;upsize -D;dnsize -D` is what yosys appends when a
# constraint is given, and it is what the flow was missing: without it ABC's `stime`
# charges the mapper's high-fanout nets in full, which overstates the delay of every
# float-bearing design by 12 to 27% and leaves the integer ones unmoved (measured
# 2026-09-17, docs/plan.md of chialu-a3eval). The classic `map -D <ps>` responds to
# its target properly and gives 3 to 8% less area at 3 to 5% more delay; it stays
# reachable as CHIALU_ABC_FLOW=map, and it is not the default because it flips
# fp_alu_cmp's front_3 seed from feasible (7577 ps) to infeasible (8949 ps).
BUFFER_TAIL = "buffer;upsize -D {clock_ps};dnsize -D {clock_ps};topo;stime"
DEFAULT_SCRIPTS = {
    "low": "+strash;&get -n;&dc2;&nf -D {clock_ps};&put;" + BUFFER_TAIL,
    "medium": "+strash;&get -n;&dc2;&dch -f;&nf -C 32 -F 8 -p -D {clock_ps};&put;" + BUFFER_TAIL,
    "high": "+strash;&get -n;&dc2;&syn2;&dc2;&dch -f;&nf -C 32 -F 16 -p -D {clock_ps};&put;" + BUFFER_TAIL,
}
MAP_SCRIPTS = {
    "low": "+strash;dc2;map -D {clock_ps};" + BUFFER_TAIL,
    "medium": "+strash;dc2;dch -f;map -D {clock_ps};" + BUFFER_TAIL,
    "high": "+strash;dc2;syn2;dc2;dch -f;map -D {clock_ps};" + BUFFER_TAIL,
}
if os.environ.get("CHIALU_ABC_FLOW", "nf") == "map":
    DEFAULT_SCRIPTS = MAP_SCRIPTS


def abc_script_for(pdk: dict, effort: str, clock_ps: int, seed: int | None = None) -> str:
    """The ABC script of an effort level (low | medium | high) for a PDK
    descriptor: the descriptor's `abc.scripts.<effort>`, else the
    default flow of that level. Every level rewrites the AIG (`&dc2`)
    before the liberty mapper `&nf`; `medium` adds structural choices
    (`&dch -f`) and a higher mapping effort, `high` a second rewriting
    round (`&syn2`) and more area-flow rounds (`&nf` admits at most 32
    priority cuts). Every level then buffers and sizes the mapped netlist
    under the same target (`buffer;upsize -D;dnsize -D`) before `stime`
    reports the delay."""
    if effort not in EFFORTS:
        raise ValueError(f"effort {effort!r}: one of {EFFORTS} (a mapping-only flow is not offered)")
    abc = pdk.get("abc") or {}
    scripts = abc.get("scripts") or {}
    script = scripts.get(effort) or DEFAULT_SCRIPTS[effort]
    script = script.replace("{clock_ps}", str(clock_ps))
    if seed is not None:
        # Resolve the descriptor override first: changing DEFAULT_SCRIPTS alone has no effect on Nangate45.
        script, n = re.subn(r"\bstrash(?=;|\s|$)", f"strash;permute -S {int(seed)}", script, count=1)
        if not n:
            raise ValueError("permuted ABC mapping requires strash in the script")
    return script


# the library's ripple chunk carries `keep_hierarchy` for the simulation-side elaboration and
# correspondence checks (chialu/verify/combinational_sim.py); a synthesis measures the flattened
# structure, so the attribute is dropped before `synth -flatten` (yosys keeps a marked instance
# otherwise, and the stat then lists several modules)
HIERARCHY_RESET = "setattr -mod -unset keep_hierarchy\nsetattr -unset keep_hierarchy\n"


def synth_command(pdk: dict, top: str, share: bool) -> str:
    tmpl = (pdk.get("yosys") or {}).get("synth") or "synth -top {top} -flatten -noabc{noshare}"
    return tmpl.replace("{top}", top).replace("{noshare}", "" if share else " -noshare")


SYNTH_REPORT = os.environ.get("CHIALU_SYNTH_REPORT", "1") != "0"   # the agent's reports beside the metric


@node(cache_id=flow_id, outputs=["ok", "area_um2", "cells", "abc_delay_ps", "seconds", "pdk", "clock_ps", "detail",
               "summary", "critical_path", "paths", "area_by_hierarchy", "report_seconds", "repeats", "seeds", "runs", "statistics", "median_rule",
               "successful_runs", "cells_run_index", "report_run"],
      resources={"eda": EDA_RESOURCE})
def synth_ppa(rtl_text: str, top: str, pdk, clock_ps: int, timeout_s: int = 1200,
              effort: str = "medium", share: bool = False, report: bool | None = None,
              repeats: int = 5, seeds: list | None = None) -> dict:
    """Yosys plus ABC liberty mapping on a PDK descriptor (a name or the
    descriptor dict): area (liberty area units, um^2 for the shipped
    PDKs), the cell count and ABC's delay (ps). `clock_ps` is ABC's &nf
    -D target; a timeout is a failed synthesis; `effort` is low | medium |
    high; `share` keeps yosys's SHARE pass. With CHIALU_SYNTH_REPORT
    (on by default) the result also carries chialu.synthreport's texts
    for the coding agent: `summary` (the units' area and arrival times),
    `critical_path` (one line), `paths` and `area_by_hierarchy`.  `report`
    overrides that switch for one call: a caller that runs in worker
    processes cannot set the environment they import under, and a study
    that wants the per-unit numbers must ask for them rather than rely on
    every worker having inherited the same variable. Area and delay are independent
    medians of all requested runs (default five); any failed run invalidates both.
    The base mapping is unchanged at repeats=1. Cells identify the run nearest
    median area, and attribution describes its own recorded name-kept base mapping.
    CHIALU_SYNTH_JOBS permits concurrent checkpoint mappings and reserves that many
    EDA slots at import time; its default is one core per active mapping."""
    from chialu.synth_records import aggregate, seeds_for
    run_seeds = seeds_for(repeats, seeds)
    from chialu.synthreport import members_of
    members = members_of(rtl_text)
    rtl_text = rtl_of(rtl_text)
    t0 = time.time()
    bad = _external_ref_failure(rtl_text, t0)
    if bad is not None:
        return bad
    with tempfile.TemporaryDirectory() as td:
        rtl, err = frontend_source(rtl_text, td)
        if rtl is None:
            return {"ok": False, "detail": f"{FRONTEND}: {err}", "seconds": round(time.time() - t0, 1)}
        # The base keeps the original in-process netlist and therefore its exact old numbers.
        # Other mappings read its RTLIL checkpoint; the import-time worker knob also
        # sets the node's EDA reservation, including synth_unit's outer module pool.
        pre = Path(td) / "pre.il"
        def one(pair):
            i, seed = pair
            return _synth_mapped(rtl, top, pdk, clock_ps, timeout_s, effort, share, time.time(),
                                 abc_seed=seed, repeat_index=i,
                                 pre_netlist=pre if i and pre.exists() else None,
                                 save_netlist=pre if i == 0 else None)
        runs = [one((0, run_seeds[0]))]
        if SYNTH_WORKERS == 1:
            runs.extend(map(one, enumerate(run_seeds[1:], 1)))
        else:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=SYNTH_WORKERS) as pool:
                runs.extend(pool.map(one, enumerate(run_seeds[1:], 1)))
        out = aggregate(runs, time.time() - t0)
        if not (SYNTH_REPORT if report is None else bool(report)) or not out.get("ok"):
            return out
        # The attribution needs the instance tree, and keeping it changes the netlist and with it
        # the metric, so the reports are measured in a pass of their own and only their texts are
        # carried back -- never their area or delay, which belong to a different netlist.
        t1 = time.time()
        rep = _synth_mapped(rtl, top, pdk, clock_ps, timeout_s, effort, share, t1,
                            report=True, members=members, hierarchy=True,
                            flow={k: out.get(k) for k in ("area_um2", "cells", "abc_delay_ps", "repeats", "cells_run_index")})
        # Attribution is a separate, hierarchy-preserving base mapping, never the median netlist.
        out["report_run"] = rep
        for k in ("summary", "critical_path", "paths", "area_by_hierarchy"):
            if k in rep:
                out[k] = rep[k]
        if not rep.get("ok"):
            out["summary"] = f"synthesis report unavailable: {str(rep.get('detail'))[:300]}"
        out["report_seconds"] = round(time.time() - t1, 1)
        out["seconds"] = round(time.time() - t0, 3)
        return out


def _synth_mapped(rtl, top: str, pdk, clock_ps: int, timeout_s: int, effort: str, share: bool,
                  t0: float, report: bool = False, members: dict | None = None,
                  hierarchy: bool = False, flow: dict | None = None, abc_seed: int | None = None,
                  repeat_index: int = 0, pre_netlist=None, save_netlist=None,
                  abc_script_override: str | None = None, keep_scopeinfo: bool = False) -> dict:
    """The yosys and ABC run of `synth_ppa` on an already converted
    Verilog file `rtl`; with `report`, the agent's reports of
    chialu.synthreport, which need `hierarchy` for the instance tree
    they attribute to. `flow` is the metric they state beside their own
    numbers, measured by the pass that did not keep the hierarchy."""
    pdk = _pdk(pdk)
    libs = liberty_files(pdk)
    clock = int(clock_ps)
    abc_script = abc_script_override or abc_script_for(pdk, effort, clock, abc_seed)
    synth_cmd = synth_command(pdk, top, share)
    lib_args = " ".join(f"-liberty {lb}" for lb in libs)
    with tempfile.TemporaryDirectory() as td:
        ys = Path(td) / "synth.ys"
        abc_file = Path(td) / "abc.script"
        abc_file.write_text(abc_commands(abc_script))
        before = after = ""
        if report:
            from chialu.synthreport import LISTINGS_AFTER_SYNTH, LISTINGS_BEFORE_SYNTH
            before, after = LISTINGS_BEFORE_SYNTH, LISTINGS_AFTER_SYNTH
        # yosys 0.68's flatten leaves one $scopeinfo cell per inlined instance, which stat counts as a cell of
        # unknown area; they go before the count
        pre = Path(save_netlist) if save_netlist else Path(td) / "pre.il"
        prefix = (f"read_rtlil {pre_netlist}\n" if pre_netlist else
                  frontend_read(rtl, top, hierarchy=hierarchy)
                  + f"hierarchy -top {top}\n{HIERARCHY_RESET}{before}{synth_cmd}\n{after}")
        cleanup = "" if keep_scopeinfo else "delete t:$scopeinfo\n"
        ys.write_text(prefix + f"write_rtlil {pre}\n"
                      f"abc {lib_args} -script {abc_file}\nopt_clean\n{cleanup}stat {lib_args}\n")
        logp = Path(td) / "yosys.log"
        status, stderr = "ok", ""
        try:
            r = subprocess.run(["yosys", "-q", "-l", str(logp), str(ys)], cwd=td,
                               capture_output=True, text=True, timeout=timeout_s,
                               preexec_fn=_die_with_parent)
            stderr = r.stderr
            if r.returncode:
                status = "fail"
        except subprocess.TimeoutExpired:
            status = "timeout"
            stderr = f"synthesis timeout after {timeout_s}s; PPA not measured"
        except OSError as e:
            status, stderr = "fail", str(e)
        log = logp.read_text() if logp.exists() else ""
        out = _mapped_numbers(log, pdk, clock, t0) if status == "ok" else {
            "ok": False, "area_um2": None, "abc_delay_ps": None, "cells": None,
            "detail": (stderr or log)[-4000:], "seconds": round(time.time() - t0, 3)}
        if not out.get("ok") or out.get("abc_delay_ps") is None:
            status = "fail" if status == "ok" else status
            out["ok"] = False
        from chialu.synth_records import put, tools_identity
        from chialu.synthdb import liberty_hash, tool_hash
        out.update({"status": status, "repeat_index": repeat_index, "abc_seed": abc_seed,
                    "abc_script": abc_script, "abc_script_text": abc_commands(abc_script),
                    "rtl": put(Path(rtl).read_bytes()), "netlist": put(pre.read_bytes()) if pre.exists() else None,
                    "mapping_input": "rtlil" if pre_netlist else "rtl", "liberties": [put(Path(lb).read_bytes()) for lb in libs],
                    "liberty_hash": liberty_hash(pdk), "tool_hash": tool_hash(pdk), "tools": tools_identity(),
                    "effort": effort, "clock_ps": clock, "share": share, "top": top, "hierarchy": hierarchy,
                    "keep_scopeinfo": keep_scopeinfo,
                    "timeout_s": timeout_s, "pdk": pdk.get("name"), "pdk_descriptor": pdk,
                    "log": put(log), "stderr": put(stderr), "yosys_script": put(ys.read_text())})
        if report and out.get("ok") and libs:
            from chialu import synthreport
            t1 = time.time()
            try:
                rep = synthreport.report(Path(td), top, libs[0], abc_file, members,
                                         flow=flow or {k: out.get(k) for k in ("area_um2", "cells", "abc_delay_ps")},
                                         timeout_s=max(60, int(timeout_s) // 2), clock_ps=clock)
            except Exception as e:  # noqa: BLE001
                rep = {"error": f"{type(e).__name__}: {str(e)[:300]}",
                       "status": "timeout" if isinstance(e, subprocess.TimeoutExpired) else "fail"}
            # The name-kept mapping is the source of the report's physical numbers,
            # so retain its input and log as well as the preparatory hierarchy pass.
            report_input = Path(td) / "report_input.il"
            report_log = Path(td) / "report_keep.log"
            log_text = report_log.read_text() if report_log.exists() else ""
            report_numbers = _mapped_numbers(log_text, pdk, clock, t1)
            out["attribution_run"] = {
                **out, **report_numbers, "purpose": "diagnostic_name_kept_base_mapping",
                "status": rep.get("status", "fail" if "error" in rep else "ok"), "ok": "error" not in rep,
                "detail": rep.get("error", ""), "mapping_input": "rtlil",
                "keep_scopeinfo": True,
                "netlist": put(report_input.read_bytes()) if report_input.exists() else None,
                "log": put(log_text), "timeout_s": max(60, int(timeout_s) // 2),
                "yosys_script": put((Path(td) / "report_keep.ys").read_text())
                if (Path(td) / "report_keep.ys").exists() else None}
            if "error" in rep:
                out["summary"] = f"synthesis report unavailable: {rep['error']}"
            else:
                out.update({k: rep[k] for k in ("summary", "critical_path", "paths", "area_by_hierarchy")})
            out["report_seconds"] = round(time.time() - t1, 1)
        return out


def _mapped_numbers(log: str, pdk: dict, clock: int, t0: float) -> dict:
    """area, cells and ABC's delay from a mapped synthesis log."""
    area = cells = delay = None
    m = re.search(r"Chip area for top module.*?:\s*([\d.]+)", log) \
        or re.search(r"Chip area for module.*?:\s*([\d.]+)", log)
    if m:
        area = float(m.group(1))
    if len(re.findall(r"Chip area for module", log)) > 1:
        return {"ok": False, "detail": "synthesis left a module hierarchy (flatten failed)",
                "seconds": round(time.time() - t0, 1)}
    m = _cells(log)
    if m:
        cells = int(m.group(1))
    dm = re.findall(r"Delay\s*=\s*([\d.]+)\s*ps", log)
    if dm:
        delay = float(dm[-1])
    note = ""
    if area is None and "\n=== " in log:
        # a module of wiring alone (a unit whose structure another unit realizes: the fp16 unpacker under a
        # shared_across_formats family) maps to no cell, and the mapped stat block (the last `=== top ===`)
        # prints neither a cells line nor an area line for it
        tail = log[log.rfind("\n=== "):]
        types = [t for t in re.findall(r"^\s*\d+\s+(\S+)\s*$", tail, re.M) if t not in ("cells", "wires", "ports")]
        if "Chip area" not in tail and (not re.search(r"\bcells\b", tail) or all(t == "$scopeinfo" for t in types)):
            area, cells, note = 0.0, 0, "no cells: the module is wiring alone"
            delay = delay if delay is not None else 0.0
    return {"ok": area is not None, "area_um2": area, "cells": cells, "abc_delay_ps": delay,
            "seconds": round(time.time() - t0, 1), "pdk": pdk.get("name"), "clock_ps": clock,
            "detail": note if area is not None else "no area in the yosys log"}


@node(cache_id=tool_flow_id, outputs=["ok", "cells", "seconds", "detail"], resources={"eda": 0.2})
def yosys_stat(rtl_text: str, top: str, timeout_s: int = 600) -> dict:
    """Gate count without liberty mapping (techmap to yosys's gate
    library): a seconds-long screen. The count is at the gate level so a
    behavioral `*` (one $mul cell before techmap) and a library
    multiplier (its cells) compare."""
    rtl_text = rtl_of(rtl_text)
    t0 = time.time()
    bad = _external_ref_failure(rtl_text, t0)
    if bad is not None:
        return {**bad, "cells": None}
    with tempfile.TemporaryDirectory() as td:
        rtl, err = frontend_source(rtl_text, td)
        if rtl is None:
            return {"ok": False, "detail": f"{FRONTEND}: {err}", "seconds": round(time.time() - t0, 1)}
        ys = Path(td) / "stat.ys"
        ys.write_text(frontend_read(rtl, top)
                      + f"hierarchy -top {top}\n{HIERARCHY_RESET}proc\nflatten\nopt -fast\ntechmap\nopt -fast\nstat\n")
        try:
            r = subprocess.run(["yosys", "-q", "-l", str(Path(td) / "y.log"), str(ys)],
                               capture_output=True, text=True, timeout=timeout_s,
                               preexec_fn=_die_with_parent)
        except subprocess.TimeoutExpired:
            return {"ok": False, "detail": "stat timeout", "seconds": round(time.time() - t0, 1)}
        log = (Path(td) / "y.log").read_text() if (Path(td) / "y.log").exists() else ""
    m = _cells(log)
    return {"ok": r.returncode == 0 and m is not None,
            "cells": int(m.group(1)) if m else None,
            "detail": "" if r.returncode == 0 else (r.stderr or log)[-2000:],
            "seconds": round(time.time() - t0, 1)}


UNIT_WORKERS = 4        # structures mapped at once by synth_unit
# the per-module results of synth_unit, keyed by the module's text and the text it
# depends on (the program with the other unit modules blanked), the PDK, the effort
# and the clock: a candidate that rewrites one unit maps that unit alone
SYNTH_CACHE_DIR = Path(os.environ.get("CHIALU_SYNTH_CACHE") or (Path.home() / ".cache" / "chialu" / "synth_unit"))
_MODULE_RE = re.compile(r"^module\s+([A-Za-z_]\w*)\b.*?^endmodule\b", re.M | re.S)


def _unit_context(text: str, module: str, units) -> str:
    """The program text without the other unit modules' bodies: what the
    mapping of `module` can depend on."""
    out, last = [], 0
    for m in _MODULE_RE.finditer(text):
        if m.group(1) in units and m.group(1) != module:
            out.append(text[last:m.start()])
            last = m.end()
    out.append(text[last:])
    return "".join(out)


def _unit_key(text: str, module: str, units, pdk: dict, effort: str, clock_ps: int, repeats: int = 5) -> str:
    h = hashlib.sha256()
    h.update(_unit_context(text, module, units).encode())
    h.update(f"|{module}|{pdk.get('name')}|{effort}|{int(clock_ps)}|".encode())
    h.update(flow_id({"pdk": pdk, "effort": effort, "repeats": repeats}).encode())
    return h.hexdigest()


@node(cache_id=flow_id, outputs=["ok", "area_um2", "attribution", "seconds", "detail"],
      resources={"eda": float(UNIT_WORKERS * SYNTH_WORKERS)})
def synth_unit(rtl_text: str, structures: list, pdk, clock_ps: int, effort: str = "medium",
               timeout_s: int = 600, repeats: int = 5) -> dict:
    """ABC map of every declared structure alone: the STRUCTURE entries
    name the module (`sv=`) realizing each; area is summed and the
    per-structure table is the attribution."""
    rtl_text = rtl_of(rtl_text)
    from concurrent.futures import ThreadPoolExecutor
    t0 = time.time()
    # before the per-module cache as well as the mapping: no result, cached or fresh, for such a text
    bad = _external_ref_failure(rtl_text, t0)
    if bad is not None:
        return {**bad, "area_um2": None, "attribution": {}}
    attribution = {}
    total = 0.0
    done = {}
    order = []          # (structure id, module) in declaration order; one run per module
    for e in structures or []:
        sid = e["_"][0] if isinstance(e.get("_"), list) else str(e.get("id", "?"))
        module = e.get("sv")          # a structure without a module of its own is inline in the top
        if module:
            order.append((sid, module))
    modules = list(dict.fromkeys(m for _, m in order))
    pdk = _pdk(pdk)
    keys = {m: _unit_key(rtl_text, m, set(modules), pdk, effort, clock_ps, repeats) for m in modules}
    results = {}
    try:
        SYNTH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        for m in modules:
            f = SYNTH_CACHE_DIR / f"{keys[m]}.json"
            if f.is_file():
                results[m] = json.loads(f.read_text())
    except OSError:
        pass
    todo = [m for m in modules if m not in results]
    with tempfile.TemporaryDirectory() as td:
        rtl, err = frontend_source(rtl_text, td) if todo else (None, "")
        if todo and rtl is None:
            return {"ok": False, "area_um2": None, "attribution": {},
                    "detail": f"{FRONTEND}: {err}", "seconds": round(time.time() - t0, 1)}

        def one(module):
            try:
                from adir.registry import underlying
                r = underlying(synth_ppa)(rtl_text, module, pdk, clock_ps, timeout_s=timeout_s,
                                           effort=effort, report=False, repeats=repeats)
            except Exception as ex:  # noqa: BLE001
                r = {"ok": False, "detail": f"{type(ex).__name__}: {ex}"}
            return module, r
        with ThreadPoolExecutor(max_workers=UNIT_WORKERS) as pool:
            for module, r in pool.map(one, todo):
                results[module] = r
                if r.get("ok"):
                    try:
                        (SYNTH_CACHE_DIR / f"{keys[module]}.json").write_text(json.dumps(r))
                    except OSError:
                        pass
    for module in modules:
        r = results[module]
        from chialu.synth_records import trace
        entry = {**trace(r), "module": module, "area_um2": r.get("area_um2"), "abc_delay_ps": r.get("abc_delay_ps"),
                 "cells": r.get("cells"), "ok": r.get("ok", False)}
        if not r.get("ok"):
            entry["detail"] = r.get("detail", "")
        done[module] = entry
        if r.get("ok") and r.get("area_um2") is not None:
            total += float(r["area_um2"])
    for sid, module in order:
        shared = [k for k, v in attribution.items() if v.get("module") == module]
        attribution[sid] = {**done[module], **({"shared_with": shared} if shared else {})}
    ok = bool(done) and all(v["ok"] for v in done.values())
    return {"ok": ok, "area_um2": total if done else None, "attribution": attribution,
            "seconds": round(time.time() - t0, 1),
            "detail": "" if ok else "; ".join(f"{k}: {v.get('detail', 'failed')}" for k, v in done.items()
                                              if not v["ok"])}
