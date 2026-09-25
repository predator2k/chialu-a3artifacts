"""The target-level checks as pytest cases: every run file loads, every
baseline seed lints, conforms against its reference, and passes the fault
campaign where the spec declares a checker.

    pytest tests/test_targets.py -n 3        # CHIALU_VERILATOR_JOBS=4

The fault campaign builds a bench per target, so the worker count and
`CHIALU_VERILATOR_JOBS` share the machine: on a 20-core host `-n 3` with
four Verilator jobs runs the suite green, while `-n 4` with two jobs
starves the `mixed_cvt_alu` build past its 900 s limit.

These are the checks that were run by hand after every change to the
generator, the judges or the flow. Each target is a separate case, so
xdist spreads them and one failure names its target.

They need the EDA tools on PATH (verilator, yosys with read_slang), so
every case here carries the `slow` marker.
"""
from __future__ import annotations

import glob
import os

import pytest

pytestmark = pytest.mark.slow


@pytest.fixture(autouse=True)
def _scratch(tmp_path, monkeypatch):
    """Every case works in its own scratch tree, which pytest removes.
    The EDA nodes make temporary directories as they run, and the flow
    writes gigabytes per design."""
    d = tmp_path / "tmp"
    d.mkdir()
    for name in ("TMPDIR", "TMP", "TEMP"):
        monkeypatch.setenv(name, str(d))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = sorted(glob.glob(os.path.join(ROOT, "targets", "*.yaml"))
                 + glob.glob(os.path.join(ROOT, "targets", "eval", "*.yaml")))
NAMES = [os.path.relpath(t, os.path.join(ROOT, "targets")) for t in TARGETS]

_LOADED: dict = {}
_SEEDS: dict = {}


def _instance(name: str):
    """The loaded instance of a run file, once per worker process."""
    if name not in _LOADED:
        from adir.instance import load
        _LOADED[name] = load(os.path.join(ROOT, "targets", name))
    return _LOADED[name]


def _seed(name: str) -> str:
    """The first seed program of a target, rendered once per worker. A
    run file whose seeds are the plans its numeric stage discovers reads
    them from its run directory's `discovered.json`; before that stage
    has run there is no seed to check, and the case says so."""
    if name not in _SEEDS:
        from pathlib import Path
        from adir.errors import BindError
        from adir.seeds import seed_programs
        from chialu.eda import rtl_of
        inst = _instance(name)
        run = Path(inst.run_dir)
        run = run if run.is_absolute() else Path(ROOT) / run
        try:
            programs = seed_programs(inst, run if (run / "discovered.json").is_file() else None)
        except BindError as e:
            if "no seeds listed" in str(e):
                pytest.skip(f"the seeds are the numeric stage's plans, and {run}/discovered.json is absent")
            raise
        _SEEDS[name] = rtl_of(programs[0][1])
    return _SEEDS[name]


def _bundle(name: str):
    arts = {a.path: a for a in _instance(name).artifacts.values()}
    return arts["verify_bundle"].texts if "verify_bundle" in arts else None


def _spec(name: str) -> dict:
    import json
    files = _bundle(name)
    return json.loads(files["spec.json"]) if files and "spec.json" in files else {}


def _rtl_seed(name: str):
    """The seed's RTL, or None where the run file's seed is a declaration
    rather than RTL. The numeric stage's backend mutates declarations, so
    its seed program is the ADIR declaration block and the RTL-level
    checks below do not apply to it."""
    text = _seed(name)
    return None if text.lstrip().startswith("ADIR-DECL") else text


@pytest.mark.parametrize("name", NAMES)
def test_run_file_loads(name: str) -> None:
    assert _instance(name) is not None


@pytest.mark.parametrize("name", NAMES)
def test_baseline_seed_lints(name: str) -> None:
    from adir.registry import underlying
    from chialu.eda import lint
    if _bundle(name) is None:
        pytest.skip("no verify bundle")
    rtl = _rtl_seed(name)
    if rtl is None:
        pytest.skip("the seed program is a declaration, not RTL")
    r = underlying(lint)(rtl)
    assert r["ok"], r["detail"][-1500:]


@pytest.mark.parametrize("name", NAMES)
def test_baseline_seed_conforms(name: str) -> None:
    from adir.registry import underlying
    from chialu.eda import conformance
    files = _bundle(name)
    if files is None:
        pytest.skip("no verify bundle")
    rtl = _rtl_seed(name)
    if rtl is None:
        pytest.skip("the seed program is a declaration, not RTL")
    if name.startswith("approx_alu"):
        pytest.xfail("the approximate baseline misses its own mred budget; pre-existing")
    r = underlying(conformance)(rtl, files)
    assert r["pass"], str(r.get("detail"))[:1500]


@pytest.mark.parametrize("name", NAMES)
def test_baseline_seed_passes_the_fault_campaign(name: str) -> None:
    from adir.registry import underlying
    from chialu.eda import checker_gen, fault
    files = _bundle(name)
    if files is None or not files.get("masks.hex", "").split():
        pytest.skip("the spec declares no checker")
    rtl = _rtl_seed(name)
    if rtl is None:
        pytest.skip("the seed program is a declaration, not RTL")
    if _spec(name).get("unit") != "alu":
        # checker_gen realizes a `check` block's rule table, which is an ALU
        # feature (docs/checker-spec-plan.md); the dot unit's residue checker
        # comes from its own generator and is covered by the selftests
        pytest.skip("the rule table and checker_gen are the ALU's")
    cg = underlying(checker_gen)(files, {})
    assert cg.get("ok"), str(cg.get("detail"))[:800]
    r = underlying(fault)(rtl, files, cg["rtl_text"], 1800)
    assert r["pass"], str(r.get("detail"))[:1500]
    assert r["escape_max"] <= 0.05, f"escape_max {r['escape_max']}"
