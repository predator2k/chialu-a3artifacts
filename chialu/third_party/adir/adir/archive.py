"""The archive of candidate records (design section 10): a jsonl file
or a sqlite table, the metric distributions `archive.*` reads, and the
front."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from .errors import UNDECIDED


class Archive:
    def __init__(self, store: str, path: Path, shared: Optional[Path] = None):
        self.store = store
        self.path = Path(path)
        self.shared = Path(shared) if shared else None
        self._records: Optional[list] = None
        if store == "sqlite":
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.path) as db:
                db.execute("CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, "
                           "iteration INTEGER, score REAL, json TEXT)")
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict):
        line = json.dumps(record, default=str)
        if self.store == "sqlite":
            with sqlite3.connect(self.path) as db:
                db.execute("INSERT OR REPLACE INTO records VALUES (?, ?, ?, ?)",
                           (record["candidate_id"], record.get("iteration"),
                            record.get("score", {}).get("combined_score"), line))
        else:
            with open(self.path, "a") as f:
                f.write(line + "\n")
        if self.shared:
            self.shared.parent.mkdir(parents=True, exist_ok=True)
            with open(self.shared, "a") as f:
                f.write(line + "\n")
        if self._records is not None:
            self._records.append(record)

    def records(self) -> list:
        if self._records is None:
            out = []
            if self.store == "sqlite":
                with sqlite3.connect(self.path) as db:
                    for (line,) in db.execute("SELECT json FROM records ORDER BY rowid"):
                        out.append(json.loads(line))
            elif self.path.is_file():
                with open(self.path) as f:
                    for line in f:
                        if line.strip():
                            out.append(json.loads(line))
            self._records = out
        return self._records

    def get(self, candidate_id: str) -> Optional[dict]:
        for r in self.records():
            if r["candidate_id"] == candidate_id:
                return r
        return None

    def metric_values(self, name: str) -> list:
        """The values of `<node>.<output>` over every record that has it."""
        out = []
        for r in self.records():
            v = _lookup(r.get("measurements", {}), name)
            if v is not None:
                out.append(v)
        return out

    def goal_values(self, level: int) -> list:
        out = []
        for r in self.records():
            gv = r.get("goal_values") or []
            if level < len(gv) and gv[level] is not None:
                out.append(gv[level])
        return out

    def ranked(self, goal, hashes: Optional[dict] = None) -> list:
        """Records on the comparison axes, feasible first, then by
        fidelity level, then by the objective at that level."""
        recs = self.records()
        if hashes:
            recs = [r for r in recs if all(r.get(k) == v for k, v in hashes.items())]

        def key(r):
            feas = 1 if r.get("feasible") else 0
            lvl = r.get("fidelity_level", -1)
            gv = r.get("goal_values") or []
            v = gv[lvl] if 0 <= lvl < len(gv) and gv[lvl] is not None else None
            if v is None:
                obj = float("inf")
            else:
                d = goal.levels[lvl][0]
                obj = v if d == "minimize" else -v
            return (-feas, -lvl, obj)
        return sorted(recs, key=key)

    def front(self, goal, hashes: Optional[dict] = None) -> list:
        """The feasible non-dominated records at the level of record for
        a Pareto goal; the best record otherwise."""
        recs = [r for r in self.ranked(goal, hashes) if r.get("feasible")
                and r.get("fidelity_level", -1) == goal.top]
        if goal.kind != "pareto":
            return recs[:1]
        pts = []
        for r in recs:
            gv = r.get("goal_values") or []
            if any(v is None for v in gv):
                continue
            pts.append((r, [v if d == "minimize" else -v
                            for (d, _), v in zip(goal.levels, gv)]))
        front = []
        for r, p in pts:
            dominated = any(all(q[i] <= p[i] for i in range(len(p))) and q != p
                            for _, q in pts)
            if not dominated:
                front.append(r)
        return front


def _lookup(d: dict, name: str):
    cur = d
    for part in name.split("."):
        if isinstance(cur, dict) and "value" in cur and "node_hash" in cur:
            cur = cur["value"]
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    if isinstance(cur, dict) and "value" in cur and "node_hash" in cur:
        cur = cur["value"]
    if isinstance(cur, bool):
        return int(cur)
    if isinstance(cur, (int, float)):
        return cur
    if isinstance(cur, dict) and {"mean", "lo", "hi"} <= set(cur):
        return cur["mean"]
    return None
