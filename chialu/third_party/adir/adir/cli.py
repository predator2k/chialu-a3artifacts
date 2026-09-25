"""The `adir` command: check, cluster, seeds, run, status, stop,
report."""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path

import yaml

from .errors import BindError
from .instance import Instance, contract, load
from .nodes import CLUSTER, Executor


def connect(inst: Instance, local: bool = False) -> bool:
    """Join the CHIA cluster of the run file when one is up: ray on the
    head's address, then CHIA's cache actor when the file has a `cache:`
    section. Without a cluster (or with `--local`) every node runs in
    this process."""
    if local or not (inst.cluster.get("provider") or {}).get("head_ip"):
        return False
    try:
        import ray  # type: ignore
    except ImportError:
        return False
    if not ray.is_initialized():
        # the domain library and a library beside the run file reach the
        # workers through PYTHONPATH (the workers see the same files)
        paths = [p for p in _sys_paths(inst) if p != str(Path(__file__).resolve().parents[1])]
        # `${PYTHONPATH}` is the worker node's own (Ray expands it there): a node without this host's paths
        # (<host> keeps its checkout elsewhere) imports its own copy instead of failing on these
        env = {"PYTHONPATH": ":".join(paths + ["${PYTHONPATH}"])}
        # opencode's model, small model and output cap reach its CLI through the environment, which a call on a
        # worker takes from the worker's, fixed here: set them from the run's opencode roles first (the
        # solution role's last, so it wins where roles differ), then hand them over with the rest
        set_opencode_roles_env(inst)
        env.update(worker_env())
        try:
            ray.init(address="auto", ignore_reinit_error=True, log_to_driver=False,
                     logging_level=logging.WARNING, runtime_env={"env_vars": env})
        except Exception as e:  # noqa: BLE001
            print(f"[adir] no ray cluster ({type(e).__name__}); nodes run in this process")
            return False
    print(f"[adir] ray cluster: {ray.cluster_resources()}")
    if inst.cluster.get("cache"):
        try:
            from chia.base.cache import start_cache  # type: ignore
            start_cache(size=4, units="GB", cache_dir_path=str(inst.run_dir / "chia_cache"),
                        yaml_path=str(inst.path))
            print(f"[adir] chia cache at {inst.run_dir / 'chia_cache'}")
        except Exception as e:  # noqa: BLE001
            print(f"[adir] chia cache not started ({type(e).__name__}: {e})")
    CLUSTER["connected"] = True
    return True


# a model credential set where `adir run` starts reaches the model workers, and so do the settings the agent
# call and the prompt read on the worker: opencode's output cap and its merged config, and every ADIR_* switch
# (ADIR_UNIT_HIERARCHY_NOTE, ADIR_AGENT_ROOT, ADIR_HISTORY_NOTES, ADIR_RAY_SCHEDULING, ...). Without them a
# worker ran with its own defaults, which a run on one host does not show.
WORKER_ENV = ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
              "GOOGLE_VERTEX_PROJECT", "GOOGLE_VERTEX_LOCATION", "GOOGLE_CLOUD_PROJECT",
              "GOOGLE_APPLICATION_CREDENTIALS", "OPENCODE_CONFIG",
              "OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX", "OPENCODE_CONFIG_CONTENT")
WORKER_ENV_PREFIXES = ("ADIR_",)


def worker_env(environ=None) -> dict:
    """The variables of this process `connect` hands the ray workers (runtime_env env_vars)."""
    environ = os.environ if environ is None else environ
    return {k: v for k, v in environ.items()
            if v and (k in WORKER_ENV or k.startswith(WORKER_ENV_PREFIXES))}


def set_opencode_roles_env(inst: Instance) -> None:
    models = inst.search.get("models") or {}
    specs = [m for r, m in models.items() if r != "solution"] + ([models["solution"]] if "solution" in models else [])
    for spec in specs:
        if isinstance(spec, dict) and str(spec.get("agent")) == "opencode" and spec.get("model"):
            from .backends.skydiscover import set_opencode_env
            set_opencode_env(spec)


