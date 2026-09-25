"""The plain agent loop of the evaluation plan (section 4): one coding
agent, the seed program, the evaluator command and the metrics, for a
fixed number of calls, without ADIR's prompt composition, archive,
plans or knowledge.

    python3 eval/plain_loop/loop.py <run.yaml> --run-dir <dir> --agent claude|codex|opencode
                                    --model <model> [--provider <id>] --calls 5 [--seed baseline] [--timeout 1800]

Each call: the agent gets a workspace holding `program.sv` (the current
best program, EVOLVE markers included), `evaluate.sh` (the evaluator:
ADIR's graph on the program, printing the metrics as JSON) and the last
metrics, and is asked to improve area and delay while every gate stays
green, editing `program.sv` in place. The loop then evaluates the file
through the same evaluator ADIR uses, keeps the best feasible program,
and logs every turn to `<run-dir>/plain_loop.jsonl` with the transcript
under `<run-dir>/plain_loop/turn_<k>/`. The count of calls is the count
of agent invocations, so the budget matches ADIR's `llm_calls`.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "third_party" / "adir"))

SYSTEM = """You are optimizing one SystemVerilog arithmetic unit for area and delay after logic synthesis.
The file program.sv in the working directory is the design. Edit it in place: change only the text
between the EVOLVE-BLOCK-START and EVOLVE-BLOCK-END marker lines, keep every marker line and the
module interfaces, and keep the design functionally identical (a conformance simulation against a
bit-exact reference and, where present, a fault-detection gate must pass). Run ./evaluate.sh to
measure the current file; it prints JSON with `feasible`, `goal_values` [area_um2, abc_delay_ps] and
the gates' details. Make one improvement per call, verify it with ./evaluate.sh, and leave the file
in its best state. Do not create other files."""


def run_check(run_file: Path, run_dir: Path) -> None:
    subprocess.run([sys.executable, "-m", "adir.cli", "check", str(run_file), "--run-dir", str(run_dir)],
                   check=True, capture_output=True, text=True)


def seed_program(run_file: Path, run_dir: Path, name: str) -> str:
    from adir.instance import load
    from adir.seeds import seed_programs
    inst = load(str(run_file), run_dir_override=str(run_dir))
    for n, prog in seed_programs(inst, run_dir):
        if n == name:
            return prog
    raise SystemExit(f"no generated seed {name!r}")


def evaluate(run_dir: Path, program: Path) -> dict:
    """The archive record of one evaluation (feasible, goal_values, score,
    hard_fail, feedback): `evaluate_program` returns the backend's view
    (metrics, artifacts, metadata), and the record it appended to the
    run's archive is read back by its candidate id."""
    from adir.evaluate_entry import evaluate_program, instance_of
    out = evaluate_program(str(run_dir), str(program))
    metrics = out.get("metrics") or {}
    cid = metrics.get("candidate_id")
    rec = instance_of(run_dir).archive(Path(run_dir)).get(cid) if cid else None
    if rec:
        return rec
    return {"candidate_id": cid, "feasible": bool(metrics.get("feasible")), "goal_values": None,
            "score": {"combined_score": float(metrics.get("combined_score") or 0.0)}, "metrics": metrics}


def evaluate_json(run_dir: str, program: str) -> str:
    """What the agent's `evaluate.sh` prints: the record's verdict fields."""
    r = evaluate(Path(run_dir), Path(program))
    return json.dumps({k: r.get(k) for k in ("feasible", "hard_fail", "goal_values", "feedback")}
                      | {"score": (r.get("score") or {}).get("combined_score")}, default=str, indent=1)


def agent_call(agent: str, model: str, ws: Path, user: str, timeout: int, provider: str = "") -> str:
    """One invocation of an agent CLI in the workspace, its stdout returned."""
    if agent == "claude":
        cmd = ["claude", "-p", "--output-format", "text", "--model", model, "--permission-mode", "acceptEdits",
               "--allowedTools", "Read,Edit,Write,Bash(./evaluate.sh*),Bash(python3 *)",
               "--append-system-prompt", SYSTEM]
        stdin = user
    elif agent == "codex":
        cmd = ["codex", "exec", "-m", model, "--sandbox", "workspace-write", "-C", str(ws), "-"]
        stdin = SYSTEM + "\n\n" + user
    elif agent == "opencode":
        # opencode's provider/model id, and its own title and summary calls kept on the same model
        from adir.backends.skydiscover import opencode_model, set_opencode_env
        spec = {"model": model, "provider": provider or None}
        set_opencode_env(spec)
        cmd = ["opencode", "run", "--model", opencode_model(spec), "--dir", str(ws), SYSTEM + "\n\n" + user]
        stdin = None
    else:
        raise SystemExit(f"agent {agent!r}: one of claude, codex, opencode")
    r = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=timeout, input=stdin)
    return (r.stdout or "") + ("\n[stderr]\n" + r.stderr[-2000:] if r.returncode else "")


