"""Constraints, the goal, fidelity levels and the score rule (design
section 4)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional

from .errors import UNDECIDED, BindError
from .expr import Expr, Interval, as_value, evaluate, parse
from .yamlfile import check_keys

CONSTRAINT_KEYS = ("metric", "expr", "le", "ge", "eq", "hard", "satisfies")
SCORE_RULES = ("ratio_to_seed", "slack", "weighted", "pareto")


@dataclass
class Constraint:
    lhs: Expr
    op: str
    rhs: Expr
    hard: bool = False
    satisfies: Optional[str] = None
    index: int = 0

    @property
    def text(self) -> str:
        sym = {"le": "<=", "ge": ">=", "eq": "=="}[self.op]
        return f"{self.lhs.text} {sym} {self.rhs.text}"

    @property
    def refs(self) -> list:
        return self.lhs.refs + self.rhs.refs

    def evaluate(self, resolve) -> dict:
        try:
            a = as_value(self.lhs.value(resolve))
            b = as_value(self.rhs.value(resolve))
        except Exception as e:  # noqa: BLE001
            return {"status": "undecided", "detail": f"{self.text}: {e}", "slack": None}
        if a is UNDECIDED or b is UNDECIDED:
            return {"status": "undecided", "slack": None, "lhs": None, "rhs": None}
        from .expr import _compare, condition_slack
        ok = _compare(self.op, a, b)
        if ok is UNDECIDED:
            return {"status": "undecided", "slack": None}
        slack = _signed_slack(self.op, a, b)
        return {"status": "satisfied" if ok else "violated", "slack": slack,
                "lhs": _plain(a), "rhs": _plain(b)}


def _plain(v):
    v = as_value(v)
    if isinstance(v, Interval):
        return v.to_json()
    if isinstance(v, (dict, list)):
        return None
    return v


def _signed_slack(op, a, b):
    a, b = as_value(a), as_value(b)
    if isinstance(a, Interval):
        a = a.mean
    if isinstance(b, Interval):
        b = b.mean
    if isinstance(a, bool):
        a = int(a)
    if isinstance(b, bool):
        b = int(b)
    if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        return None
    scale = max(abs(a), abs(b), 1e-12)
    if op == "le":
        return (b - a) / scale
    if op == "ge":
        return (a - b) / scale
    return -abs(a - b) / scale if a != b else 0.0


def parse_constraints(rows, path: str = "constraints") -> list:
    out = []
    for i, row in enumerate(rows or []):
        p = f"{path}[{i}]"
        if not isinstance(row, dict):
            raise BindError(p, "a constraint is a mapping")
        check_keys(row, CONSTRAINT_KEYS, p)
        if ("metric" in row) == ("expr" in row):
            raise BindError(p, "exactly one of metric | expr")
        ops = [k for k in ("le", "ge", "eq") if k in row]
        if len(ops) != 1:
            raise BindError(p, "exactly one of le | ge | eq")
        lhs = Expr(row.get("metric", row.get("expr")))
        rhs_raw = row[ops[0]]
        rhs = Expr(rhs_raw) if isinstance(rhs_raw, str) else Expr(repr(rhs_raw) if not isinstance(rhs_raw, bool) else ("true" if rhs_raw else "false"))
        if isinstance(rhs_raw, bool):
            rhs = _BoolExpr(rhs_raw)
        out.append(Constraint(lhs, ops[0], rhs, bool(row.get("hard", False)),
                              row.get("satisfies"), i))
    return out


class _BoolExpr(Expr):
    def __init__(self, v: bool):
        self.text = "true" if v else "false"
        self.ast = ("num", v)
        self.refs = []


@dataclass
class Goal:
    kind: str                      # single | pareto | fidelity
    levels: list                   # [(direction, Expr)]; one for single
    score_rule: str = "ratio_to_seed"
    infeasible: str = "zero"       # zero | slack
    weights: Optional[dict] = None

    @property
    def refs(self) -> list:
        return [r for _, e in self.levels for r in e.refs]

    @property
    def top(self) -> int:
        return len(self.levels) - 1

    def value(self, resolve, level: int):
        d, e = self.levels[level]
        try:
            v = as_value(e.value(resolve))
        except Exception:  # noqa: BLE001
            return UNDECIDED
        if isinstance(v, Interval):
            v = v.mean
        if isinstance(v, bool):
            v = int(v)
        if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)):
            return v
        return UNDECIDED

    def values(self, resolve) -> list:
        return [self.value(resolve, i) for i in range(len(self.levels))]

    def highest_level(self, values: list) -> int:
        """The highest level with a value, or -1."""
        for i in range(len(values) - 1, -1, -1):
            if values[i] is not UNDECIDED:
                return i
        return -1

    def better(self, a: float, b: float, level: int) -> bool:
        d = self.levels[level][0]
        return a < b if d == "minimize" else a > b


def parse_goal(raw, path: str = "goal") -> Goal:
    if not isinstance(raw, dict):
        raise BindError(path, "goal is a mapping")
    check_keys(raw, ("minimize", "maximize", "pareto", "fidelity", "score"), path)
    heads = [k for k in ("minimize", "maximize", "pareto", "fidelity") if k in raw]
    if len(heads) != 1:
        raise BindError(path, "exactly one of minimize | maximize | pareto | fidelity")
    head = heads[0]
    if head in ("minimize", "maximize"):
        levels = [(head, Expr(raw[head]))]
        kind = "single"
    else:
        entries = raw[head]
        if not isinstance(entries, list) or not entries:
            raise BindError(f"{path}.{head}", "a non-empty list of {minimize: expr} or {maximize: expr}")
        levels = []
        for i, ent in enumerate(entries):
            if isinstance(ent, str):
                levels.append(("minimize", Expr(ent)))
                continue
            if not isinstance(ent, dict) or len(ent) != 1 or next(iter(ent)) not in ("minimize", "maximize"):
                raise BindError(f"{path}.{head}[{i}]", "{minimize: expr} or {maximize: expr}")
            (d, e), = ent.items()
            levels.append((d, Expr(e)))
        kind = head
    score = raw.get("score") or {}
    check_keys(score, ("rule", "infeasible", "weights"), f"{path}.score")
    rule = score.get("rule", "pareto" if kind == "pareto" else "ratio_to_seed")
    if rule not in SCORE_RULES:
        raise BindError(f"{path}.score.rule", f"{rule!r} (one of {SCORE_RULES})")
    infeasible = score.get("infeasible", "zero")
    if infeasible not in ("zero", "slack"):
        raise BindError(f"{path}.score.infeasible", "zero | slack")
    return Goal(kind, levels, rule, infeasible, score.get("weights"))


def feasibility(results: list) -> dict:
    """From constraint results: hard failure, feasibility, the worst
    normalized violation among soft rows."""
    hard_fail = any(r["hard"] and r["status"] != "satisfied" for r in results)
    soft = [r for r in results if not r["hard"]]
    feasible = not hard_fail and all(r["status"] == "satisfied" for r in soft)
    viol = 0.0
    for r in soft:
        if r["status"] == "violated" and r.get("slack") is not None:
            viol = max(viol, min(1.0, -r["slack"]))
        elif r["status"] != "satisfied":
            viol = max(viol, 1.0)
    return {"hard_fail": hard_fail, "feasible": feasible, "violation": viol}


def combined_score(goal: Goal, values: list, seed_values: list, feas: dict,
                   screen_distance: Optional[float] = None) -> float:
    """The score rule (design section 4.6)."""
    if feas["hard_fail"]:
        return 0.0
    level = goal.highest_level(values)
    if level < 0:
        # screened out before any level, or no goal value at all
        if goal.infeasible == "slack" and screen_distance is not None:
            return 0.5 * (1.0 - min(1.0, max(0.0, screen_distance)))
        return 0.0
    if not feas["feasible"]:
        if goal.infeasible == "slack":
            return 0.5 * (1.0 - min(1.0, feas["violation"]))
        return 0.0
    v = values[level]
    if goal.score_rule == "weighted" and goal.weights:
        total = 0.0
        for i, (d, e) in enumerate(goal.levels):
            w = float(goal.weights.get(e.text, 0.0))
            s = seed_values[i] if i < len(seed_values) else UNDECIDED
            if values[i] is UNDECIDED or s is UNDECIDED:
                continue
            total += w * _ratio(d, values[i], s)
        return total
    d = goal.levels[level][0]
    s = seed_values[level] if level < len(seed_values) else UNDECIDED
    if s is UNDECIDED:
        return 1.0
    return _ratio(d, v, s)


def _ratio(direction: str, v: float, seed: float) -> float:
    if direction == "minimize":
        if v == 0:
            return 1.0 if seed == 0 else 1e9
        return float(seed) / float(v)
    if seed == 0:
        return 1.0 if v == 0 else 1e9
    return float(v) / float(seed)
