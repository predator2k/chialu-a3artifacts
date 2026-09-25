"""The verification bundle of a target, built from the verify layer.

A bundle names the DUT module, carries the testbench, the vectors and
the expected words (bit-exact gates) or the dump-mode judge (accuracy
budgets), the fault harness and the generated checker when the unit is
checked, and the seed text; the bundle's `files` ship as strings to the
EDA node, so nothing depends on a working directory."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from chialu.verify.harness import (build_fault_verification,
                                    build_verification)

TARGETS_DIR = Path(__file__).resolve().parent


@dataclass
class Bundle:
    name: str
    dut: str
    files: dict                      # tb.sv, vectors.hex[, expected.hex]
    n_vectors: int
    fault_files: dict = field(default_factory=dict)   # fault_tb.sv, masks.hex
    checker_rtl: str = ""
    checker_name: str = ""
    fault_check: object = None       # callable(dump_text) -> (ok, viol, rep)
    freeze: dict = field(default_factory=dict)
    spec: dict = field(default_factory=dict)    # effective verify config
    unit: dict = field(default_factory=dict)    # prompt texts
    seed_text: str = ""
    algorithm_text: str = ""
    conf_check: object = None        # callable(dump_text) -> (ok, viol, rep) for dump-mode gates
    exact: bool = True               # the conformance gate is bit-exact (self-checking tb)
    explain: object = None           # callable(mismatch line) -> readable text
    structures: object = None        # StructureManifest of the seed


VERIFY_KEYS = ("n_random", "seed", "n_random_masks", "detect", "exhaustive")


def apply_overrides(spec: dict, overrides: dict | None) -> dict:
    """A `verify` override set laid over a bundle's spec: stimulus count
    and seed, fault-mask count, checker thresholds (`detect: {metric:
    [op, bound]}`), exhaustive on/off."""
    for k, v in (overrides or {}).items():
        if k not in VERIFY_KEYS:
            raise ValueError(f"verify: unknown key {k!r} (known: {VERIFY_KEYS})")
        if k == "detect":
            if "detect" not in spec:
                raise ValueError("verify.detect: this bundle has no checker")
            det = dict(spec["detect"])
            for metric, ob in (v or {}).items():
                if metric not in det:
                    raise ValueError(f"verify.detect: unknown metric {metric!r} (known: {sorted(det)})")
                op, bound = ob
                if op not in ("==", "<=", ">=", "<", ">"):
                    raise ValueError(f"verify.detect.{metric}: op {op!r}")
                det[metric] = (op, float(bound) if op != "==" or isinstance(bound, float) else bound)
            spec["detect"] = det
        else:
            spec[k] = v
    return spec


def public_spec(spec: dict) -> dict:
    """The spec without callables, for summaries and spec.json."""
    out = {}
    for k, v in spec.items():
        if callable(v):
            continue
        if k == "detect":
            v = {m: list(ob) for m, ob in v.items()}
        out[k] = v
    return out


def build_from_spec(name: str, spec: dict, out_dir, unit: dict,
                    seed_text: str, algorithm_text: str,
                    checker_rtl: str | None = None,
                    overrides: dict | None = None) -> Bundle:
    """The verify bundle of a spec: the testbench, vectors and expected
    words (plus the fault harness when the spec names a checker), with
    the unit's prompt texts, seed and algorithm reference attached."""
    spec = apply_overrides(dict(spec), overrides)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # one builder at a time per directory: run files that share a run directory (a numeric stage's
    # per-scheme files) loaded at once by two processes wrote and read the same tb.sv, vectors.hex and
    # freeze.json, and one read a freeze.json the other had just truncated
    import fcntl
    with open(out / ".bundle.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _build_locked(name, spec, out, unit, seed_text, algorithm_text, checker_rtl)


def _build_locked(name, spec, out, unit, seed_text, algorithm_text, checker_rtl) -> Bundle:
    ver = build_verification(spec, out)
    files = {f: (out / f).read_text() for f in ("tb.sv", "vectors.hex")}
    if (out / "expected.hex").exists():
        files["expected.hex"] = (out / "expected.hex").read_text()
    b = Bundle(name, spec["dut_name"], files, len(ver.vecs),
               freeze=json.loads((out / "freeze.json").read_text()))
    b.spec = public_spec(spec)
    b.unit = unit
    b.seed_text = seed_text
    b.algorithm_text = algorithm_text
    b.exact = (out / "expected.hex").exists()
    b.explain = ver.explain
    if not b.exact:
        def conf_check(dump_text: str):
            p = out / "dump.hex"
            p.write_text(dump_text)
            return ver.check(p)
        b.conf_check = conf_check
    if spec.get("checker_name"):
        _plan, check = build_fault_verification(
            spec, ver, out, n_random_masks=spec.get("n_random_masks", 2000))
        b.fault_files = {f: (out / f).read_text()
                         for f in ("fault_tb.sv", "masks.hex", "vectors.hex")}
        b.checker_rtl = checker_rtl
        b.checker_name = spec["checker_name"]

        def fault_check(dump_text: str):
            p = out / "fault_dump.hex"
            p.write_text(dump_text)
            return check(p)
        b.fault_check = fault_check
    return b