def score_of(rec: dict) -> float:
    return float(((rec or {}).get("score") or {}).get("combined_score") or 0.0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_file", nargs="?")
    ap.add_argument("--run-dir")
    ap.add_argument("--agent", default="claude", choices=("claude", "codex", "opencode"))
    ap.add_argument("--model")
    ap.add_argument("--provider", default="", help="opencode's provider id (the model is then the provider's own id)")
    ap.add_argument("--calls", type=int, default=5)
    ap.add_argument("--seed", default="baseline")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--evaluate-only", nargs=2, metavar=("RUN_DIR", "PROGRAM"),
                    help="evaluate one program in an existing run and print its verdict (the agent's evaluate.sh)")
    a = ap.parse_args(argv)
    if a.evaluate_only:
        print(evaluate_json(*a.evaluate_only))
        return 0
    if not (a.run_file and a.run_dir and a.model):
        ap.error("run_file, --run-dir and --model are required")
    run_file, run_dir = Path(a.run_file).resolve(), Path(a.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    run_check(run_file, run_dir)
    if not (run_dir / "seeds").is_dir():
        # the graph's gates compare a candidate with the seed (`seed.yosys_stat.cells`, `seed.synth_unit.area_um2`),
        # so the run needs the baseline's record: `adir seeds` of a copy whose only seed is the baseline
        from chialu.pipeline import calibration_run_file
        subprocess.run([sys.executable, "-m", "adir.cli", "seeds", str(calibration_run_file(run_file)),
                        "--run-dir", str(run_dir), "--local"], check=True, capture_output=True, text=True)
        run_check(run_file, run_dir)
    loop_dir = run_dir / "plain_loop"
    loop_dir.mkdir(exist_ok=True)
    best_prog = seed_program(run_file, run_dir, a.seed)
    (loop_dir / "seed.sv").write_text(best_prog)
    best = evaluate(run_dir, loop_dir / "seed.sv")
    log = (run_dir / "plain_loop.jsonl").open("a")
    log.write(json.dumps({"turn": 0, "kind": "seed", "feasible": best.get("feasible"), "goal_values": best.get("goal_values"),
                          "score": score_of(best)}) + "\n")
    log.flush()
    print(f"[plain_loop] seed {a.seed}: feasible={best.get('feasible')} goal={best.get('goal_values')} score={score_of(best):.3f}")
    eval_sh = ("#!/bin/sh\n" f"exec {sys.executable} {Path(__file__).resolve()} --evaluate-only {run_dir} \"$(pwd)/program.sv\"\n")
    for k in range(1, a.calls + 1):
        ws = loop_dir / f"turn_{k}"
        if ws.exists():
            shutil.rmtree(ws)
        ws.mkdir()
        (ws / "program.sv").write_text(best_prog)
        (ws / "evaluate.sh").write_text(eval_sh)
        os.chmod(ws / "evaluate.sh", 0o755)
        fb = best.get("feedback") or {}
        user = (f"Call {k} of {a.calls}. Current program: program.sv (feasible={best.get('feasible')}, "
                f"goal_values [area_um2, abc_delay_ps] = {best.get('goal_values')}).\n"
                f"Evaluator feedback of the current program:\n{json.dumps(fb, default=str)[:4000]}\n\n"
                "Improve area or delay without breaking a gate. Edit program.sv in place and verify with ./evaluate.sh.")
        t0 = time.time()
        try:
            reply = agent_call(a.agent, a.model, ws, user, a.timeout, a.provider)
        except subprocess.TimeoutExpired:
            reply = "[timeout]"
        (ws / "transcript.md").write_text(f"# User\n\n{user}\n\n# Reply\n\n{reply}\n")
        rec = evaluate(run_dir, ws / "program.sv")
        improved = bool(rec.get("feasible")) and score_of(rec) > score_of(best)
        entry = {"turn": k, "feasible": rec.get("feasible"), "hard_fail": rec.get("hard_fail"),
                 "goal_values": rec.get("goal_values"), "score": score_of(rec), "improved": improved,
                 "agent_seconds": round(time.time() - t0, 1)}
        log.write(json.dumps(entry, default=str) + "\n")
        log.flush()
        print(f"[plain_loop] turn {k}: feasible={rec.get('feasible')} goal={rec.get('goal_values')} "
              f"score={score_of(rec):.3f}{' (best)' if improved else ''} in {entry['agent_seconds']}s")
        if improved:
            best, best_prog = rec, (ws / "program.sv").read_text()
            (loop_dir / "best.sv").write_text(best_prog)
    print(f"[plain_loop] best: feasible={best.get('feasible')} goal={best.get('goal_values')} score={score_of(best):.3f}; "
          f"log {run_dir / 'plain_loop.jsonl'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
