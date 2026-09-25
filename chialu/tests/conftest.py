"""Report a failing test the moment it fails, not in the summary at the end of the run.

Under pytest-xdist every worker's report reaches the controller through `pytest_runtest_logreport`,
so a failure of a long suite prints its error while the rest still runs. Each failure is also appended
to `$CHIALU_TEST_FAILURES` (default `<basetemp or cwd>/failures.log`) for a tail from another shell.
"""
from __future__ import annotations

import os
import time
from pathlib import Path


def _failure_log(config) -> Path:
    p = os.environ.get("CHIALU_TEST_FAILURES")
    if p:
        return Path(p)
    base = config.getoption("basetemp", None)
    return Path(base) / "failures.log" if base else Path("failures.log")


def pytest_runtest_logreport(report):
    if not report.failed:
        return
    import pytest
    config = pytest._chialu_config  # set in pytest_configure
    text = report.longreprtext or ""
    lines = [l for l in text.splitlines() if l.startswith("E ")] or text.splitlines()[-15:]
    head = f"FAILED ({report.when}) {report.nodeid} after {report.duration:.0f} s"
    tr = config.pluginmanager.get_plugin("terminalreporter")
    if tr is not None:
        tr.write_line("")
        tr.write_line(head, red=True, bold=True)
        for l in lines[-25:]:
            tr.write_line("    " + l[:300])
    try:
        log = _failure_log(config)
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a") as f:
            f.write(f"--- {time.strftime('%Y-%m-%dT%H:%M:%S')} {head}\n{text}\n")
    except OSError:
        pass


def pytest_configure(config):
    import pytest
    pytest._chialu_config = config
