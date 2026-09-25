"""The evaluator entry a backend calls: `evaluate_program(run_dir,
program_path)` rebinds the instance from contract.json, evaluates the
program and returns the metrics, the metadata and the artifacts;
`evaluate_for_backend` returns SkyDiscover's EvaluationResult. The
program text is kept under `<run>/programs/` by candidate id, which the
composer reads back as the parent or a context program."""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path

from .composer import program_ext, save_program
from .composer import program_path as _program_file
from .errors import BindError
from .evaluate import (backend_result, candidate_from_program, evaluate_candidate,
                       load_seed_values, malformed_record, seed_programs_of, replan_program)
from .instance import load
from .nodes import Executor, InfrastructureError
from .prompts import take_sidecar

_CACHE: dict = {}
_LOCK = threading.Lock()


def instance_of(run_dir: Path):
    run_dir = Path(run_dir)
    key = str(run_dir)
    with _LOCK:
        if key not in _CACHE:
            c = json.loads((run_dir / "contract.json").read_text())
            _CACHE[key] = load(c["file"], run_dir_override=str(run_dir),
                               search_override={"backend": c["search"]["backend"]})
        return _CACHE[key]


def _next_iteration(run_dir: Path) -> int:
    counter = run_dir / "iteration.txt"
    with _LOCK:
        it = int(counter.read_text()) + 1 if counter.is_file() else 1
        counter.write_text(str(it))
    return it


def seed_record_of(inst, run_dir: Path, program_path, program: str):
    """The seed record of a program the backend hands over from
    `<run>/seeds/` itself (its initial program at start), with the
    text unchanged; None for a program from anywhere else, including
    a candidate whose text happens to equal a seed's."""
    try:
        Path(program_path).resolve().relative_to((Path(run_dir) / "seeds").resolve())
    except (ValueError, OSError):
        return None
    sha = hashlib.sha256(program.encode()).hexdigest()
    for r in inst.archive(run_dir).records():
        if r.get("is_seed") and r.get("source_sha256") == sha:
            return r
    return None


