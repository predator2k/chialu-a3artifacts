"""Every selftest module as a pytest case, so the suite runs in
parallel under pytest-xdist.

    CHIALU_VERILATOR_JOBS=1 pytest -n 80                  # everything (<host>)
    CHIALU_VERILATOR_JOBS=1 pytest -n 80 -m "not slow"    # the fast set
    CHIALU_CAMPAIGNS=1 CHIALU_VERILATOR_JOBS=1 pytest -n 80   # with the coverage campaigns

The load is the workers times a module's own jobs times Verilator's `-j`
(CHIALU_VERILATOR_JOBS, 6 in chialu-env.sh): `-n auto` at the default
`-j` put several hundred compilers on <host>'s 128 cores. With `-j 1`
and the sharded modules' own pools cut to one job, 80 workers stay
under the core count with room for the host's other users.

A module is run as `python3 -m <module>` in a subprocess, which is how
each one is written to be run, and its exit code is the verdict. The
module list and the slow set come from `chialu.selftests`, so discovery
has one definition.

Memory bounds it too: one synthesis of the vec_dot_acc seed peaks at
8.78 GB, so a 23 GB host runs the slow set at `-n 2`.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

import os

from chialu.selftests import CAMPAIGNS, GUARD, ROOT, SLOW, discover, shards

MODULES = discover()
# the limits are <host>'s (AMD EPYC 9374F); a slower host scales them: <host>'s Xeon E5-2699 v4 builds a Verilator
# model about three times slower per core, so the suite runs there with CHIALU_TEST_TIMEOUT_SCALE=3
_SCALE = float(os.environ.get("CHIALU_TEST_TIMEOUT_SCALE", "1"))
TIMEOUT_FAST = int(600 * _SCALE)
TIMEOUT_SLOW = int(7200 * _SCALE)
TIMEOUT_CAMPAIGN = int(6 * 3600 * _SCALE)
RUN_CAMPAIGNS = os.environ.get("CHIALU_CAMPAIGNS") == "1"

# the modules whose command line requires an output directory; pytest gives each its own tmp_path
NEEDS_OUT = {
    "chialu.verify.variant_selftest",
    "chialu.verify.composition_selftest",
}


def _ids(module: str) -> str:
    return module.replace("chialu.verify.", "").replace("chialu.targets.rtl.families.", "families.")


def _params() -> list:
    """One case per shard of a module (`chialu.selftests.shards`): the long
    modules run as slices of a few minutes that xdist spreads over the cores."""
    out = []
    for m in MODULES:
        marks = []
        if m in CAMPAIGNS:
            marks = [pytest.mark.slow, pytest.mark.skipif(
                not RUN_CAMPAIGNS, reason=f"a coverage campaign of hours: CHIALU_CAMPAIGNS=1, or python3 -m {m}")]
        elif m in SLOW:
            marks = [pytest.mark.slow]
        for label, argv in shards(m):
            out.append(pytest.param(m, list(argv), marks=marks, id=_ids(m) + (f"[{label}]" if label else "")))
    return out


@pytest.mark.parametrize("module,shard", _params())
def test_selftest(module: str, shard: list, tmp_path) -> None:
    """The module exits 0.

    `TMPDIR` points at this case's own directory, so a module that makes
    its own scratch tree with `tempfile.mkdtemp` leaves it there and
    pytest removes it with the rest. Several modules write gigabytes and
    clean up nothing: eight of them in parallel filled a 327 GB disk.
    """
    scratch = tmp_path / "tmp"
    scratch.mkdir()
    env = {GUARD: "1", "TMPDIR": str(scratch), "TMP": str(scratch), "TEMP": str(scratch)}
    timeout = TIMEOUT_CAMPAIGN if module in CAMPAIGNS else TIMEOUT_SLOW if module in SLOW else TIMEOUT_FAST
    argv = [sys.executable, "-m", module, *shard]
    if module in NEEDS_OUT:
        argv += ["--out", str(tmp_path)]
    try:
        r = subprocess.run(argv, cwd=str(ROOT),
                           capture_output=True, text=True, timeout=timeout,
                           env={**_environ(), **env})
    except subprocess.TimeoutExpired:
        pytest.fail(f"{module} did not finish in {timeout}s")
    if r.returncode != 0:
        tail = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-25:]
        pytest.fail(f"{module} exited {r.returncode}\n" + "\n".join(tail))


def _environ() -> dict:
    import os
    return dict(os.environ)
