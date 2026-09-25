"""`adir.instance` (design section 6.9): another ADIR file run as a
node, its `fixed` variables bound from the outer candidate, cached
under the values of those bindings and the inner hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .errors import BindError
from .instance import load


def run_subinstance(outer, run: Path, kwargs: dict) -> dict:
    file = kwargs.get("file")
    bindings = kwargs.get("bindings") or {}
    budget = kwargs.get("budget") or {}
    if not file:
        raise BindError("adir.instance", "inputs.file is required")
    path = Path(file)
    if not path.is_absolute():
        path = outer.base_dir / path
    inner = load(path)
    for name, value in bindings.items():
        b = inner.bindings.get(name)
        if b is None or b.time != "fixed":
            raise BindError("adir.instance", f"bindings.{name}: not a fixed variable of the inner file")
    collide = set(v.name for v in inner.searched()) & set(v.name for v in outer.searched())
    if collide:
        raise BindError("adir.instance", f"inner and outer search variables collide: {sorted(collide)}")
    # rebind the inner file with the outer values as fixed bindings
    raw = json.loads(json.dumps(inner.raw, default=str))
    for name, value in bindings.items():
        raw["variables"][name] = {"fixed": value}
    key = hashlib.sha256(json.dumps({"bindings": bindings, "space": inner.hashes["space_hash"],
                                     "evaluator": inner.hashes["evaluator_hash"],
                                     "search": json.dumps(inner.search, sort_keys=True, default=str)},
                                    sort_keys=True, default=str).encode()).hexdigest()[:16]
    sub_run = Path(run) / "sub" / key
    done = sub_run / "result.json"
    if done.is_file():
        return json.loads(done.read_text())
    sub_run.mkdir(parents=True, exist_ok=True)
    import yaml
    sub_yaml = sub_run / "run.yaml"
    sub_yaml.write_text(yaml.safe_dump({**inner.cluster, "adir": {**raw, "run_dir": str(sub_run)}},
                                       sort_keys=False))
    inst = load(sub_yaml)
    if budget:
        inst.search = dict(inst.search)
        if "iterations" in budget:
            inst.search["iterations"] = int(budget["iterations"])
        if "wall_hours" in budget:
            inst.search["budget"] = {**(inst.search.get("budget") or {}), "wall_hours": budget["wall_hours"]}
    from .cli import do_check, do_seeds
    do_check(inst, sub_run, quiet=True)
    recs = do_seeds(inst, sub_run, quiet=True)
    iterations = 0
    if inst.is_numeric:
        from .backends import numeric
        res = numeric.run(inst, sub_run)
        iterations = res["iterations"]
    archive = inst.archive(sub_run)
    front = archive.front(inst.goal)
    best = front[0] if front else (archive.ranked(inst.goal)[0] if archive.records() else None)
    out = {"iterations": iterations, "seeds": len(recs), "run_dir": str(sub_run),
           "front": [r["candidate_id"] for r in front],
           "cost": {"records": len(archive.records())},
           "best": {}}
    if best:
        out["best"] = {n: m["value"] for n, m in best["measurements"].items()}
        out["best"]["sha256"] = best["source_sha256"]
        out["best"]["goal_values"] = best["goal_values"]
        out["best"]["combined_score"] = best["score"]["combined_score"]
    done.write_text(json.dumps(out, default=str))
    return out
