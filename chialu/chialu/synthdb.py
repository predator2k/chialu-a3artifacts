"""The synthesis database of the family library: one row per measured
design point of a family at a geometry under a flow, on any PDK the
user builds.

    python3 -m chialu.synthdb build  --pdk nangate45 [--kinds adder,shifter] [--families ...]
                                     [--widths 8,16,32] [--effort medium] [--jobs 8] [--host host@ip]
    python3 -m chialu.synthdb status  [--pdk nangate45]
    python3 -m chialu.synthdb query   --kind adder --width 24 [--family ...] [--fastest|--smallest]
    python3 -m chialu.synthdb verify  [--pdk nangate45] [--sample 20]
    python3 -m chialu.synthdb merge   <other database directory>

A row has five parts, and its key is the first three:

* `point`: the complete binding of one structure: `kind`, `family`,
  `choices` (every design choice of the family, the defaults written
  out, plus the pins a curated variant adds beyond the space), and
  `slots` ({slot: {family, choices, slots}} recursively, so the row says
  which significand adder, which alignment shifter and which
  leading-zero path an fp adder was measured with); `point_id` is the
  hash of the canonical point.
* `geometry`: `width`, and per kind what the realizer derives from it
  (the float format of an fp kind, the function and format of an SFU
  point, the signedness of a multiplier, the digits of a decimal kind).
* `flow`: `pdk`, `liberty_hash`, `effort`, `clock_ps` (ABC's target for
  the mapping), `tool_hash`.
* `result`: `status` (ok | fail | skip), `area_um2`, `cells`,
  `delay_ps` (the module's critical path after mapping at `clock_ps`;
  the loop's own synthesis re-measures a structure in context),
  `seconds`, `detail`.
* `provenance`: `gen_hash` (the generated text), `module`, `date`,
  `tags` (`base`, or `moved:<pin>` for the pins the build's sampling
  moved off the family's baseline: a note, not identity) and `label`.

The build's sampling is the baseline (every slot at its space's first
family, every choice at its default) plus one point per value of each
choice and per alternative family of each slot; the row records the
whole point, so a model over the rows needs no knowledge of that
policy, and a point measured elsewhere (a full product, a seed's
`synth_unit` attribution) fits the same table. The generators consume
a flat pin dictionary (`point_pins`), and readers get a flat view of a
row (`flat`) with the point, geometry, flow and result fields beside
the nested parts.

The files are `chialu/synth/<pdk>/<kind>.jsonl`, split into
`<kind>/<family>.jsonl` once a file would pass 10 MB, with a
`manifest.json` per PDK (the schema, the descriptor and liberty hashes,
the row counts, the generator hashes). Plain text keeps every file
diffable and the repository off Git LFS.

`build` is incremental: a row whose generated text still hashes the
same under the same tools is kept, a changed one is re-synthesized,
and the build is resumable (every row is appended as it lands).
`--host` runs the same build on an EDA host over ssh and fetches the
files back.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import date
from pathlib import Path

from chialu.synth_records import trace, seeds_for
from chialu.characterize import FP_DB_KINDS          # the kinds whose point names its float format
from chialu.targets.rtl import families as FAM

DB_DIR = Path(__file__).resolve().parent / "synth"
SHARD_BYTES = 10 * 1024 * 1024        # a file over this splits per family (GitHub warns at 50 MB)

# the width grid: the powers of two the seeds build on and the points between them
DENSE_WIDTHS = (4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512)
DEFAULT_WIDTHS = (8, 16, 24, 32, 48, 64)

# how a kind's delay grows with the width, for the interpolation of a width the database lacks
WIDTH_LAW = {
    "adder": "log", "incrementer": "log", "comparator": "log", "lzc": "log", "bitcount": "log",
    "shifter": "log", "logic": "flat", "multiplier": "log", "divider": "linear",
    "fp_adder": "log", "fp_multiplier": "log", "fp_comparator": "log", "fp_divider": "linear",
    "fp_sqrt": "linear", "rounder": "log", "unpacker": "log", "posit_unit": "log",
    "sd_adder": "flat", "rns_adder": "log", "rns_multiplier": "log", "rns_comparator": "log",
    "bcd_adder": "log", "bcd_multiplier": "log", "bcd_divider": "linear", "sfu": "log", "dot": "log",
    "checker": "log",
}
# the families whose delay is linear in the width whatever their kind's law
LINEAR_FAMILIES = {"ripple_carry", "manchester_carry_chain", "carry_save_array", "restoring_nonrestoring",
                   "srt_radix2", "online_msdf", "digit_recurrence_sqrt_combined", "linear_chain"}


def _canon(d: dict) -> str:
    """A pin or parameter dictionary as a canonical string (the key)."""
    return json.dumps({str(k): (v if isinstance(v, (int, float, bool, str)) else str(v))
                       for k, v in sorted((d or {}).items())}, sort_keys=True, separators=(",", ":"))


def _hash(text: str) -> str:
    return hashlib.blake2b(text.encode(), digest_size=8).hexdigest()


SCHEMA = 2


def _cjson(d) -> str:
    return json.dumps(d, sort_keys=True, separators=(",", ":"), default=str)


def point_id(point: dict) -> str:
    """The hash of a point without its id: two rows of one binding share it."""
    return _hash(_cjson({k: v for k, v in point.items() if k != "point_id"}))


def row_key(r: dict) -> tuple:
    """(flow, geometry, point id): what identifies a measurement."""
    return (_cjson(r.get("flow") or {}), _cjson(r.get("geometry") or {}), r["point"]["point_id"])


def _default(dom):
    """The default member of a domain: its own `default`, else the first member."""
    try:
        v = dom.default()
        if v is not None:
            return v
    except Exception:  # noqa: BLE001
        pass
    try:
        members = dom.members()
        return members[0] if members else None
    except Exception:  # noqa: BLE001
        return None


def point_of(kind: str, family: str, pins: dict | None) -> dict:
    """The complete nested point of a family under flat generator pins:
    every design choice (the pin's value, else the domain's default),
    the pins the space does not declare (a curated variant's) beside
    them, and every slot the family opens with the family bound there
    and that family's own choices and slots. Underscore pins are the
    geometry's (`geometry_of`) and stay out."""
    pins = {str(k): v for k, v in (pins or {}).items() if not str(k).startswith("_")}
    fam = next((f for f in families_of(kind) if f.name == family), None)

    def node(f, prefix: str, depth: int) -> dict:
        choices: dict = {}
        for c, dom in ((f.design_choices or {}) if f is not None else {}).items():
            choices[c] = pins.get(prefix + c, _default(dom))
        slots: dict = {}
        comps = (f.components or {}) if f is not None else {}
        for slot, sub in comps.items():
            members = [g.name for g in sub.families]
            if not members:
                continue
            pick = pins.get(f"{prefix}{slot}.family")
            if pick not in members:
                pick = members[0]
            child = _family(sub, pick)
            slots[slot] = {"family": pick, **node(child, f"{prefix}{slot}.", depth + 1)} if depth < SLOT_DEPTH \
                else {"family": pick, "choices": {}, "slots": {}}
        # a pin the space does not declare at this level (a curated variant's) is a choice too; a slot's
        # `family` is the slot node's own field
        for k, v in pins.items():
            if not k.startswith(prefix):
                continue
            rest = k[len(prefix):]
            head = rest.split(".", 1)[0]
            if rest == "family":
                continue
            if "." not in rest and rest not in choices:
                choices[rest] = v
            elif "." in rest and head not in slots and head not in comps:
                choices.setdefault(rest, v)
        return {"choices": choices, "slots": slots}

    point = {"kind": kind, "family": family, **node(fam, "", 0)}
    point["point_id"] = point_id(point)
    return point


def point_pins(point: dict) -> dict:
    """The flat pins the generators take, from a nested point."""
    out: dict = {}

    def walk(n: dict, prefix: str):
        for c, v in (n.get("choices") or {}).items():
            out[prefix + c] = v
        for slot, sub in (n.get("slots") or {}).items():
            out[f"{prefix}{slot}.family"] = sub.get("family")
            walk(sub, f"{prefix}{slot}.")

    walk(point, "")
    return out


def geometry_of(kind: str, width: int, pins: dict | None = None) -> dict:
    """What the realizer builds a point at beyond its binding: the width,
    and per kind the format, function or signedness the width and the
    condition pins name (`characterize.realize`)."""
    pins = pins or {}
    g: dict = {"width": int(width)}
    if kind == "sfu":
        g["function"] = pins.get("_fn")
        g["format"] = pins.get("_fmt")
    elif kind == "multiplier":
        g["signed"] = bool(pins.get("_signed", True))
    elif kind in FP_DB_KINDS:
        # the point names its format (`_fmt`) and, where a datapath shared among formats computes on a
        # wider layout than the format's own, that geometry (`_geom`): fp16 and bf16 are both 16 bits
        try:
            from chialu import characterize as CH
            fmt, geom, _e = CH.fp_geom(int(width), pins.get("_fmt"), pins.get("_geom"))
            g["format"] = fmt.name
            g["exp_bits"] = getattr(fmt, "exp_bits", None)
            g["man_bits"] = getattr(fmt, "man_bits", None)
            if pins.get("_geom"):
                g["geom"] = geom.tag()
        except Exception:  # noqa: BLE001 - a width the realizer has no format for stays a width
            pass
    elif kind == "posit_unit":
        try:
            from chialu import characterize as CH
            pg = CH.posit_geom(int(width))
            if pg is not None:
                g["format"] = pg[0].name
        except Exception:  # noqa: BLE001
            pass
    elif kind in ("bcd_adder", "bcd_multiplier", "bcd_divider"):
        g["digits"] = int(width) // 4
    return g


def condition_pins(kind: str, geometry: dict) -> dict:
    """The underscore pins a generator reads for a geometry (the reverse of geometry_of)."""
    if kind == "sfu":
        return {"_fn": geometry.get("function"), "_fmt": geometry.get("format")}
    if kind == "multiplier" and "signed" in geometry:
        return {"_signed": bool(geometry["signed"])}
    if kind in FP_DB_KINDS and geometry.get("format"):
        out = {"_fmt": geometry["format"]}
        if geometry.get("geom"):
            out["_geom"] = geometry["geom"]
        return out
    return {}


def tags_of(label: str) -> list:
    """The sampling note of a point's label: `base`, or `moved:<pin>` per moved pin."""
    lab = label.split(":", 1)[1] if ":" in label else label
    if not lab or lab == "base":
        return ["base"]
    return ["moved:" + part.split("=", 1)[0] for part in lab.split(",") if part]


def make_row(pdk_name: str, effort: str, clock_ps: int, lib_hash: str, kind: str, family: str, pins: dict,
             width: int, label: str, module: str, gen_hash: str, result: dict, repeats: int = 5) -> dict:
    """One row of the schema from a build's point and its measurement."""
    return {"point": point_of(kind, family, pins),
            "geometry": geometry_of(kind, width, pins),
            "flow": {"pdk": pdk_name, "liberty_hash": lib_hash, "effort": effort, "clock_ps": int(clock_ps),
                     "tool_hash": tool_hash(pdk_name), "repeats": repeats, "seeds": seeds_for(repeats)},
            "result": {**trace(result), "status": result.get("status", "fail"), "area_um2": result.get("area_um2"),
                       "cells": result.get("cells"), "delay_ps": result.get("delay_ps"),
                       "seconds": result.get("seconds"), "detail": result.get("detail", "")},
            "provenance": {"gen_hash": gen_hash, "module": module, "date": date.today().isoformat(),
                           "tags": tags_of(label), "label": label}}


def flat(r: dict) -> dict:
    """A row as one flat read view: the point's kind and family, the
    generator pins (the point's plus the geometry's condition pins), the
    width and the other geometry fields, the flow, the result and the
    provenance fields at the top level, and the nested parts beside
    them. Readers sort and filter on this; the stored row is the nested
    one."""
    pt, geo, flow, res, prov = (r.get(k) or {} for k in ("point", "geometry", "flow", "result", "provenance"))
    kind = pt.get("kind")
    pins = dict(point_pins(pt))
    pins.update(condition_pins(kind, geo))
    v = {"kind": kind, "family": pt.get("family"), "point_id": pt.get("point_id"), "pins": pins,
         "width": geo.get("width"), **{k: v_ for k, v_ in geo.items() if k != "width"},
         "pdk": flow.get("pdk"), "effort": flow.get("effort", "medium"), "clock_ps": flow.get("clock_ps"),
         "lib_hash": flow.get("liberty_hash"), "tool_hash": flow.get("tool_hash"),
         "status": res.get("status", "ok"), "area_um2": res.get("area_um2"), "cells": res.get("cells"),
         "delay_ps": res.get("delay_ps"), "seconds": res.get("seconds"), "detail": res.get("detail", ""),
         "gen_hash": prov.get("gen_hash"), "module": prov.get("module"), "date": prov.get("date"),
         "tags": list(prov.get("tags") or []), "variant": prov.get("label", ""),
         "point": pt, "geometry": geo, "flow": flow, "result": res, "provenance": prov}
    if "graph" in r:
        v["graph"] = r["graph"]
    return v


# ---- the PDK descriptor ---------------------------------------------------------------------
def pdk_descriptor(spec: str, liberty: str | None = None, name: str | None = None) -> dict:
    """The descriptor of a build: a name or alias under pdk/, a descriptor
    file anywhere, or liberty files with a name (the shipped ABC scripts
    and yosys command apply)."""
    if liberty:
        libs = [{"path": p.strip()} for p in liberty.split(",") if p.strip()]
        return {"name": name or "custom", "liberty": libs, "area_unit": "um2"}
    p = Path(spec)
    if p.is_file():
        import yaml
        d = yaml.safe_load(p.read_text()) or {}
        d.setdefault("name", p.stem)
        return d
    import pdk as pdk_pkg
    return pdk_pkg.resolve(spec)


_LIB_FILE_HASH: dict = {}


def _file_hash(path: Path) -> str:
    """A hash of a whole file, cached on its path, size and mtime. An edit
    past the first kilobyte changes the hash, which a prefix hash misses,
    and the cache keeps a 40 MB liberty from being read once per row."""
    st = path.stat()
    key = (str(path), st.st_size, int(st.st_mtime))
    got = _LIB_FILE_HASH.get(key)
    if got is None:
        h = hashlib.blake2b(digest_size=16)
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        got = _LIB_FILE_HASH[key] = h.hexdigest()
    return got


def liberty_hash(pdk: dict) -> str:
    """A hash of the liberty files the descriptor names, over each file's
    whole content."""
    from chialu import eda
    h = hashlib.blake2b(digest_size=8)
    try:
        for f in eda.liberty_files(pdk):
            p = Path(f)
            h.update(p.name.encode())
            h.update(_file_hash(p).encode())
    except Exception:                                   # noqa: BLE001 - a missing liberty is reported by the build
        h.update(b"missing")
    return h.hexdigest()


def tool_versions(pdk=None) -> str:
    """The version line of the tools a measurement passes through, which
    is the mapper and the SystemVerilog converter. A row measured under
    other versions is not comparable with one measured here, and the
    liberty hash does not say so. The ABC script joins the line, since a
    row mapped under `&nf` is not comparable with one mapped under
    `map -D`, and the script is read from the PDK descriptor, which is
    where the script the flow runs lives; `chialu.eda.DEFAULT_SCRIPTS` is
    the fallback for a descriptor that names none."""
    import subprocess
    out = []
    for cmd in (["yosys", "-V"], ["verilator", "--version"]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            out.append(f"{cmd[0]} {(r.stdout or r.stderr).strip().splitlines()[0][:60]}")
        except Exception:                               # noqa: BLE001 - a missing tool is reported by the build
            out.append(f"{cmd[0]} absent")
    from chialu.eda import DEFAULT_SCRIPTS, FRONTEND
    out.append("frontend " + FRONTEND)   # the frontend decides the RTLIL one text becomes
    script = ""
    if pdk is not None:
        try:
            from chialu.eda import _pdk
            script = ((_pdk(pdk).get("abc") or {}).get("scripts") or {}).get("medium", "")
        except Exception:                               # noqa: BLE001 - an unreadable descriptor falls back
            script = ""
    out.append("abc " + (script or DEFAULT_SCRIPTS["medium"]))
    return " | ".join(out)


def tool_hash(pdk=None) -> str:
    key = "" if pdk is None else str(pdk if isinstance(pdk, str) else (pdk or {}).get("name", pdk))
    got = _TOOLS.get(key)
    if got is None:
        got = _TOOLS[key] = _hash(tool_versions(pdk))
    return got


_TOOLS: dict = {}


# ---- the database files ---------------------------------------------------------------------
def db_dir(pdk_name: str) -> Path:
    """`CHIALU_SYNTH_DIR` puts the database elsewhere (a rebuild written beside the one in use)."""
    root = os.environ.get("CHIALU_SYNTH_DIR")
    return (Path(root) if root else DB_DIR) / pdk_name


def shard_path(pdk_name: str, kind: str, family: str) -> Path:
    """The file a row belongs in: the kind's file, or the family's file
    under the kind's directory once the kind's file passed the cap."""
    d = db_dir(pdk_name)
    flat = d / f"{kind}.jsonl"
    split = d / kind
    if split.is_dir():
        return split / f"{family}.jsonl"
    if flat.exists() and flat.stat().st_size > SHARD_BYTES:
        return flat            # the caller splits it (see `_split`)
    return flat


def _split(pdk_name: str, kind: str) -> None:
    """The kind's file split into one file per family (called when it
    passes the cap)."""
    d = db_dir(pdk_name)
    flat_f = d / f"{kind}.jsonl"
    if not flat_f.exists():
        return
    rows = [json.loads(l) for l in flat_f.read_text().splitlines() if l.strip()]
    out = d / kind
    out.mkdir(parents=True, exist_ok=True)
    by: dict = {}
    for r in rows:
        by.setdefault(r["point"]["family"], []).append(r)
    for fam, rs in by.items():
        (out / f"{fam}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rs))
    flat_f.unlink()


def load(pdk_name: str, kinds=None) -> list:
    """Every row of a PDK's database (both layouts), the newest row per
    key. A row of the earlier flat schema (no `point`) is not read."""
    d = db_dir(pdk_name)
    out: dict = {}
    files = []
    if d.is_dir():
        files += sorted(d.glob("*.jsonl"))
        files += sorted(d.glob("*/*.jsonl"))
    for f in files:
        kind = f.stem if f.parent == d else f.parent.name
        if kinds and kind not in kinds:
            continue
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(r.get("point"), dict):
                continue
            if kinds and r["point"].get("kind") not in kinds:
                continue
            k = row_key(r)
            prev = out.get(k)
            if prev is None or str((r.get("provenance") or {}).get("date", "")) >= str((prev.get("provenance") or {}).get("date", "")):
                out[k] = r
    return list(out.values())


def write_rows(pdk_name: str, rows: list) -> None:
    """Append rows to their shards (splitting a kind's file that passes the cap)."""
    d = db_dir(pdk_name)
    d.mkdir(parents=True, exist_ok=True)
    for r in rows:
        kind, fam = r["point"]["kind"], r["point"]["family"]
        p = shard_path(pdk_name, kind, fam)
        if p.name == f"{kind}.jsonl" and p.exists() and p.stat().st_size > SHARD_BYTES:
            _split(pdk_name, kind)
            p = shard_path(pdk_name, kind, fam)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as fh:
            fh.write(json.dumps(r) + "\n")


def compact(pdk_name: str) -> int:
    """Every shard rewritten with one row per key (the newest), sorted;
    returns the row count."""
    rows = load(pdk_name)
    d = db_dir(pdk_name)
    if d.is_dir():
        for f in list(d.glob("*.jsonl")) + list(d.glob("*/*.jsonl")):
            f.unlink()
    by: dict = {}
    for r in rows:
        by.setdefault(r["point"]["kind"], []).append(r)
    d.mkdir(parents=True, exist_ok=True)
    for kind, rs in by.items():
        rs.sort(key=lambda r: (r["point"]["family"], _cjson(r.get("geometry")), r["point"]["point_id"]))
        text = "".join(json.dumps(r) + "\n" for r in rs)
        if len(text.encode()) > SHARD_BYTES:
            sub = d / kind
            sub.mkdir(parents=True, exist_ok=True)
            byf: dict = {}
            for r in rs:
                byf.setdefault(r["point"]["family"], []).append(r)
            for fam, frs in byf.items():
                (sub / f"{fam}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in frs))
        else:
            (d / f"{kind}.jsonl").write_text(text)
    return len(rows)


def missing_slots(row: dict) -> list:
    """The slots the row's family opens that the row's point does not
    bind (none for a row the build wrote, since `point_of` binds every
    slot; a row from elsewhere may leave one open)."""
    pt = row["point"]
    pins = point_pins(pt)
    _full, slots = structure(pt.get("kind", ""), pt.get("family", ""), pins)
    return [s_ for s_ in slots if f"{s_}.family" not in pins]


def prune(pdk_name: str, apply: bool = False) -> int:
    """Drop every row whose structure is not fully bound. Returns the
    number dropped; `apply` false only reports."""
    rows = load(pdk_name)
    keep, drop = [], []
    for r in rows:
        (drop if missing_slots(r) else keep).append(r)
    by: dict = {}
    for r in drop:
        by[r["point"]["kind"]] = by.get(r["point"]["kind"], 0) + 1
    for kind, n in sorted(by.items(), key=lambda kv: -kv[1]):
        print(f"  {kind:16s} {n}")
    print(f"[synthdb] {len(drop)} of {len(rows)} rows leave a slot unbound, {len(keep)} stay")
    if apply:
        d = db_dir(pdk_name)
        if d.is_dir():
            for f in list(d.glob("*.jsonl")) + list(d.glob("*/*.jsonl")):
                f.unlink()
        write_rows(pdk_name, keep)
        compact(pdk_name)
    return len(drop)


def write_manifest(pdk_name: str, pdk: dict, rows: list) -> None:
    d = db_dir(pdk_name)
    d.mkdir(parents=True, exist_ok=True)
    counts: dict = {}
    for r in rows:
        counts[r["point"]["kind"]] = counts.get(r["point"]["kind"], 0) + 1
    files = {}
    for f in sorted(list(d.glob("*.jsonl")) + list(d.glob("*/*.jsonl"))):
        files[str(f.relative_to(d))] = f.stat().st_size
    man = {"schema": SCHEMA, "row_key": ["flow", "geometry", "point.point_id"],
           "pdk": pdk_name, "descriptor_hash": _hash(_canon({k: str(v) for k, v in pdk.items()})),
           "liberty_hash": liberty_hash(pdk), "tool_hash": tool_hash(pdk), "tools": tool_versions(pdk),
           "rows": len(rows), "rows_per_kind": counts,
           "files": files, "date": date.today().isoformat(),
           "generators": generator_hashes()}
    (d / "manifest.json").write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")


def generator_hashes() -> dict:
    """A content hash per generator module, so a stale row is visible."""
    out = {}
    base = Path(__file__).resolve().parent / "targets" / "rtl" / "families"
    for f in sorted(base.glob("*.py")) + sorted(base.glob("*.sv")):
        out[f.name] = _hash(f.read_text())
    return out


# ---- the characterization points -------------------------------------------------------------
_ROOTS: dict = {}                # COV.roots() costs about 9 s, and every kind asks for it
_POINTS: dict = {}               # (kind -> the space's points), which do not depend on the width
_FAMS: dict = {}                 # (kind -> its families), resolved once


def _roots() -> dict:
    if not _ROOTS:
        from chialu.targets.rtl.families import coverage as COV
        _ROOTS.update(COV.roots())
    return _ROOTS


# the space a kind's families come from, for the kinds no unit template opens as a root
# (`COV.roots()` carries the rest, and a space that serves several kinds is named by each)
KIND_SPACES = {
    "incrementer": ("chialu.spaces.adder_spaces", "incrementer_space", ()),
    "lzc": ("chialu.spaces.shift_simd_spaces", "lzc_space", ()),
    "rotator": ("chialu.spaces.shift_simd_spaces", "rotator_space", ()),
    "bitcount": ("chialu.spaces.shift_simd_spaces", "bitcount_space", ()),
    "comparator": ("chialu.spaces.adder_spaces", "comparator_space", ()),
    "sd_adder": ("chialu.spaces.redundant_spaces", "signed_digit_space", ()),
    "rns_adder": ("chialu.spaces.redundant_spaces", "rns_space", ()),
    "rns_multiplier": ("chialu.spaces.redundant_spaces", "rns_space", ()),
    "rns_comparator": ("chialu.spaces.redundant_spaces", "rns_space", ()),
    "bcd_adder": ("chialu.spaces.decimal_spaces", "decimal_adder_space", ()),
    "bcd_multiplier": ("chialu.spaces.decimal_spaces", "decimal_mul_space", ()),
    "bcd_divider": ("chialu.spaces.decimal_spaces", "decimal_div_space", ()),
    "fp_sqrt": ("chialu.spaces.fp_spaces", "fp_div_space", ()),
}

# a slot tree deeper than this is a space that reopens itself rather than a structure
SLOT_DEPTH = 6


def families_of(kind: str) -> list:
    """The families of a kind, from the spaces the unit templates open
    and, for a kind no template opens as a root, from `KIND_SPACES`."""
    if kind in _FAMS:
        return _FAMS[kind]
    out, seen = [], set()
    for k, spaces in _roots().items():
        if k != kind:
            continue
        for space, _opener in spaces:
            for f in space.families:
                if f.name not in seen:
                    seen.add(f.name)
                    out.append(f)
    if not out:
        spec = KIND_SPACES.get(kind)
        if spec is not None:
            mod = __import__(spec[0], fromlist=[spec[1]])
            for f in getattr(mod, spec[1])(*spec[2]).families:
                if f.name not in seen:
                    seen.add(f.name)
                    out.append(f)
    keep = KIND_FAMILIES.get(kind)
    if keep:
        out = [f for f in out if f.name in keep]
    _FAMS[kind] = out
    return out


def _family(space, name: str):
    for f in space.families:
        if f.name == name:
            return f
    return None


def _resolve(fam, prefix: str, slots: dict, binding: dict, depth: int = 0) -> None:
    """Bind every slot the family opens, and every slot the bound family
    opens under it. `slots[path]` is the slot's space and its members;
    `binding[path + '.family']` is the family bound there, which is the
    caller's when it named one and the space's first member otherwise."""
    if depth > SLOT_DEPTH:
        return
    for slot, sub in (fam.components or {}).items():
        path = prefix + slot
        members = [g.name for g in sub.families]
        if not members:
            continue
        slots[path] = (sub, members)
        pick = binding.get(path + ".family")
        if pick not in members:
            pick = members[0]
        binding[path + ".family"] = pick
        child = _family(sub, pick)
        if child is not None:
            _resolve(child, path + ".", slots, binding, depth + 1)


def structure(kind: str, family: str, pins: dict | None = None) -> tuple:
    """(complete pins, slot paths) of one structure: the caller's pins
    with every slot of the family, and of every family bound under it,
    named explicitly. A point whose pins go through this names the
    sub-structure it was measured with rather than inheriting the
    generator's undeclared default."""
    fam = None
    for f in families_of(kind):
        if f.name == family:
            fam = f
            break
    if fam is None:
        return dict(pins or {}), []
    binding = {k: v for k, v in (pins or {}).items() if str(k).endswith(".family")}
    slots: dict = {}
    _resolve(fam, "", slots, binding)
    out = dict(pins or {})
    for k, v in binding.items():
        out.setdefault(k, v)
    return out, sorted(slots)


def _space_points(kind: str, width: int) -> list:
    """(family, pins) of a kind from its space: every family at the
    baseline binding, one point per value of each of the family's own
    choices, and one point per alternative family of each slot the
    baseline opens.

    The baseline binds every slot to its space's first family, so the
    sub-structures a point was measured with are in the row rather than
    in the generator's `_pin` default. The slot points move one slot at
    a time off that baseline, which answers which sub-structure a top
    family is best served by; a sub-structure's own interactions are
    measured under its own kind, since the cross product of the slots
    does not fit a database. A point that renders the baseline's text
    costs one generation rather than one synthesis, since the build
    maps one text once."""
    from chialu.targets.rtl.families import coverage as COV
    if kind in _POINTS:
        return [(f, dict(p)) for f, p in _POINTS[kind]]
    out = []
    for fam in families_of(kind):
        slots: dict = {}
        base: dict = {}
        _resolve(fam, "", slots, base)
        out.append((fam.name, dict(base)))
        for choice, dom in (fam.design_choices or {}).items():
            for v in COV.samples(dom):
                out.append((fam.name, dict(base, **{choice: v})))
        for path, (sub, members) in sorted(slots.items()):
            for m in members:
                if m == base[path + ".family"]:
                    continue
                alt = {k: v for k, v in base.items() if not k.startswith(path + ".")}
                alt[path + ".family"] = m
                child = _family(sub, m)
                if child is not None:
                    _resolve(child, path + ".", {}, alt)
                out.append((fam.name, alt))
    _POINTS[kind] = [(f, dict(p)) for f, p in out]
    return out


# The pins a generator needs that its space does not carry. The SFU's function and format are the
# point's operating condition rather than a structure, the way the width is: the family's baseline
# is measured at every function the family serves, and a point that moves a choice or a slot holds
# the function fixed, so the slot's cost is read against one function rather than across several.
def sfu_conditions(width: int, family: str) -> list:
    """[(pins, label)] the conditions an SFU family is measured at: the
    format the width names and each function the family serves."""
    from chialu import characterize as CH
    point = CH.SFU_POINTS.get(width)
    if not point:
        return []
    fmt, fns = point
    if family in ("direct_lut", "compressed_lut") and width > 12:
        return []                                       # the value tables serve formats of at most 12 bits
    serves = CH.SFU_FN_OF.get(family, fns)
    return [({"_fn": fn, "_fmt": fmt}, fn) for fn in fns if fn in serves]


def fp_conditions(width: int, family: str) -> list:
    """[(pins, label)] the geometries a float family is measured at:
    every float format of the width the run files build
    (characterize's `fp_formats_of`), each on its own geometry and on
    every union geometry a shared plan would widen it to
    (`fp_geoms_of`). A width no float format has is not characterized,
    which is what keeps a 24-bit "float" row out of the database."""
    from chialu import characterize as CH
    out = []
    for name in CH.fp_formats_of(width):
        for geom in CH.fp_geoms_of(name):
            out.append(({"_fmt": name, **({"_geom": geom} if geom else {})},
                        name if not geom else f"{name}@{geom}"))
    return out


# The pins a point carries beside its binding, per kind: the SFU's function and format, a float
# kind's format. `CONDITION_CROSS` says how a kind's points meet them: `baseline` measures the
# family's baseline at every condition and every other point at the first alone (the SFU, whose
# functions are many and whose slots cost the same under each), `full` measures every point at
# every condition (the float kinds, where a format changes every width of the datapath).
CONDITION_PINS = {"sfu": sfu_conditions, **{k: fp_conditions for k in FP_DB_KINDS}}
CONDITION_CROSS = {"sfu": "baseline"}

# a space that serves two kinds: the families each kind realizes. fp_div_space carries the division
# and the square root, and the fp_divider realizer builds a divider whatever family it is handed, so
# the square-root family would enter the database as a divider's measurement under its name.
KIND_FAMILIES = {"fp_divider": ("sig_div_then_round",), "fp_sqrt": ("sig_sqrt_then_round",)}


def points(kind: str, width: int) -> list:
    """[(family, pins, label)] of a kind at a width: the generator's own
    registration (`char_points(width)` of its module) when it has one,
    the kind's space otherwise, and the curated variants in both cases.
    Every point's pins go through `structure`, so each names the
    sub-structure in every slot rather than leaving it to the
    generator's default. The label names what the point moves off the
    baseline."""
    from chialu import characterize as CH
    pts = []
    gen = GENERATOR_OF.get(kind)
    if gen is not None:
        mod = __import__(gen, fromlist=["char_points"])
        fn = getattr(mod, "char_points", None)
        if fn is not None:
            pts = [(f, p) for f, p in fn(width)]
    if not pts:
        pts = _space_points(kind, width)
    # the curated variants as well: they carry the pins a space does not declare (the signedness,
    # a format, a geometry), and their slot bindings stand where they name one
    pts = list(pts) + [(f, p) for f, p, _lab in CH.variants(kind, width)]
    cond_of = CONDITION_PINS.get(kind)
    if cond_of is not None:
        policy = CONDITION_CROSS.get(kind, "full")
        base_of, crossed = {}, []
        for fam, pins in pts:
            conds = cond_of(width, fam)
            if not conds:
                continue
            keys = {k for c, _l in conds for k in c}
            if keys & set(pins):
                crossed.append((fam, pins))              # the point names its own condition
                continue
            if fam not in base_of:
                base_of[fam] = _canon(structure(kind, fam, {})[0])
            at_base = policy == "full" or _canon(pins) == base_of[fam]
            for cond, _clab in (conds if at_base else conds[:1]):
                crossed.append((fam, dict(pins, **cond)))
        pts = crossed
    keep = KIND_FAMILIES.get(kind)
    bases, base_ids = {}, {}
    seen, out = set(), []
    for fam, pins in pts:
        if keep and fam not in keep:
            continue
        full, _slots = structure(kind, fam, pins)
        # a point is identified as it is stored (point_of fills every choice's default), so the
        # family's base and a point that sets a choice to its default are one point, labelled base;
        # before, both were built and stored as one row, and the label written last won
        pid = point_of(kind, fam, full)["point_id"]
        key = (fam, _canon({k: v for k, v in full.items() if str(k).startswith("_")}), pid)
        if key in seen:
            continue
        seen.add(key)
        if fam not in bases:
            bases[fam] = structure(kind, fam, {})[0]
            base_ids[fam] = point_of(kind, fam, bases[fam])["point_id"]
        moved = {} if pid == base_ids[fam] else collapsed_moves(full, bases[fam])
        lab = ",".join(f"{k}={v}" for k, v in sorted(moved.items())) or "base"
        cond = full.get("_fn") or full.get("_fmt")       # the condition a point is measured at
        if cond:
            lab = f"{cond}:{lab}"
        out.append((fam, full, lab[:60]))
    return out


# the module a kind's characterization points come from, when the generator registers them
GENERATOR_OF = {
    "adder": "chialu.targets.rtl.families.adder_ext",
    "multiplier": "chialu.targets.rtl.families.mul_ext",
    "divider": "chialu.targets.rtl.families.div",
    "sfu": "chialu.targets.rtl.families.sfu",
    "dot": "chialu.targets.rtl.families.dot",
}


# ---- the build -------------------------------------------------------------------------------
def rtl_of(kind: str, family: str, pins: dict, width: int):
    """(module, rtl text) of a characterization point, or (None, ""). The
    point's condition pins (a float format, an SFU function) travel in
    `pins`, so the realizer and the wrapper build the same geometry."""
    from chialu import characterize as CH
    m = CH.realize(kind, family, pins, width)
    if m is None:
        return None, ""
    texts = FAM.module_texts(m.name, m.text)
    return m, "\n".join(texts.values()) + "\n" + CH.wrapper(kind, m, width, pins)


# the width range a kind is characterized over: a structure whose area grows with the square
# of the width is measured up to the width its units are actually built at, and a structure
# whose operand is a format is measured over the formats' widths
KIND_WIDTHS = {
    "multiplier": (4, 64), "divider": (8, 32), "dot": (8, 32), "sfu": (8, 32),
    "fp_adder": (8, 64), "fp_multiplier": (8, 64), "fp_comparator": (8, 64), "fp_divider": (8, 64),
    "fp_sqrt": (8, 64), "rounder": (8, 64), "unpacker": (8, 64), "posit_unit": (8, 32),
    "bcd_adder": (8, 32), "bcd_multiplier": (8, 32), "bcd_divider": (8, 32),
    "rns_adder": (8, 32), "rns_multiplier": (8, 32), "rns_comparator": (8, 32),
    "sd_adder": (4, 64), "checker": (4, 64),
}


SEED_WIDTHS_FILE = DB_DIR / "seed_widths.json"


def seed_geometries(refresh: bool = False, targets_dir: Path | None = None) -> dict:
    """{"widths": {kind: the widths the run files' structures are built
    at}, "formats": [the float formats their float structures are built
    at]}, harvested from each run file's structure manifest. The dense
    grid is a ladder of round widths and a seed's structures are not on
    it (a 281-bit accumulator frame, a 22-bit product, a 9-bit shift
    amount), so a query at a seed's own width would interpolate without
    them; and a float structure's geometry is its format, not its width,
    so the formats are harvested beside the widths (a block mode's
    element format stands for it). The harvest is cached, since loading
    every run file costs minutes."""
    if not refresh and SEED_WIDTHS_FILE.is_file():
        try:
            d = json.loads(SEED_WIDTHS_FILE.read_text())
            if isinstance(d, dict) and "widths" in d:
                return {"widths": {k: list(v) for k, v in (d.get("widths") or {}).items()},
                        "formats": list(d.get("formats") or []), "geoms": list(d.get("geoms") or [])}
            return {"widths": {k: list(v) for k, v in d.items()}, "formats": [], "geoms": []}   # the pre-2026-09-20 file
        except (OSError, json.JSONDecodeError):
            pass
    import tempfile
    from adir.instance import load as load_instance
    from chialu.verify.formats import BlockFormat, FloatFormat, parse_format
    out: dict = {}
    formats: set = set()
    geoms: set = set()
    d = targets_dir or (DB_DIR.parent.parent / "targets")
    for f in sorted(list(Path(d).glob("*.yaml")) + list(Path(d).glob("*/*.yaml"))):
        if f.name.endswith((".numeric.yaml", ".cal.yaml", ".calib.yaml", ".nollm.yaml")) or ".free_" in f.name \
                or ".pipeline." in f.name or ".nollm." in f.name:
            continue                                    # a derived copy of a run file beside it
        try:
            inst = load_instance(str(f), run_dir_override=tempfile.mkdtemp(prefix="chialu_widths_"))
            man = (inst.elaboration.info or {}).get("manifest") or []
        except Exception as e:                          # noqa: BLE001 - a run file that no longer loads is reported
            print(f"[synthdb] {f.name}: {type(e).__name__}: {str(e)[:100]}")
            continue
        for st in man:
            kind = st.get("slot") or st.get("kind")
            w = st.get("width")
            if not kind or not w:
                continue
            out.setdefault(kind, set()).add(int(w))
            if kind in FP_DB_KINDS and st.get("format"):
                try:
                    fmt = parse_format(str(st["format"]))
                except ValueError:
                    continue
                if isinstance(fmt, BlockFormat):
                    fmt = fmt.elem
                if isinstance(fmt, FloatFormat):
                    formats.add(fmt.name)
        # the geometry every float mode computes at when any of them shares a datapath: a float row is read
        # there for such a plan, so the points are measured there as well
        try:
            from chialu.targets.rtl.alu_seed import union_geometry
            g = union_geometry((inst.elaboration.info or {}).get("spec") or {})
            if g is not None:
                geoms.add(g.tag())
        except Exception:  # noqa: BLE001 - a unit with no float mode shares no geometry
            pass
    doc = {"widths": {k: sorted(v) for k, v in sorted(out.items())}, "formats": sorted(formats),
           "geoms": sorted(geoms)}
    try:
        SEED_WIDTHS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SEED_WIDTHS_FILE.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    except OSError:
        pass
    return doc


def seed_widths(refresh: bool = False, targets_dir: Path | None = None) -> dict:
    """{kind: the widths the run files' structures are built at}."""
    return seed_geometries(refresh, targets_dir)["widths"]


def seed_formats(refresh: bool = False, targets_dir: Path | None = None) -> list:
    """The float formats the run files' float structures are built at,
    which is what a float kind's points are measured at beside the
    format its width names by default (`characterize.fp_formats_of`)."""
    return seed_geometries(refresh, targets_dir)["formats"]


def seed_geoms(refresh: bool = False, targets_dir: Path | None = None) -> list:
    """The union geometries the run files' float modes compute at when
    one of their float kinds shares a datapath (alu_seed.union_geometry):
    a float point is measured at its format's own geometry and at each
    of these, since a shared plan reads the rows there."""
    return seed_geometries(refresh, targets_dir)["geoms"]


def widths_for(kind: str, widths) -> list:
    """The widths a kind is built at, which is the request inside the
    kind's own range."""
    lo, hi = KIND_WIDTHS.get(kind, (4, 512))
    return [w for w in widths if lo <= w <= hi]


def build_tasks(kinds, widths, families=None, extra: dict | None = None) -> list:
    """Every characterization point as (kind, family, pins, label, width),
    without generating anything: the generation is the worker's, so a
    build starts synthesizing at once. `extra` adds widths per kind,
    which is how a seed's own widths join the grid."""
    out = []
    for kind in kinds:
        ws = sorted(set(widths_for(kind, widths)) | {int(w) for w in (extra or {}).get(kind, [])})
        for w in ws:
            for family, pins, lab in points(kind, w):
                if families and family not in families:
                    continue
                out.append((kind, family, pins, lab, w))
    out.sort(key=lambda t: (t[4], t[0], t[1]))       # the narrow widths first, so a partial build covers them
    return out


# A heavy point is one whose module text is large, which the width does not tell: a 512-bit ripple
# adder is 1 KB and a 512-bit bit counter under 1 KB, while an RNS channel multiplier at 32 bits is
# 614 KB, a 64-bit Booth multiplier is 463 KB, and a 512-bit prefix adder is 253 KB. A 128-bit
# prefix adder is 44 KB and maps in seconds, so the threshold stands above it. A heavy point waits
# for the machine to have room rather than for a slot: a run of the dense build on the EDA host
# (20 cores, 25 GB) under four jobs and one heavy slot held 17 GB free at a load of 7 and mapped
# 18 points in fourteen minutes, since every worker sat on the slot while the largest mapper of the
# whole run took 0.7 GB.
WIDE_BYTES = 200_000
# A module past this size is not characterized at all: the tools need more than ten gigabytes for it
# (yosys held 11.7 GB on a 614 KB module), which is what a machine runs out of. The row
# says the point was skipped and how large it was, so the gap is visible rather than silent. A module
# this size is a generator that expands rather than a structure worth a row.
SKIP_BYTES = int(os.environ.get("CHIALU_SKIP_BYTES", "500000"))
# A heavy point starts only while the machine has this much memory free, which is what keeps a build
# off the out-of-memory killer. The two host crashes of 2026-09-13 ran fourteen and six mappings of
# modules above `SKIP_BYTES`, one of which took 20 GB on a 25 GB machine.
MEM_FLOOR = int(os.environ.get("CHIALU_MEM_FLOOR_MB", "6144")) * 1024 * 1024
MEM_WAIT_S = 10                                        # between two reads of the free memory
MEM_WAIT_MAX = 600                                     # a point starts anyway after this long


def available_memory() -> int | None:
    """Bytes a new mapper can take, or None where the machine does not
    say. Linux answers from MemAvailable; macOS from the free, inactive,
    speculative and purgeable pages `vm_stat` counts."""
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        pass
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=20).stdout
        page = 4096
        m = re.search(r"page size of (\d+) bytes", out)
        if m:
            page = int(m.group(1))
        free = 0
        for label in ("Pages free", "Pages inactive", "Pages speculative", "Pages purgeable"):
            m = re.search(rf"{label}:\s+(\d+)", out)
            if m:
                free += int(m.group(1))
        return free * page if free else None
    except Exception:                                   # noqa: BLE001 - an unknown machine gates nothing
        return None


def wait_for_memory(floor: int = MEM_FLOOR) -> float:
    """Hold until the machine has `floor` bytes free. Returns the seconds
    waited; a machine that does not report its memory waits none."""
    t0 = time.time()
    while time.time() - t0 < MEM_WAIT_MAX:
        free = available_memory()
        if free is None or free >= floor:
            break
        time.sleep(MEM_WAIT_S)
    return time.time() - t0


DB_CLOCK_PS = 10          # far below any structure's reach, as the whole unit's MIN_DELAY_PS is below any unit's


def clock_target(kind: str, width: int) -> int:
    """ABC's delay target for a point: `DB_CLOCK_PS`, below the reach of
    every structure, so a row is the module mapped for its least delay --
    the mapping the whole unit gets at MIN_DELAY_PS (targets/make_targets.py).
    A reachable target (the 1-6 ns this used to give) maps a module for
    area and measures a delay the unit's own mapping never produces."""
    return DB_CLOCK_PS


def run_job(pdk: dict, effort: str, timeout_s: int, job: dict, lib_hash: str, repeats: int = 5) -> dict:
    """Synthesize one point and return its row."""
    from adir.registry import underlying              # the plain function: an in-process synthesis, no cluster
    from chialu import eda
    t0 = time.time()
    clock = clock_target(job["kind"], job["width"])
    r = underlying(eda.synth_ppa)(job["rtl"], "chr_top", pdk, clock, timeout_s=timeout_s, effort=effort, repeats=repeats, report=False)
    result = {**trace(r), "status": "ok" if r.get("ok") else "fail", "area_um2": r.get("area_um2"), "cells": r.get("cells"),
              "delay_ps": r.get("abc_delay_ps"), "seconds": round(time.time() - t0, 1),
              "detail": "" if r.get("ok") else (r.get("detail") or "")[:200]}
    row = make_row(pdk["name"], effort, clock, lib_hash, job["kind"], job["family"], job["pins"], job["width"],
                   job["label"], job["module"], job["gen_hash"], result, repeats)
    if job["family"] in FAM.PREFIX_FAMILIES and job["kind"] == "adder":
        from chialu.targets.rtl.families import prefix
        try:
            g = prefix.build(job["width"], FAM.prefix_spec(job["family"], job["pins"], job["width"]))
            row["graph"] = {k: v for k, v in g.summary().items() if k != "n"}
        except ValueError:
            pass
    return row


# A build's points run in processes rather than threads. A point is generated in Python and then
# mapped by yosys, and only the yosys call releases the interpreter lock, so under a thread pool the
# generation of every point of the whole build runs on one core: a generator-heavy run under
# `--jobs 100` held 0.50 rows/s with no yosys process alive at the sample and a load of 7 on a
# 128-core machine, which is 14 hours for the 26,710 points of a dense build. The fork is what keeps
# the change small: a worker inherits the task list, the rows already in the database and the PDK
# descriptor rather than being sent them, so a task is an index and only the finished row travels
# back. The writing therefore stays in the parent, and with it the two properties the loop had --
# a row is appended the moment it lands, so an interrupted build keeps what it finished, and the
# rows are taken as they complete, so one slow mapping does not hold back the rows behind it.
_BUILD: dict = {}                # what a forked worker reads, filled in the parent before the fork


def _build_point(i: int) -> tuple:
    """One point of a build in a worker: (the row to write, or None for a
    point the generator does not realize or the database already holds,
    the counters the parent adds up). The counters travel with the row
    rather than living in a shared structure, since a worker is a process
    here and a plain dictionary no longer shares."""
    b = _BUILD
    kind, family, pins, lab, w = b["tasks"][i]
    pdk, pdk_name, effort, lib_hash = b["pdk"], b["pdk_name"], b["effort"], b["lib_hash"]
    measured, stat = b["measured"], {}

    def row_for(module, gh, result):
        return make_row(pdk_name, effort, clock_target(kind, w), lib_hash, kind, family, pins, w, lab,
                        module, gh, result, b["repeats"])

    pins, _slots = structure(kind, family, pins)
    key = row_key(row_for("", "", {"status": "fail"}))
    try:
        m, rtl = rtl_of(kind, family, pins, w)
    except Exception as e:                                # noqa: BLE001 - a generator's own reason
        return row_for("", "", {"status": "fail", "detail": f"{type(e).__name__}: {str(e)[:120]}"}), stat
    if m is None:
        return None, stat
    gh = _hash(rtl)
    prev = b["have"].get(key)
    if prev is not None and (prev.get("provenance") or {}).get("gen_hash") == gh \
            and (prev.get("flow") or {}).get("tool_hash") == tool_hash(pdk_name):
        stat["skip"] = 1                                 # a row from other tools is measured again here
        return None, stat
    # the memo of the measured texts: a plain dictionary under threads, a manager's proxy under
    # processes, so identical module text is still synthesized once whichever worker meets it. Both
    # `get` and `setdefault` are one atomic operation on either, which is what the lock used to buy;
    # two workers that miss at the same moment measure the same text twice, as they did before.
    done = measured.get(gh)
    if done is not None:
        stat["memo"] = 1
        return row_for(m.name, gh, dict(done)), stat
    if len(rtl) >= SKIP_BYTES:
        result = {"status": "skip", "seconds": 0, "detail": f"the module is {len(rtl) // 1024} KB, past the "
                  f"{SKIP_BYTES // 1024} KB the tools carry"}
        measured.setdefault(gh, result)
        stat["skipped_big"] = 1
        return row_for(m.name, gh, result), stat
    job = {"kind": kind, "family": family, "pins": pins, "label": lab, "width": w,
           "module": m.name, "rtl": rtl, "gen_hash": gh}
    try:
        if len(rtl) >= WIDE_BYTES:                       # a heavy point's mapper takes gigabytes
            with b["wide"]:                              # the semaphore is the machine's, not the worker's
                waited = wait_for_memory()
                if waited:
                    stat["mem_wait_s"] = waited
                row = run_job(pdk, effort, b["timeout_s"], job, lib_hash, b["repeats"])
        else:
            row = run_job(pdk, effort, b["timeout_s"], job, lib_hash, b["repeats"])
        result = dict(row["result"])
        graph = row.get("graph")
    except Exception as e:                               # noqa: BLE001 - one point never ends a build
        result = {"status": "fail", "detail": f"{type(e).__name__}: {str(e)[:160]}"}
        graph = None
    measured.setdefault(gh, result)
    stat["synth"] = 1
    out = row_for(m.name, gh, result)
    if graph:
        out["graph"] = graph
    return out, stat


def build(pdk_name: str, kinds, widths, effort: str, jobs_n: int, timeout_s: int,
          families=None, limit: int = 0, liberty: str | None = None, name: str | None = None,
          seeds: bool = False, wide_jobs: int = 2, repeats: int = 5) -> int:
    import multiprocessing as mp
    import threading
    from concurrent.futures import BrokenExecutor, as_completed

    pdk = pdk_descriptor(pdk_name, liberty, name)
    pdk_name = pdk["name"]
    lib_hash = liberty_hash(pdk)
    tool_hash(pdk_name)          # the tool versions are read once here rather than in every worker
    have = {row_key(r): r for r in load(pdk_name)}
    extra = seed_widths() if seeds else None
    tasks = build_tasks(kinds, widths, families, extra)
    if limit:
        tasks = tasks[:limit]
    # CHIALU_SYNTHDB_POOL=thread is the way back to the pool this build used to run on, for a machine
    # whose fork a tool does not survive and for reading a traceback in one process
    procs = jobs_n > 1 and os.environ.get("CHIALU_SYNTHDB_POOL", "process") != "thread" \
        and "fork" in mp.get_all_start_methods()
    print(f"[synthdb] {len(have)} rows present, {len(tasks)} points on {pdk_name} "
          f"(effort {effort}, {jobs_n} {'processes' if procs else 'threads'}) -> {db_dir(pdk_name)}", flush=True)
    # the heavy points run few at a time and each waits for the machine to have room; wide_jobs 0
    # leaves them to the memory floor alone. Under processes the semaphore is a kernel one the
    # children inherit through the fork, so the gate counts the machine's heavy mappings rather than
    # each worker's own.
    n_wide = wide_jobs if wide_jobs > 0 else max(1, jobs_n)
    ctx = mp.get_context("fork") if procs else None
    manager = ctx.Manager() if procs else None
    measured = manager.dict() if procs else {}   # gen_hash -> the result of the text (one synthesis per text)
    wide = ctx.BoundedSemaphore(n_wide) if procs else threading.Semaphore(n_wide)
    state = {"done": 0, "ok": 0, "skip": 0, "synth": 0}
    t0 = time.time()
    _BUILD.update({"tasks": tasks, "have": have, "pdk": pdk, "pdk_name": pdk_name, "effort": effort,
                   "lib_hash": lib_hash, "timeout_s": timeout_s, "measured": measured, "wide": wide, "repeats": repeats})
    pool = ProcessPoolExecutor(max_workers=jobs_n, mp_context=ctx) if procs \
        else ThreadPoolExecutor(max_workers=jobs_n)
    broken = ""
    try:
        # as_completed rather than map: map yields in the order the points were submitted, so one slow
        # mapping holds back every row behind it and a build that is interrupted there loses them
        with pool:
            futures = [pool.submit(_build_point, i) for i in range(len(tasks))]
            try:
                for fut in as_completed(futures):
                    try:
                        row, stat = fut.result()
                    except BrokenExecutor as e:          # a worker the kernel killed takes the pool with it
                        broken = broken or f"{type(e).__name__}: {str(e)[:120]}"
                        continue
                    for k, v in stat.items():
                        state[k] = state.get(k, 0) + v
                    if row is None:
                        continue
                    write_rows(pdk_name, [row])
                    state["done"] += 1
                    state["ok"] += row["result"]["status"] == "ok"
                    if state["done"] % 50 == 0:
                        dt = time.time() - t0
                        print(f"  {state['done']} rows ({state['ok']} ok, {state['synth']} synthesized, "
                              f"{state['skip']} unchanged), {dt:.0f}s, "
                              f"{state['done'] / max(dt, 1e-9):.1f} rows/s", flush=True)
            except KeyboardInterrupt:                    # the points still queued are dropped rather than
                pool.shutdown(wait=False, cancel_futures=True)   # drained, so ^C stops the build now; the
                raise                                    # rows it wrote stand and the command resumes it
    finally:
        _BUILD.clear()
        if manager is not None:
            manager.shutdown()
    done, ok = state["done"], state["ok"]
    rows = load(pdk_name)
    compact(pdk_name)
    write_manifest(pdk_name, pdk, rows)
    if state.get("mem_wait_s"):
        print(f"[synthdb] {state['mem_wait_s']:.0f}s spent waiting for {MEM_FLOOR // 2**20} MB of free memory")
    if state.get("skipped_big"):
        print(f"[synthdb] {state['skipped_big']} points skipped: the module passes {SKIP_BYTES // 1024} KB")
    if state.get("memo"):
        print(f"[synthdb] {state['memo']} points took the result of a text the build had already measured")
    if broken:
        print(f"[synthdb] the worker pool died ({broken}); the rows written so far stand and the same "
              f"command resumes the build")
    print(f"[synthdb] {done} rows written ({ok} ok) in {time.time() - t0:.0f}s; {len(rows)} rows in the database")
    return 1 if broken else 0


# ---- the queries -----------------------------------------------------------------------------
def _law(kind: str, family: str) -> str:
    if family in LINEAR_FAMILIES:
        return "linear"
    return WIDTH_LAW.get(kind, "log")


def _scale(law: str, w_from: int, w_to: int) -> float:
    """The factor a delay measured at `w_from` takes to `w_to` under a law."""
    import math
    if w_from == w_to or w_from <= 0 or w_to <= 0:
        return 1.0
    if law == "flat":
        return 1.0
    if law == "linear":
        return w_to / w_from
    if law == "quadratic":
        return (w_to / w_from) ** 2
    if law == "nlogn":
        return (w_to * max(1.0, math.log2(max(2, w_to)))) / (w_from * max(1.0, math.log2(max(2, w_from))))
    return max(1.0, math.log2(max(2, w_to))) / max(1.0, math.log2(max(2, w_from)))


# Area follows a different law from delay: a parallel multiplier's delay grows with the log of the
# width while its array grows with the square. The database's own rows show it, `behavioral_star`
# going 1740 um2 at 16 bits to 7138 at 32, which a linear scale under-prices by a factor of two.
AREA_LAW = {
    "multiplier": "quadratic", "fp_multiplier": "quadratic", "bcd_multiplier": "quadratic",
    "rns_multiplier": "quadratic", "dot": "quadratic",
    "divider": "quadratic", "fp_divider": "quadratic", "bcd_divider": "quadratic", "fp_sqrt": "quadratic",
    "shifter": "nlogn", "sfu": "quadratic",
}
# the families whose area is linear in the width whatever their kind's law: a digit-serial or
# iterative structure holds one stage whatever the operand width
LINEAR_AREA_FAMILIES = {"carry_save_array", "restoring_nonrestoring", "srt_radix2", "online_msdf",
                        "digit_recurrence_sqrt_combined", "linear_chain"}


def _area_law(kind: str, family: str) -> str:
    if family in LINEAR_AREA_FAMILIES:
        return "linear"
    return AREA_LAW.get(kind, "linear")


def _loglog(w_lo: int, v_lo: float, w_hi: int, v_hi: float, w: int) -> float:
    """A value at `w` interpolated between two measured widths in log-log
    space, which fits a power law of any exponent without naming it. The
    two points decide the exponent, so an area that grows with the square
    and one that grows with the width are both read off the same rows."""
    import math
    if v_lo <= 0 or v_hi <= 0 or w_lo <= 0 or w_hi <= 0 or w_lo == w_hi:
        return v_lo
    e = (math.log(v_hi) - math.log(v_lo)) / (math.log(w_hi) - math.log(w_lo))
    return float(v_lo * (w / w_lo) ** e)


def active_pins(kind: str, family: str, pins: dict, width: int) -> tuple:
    """(pins without the choices inactive under the rest, the dropped names). A row of an earlier build
    wrote every choice out -- its defaults included -- and the generators now refuse a value given to a
    choice the chosen structure does not read (`<family>.<key>: inactive`), which took the baselines of
    whole families (parallel_prefix, carry_select, the two-path fp adder) with it. Such a value selects
    nothing, so the point is the same design without it."""
    from chialu.variant_contracts import family_schemas, recursive_inactive_parameters
    for schema in family_schemas(kind, family, width):
        try:
            dead = recursive_inactive_parameters(schema, dict(pins))
        except Exception:                                 # noqa: BLE001 - another schema of the family may fit
            continue
        drop = sorted(n for n in pins if any(n == k or n.startswith(k + ".") for k in dead))
        if drop:
            return {n: x for n, x in pins.items() if n not in drop}, drop
    return dict(pins), []


def _resynth_point(i: int) -> tuple:
    """One text of a resynthesis in a worker: (its index, the result, the text's hash)."""
    b = _BUILD
    r = b["texts"][i]
    v = flat(r)
    pins, dropped = dict(v.get("pins") or {}), []
    try:
        try:
            m, rtl = rtl_of(v["kind"], v["family"], pins, int(v["width"]))
        except ValueError as e:
            if "inactive" not in str(e):
                raise
            pins, dropped = active_pins(v["kind"], v["family"], pins, int(v["width"]))
            if not dropped:
                raise
            m, rtl = rtl_of(v["kind"], v["family"], pins, int(v["width"]))
    except Exception as e:                                # noqa: BLE001 - a generator's own reason
        return i, {"status": "fail", "detail": f"{type(e).__name__}: {str(e)[:120]}"}, ""
    if m is None:
        return i, {"status": "fail", "detail": "the generator no longer realizes this point"}, ""
    gh = _hash(rtl)
    if len(rtl) >= SKIP_BYTES:
        return i, {"status": "skip", "seconds": 0, "detail": f"the module is {len(rtl) // 1024} KB, past the "
                   f"{SKIP_BYTES // 1024} KB the tools carry"}, gh
    job = {"kind": v["kind"], "family": v["family"], "pins": pins, "label": v.get("variant", "-"),
           "width": int(v["width"]), "module": m.name, "rtl": rtl, "gen_hash": gh}
    note = f"inactive choices dropped: {', '.join(dropped)}" if dropped else ""
    try:
        if len(rtl) >= WIDE_BYTES:
            with b["wide"]:
                wait_for_memory()
                row = run_job(b["pdk"], b["effort"], b["timeout_s"], job, b["lib_hash"], b["repeats"])
        else:
            row = run_job(b["pdk"], b["effort"], b["timeout_s"], job, b["lib_hash"], b["repeats"])
        result = dict(row["result"])
        if note:
            result["detail"] = (result.get("detail") or "") + ("; " if result.get("detail") else "") + note
        return i, result, gh
    except Exception as e:                               # noqa: BLE001 - one point never ends the run
        return i, {"status": "fail", "detail": f"{type(e).__name__}: {str(e)[:160]}"}, gh


def resynth(pdk_name: str, src: Path, effort: str, jobs_n: int, timeout_s: int, shard: str = "1/1",
            wide_jobs: int = 0, skip_kinds=(), repeats: int = 5) -> int:
    """Every row of the database at `src` measured again under the flow
    here (`clock_target`), written to `db_dir(pdk_name)`
    (`CHIALU_SYNTH_DIR`): the same points, geometries and labels, so the
    rebuilt database covers exactly what the old one did. One synthesis
    per generated text, rows appended as they land, resumable; `shard`
    k/n takes the texts whose point hash falls in part k of n, for a run
    split over hosts (the parts merge with `merge`); `skip_kinds` leaves kinds out (the divider and
    square-root families spend most of an hour in Python per point building their seed tables)."""
    import multiprocessing as mp
    from concurrent.futures import BrokenExecutor, as_completed

    pdk = pdk_descriptor(pdk_name)
    lib_hash = liberty_hash(pdk)
    th = tool_hash(pdk_name)
    old = os.environ.get("CHIALU_SYNTH_DIR")
    os.environ["CHIALU_SYNTH_DIR"] = str(src)
    try:
        rows = load(pdk_name)
    finally:
        if old is None:
            del os.environ["CHIALU_SYNTH_DIR"]
        else:
            os.environ["CHIALU_SYNTH_DIR"] = old
    k, n = (int(x) for x in shard.split("/"))

    def moved(r):
        out = json.loads(json.dumps(r))
        out.pop("graph", None)
        out["flow"] = {"pdk": pdk["name"], "liberty_hash": lib_hash, "effort": effort,
                       "clock_ps": int(clock_target(r["point"]["kind"], 0)), "tool_hash": th,
                       "repeats": repeats, "seeds": seeds_for(repeats)}
        return out

    have = {row_key(r) for r in load(pdk_name) if (r.get("result") or {}).get("status") in ("ok", "skip")}
    todo: dict = {}                     # (kind, width, fmt, point) -> the source rows measured as that text
    for r in rows:
        if int(r["point"]["point_id"], 16) % n != k - 1 or r["point"]["kind"] in skip_kinds \
                or row_key(moved(r)) in have:
            continue
        todo.setdefault(row_key(moved(r))[1:], []).append(r)
    texts = [rs[0] for rs in todo.values()]
    groups = list(todo.values())
    procs = jobs_n > 1 and "fork" in mp.get_all_start_methods()
    ctx = mp.get_context("fork") if procs else None
    wide = ctx.BoundedSemaphore(wide_jobs if wide_jobs > 0 else jobs_n) if procs else None
    print(f"[synthdb] resynth {len(rows)} rows of {src} (shard {shard}): {len(texts)} to measure at "
          f"{clock_target('', 0)} ps, {len(have)} present -> {db_dir(pdk_name)}", flush=True)
    _BUILD.update({"texts": texts, "pdk": pdk, "effort": effort, "lib_hash": lib_hash, "timeout_s": timeout_s,
                   "wide": wide, "repeats": repeats})
    t0, done, ok = time.time(), 0, 0
    try:
        with ProcessPoolExecutor(max_workers=jobs_n, mp_context=ctx) as pool:
            futs = [pool.submit(_resynth_point, i) for i in range(len(texts))]
            for fut in as_completed(futs):
                try:
                    i, result, gh = fut.result()
                except BrokenExecutor as e:
                    print(f"[synthdb] the worker pool died ({e}); rerun to resume", flush=True)
                    return 1
                out = []
                for r in groups[i]:
                    new = moved(r)
                    new["result"] = {**trace(result), "status": result.get("status", "fail"), "area_um2": result.get("area_um2"),
                                     "cells": result.get("cells"), "delay_ps": result.get("delay_ps"),
                                     "seconds": result.get("seconds"), "detail": result.get("detail", "")}
                    new["provenance"] = dict(r.get("provenance") or {}, gen_hash=gh or
                                             (r.get("provenance") or {}).get("gen_hash"), date=date.today().isoformat())
                    out.append(new)
                write_rows(pdk_name, out)
                done += 1
                ok += result.get("status") == "ok"
                if done % 200 == 0:
                    dt = time.time() - t0
                    print(f"  {done}/{len(texts)} texts ({ok} ok), {dt:.0f}s, {done / max(dt, 1e-9):.2f}/s", flush=True)
    finally:
        _BUILD.clear()
    print(f"[synthdb] resynth: {done} texts measured ({ok} ok) in {time.time() - t0:.0f}s", flush=True)
    return 0


def views(pdk_name: str, kinds=None) -> list:
    """Every row of a database as a flat view (`flat`)."""
    return [flat(r) for r in load(pdk_name, kinds=kinds)]


_FLOW_WARNED: set = set()


def _flow_filter(pdk_name: str, rows: list, kind: str) -> list:
    """The rows measured under the flow that runs here. A row whose
    `tool_hash` is another flow's was mapped under another ABC script or
    another yosys, so its area and delay are not comparable with a
    measurement taken now. A row without a hash predates the field and is
    kept. When the filter would empty a kind the database has rows for,
    the rows are served with a warning naming the two hashes and the
    count, since an empty read turns the numeric stage's coverage to zero
    and hides the mismatch instead of reporting it. `CHIALU_DB_FLOW=strict`
    drops them instead."""
    here = tool_hash(pdk_name)
    repeats = int(os.environ.get("CHIALU_SYNTH_DB_REPEATS", "5"))
    keep = [r for r in rows if r.get("tool_hash") in (None, "", here)
            and (r.get("flow") or {}).get("repeats", 1) == repeats]
    if len(keep) == len(rows):
        return keep
    dropped = len(rows) - len(keep)
    others = sorted({r.get("tool_hash") for r in rows if r.get("tool_hash") not in (None, "", here)})
    strict = os.environ.get("CHIALU_DB_FLOW", "warn") == "strict"
    if keep or strict:
        key = (pdk_name, kind, "drop")
        if key not in _FLOW_WARNED:
            _FLOW_WARNED.add(key)
            print(f"[synthdb] {pdk_name}/{kind}: {dropped} rows measured under another flow "
                  f"({', '.join(others)}; requested repeats={repeats}) dropped, {len(keep)} kept at {here}", file=sys.stderr)
        return keep
    key = (pdk_name, kind, "serve")
    if key not in _FLOW_WARNED:
        _FLOW_WARNED.add(key)
        print(f"[synthdb] {pdk_name}/{kind}: every one of the {dropped} rows was measured under another "
              f"flow ({', '.join(others)}; requested repeats={repeats}) and the flow here is {here}; the rows are served anyway, so "
              f"the estimate is not comparable with a measurement. Re-characterize, or set "
              f"CHIALU_DB_FLOW=strict to drop them", file=sys.stderr)
    return [dict(r, stale_flow=True) for r in rows]


def rows_of(pdk_name: str, kind: str, family: str | None = None, effort: str | None = None,
            flow: bool = True) -> list:
    """The measured rows of a kind as flat views: status ok with a delay.
    `flow` keeps the rows measured under the flow that runs here; False
    reads every row whatever its `tool_hash`."""
    out = [r for r in views(pdk_name, kinds=(kind,)) if r["kind"] == kind and r["status"] == "ok"
           and r["delay_ps"] is not None]
    if family:
        out = [r for r in out if r["family"] == family]
    if effort:
        out = [r for r in out if r["effort"] == effort]
    if flow and out:
        out = _flow_filter(pdk_name, out, kind)
    return out


def at_width(pdk_name: str, kind: str, width: int, family: str | None = None, effort: str | None = None,
             fmt: str | None = None, geom: str | None = None) -> list:
    """Every row of a kind at a width: the exact rows when the database
    has that width, else the nearest width's rows scaled by the kind's
    law, each marked with the width it came from. `fmt` names a float
    kind's format and `geom` the geometry a datapath shared among
    formats computes at; a format the database lacks falls back to the
    width's other rows, marked `format_from`, since a float row of
    another format is a different circuit and the caller reports it."""
    rows = rows_of(pdk_name, kind, family, effort)
    if not rows:
        return []
    if kind in FP_DB_KINDS:
        want = [r for r in rows if r.get("format") == fmt and r.get("geom") == geom] if fmt else \
            [r for r in rows if not r.get("geom")]
        if want:
            rows = want
        elif fmt:
            other = [r for r in rows if r.get("format") == fmt] or [r for r in rows if not r.get("geom")]
            rows = [dict(r, format_from=r.get("format"), geom_from=r.get("geom")) for r in (other or rows)]
    widths = sorted({int(r["width"]) for r in rows})
    if width in widths:
        return [dict(r, from_width=width) for r in rows if int(r["width"]) == width]
    lo = max([w for w in widths if w < width], default=None)
    hi = min([w for w in widths if w > width], default=None)
    src = hi if (lo is None or (hi is not None and hi - width <= width - lo)) else lo
    # a point measured at both bracketing widths fixes its own exponent, so its area and delay are
    # interpolated in log-log space; a point measured at one width alone is scaled by the kind's law
    other = lo if src == hi else hi
    partner = {}
    if other is not None:
        partner = {r["point_id"]: r for r in rows if int(r["width"]) == other}
    out = []
    for r in rows:
        if int(r["width"]) != src:
            continue
        o = partner.get(r["point_id"])
        if o is not None:
            w_lo, w_hi = (src, other) if src < other else (other, src)
            r_lo, r_hi = (r, o) if src < other else (o, r)
            delay = _loglog(w_lo, r_lo["delay_ps"] or 0, w_hi, r_hi["delay_ps"] or 0, width)
            area = _loglog(w_lo, r_lo["area_um2"] or 0, w_hi, r_hi["area_um2"] or 0, width)
            out.append(dict(r, from_width=src, width=width, delay_ps=delay, area_um2=area,
                            interpolated=True, bracketed=True))
            continue
        f = _scale(_law(kind, r["family"]), src, width)
        fa = _scale(_area_law(kind, r["family"]), src, width)
        out.append(dict(r, from_width=src, width=width, delay_ps=(r["delay_ps"] or 0) * f,
                        area_um2=(r["area_um2"] or 0) * fa,
                        interpolated=True, bracketed=False))
    return out


def fastest(pdk_name: str, kind: str, width: int, effort: str | None = None, fmt: str | None = None) -> dict:
    """{family: its fastest row} at a width (and a float format)."""
    out: dict = {}
    for r in sorted(at_width(pdk_name, kind, width, effort=effort, fmt=fmt),
                    key=lambda r: (r["delay_ps"], r.get("area_um2") or 0)):
        out.setdefault(r["family"], r)
    return out


def smallest(pdk_name: str, kind: str, width: int, effort: str | None = None, fmt: str | None = None) -> dict:
    out: dict = {}
    for r in sorted(at_width(pdk_name, kind, width, effort=effort, fmt=fmt),
                    key=lambda r: (r.get("area_um2") or 0, r["delay_ps"])):
        out.setdefault(r["family"], r)
    return out


def decompose(pdk_name: str, parts: list, effort: str | None = None) -> dict:
    """The sum of a composite's components: `parts` is [(kind, family,
    width)] (a family None takes the kind's fastest); returns the parts'
    rows, the delay sum (a serial path) and the area sum."""
    got, d_sum, a_sum = [], 0.0, 0.0
    for kind, family, width in parts:
        cand = at_width(pdk_name, kind, int(width), family=family, effort=effort)
        if not cand:
            got.append({"kind": kind, "family": family, "width": width, "missing": True})
            continue
        r = min(cand, key=lambda r: r["delay_ps"])
        got.append(r)
        d_sum += r["delay_ps"] or 0
        a_sum += r.get("area_um2") or 0
    return {"parts": got, "delay_ps": d_sum, "area_um2": a_sum}


def flat_pins(nested: dict, prefix: str = "") -> dict:
    """A nested declaration mapping ({"sig_adder": {"family": ..., "topology": ...}})
    as the dotted pins a row carries ({"sig_adder.family": ..., "sig_adder.topology": ...})."""
    out = {}
    for k, v in (nested or {}).items():
        if isinstance(v, dict):
            out.update(flat_pins(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


def estimate_structure(pdk_name: str, kind: str, family: str, pins: dict, width: int,
                       effort: str | None = "medium", fmt: str | None = None, geom: str | None = None) -> dict:
    """The area and delay the database predicts for one structure of a
    family at a width under `pins`: the family's baseline row at that
    width (the nearest width scaled by the kind's law where the width
    is absent) plus, for every move the declaration makes off the
    baseline, the difference the row that makes that one move measured.
    A move no row makes is reported in `unmodeled` and contributes
    nothing. `fmt` and `geom` name a float structure's format and, where
    it shares a datapath among formats, the geometry that datapath
    computes at. Returns {} when the database has no row of the
    family.

    The baseline is the row that is the family at its own defaults,
    found by identity (point_of's point_id), not by its label: the
    build stores `base` and `<choice>=<its default>` as one row, and the
    label written last wins, which left most groups without a `base`
    tag and the baseline an arbitrary variant. A move is counted as the
    build counts it (collapsed_moves): a family change is one move, not
    one per pin of the family it opens. The moves' areas and delays add,
    but for a float adder's delay, which takes no nested move: its align
    shifter, leading-zero anticipation and normalization share one path,
    and single-pin deltas, summed, took one to 0 ps. How to combine the
    delay deltas was measured two ways, and they disagree. On the
    database's own rows that make two or three moves, the largest
    slowdown plus the largest speedup has 15.6% delay error where the
    sum has 20.6%. But a structure of an ALU combines five to ten moves,
    and there, ranking designs of one plan by the estimate -- what the
    numeric stage does -- the sum is far better: 0.41 where max+min
    gives 0.25 on int_subword_alu (0.15 before this estimate), and
    without the float adder's deltas fp_alu_cmp_plans keeps 0.26 and
    0.22 in its two measured plans (0.29 and 0.21 before; 0.15 and 0.18
    with them)."""
    rows = at_width(pdk_name, kind, width, family=family, effort=effort, fmt=fmt, geom=geom)
    if not rows:
        return {}
    try:
        base_id = point_of(kind, family, {})["point_id"]
    except Exception:  # noqa: BLE001 - a family the space does not declare keeps the label rule
        base_id = None
    base = next((r for r in rows if base_id is not None and r.get("point_id") == base_id), None) \
        or next((r for r in rows if "base" in (r.get("tags") or ())), None) \
        or min(rows, key=lambda r: len(r.get("pins") or {}))
    base_pins = dict(base.get("pins") or {})

    def key_of(v) -> str:
        return json.dumps(v, sort_keys=True, default=str)

    deltas: dict = {}
    for r in rows:
        if r is base:
            continue
        moved = collapsed_moves(r.get("pins") or {}, base_pins)
        if len(moved) == 1:
            (k, v), = moved.items()
            deltas[(k, key_of(v))] = ((r.get("area_um2") or 0) - (base.get("area_um2") or 0),
                                      (r.get("delay_ps") or 0) - (base.get("delay_ps") or 0))
    area, delay = float(base.get("area_um2") or 0), float(base.get("delay_ps") or 0)
    modeled, unmodeled, d_delay = [], [], []
    for k, v in sorted(collapsed_moves(flat_pins(pins), base_pins).items()):
        d = deltas.get((k, key_of(v)))
        if d is None:
            unmodeled.append(f"{k}={v}")
            continue
        area += d[0]
        d_delay.append(d[1])
        modeled.append(f"{k}={v}")
    if kind != "fp_adder":
        delay += sum(d_delay)
    if base.get("format_from") and base["format_from"] != fmt:
        unmodeled.append(f"no {fmt} row: the row of {base['format_from']} stands in")
    return {"area_um2": max(0.0, area), "delay_ps": max(0.0, delay), "family": family, "kind": kind,
            "width": width, "from_width": base.get("from_width", width), "interpolated": bool(base.get("interpolated")),
            "format": base.get("format"), "geom": base.get("geom"), "modeled": modeled, "unmodeled": unmodeled}

# ---- status, verify, merge -------------------------------------------------------------------
def collapsed_moves(pins: dict, base: dict) -> dict:
    """{move: value} of `pins` off `base`, counted as the build counts a move: a slot whose family
    changed is one move, `<slot>.family`, however many pins of the family it opens differ with it
    (the rule slot_report reads its slot points by)."""
    diff = {k for k in set(pins) | set(base) if not str(k).startswith("_") and pins.get(k) != base.get(k)}
    heads = sorted((k[:-len(".family")] for k in diff if k.endswith(".family")), key=len)
    out = {}
    for k in diff:
        if any(k != h + ".family" and k.startswith(h + ".") for h in heads):
            continue
        out[k] = pins.get(k)
    return out


def moved_pins(row: dict, base: dict) -> list:
    """The pins a row moves off its family's baseline binding."""
    pins = row.get("pins") or {}
    return sorted(k for k in set(pins) | set(base)
                  if base.get(k) != pins.get(k) and not str(k).startswith("_"))


def slot_report(pdk_name: str, kind: str | None = None, width: int | None = None) -> int:
    """What each slot buys, per kind and family: how many of the slot's
    members map to a netlist of their own, and the delay from the
    fastest member to the slowest. A slot whose members all map to one
    netlist is one the generator does not read; a slot whose members
    differ by a few picoseconds is one the top family does not depend
    on. The netlist rather than the module text is the test, because a
    module's name carries a hash of its pins, so an unread pin changes
    the text without changing the circuit.

    A row is a point of slot P when the pins it moves off the family's
    baseline are `P.family` and pins under `P.`, which is what a slot's
    alternative family moves: binding it re-resolves the slots that
    family opens under itself."""
    rows = [r for r in views(pdk_name) if r["status"] == "ok" and r["delay_ps"]]
    if kind:
        rows = [r for r in rows if r["kind"] == kind]
    if width:
        rows = [r for r in rows if r["width"] == width]
    bases: dict = {}
    for r in rows:
        key = (r["kind"], r["family"])
        if key not in bases:
            bases[key] = structure(r["kind"], r["family"], {})[0]

    def netlist(r: dict) -> tuple:
        return (r.get("cells"), r.get("area_um2"))

    def condition(r: dict) -> str:
        """The operating condition a row was measured at (the SFU's
        function), which a slot's cost is read against."""
        return str((r.get("pins") or {}).get("_fn") or "")

    baseline: dict = {}      # (kind, family, width, condition) -> the row at the baseline binding
    points: dict = {}        # (kind, family, slot) -> the rows that move that slot alone
    for r in rows:
        base = bases[(r["kind"], r["family"])]
        moved = moved_pins(r, base)
        if not moved:
            baseline[(r["kind"], r["family"], r["width"], condition(r))] = r
            continue
        heads = {m[: -len(".family")] for m in moved if m.endswith(".family")}
        if not heads:
            continue                         # a choice point rather than a slot point
        path = min(heads, key=len)           # the slot moved; the rest are the slots its family opens
        if any(m != path + ".family" and not m.startswith(path + ".") for m in moved):
            continue                         # a point that moves more than the one slot
        points.setdefault((r["kind"], r["family"], path), []).append(r)

    agg: dict = {}
    for (k, f, path), rs in points.items():
        e = {"nets": set(), "delay": [], "members": set()}
        for r in rs:
            member = str((r.get("pins") or {}).get(path + ".family"))
            e["members"].add(member)
            e["nets"].add(netlist(r))
            e["delay"].append((r["delay_ps"], member, r["width"]))
        for w, c in {(r["width"], condition(r)) for r in rs}:
            br = baseline.get((k, f, w, c))
            if br is not None:
                e["nets"].add(netlist(br))
                e["delay"].append((br["delay_ps"], "(baseline)", w))
        agg[(k, f, path)] = e

    print(f"{'kind/family':34s} {'slot':26s} {'memb':>4s} {'nets':>4s} {'fastest':>32s} {'slowest':>32s}")
    n_flat = 0
    for (k, f, path), e in sorted(agg.items()):
        best, worst = min(e["delay"]), max(e["delay"])
        flat = len(e["nets"]) == 1
        n_flat += flat
        print(f"{k + '/' + f:34.34s} {path:26.26s} {len(e['members']):4d} {len(e['nets']):4d} "
              f"{best[1] + ' ' + str(round(best[0])) + 'ps@' + str(best[2]):>32.32s} "
              f"{worst[1] + ' ' + str(round(worst[0])) + 'ps@' + str(worst[2]):>32.32s}"
              f"{'   one netlist' if flat else ''}")
    print(f"[synthdb] {len(agg)} slots measured, {n_flat} of them map to one netlist whatever the member")
    return 0


def status(pdk_name: str, widths=None, per_kind: dict | None = None) -> int:
    rows = views(pdk_name)
    d = db_dir(pdk_name)
    man = {}
    if (d / "manifest.json").exists():
        man = json.loads((d / "manifest.json").read_text())
    cur = generator_hashes()
    stale_gen = sorted(k for k, v in (man.get("generators") or {}).items() if cur.get(k) != v)
    by: dict = {}
    for r in rows:
        by.setdefault(r["kind"], {"rows": 0, "ok": 0, "widths": set(), "families": set()})
        e = by[r["kind"]]
        e["rows"] += 1
        e["ok"] += r["status"] == "ok"
        e["widths"].add(int(r.get("width") or 0))
        e["families"].add(r["family"])
    print(f"[synthdb] {pdk_name}: {len(rows)} rows in {db_dir(pdk_name)}"
          + (f", built {man.get('date')}" if man else " (no manifest)"))
    print(f"  {'kind':16s} {'rows':>6s} {'ok':>6s} {'families':>9s}  widths")
    for kind in sorted(by):
        e = by[kind]
        print(f"  {kind:16s} {e['rows']:6d} {e['ok']:6d} {len(e['families']):9d}  "
              + ",".join(str(w) for w in sorted(e["widths"])))
    if stale_gen:
        print(f"  stale generators since the build: {', '.join(stale_gen)}")
    seen_tools = {r.get("tool_hash") for r in rows}
    here = tool_hash(pdk_name)
    other = sorted(t for t in seen_tools if t and t != here)
    unknown = sum(1 for r in rows if not r.get("tool_hash"))
    if other or unknown:
        print(f"  tools here: {tool_versions(pdk_name)} ({here})")
        if other:
            print(f"  rows measured under other tools: {', '.join(other)} "
                  f"({sum(1 for r in rows if r.get('tool_hash') in other)} rows)")
        if unknown:
            print(f"  rows without a tool version: {unknown}")
    if widths or per_kind:
        missing = []
        for kind in sorted(by):
            have_w = by[kind]["widths"]
            want = list(widths or []) + [int(w) for w in (per_kind or {}).get(kind, [])]
            for w in sorted(set(want)):
                if w not in have_w:
                    missing.append(f"{kind}@{w}")
        if missing:
            print(f"  widths not built: {', '.join(missing[:40])}" + (" ..." if len(missing) > 40 else ""))
    return 0


def verify(pdk_name: str, sample: int, effort: str, timeout_s: int, jobs_n: int, tol: float = 0.02) -> int:
    """Re-synthesize a random sample of rows and compare: a row whose
    delay or area moves by more than `tol` is reported (a changed
    generator, a changed liberty, or a non-deterministic mapping)."""
    pdk = pdk_descriptor(pdk_name)
    rows = [r for r in views(pdk_name) if r["status"] == "ok"]
    if not rows:
        print(f"[synthdb] {pdk_name}: no rows to verify")
        return 1
    random.seed(0)
    pick = random.sample(rows, min(sample, len(rows)))
    lib_hash = liberty_hash(pdk)
    bad = 0

    def one(r):
        m, rtl = rtl_of(r["kind"], r["family"], r.get("pins") or {}, int(r["width"]))
        if m is None:
            return r, None, "the generator no longer realizes this point"
        job = {"kind": r["kind"], "family": r["family"], "pins": r.get("pins") or {}, "label": r.get("variant", "-"),
               "width": int(r["width"]), "module": m.name, "rtl": rtl, "gen_hash": _hash(rtl)}
        return r, flat(run_job(pdk, r.get("effort") or effort, timeout_s, job, lib_hash,
                                    (r.get("flow") or {}).get("repeats", 1))), None

    with ThreadPoolExecutor(max_workers=jobs_n) as pool:
        for r, now, err in pool.map(one, pick):
            name = f"{r['kind']}/{r['family']}@{r['width']} {r.get('variant', '-')}"
            if err:
                print(f"  MISSING {name}: {err}")
                bad += 1
                continue
            if now["status"] != "ok":
                print(f"  FAIL    {name}: {now.get('detail', '')[:80]}")
                bad += 1
                continue
            dd = abs((now["delay_ps"] or 0) - (r["delay_ps"] or 0)) / max(1e-9, r["delay_ps"] or 1)
            da = abs((now["area_um2"] or 0) - (r["area_um2"] or 0)) / max(1e-9, r["area_um2"] or 1)
            tools = "" if r.get("tool_hash") in (None, "", now["tool_hash"]) else " (measured under other tools)"
            if now["gen_hash"] != r.get("gen_hash"):
                print(f"  STALE   {name}: the generator's text changed (delay {r['delay_ps']:.0f} -> "
                      f"{now['delay_ps']:.0f} ps){tools}")
                bad += 1
            elif dd > tol or da > tol:
                print(f"  MOVED   {name}: delay {r['delay_ps']:.0f} -> {now['delay_ps']:.0f} ps, "
                      f"area {r['area_um2']:.0f} -> {now['area_um2']:.0f}{tools}")
                bad += 1
    print(f"[synthdb] verify {pdk_name}: {len(pick)} rows re-synthesized, {bad} differ")
    return 0 if bad == 0 else 1


def merge(pdk_name: str, other: Path) -> int:
    """The union of this database and another directory's, the newer row
    of a key winning."""
    rows = {row_key(r): r for r in load(pdk_name)}
    n_new = n_upd = 0
    files = list(other.glob("*.jsonl")) + list(other.glob("*/*.jsonl"))
    for f in files:
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if not isinstance(r.get("point"), dict):
                continue                                  # a row of the earlier flat schema
            k = row_key(r)
            prev = rows.get(k)
            if prev is None:
                rows[k] = r
                n_new += 1
            elif str((r.get("provenance") or {}).get("date", "")) > str((prev.get("provenance") or {}).get("date", "")):
                rows[k] = r
                n_upd += 1
    d = db_dir(pdk_name)
    if d.is_dir():
        for f in list(d.glob("*.jsonl")) + list(d.glob("*/*.jsonl")):
            f.unlink()
    write_rows(pdk_name, list(rows.values()))
    compact(pdk_name)
    print(f"[synthdb] merge {other} into {pdk_name}: {n_new} new rows, {n_upd} newer rows, {len(rows)} total")
    return 0


# ---- the EDA host ----------------------------------------------------------------------------
def build_on_host(host: str, argv: list, repo_dir: str = "~/chiALU", pdk_name: str = "nangate45") -> int:
    """The same build on an EDA host: main is pushed there (ops/hostctl.sh
    deploy), the build runs in a tmux window, and the database directory
    is fetched back when it ends."""
    here = Path(__file__).resolve().parent.parent
    dep = subprocess.run(["sh", str(here / "ops" / "hostctl.sh"), "deploy"], capture_output=True, text=True)
    if dep.returncode != 0:
        print(dep.stdout + dep.stderr)
        return 1
    cmd = "python3 -m chialu.synthdb " + " ".join(a for a in argv if a != "--host" and a != host)
    win = f"synthdb_{pdk_name}"
    # RAY_TMPDIR moves `address="auto"` off /tmp/ray, whose ray_current_cluster names a head that a
    # past run left behind: the worker's ray.init then waits minutes per attempt on a dead address
    script = ("#!/bin/bash\n"
              "export PATH=$HOME/miniconda3/envs/chia_env/bin:$HOME/tools/bin:"
              "$HOME/tools/oss-cad-suite/bin:$HOME/.local/bin:$PATH\n"
              "export PYTHONUNBUFFERED=1 RAY_DISABLE_IMPORT_WARNING=1\n"
              "export RAY_TMPDIR=$HOME/.ray_synthdb\n"
              f"cd {repo_dir}\n{cmd}\n" 'echo "EXIT=$?"\n')
    # a detached process rather than a tmux window: a window whose command fails leaves an empty log
    remote = (f"cd {repo_dir} && mkdir -p run/{win} && cat > run/{win}/go.sh <<'GOSH'\n{script}GOSH\n"
              f"chmod +x run/{win}/go.sh && nohup setsid ./run/{win}/go.sh > run/{win}/run.log 2>&1 < /dev/null & "
              f"sleep 5; tail -3 run/{win}/run.log")
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=30", "-o", "LogLevel=ERROR", host, remote],
                       capture_output=True, text=True)
    print((r.stdout + r.stderr).strip())
    print(f"[synthdb] the build runs on {host} ({repo_dir}/run/{win}/run.log); it is incremental, so the same "
          f"command resumes it after an interruption. Fetch it with: "
          f"python3 -m chialu.synthdb fetch --host {host} --pdk {pdk_name}")
    return 0 if r.returncode == 0 else 1


def fetch_from_host(host: str, pdk_name: str, repo_dir: str = "~/chiALU") -> int:
    """The host's database directory copied into this repository and merged."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run(["rsync", "-a", f"{host}:{repo_dir}/chialu/synth/{pdk_name}/", td + "/"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print((r.stdout + r.stderr)[-800:])
            return 1
        return merge(pdk_name, Path(td))


# ---- the command line ------------------------------------------------------------------------
def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(prog="python3 -m chialu.synthdb", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="synthesize the missing or changed rows")
    b.add_argument("--pdk", default="nangate45", help="a descriptor name under pdk/, or a descriptor file")
    b.add_argument("--liberty", default=None, help="liberty files instead of a descriptor (comma separated)")
    b.add_argument("--name", default=None, help="the database name under --liberty")
    b.add_argument("--kinds", default=None, help="the kinds to build (default: every kind with points)")
    b.add_argument("--families", default=None)
    b.add_argument("--widths", default=",".join(str(w) for w in DEFAULT_WIDTHS),
                   help=f"a width list, or `dense` for {DENSE_WIDTHS}")
    b.add_argument("--seeds", action="store_true",
                   help="add the widths the run files' structures are built at")
    b.add_argument("--repeats", type=int, default=5)
    b.add_argument("--effort", default="medium", choices=("low", "medium", "high"))
    b.add_argument("--jobs", type=int, default=max(2, (os.cpu_count() or 4) - 2))
    b.add_argument("--wide-jobs", type=int, default=0,
                   help=f"points whose module passes {WIDE_BYTES // 1000} KB running at once "
                        f"(default 0: as many as --jobs, each starting only while "
                        f"{MEM_FLOOR // 2**20} MB are free)")
    b.add_argument("--timeout", type=int, default=900)
    b.add_argument("--limit", type=int, default=0)
    b.add_argument("--host", default=None, help="run the build on an EDA host (user@ip) and fetch it back")

    s_ = sub.add_parser("status", help="the rows per kind, the widths built and the stale generators")
    s_.add_argument("--pdk", default="nangate45")
    s_.add_argument("--widths", default=None)
    s_.add_argument("--seeds", action="store_true", help="check the widths the run files' structures need")

    q = sub.add_parser("query", help="rows at a width")
    q.add_argument("--pdk", default="nangate45")
    q.add_argument("--kind", required=True)
    q.add_argument("--width", type=int, required=True)
    q.add_argument("--family", default=None)
    q.add_argument("--format", default=None, help="a float kind's format (fp16, bf16, ...; default: every row of the width)")
    q.add_argument("--effort", default=None)
    q.add_argument("--smallest", action="store_true", help="the smallest per family rather than the fastest")
    q.add_argument("--decompose", default=None,
                   help="kind:family:width,... summed as a serial path (a family `-` takes the kind's fastest)")

    v = sub.add_parser("verify", help="re-synthesize a sample and compare")
    v.add_argument("--pdk", default="nangate45")
    v.add_argument("--sample", type=int, default=20)
    v.add_argument("--effort", default="medium")
    v.add_argument("--timeout", type=int, default=900)
    v.add_argument("--jobs", type=int, default=max(2, (os.cpu_count() or 4) - 2))

    m = sub.add_parser("merge", help="union with another database directory")
    m.add_argument("other")
    m.add_argument("--pdk", default="nangate45")

    rs = sub.add_parser("resynth", help="measure every row of another database again under this flow")
    rs.add_argument("src", help="the database root to read (holding <pdk>/); rows go to CHIALU_SYNTH_DIR or the default")
    rs.add_argument("--pdk", default="nangate45")
    rs.add_argument("--repeats", type=int, default=5)
    rs.add_argument("--effort", default="medium", choices=("low", "medium", "high"))
    rs.add_argument("--jobs", type=int, default=max(2, (os.cpu_count() or 4) - 2))
    rs.add_argument("--wide-jobs", type=int, default=0)
    rs.add_argument("--timeout", type=int, default=1800)
    rs.add_argument("--shard", default="1/1", help="k/n: the part of the points this host measures")
    rs.add_argument("--skip-kinds", default="", help="kinds left out (comma separated)")

    f = sub.add_parser("fetch", help="copy a host's database into this repository")
    f.add_argument("--host", required=True)
    f.add_argument("--pdk", default="nangate45")

    pr = sub.add_parser("prune", help="drop the rows that name no sub-structure")
    pr.add_argument("--pdk", default="nangate45")
    pr.add_argument("--apply", action="store_true", help="rewrite the files (default: report alone)")

    sl = sub.add_parser("slots", help="what each slot buys: the members' netlists and delays")
    sl.add_argument("--pdk", default="nangate45")
    sl.add_argument("--kind", default=None)
    sl.add_argument("--width", type=int, default=None)

    a = ap.parse_args(argv)
    if a.cmd == "build":
        if a.host:
            return build_on_host(a.host, argv, pdk_name=(a.name or a.pdk))
        widths = list(DENSE_WIDTHS) if a.widths == "dense" else [int(x) for x in a.widths.split(",")]
        kinds = a.kinds.split(",") if a.kinds else [k for k in KINDS_WITH_POINTS]
        fams = a.families.split(",") if a.families else None
        return build(a.pdk, kinds, widths, a.effort, a.jobs, a.timeout, fams, a.limit, a.liberty, a.name,
                     a.seeds, a.wide_jobs, a.repeats)
    if a.cmd == "resynth":
        return resynth(a.pdk, Path(a.src), a.effort, a.jobs, a.timeout, a.shard, a.wide_jobs,
                       tuple(x for x in a.skip_kinds.split(",") if x), a.repeats)
    if a.cmd == "slots":
        return slot_report(a.pdk, a.kind, a.width)
    if a.cmd == "prune":
        prune(a.pdk, a.apply)
        return 0
    if a.cmd == "status":
        ws = [int(x) for x in a.widths.split(",")] if a.widths else None
        if a.seeds:
            sw = seed_widths()
            print(f"[synthdb] the run files' structure widths: "
                  + ", ".join(f"{k} {','.join(str(w) for w in v)}" for k, v in sorted(sw.items())))
            return status(a.pdk, ws, sw)
        return status(a.pdk, ws)
    if a.cmd == "query":
        if a.decompose:
            parts = []
            for spec in a.decompose.split(","):
                k, fam, w = spec.split(":")
                parts.append((k, None if fam == "-" else fam, int(w)))
            r = decompose(a.pdk, parts, a.effort)
            for p in r["parts"]:
                if p.get("missing"):
                    print(f"  {p['kind']:14s} {str(p['family']):22s} {p['width']:4d}  (no rows)")
                else:
                    src = "" if p.get("from_width") == p["width"] else f" (from {p.get('from_width')})"
                    print(f"  {p['kind']:14s} {p['family']:22s} {p['width']:4d}  {p['delay_ps']:8.0f} ps  "
                          f"{(p.get('area_um2') or 0):9.0f} um2{src}")
            print(f"  {'sum':14s} {'':22s} {'':4s}  {r['delay_ps']:8.0f} ps  {r['area_um2']:9.0f} um2")
            return 0
        sel = smallest(a.pdk, a.kind, a.width, a.effort, a.format) if a.smallest \
            else fastest(a.pdk, a.kind, a.width, a.effort, a.format)
        if a.family:
            sel = {k: v for k, v in sel.items() if k == a.family}
        if not sel:
            print(f"[synthdb] no rows for {a.kind} on {a.pdk}")
            return 1
        print(f"  {'family':26s} {'variant':30s} {'delay ps':>9s} {'area um2':>9s}  width")
        for fam, r in sorted(sel.items(), key=lambda kv: kv[1]["delay_ps"]):
            src = f"{r['width']}" + ("" if r.get("from_width") == r["width"] else f" (from {r.get('from_width')})")
            print(f"  {fam:26s} {str(r.get('variant', '-'))[:30]:30s} {r['delay_ps']:9.0f} {(r.get('area_um2') or 0):9.0f}  {src}")
        return 0
    if a.cmd == "verify":
        return verify(a.pdk, a.sample, a.effort, a.timeout, a.jobs)
    if a.cmd == "merge":
        return merge(a.pdk, Path(a.other))
    if a.cmd == "fetch":
        return fetch_from_host(a.host, a.pdk)
    return 1


# the kinds a build covers by default: every kind with characterization points.
# `fp_fma` belongs here and was missing: characterize.FP_DB_KINDS already lists it and geometry_of
# already gives it the float branch (format plus the shared geometry), so a build of it succeeds --
# 788 rows, 724 of them measured, in ten minutes. Its absence left every fused multiply-add unpriced,
# which is most of what fp_alu_cmp's coverage of 0.778 was missing. It is not a module under
# `separate_multiplier_and_adder`, where the adder and the multiplier realize it
# (targets/rtl/families/partition.py), but that is a property of the selection, not of the kind: the
# estimate prices the structures a partition actually makes, so a row that no unit asks for is
# simply never read.
# Still absent, and for different reasons:
#   `quantizer` carries no slot and so no family. It is glue -- the OR of a mode's unit buses, the
#      mode mux, the flag map -- which docs/demo-plan.md says is measured per target by
#      chialu.profile rather than characterized, because it depends on how many modes and units the
#      target has and is not a reusable (kind, family, width) point.
#   `converter` has no characterization path at all: characterize.realize returns None for it, and
#      geometry_of has no branch for the (source format, target format) pair its cost depends on --
#      the declaration expresses that pair in the variable names instead
#      (`core.converter.m0.fp16.exp_adder.family`), which the point key cannot carry. Giving it rows
#      needs a realizer and a geometry key, not a line here.
KINDS_WITH_POINTS = ("adder", "incrementer", "lzc", "shifter", "rotator", "comparator", "bitcount", "logic",
                     "multiplier", "divider", "fp_adder", "fp_multiplier", "fp_fma", "fp_comparator",
                     "fp_divider", "fp_sqrt", "rounder", "unpacker", "posit_unit", "sd_adder", "rns_adder",
                     "rns_multiplier", "rns_comparator", "bcd_adder", "bcd_multiplier", "bcd_divider",
                     "sfu", "dot", "checker")


if __name__ == "__main__":
    raise SystemExit(main())