def evaluate_program(run_dir, program_path) -> dict:
    run_dir = Path(run_dir)
    inst = instance_of(run_dir)
    program = Path(program_path).read_text()
    same = seed_record_of(inst, run_dir, program_path, program)
    if same is not None:
        # the backend evaluates its initial program when it starts, from the seed's
        # own file; `adir seeds` measured it, so its record is returned rather than
        # evaluated and appended again, and no call's sidecar is taken for it
        return backend_result(inst, same)
    side = take_sidecar(run_dir, program, inst)
    it = _next_iteration(run_dir)
    meta = {"source_path": str(program_path), "model": side.get("model"),
            "prompt_config": side.get("prompt_config"), "tactic_id": side.get("tactic_id"),
            "instruction_id": side.get("instruction_id"),
            "history": side.get("history") or []}
    parent = inst.archive(run_dir).get(side.get("parent_id") or "") if side.get("parent_id") else None
    parent_program = None
    if parent is not None:
        pp = _program_file(run_dir, parent["candidate_id"], program_ext(inst))
        parent_program = pp.read_text() if pp.is_file() else None
    # the members whose text the candidate changed against its parent, before any replan: what a
    # node that judges the agent's own writing (chiALU's review) reads through `candidate.touched`
    seeds_a = inst.seed_artifacts()
    if parent_program is not None and seeds_a:
        try:
            from .artifacts import touched_members
            meta["touched"] = touched_members(seeds_a[0], program, parent_program)
        except Exception:  # noqa: BLE001 - a program the splitter refuses is judged whole
            meta["touched"] = []
    else:
        meta["touched"] = []
    # `search.replan: false` (an ablation) keeps a candidate's text as the model wrote it: a changed
    # declaration is not re-rendered from the library, so the text must realize it on its own
    if parent is not None and getattr(inst.template, "replan", None) is not None \
            and inst.search.get("replan", True):
        try:
            new = replan_program(inst, program, parent, parent_program)
        except Exception as e:  # noqa: BLE001 -- the template cannot realize the declared plan
            new = None
            replan_error = f"the declaration cannot be rendered: {e}"
        else:
            replan_error = None
        if new is not None:
            program = new
            meta["replanned"] = True
    else:
        replan_error = None
    dup = duplicate_of(inst, run_dir, program)
    if dup:
        meta["duplicate_of"] = dup
    try:
        if replan_error:
            raise BindError("declaration", replan_error)
        cand = candidate_from_program(inst, program, iteration=it, parent_id=side.get("parent_id"),
                                      meta=meta)
    except Exception as e:  # noqa: BLE001
        # a program the parser or the template refuses (a BindError, or a value error such as a bool
        # declared as 'True') is a hard failure with the reason as feedback, not an evaluator error the
        # backend retries and forgets (and, at one attempt an iteration, an iteration with no record)
        if not isinstance(e, BindError):
            _log_eval_error(run_dir, it, "parse")
        rec = malformed_record(inst, run_dir, program, str(e), archive=inst.archive(run_dir),
                               iteration=it, parent_id=side.get("parent_id"), **meta)
        cand = None
    if cand is not None:
        workers = int(inst.search.get("parallel_nodes") or 8)
        tries = 1 + max(0, int(os.environ.get("ADIR_INFRA_REEVALUATE") or 2))
        try:
            for attempt in range(tries):
                try:
                    rec = evaluate_candidate(inst, run_dir, cand, seed_values=load_seed_values(run_dir),
                                             archive=inst.archive(run_dir),
                                             executor=Executor(run_dir / "cache", workers=workers),
                                             seed_programs=seed_programs_of(run_dir), parent_program=parent_program)
                    break
                except InfrastructureError:
                    # ray failed, not the candidate: evaluate it again (the nodes that finished are cache hits)
                    _log_eval_error(run_dir, it, f"infrastructure, attempt {attempt + 1} of {tries}")
                    if attempt + 1 >= tries:
                        raise
                    time.sleep(30 * (attempt + 1))
        except InfrastructureError as e:
            rec = malformed_record(inst, run_dir, program, f"{e}", archive=inst.archive(run_dir),
                                   iteration=it, parent_id=side.get("parent_id"), infrastructure=True, **meta)
        except Exception as e:  # noqa: BLE001
            # an evaluator fault the graph did not turn into a node failure: the candidate is recorded
            # infeasible with the error (so the iteration is not lost), and the traceback is kept
            _log_eval_error(run_dir, it, "evaluate")
            rec = malformed_record(inst, run_dir, program, f"evaluator error: {type(e).__name__}: {e}",
                                   archive=inst.archive(run_dir), iteration=it,
                                   parent_id=side.get("parent_id"), **meta)
    save_program(run_dir, rec["candidate_id"], program_ext(inst), program)
    with _LOCK:
        with open(run_dir / "chia_eval_log.jsonl", "a") as f:
            f.write(json.dumps({"iteration": it, "candidate_id": rec["candidate_id"],
                                "score": rec["score"]["combined_score"], "feasible": rec["feasible"],
                                "level": rec["fidelity_level"], "parent_id": rec["parent_id"],
                                "prompt_config": meta["prompt_config"], "tactic_id": meta["tactic_id"],
                                "instruction_id": meta["instruction_id"],
                                "seconds": rec["cost"]["seconds"]}) + "\n")
    return backend_result(inst, rec)


def duplicate_of(inst, run_dir: Path, program: str):
    """The id of an evaluated candidate whose program text is `program`'s, byte for byte, else None."""
    sha = hashlib.sha256(program.encode()).hexdigest()
    try:
        for r in inst.archive(run_dir).records():
            if r.get("source_sha256") == sha and not r.get("not_evaluated"):
                return r.get("candidate_id")
    except Exception:  # noqa: BLE001 -- no archive, nothing to compare with
        return None
    return None


def _log_eval_error(run_dir: Path, it, stage: str) -> None:
    """The traceback of an unexpected evaluation error, appended to `<run>/eval_errors.log`."""
    import traceback
    try:
        with _LOCK, open(Path(run_dir) / "eval_errors.log", "a") as f:
            f.write(f"--- {time.strftime('%Y-%m-%dT%H:%M:%S')} iteration {it} ({stage})\n{traceback.format_exc()}\n")
    except OSError:
        pass


def evaluate_for_backend(run_dir, program_path):
    """SkyDiscover's EvaluationResult (metrics and artifacts) when the
    package is importable, else the plain dict."""
    r = evaluate_program(run_dir, program_path)
    try:
        from skydiscover.evaluation.evaluation_result import EvaluationResult  # type: ignore
    except ImportError:
        return r
    return EvaluationResult(metrics=r["metrics"], artifacts=r["artifacts"])