def executor_for(inst: Instance, run: Path) -> Executor:
    return Executor(run / "cache", workers=int(inst.search.get("parallel_nodes") or 8))


def _sys_paths(inst: Instance) -> list:
    paths = [str(Path(__file__).resolve().parents[1]), str(inst.base_dir), str(Path.cwd())]
    lib = inst.template.name.split(".")[0]
    try:
        import importlib
        mod = importlib.import_module(lib)
        if getattr(mod, "__file__", None):
            paths.append(str(Path(mod.__file__).resolve().parents[1]))
    except Exception:  # noqa: BLE001
        pass
    out = []
    for p in paths:
        if p not in out:
            out.append(p)
    return out


def do_check(inst: Instance, run: Path, quiet: bool = False) -> dict:
    from .backends import skydiscover
    from .composer import COMPOSER_VERSION, skeleton_hash, system_text
    run.mkdir(parents=True, exist_ok=True)
    c = contract(inst)
    (run / "contract.json").write_text(json.dumps(c, indent=1, default=str))
    (run / "space.json").write_text(json.dumps(inst.space, indent=1, default=str))
    (run / "graph.json").write_text(json.dumps(inst.graph.to_json(), indent=1, default=str))
    seeds_records = []
    for p in sorted((run / "seeds").glob("*/record.json")) if (run / "seeds").is_dir() else []:
        seeds_records.append(json.loads(p.read_text()))
    (run / "problem.md").write_text(system_text(inst, seeds_records))
    if not inst.is_numeric:
        cfg = skydiscover.write(inst, run, _sys_paths(inst))
    else:
        (run / "evaluator.py").write_text(skydiscover.EVALUATOR_PY.format(sys_paths=_sys_paths(inst)))
        cfg = {}
    import hashlib
    search_hash = hashlib.sha256(json.dumps({"config": cfg, "composer": COMPOSER_VERSION,
                                             "skeleton": skeleton_hash(),
                                             "prompts": inst.search.get("prompts"),
                                             "instructions": inst.search.get("instructions"),
                                             "operators": inst.search.get("operators")},
                                            sort_keys=True, default=str).encode()).hexdigest()
    inst.hashes["search_hash"] = search_hash
    c["search_hash"] = search_hash
    (run / "contract.json").write_text(json.dumps(c, indent=1, default=str))
    if not quiet:
        print(f"[adir check] {inst.template.name}: {len(inst.bindings)} variables "
              f"({len(inst.searched())} searched), {len(inst.artifacts)} artifacts, "
              f"{len(inst.graph.active)} nodes in the graph, {len(inst.constraints)} constraints "
              f"({len(inst.hard_constraints())} hard); run dir {run}")
        if inst.missing_env:
            print(f"[adir check] unset environment names: {sorted(inst.missing_env)}")
    return c


def do_seeds(inst: Instance, run: Path, quiet: bool = False, discover_ask=None) -> list:
    from .seeds import run_seeds
    log = None if quiet else (lambda m: print(f"[adir seeds] {m}"))
    from .discover import discover_spec
    n = discover_spec(inst)[0]
    want_brief = (inst.task or {}).get("author") == "discover" and not (run / "task_brief.md").is_file()
    if (n and not (run / "discovered.json").is_file()) or want_brief:
        from .discover import discover_plans, task_brief
        if discover_ask is None:
            from .backends.skydiscover import make_inner
            inner = make_inner(inst, run, "discover")

            def discover_ask(system, user):
                import asyncio
                return asyncio.run(inner.generate(system, [{"role": "user", "content": user}]))
        if want_brief:
            task_brief(inst, run, discover_ask, log=log)
        if n and not (run / "discovered.json").is_file():
            discover_plans(inst, run, discover_ask, log=log)
    recs = run_seeds(inst, run, executor_for(inst, run), log=log)
    if not quiet:
        for r in recs:
            print(f"[adir seeds] {r['seed_name']}: {'feasible' if r['feasible'] else 'infeasible'}"
                  f"{' (hard failure)' if r['hard_fail'] else ''}, goal {r['goal_values']}, "
                  f"score {r['score']['combined_score']:.3f}"
                  + (f"; {r['stderr'][:200]}" if r.get("stderr") else ""))
    # the problem text now carries the seeds; a composed message for inspection
    from .composer import sample_user, system_text
    (run / "problem.md").write_text(system_text(inst, recs))
    if not inst.is_numeric:
        (run / "prompt_sample.md").write_text(sample_user(inst, run))
    return recs


