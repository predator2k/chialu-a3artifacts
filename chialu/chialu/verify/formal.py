"""Prove generated combinational RTL against a compiled Python golden contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from functools import lru_cache

from chialu.targets.rtl import families as FAM
from chialu.verify.symbolic import compile_reference, Unsupported


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


@lru_cache(maxsize=1)
def toolchain():
    """Identify the converters and solvers whose evidence may be reused."""
    versions = {}
    for command in (("yosys", "-V"), ("verilator", "--version")):
        try:
            run = subprocess.run(command, capture_output=True, text=True, timeout=5)
            versions[command[0]] = run.stdout + run.stderr
        except (OSError, subprocess.TimeoutExpired):
            versions[command[0]] = "unavailable"
    return versions


def proof_key(source):
    return digest(json.dumps([source, toolchain()], sort_keys=True))


def module_source(module):
    return "\n".join(FAM.module_texts(module.name, module.text).values())


def miter(module, adapter):
    """Compare every output and require the Python reference to be defined."""
    golden = compile_reference(adapter)
    inputs = [p for p in adapter.ports if p.direction == "input"]
    outputs = [p for p in adapter.ports if p.direction == "output"]
    ports = [f"input wire [{p.width-1}:0] {p.name}" for p in inputs] + ["output wire bad"]
    lines = [f"module verification_miter({', '.join(ports)});", "wire defined, admitted;"]
    for prefix in ("got", "expected"):
        lines += [f"wire [{p.width-1}:0] {prefix}_{p.name};" for p in outputs]
    parameters = ", ".join(f".{k}({v})" for k, v in module.params.items())
    connections = [f".{p.name}({p.name})" for p in inputs]
    actual = connections + [f".{p.name}(got_{p.name})" for p in outputs]
    expected = connections + [f".{p.name}(expected_{p.name})" for p in outputs]
    expected += [".defined(defined)", ".admitted(admitted)"]
    lines += [f"{module.name} " + (f"#({parameters}) " if parameters else "") + f"dut({', '.join(actual)});",
              f"python_golden reference({', '.join(expected)});"]
    differs = " || ".join(f"got_{p.name} != expected_{p.name}" for p in outputs)
    lines += [f"assign bad = admitted && (!defined || {differs});", "endmodule", ""]
    return module_source(module) + "\n" + golden + "\n" + "\n".join(lines)


def prove_source(source, directory, timeout=60):
    """Retain inputs, the solver script and its result for replay; a timeout is unproved."""
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    result = {"status": "unproved", "source_sha256": digest(source), "source_bytes": len(source.encode()),
              "method": "yosys_sat_python_reference", "directory": str(directory), "toolchain": toolchain()}
    (directory / "miter.sv").write_text(source)
    missing = [name for name in ("yosys",) if not shutil.which(name)]
    if missing:
        result["detail"] = "missing tools: " + ", ".join(missing)
    else:
        try:
            # yosys reads the miter's SystemVerilog through the flow's frontend
            from chialu.eda import frontend_read
            script = (frontend_read(directory / "miter.sv", "verification_miter")
                      + "hierarchy -check -top verification_miter\n"
                      "prep -top verification_miter -flatten\n"
                      "memory_map\nopt_clean\ncheck -assert\n"
                      f"sat -timeout {max(1, int(timeout))} -set-def-inputs -prove bad 0 "
                      "-show-inputs -show-outputs -dump_vcd counterexample.vcd\n")
            (directory / "prove.ys").write_text(script)
            run = subprocess.run(["yosys", "-s", "prove.ys"], cwd=directory, capture_output=True, text=True,
                                 timeout=timeout + 5)
            log = run.stdout + run.stderr
            (directory / "yosys.log").write_text(log)
            if run.returncode == 0 and "SAT proof finished - no model found: SUCCESS!" in log:
                result["status"] = "proved"
            elif run.returncode == 0 and "SAT proof finished - model found: FAIL!" in log:
                result["status"] = "failed"
                result["detail"] = "counterexample.vcd and yosys.log contain a counterexample"
            else:
                result["detail"] = "solver did not prove the contract: " + log[-2000:]
        except subprocess.TimeoutExpired:
            result["detail"] = f"tool timeout after {timeout} seconds"
    result["seconds"] = round(time.monotonic() - start, 3)
    (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def prove(module, adapter, directory, timeout=60):
    try:
        source = miter(module, adapter)
    except Unsupported as error:
        return {"status": "unproved", "detail": str(error)}
    return prove_source(source, directory, timeout)