def do_run(inst: Instance, run: Path, resume: bool = False, iterations=None, seed=None) -> dict:
    (run / "status.json").write_text(json.dumps({"state": "running", "pid": os.getpid(),
                                                 "started": time.time()}))
    stop_flag = run / "stop"
    if stop_flag.exists():
        stop_flag.unlink()
    if iterations is not None:
        inst.search["iterations"] = int(iterations)
    try:
        if inst.is_numeric:
            from .backends import numeric

            def on_record(rec):
                if stop_flag.exists():
                    raise KeyboardInterrupt
            res = numeric.run(inst, run, executor=executor_for(inst, run), on_record=on_record,
                              log=lambda m: print(f"[adir run] {m}"))
        else:
            from .backends import skydiscover
            res = skydiscover.run(inst, run, resume=resume, iterations=iterations, seed=seed)
    except KeyboardInterrupt:
        res = {"stopped": True}
    (run / "status.json").write_text(json.dumps({"state": "done", "result": res}, default=str))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="adir")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for cmd in ("check", "cluster", "seeds", "run", "status", "stop", "report"):
        p = sub.add_parser(cmd)
        p.add_argument("file")
        p.add_argument("--run-dir")
        p.add_argument("--backend", help="override search.backend (random | grid | smac | nsga2 | ...)")
        if cmd in ("seeds", "run", "report"):
            p.add_argument("--local", action="store_true",
                           help="run every node in this process even when a cluster is up")
        if cmd == "run":
            p.add_argument("--resume", action="store_true")
            p.add_argument("--iterations", type=int, help="override search.iterations (the run's total, also on --resume)")
            p.add_argument("--seed", type=int, help="override search.random_seed: one per repetition")
    args = ap.parse_args(argv)
    try:
        override = {"backend": args.backend} if args.backend else None
        inst = load(args.file, run_dir_override=args.run_dir, search_override=override)
        run = inst.run_dir
        if args.cmd == "check":
            do_check(inst, run)
        elif args.cmd == "cluster":
            run.mkdir(parents=True, exist_ok=True)
            (run / "cluster.yaml").write_text(yaml.safe_dump(inst.cluster, sort_keys=False))
            print(run / "cluster.yaml")
        elif args.cmd == "seeds":
            do_check(inst, run, quiet=True)      # the contract follows the run file every time
            connect(inst, args.local)
            do_seeds(inst, run)
        elif args.cmd == "run":
            do_check(inst, run, quiet=True)
            connect(inst, args.local)
            from .seeds import completed_seeds
            if not completed_seeds(run):
                do_seeds(inst, run)
            res = do_run(inst, run, resume=args.resume, iterations=args.iterations, seed=args.seed)
            print(json.dumps(res, default=str))
        elif args.cmd == "status":
            f = run / "status.json"
            print(f.read_text() if f.is_file() else "no run")
            arch = inst.archive(run)
            recs = arch.records()
            print(f"records: {len(recs)}, feasible: {sum(1 for r in recs if r.get('feasible'))}")
        elif args.cmd == "stop":
            (run / "stop").write_text("stop")
            f = run / "status.json"
            if f.is_file():
                st = json.loads(f.read_text())
                if st.get("state") == "running" and st.get("pid"):
                    try:
                        os.kill(int(st["pid"]), signal.SIGINT)
                    except OSError:
                        pass
            print("stop requested")
        elif args.cmd == "report":
            from .report import report
            connect(inst, args.local)
            s = report(inst, run)
            print(json.dumps({k: s[k] for k in ("records", "feasible", "front", "best", "best_score")},
                             default=str))
    except BindError as e:
        print(f"adir: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
