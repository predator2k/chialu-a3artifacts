"""Numeric backends over space.json (design section 9.2): a candidate
is a declaration block alone. `random` and `grid` are built in; `smac`
(SMAC3) and `nsga2` (pymoo) drive the same evaluator through the
libraries of those names. Backend keys pass through under
`search.numeric`."""
from __future__ import annotations

import itertools
import json
import random
from typing import Optional
import time
from pathlib import Path

from ..domains import sample_from_json
from ..errors import BindError
from ..evaluate import candidate_from_program, declaration_program, evaluate_candidate
from ..instance import Instance
from ..nodes import Executor
from ..variables import ABSENT, _pick, admissible_members, binding_lookup, default_under, member_exclusions


def _sibling_lookup(inst: Instance, vals: dict):
    """The lookup of a member condition over a partial assignment: a
    searched sibling the assignment holds is decided, one it lacks is
    absent (inactive, or not yet reached in the order)."""
    return binding_lookup(inst.bindings, lambda n: vals[n] if n in vals else ABSENT)


def _active(var, inst, vals, active, lookup=None):
    """A fixed intermediate child does not reopen an inactive ancestor; a variable whose `inactive_when`
    clause holds over the values drawn so far is inactive too. `lookup` is `_sibling_lookup(inst, vals)`
    when the caller holds one (it reads `vals` live, so one per draw serves every variable)."""
    if var.inactive_when and var.inactive(lookup or _sibling_lookup(inst, vals)):
        return False
    if var.when is None:
        return True
    parent = var.when[0]
    if parent not in active:
        return False
    binding = inst.bindings.get(parent)
    if binding.time == "runtime":
        return any(var.condition_holds(m) for m in binding.members)
    value = vals.get(parent) if binding.time == "search" else binding.value
    return value is not None and var.condition_holds(value)


def activation_path(inst: Instance, name: str, value, rng: random.Random) -> Optional[dict]:
    """{variable: value} that sets `name` to `value` and each of its ancestors to a member (drawn at random
    among those admitting the child) that opens it, or None when some ancestor has no such searched member.
    Sibling conditions (`inactive_when`, member conditions) are not solved here: a caller samples with the
    path forced and checks that `name` came out active with `value`. None too when an `inactive_when` clause
    of `name` or an ancestor holds whatever the path draws (`_surely_inactive`): no draw could set it."""
    forced = {name: value}
    options = {name: [value]}
    by_name = _vars_by_name(inst)
    var = by_name.get(name)
    chain = []
    while var is not None:
        chain.append(var)
        if var.when is None:
            break
        parent = var.when[0]
        pb = inst.bindings.get(parent)
        if pb is None:
            return None
        if pb.time == "fixed":
            if not var.condition_holds(pb.value):
                return None
        elif pb.time == "search":
            if not pb.domain.finite():
                return None
            ok = [m for m in pb.domain.members() if var.condition_holds(m)]
            if not ok:
                return None
            forced[parent] = rng.choice(ok)
            options[parent] = ok
        else:
            if not any(var.condition_holds(m) for m in pb.members):
                return None
        var = by_name.get(parent)
    # checked after the walk, so the draws from `rng` are those of a path that is kept
    if any(_surely_inactive(inst, v, forced, options, by_name) for v in chain):
        return None
    return forced


def _vars_by_name(inst: Instance) -> dict:
    order = inst.variable_order()
    cache = getattr(inst, "_var_by_name", None)
    if cache is None or cache[0] != len(order):
        cache = (len(order), {v.name: v for v in order})      # constant-time ancestor lookups (fp: 25k variables)
        inst._var_by_name = cache
    return cache[1]


def _surely_inactive(inst: Instance, var, forced: dict, options: dict, by_name: dict) -> bool:
    """Whether an `inactive_when` clause of `var` holds in every declaration that sets the `forced` values:
    each term's sibling is on the path with every member the path could draw for it (`options`) within the
    clause's members, fixed or run-time within them, or a searched sibling that is
    surely active (no `inactive_when` of its own, its parent forced or fixed at a member that opens it) and
    whose whole domain lies within them. E.g. `modulus_value` is inactive under end_around_carry unless
    `modulus` is generic_p_correction, and narrow widths drop that member from `modulus`'s domain: forcing
    every value of 3..4095 would cost a few draws each and never set one. False when unsure."""
    def holds(sib, allowed):
        if sib in options:
            return all(_in(allowed, m) for m in options[sib])
        b = inst.bindings.get(sib)
        if b is None:
            return False
        if b.time == "fixed":
            return _in(allowed, b.value)
        if b.time == "runtime":
            return all(_in(allowed, x) for x in b.members)
        sv = by_name.get(sib)
        if sv is None or sv.inactive_when or not b.domain.finite():
            return False
        if sv.when is not None:
            parent = sv.when[0]
            if parent in options:
                pvs = options[parent]
            else:
                pb = inst.bindings.get(parent)
                pvar = by_name.get(parent)
                if pb is None or pb.time != "fixed" or pvar is None or pvar.when is not None:
                    return False
                pvs = [pb.value]
            if not all(sv.condition_holds(pv) for pv in pvs):
                return False
        return all(_in(allowed, m) for m in b.domain.members())
    return any(all(holds(sib, allowed) for sib, allowed in clause) for clause in var.inactive_when)


def _in(values, v) -> bool:
    return any(v == x for x in values)


def sample_declaration(inst: Instance, rng: random.Random, forced: Optional[dict] = None) -> dict:
    """One declaration: parents before children, inactive children
    absent, a conditioned member drawn only where the values already
    drawn admit it. `forced` fixes some variables to given members where they are active and admit them
    (coverage sampling: activation_path)."""
    vals, active = {}, set()
    forced = forced or {}
    lookup = _sibling_lookup(inst, vals)
    for var in inst.variable_order():
        b = inst.bindings.get(var.name)
        if b is None or not _active(var, inst, vals, active, lookup):
            continue
        active.add(var.name)
        if b.time != "search":
            continue
        if var.name in forced:
            want = forced[var.name]
            if b.domain.contains(want) and (not var.member_when or not b.domain.finite()
                                            or want in admissible_members(var, b.domain, lookup)):
                vals[var.name] = want
                continue
        if var.member_when and b.domain.finite():
            vals[var.name] = rng.choice(admissible_members(var, b.domain, lookup))
        else:
            vals[var.name] = b.domain.sample(rng)
    return vals


def grid_declarations(inst: Instance, limit: int) -> list:
    searched = [inst.bindings[v.name] for v in inst.searched()]
    for b in searched:
        if not b.domain.finite():
            raise BindError("search.backend", f"grid needs finite domains ({b.name} is not)")
    names = [b.name for b in searched]
    out = []
    for combo in itertools.product(*[b.domain.members() for b in searched]):
        vals = dict(zip(names, combo))
        out.append(_prune(inst, vals))
        if len(out) >= limit:
            break
    return out


def _prune(inst: Instance, vals: dict) -> dict:
    """The active subset of a full assignment: a conditional child stays
    only when its parent's value admits it, and a member the other values
    exclude is repaired to the first member they admit."""
    out, active = {}, set()
    for var in inst.variable_order():
        if not _active(var, inst, out, active):
            continue
        active.add(var.name)
        if var.name not in vals:
            continue
        v = vals[var.name]
        if var.member_when:
            b = inst.bindings.get(var.name)
            dom = b.domain if b is not None and b.time == "search" else var.domain
            lookup = _sibling_lookup(inst, out)
            if _pick(member_exclusions(var, dom, lookup), v) is not None:
                v = default_under(var, dom, lookup)
        out[var.name] = v
    return out


class _Loop:
    """What every numeric backend shares: the evaluation of one
    declaration into a record, the stop rules, the counters."""

    def __init__(self, inst: Instance, run_dir: Path, executor, log, on_record):
        self.inst = inst
        self.run_dir = Path(run_dir)
        self.executor = executor or Executor(self.run_dir / "cache")
        self.log = log
        self.on_record = on_record
        self.archive = inst.archive(self.run_dir)
        s = inst.search
        self.n = int(s.get("iterations", 100))
        self.plateau = int((s.get("stop") or {}).get("plateau_iterations") or 0)
        self.wall = float((s.get("budget") or {}).get("wall_hours") or 0) * 3600
        self.t0 = time.time()
        self.best = None
        self.since = 0
        self.done = 0
        self.stop_reason = None

    def evaluate(self, vals: dict, operator: str) -> dict:
        program = declaration_program(self.inst, vals)
        cand = candidate_from_program(self.inst, program, iteration=self.done + 1,
                                      meta={"operator": operator})
        rec = evaluate_candidate(self.inst, self.run_dir, cand, archive=self.archive,
                                 executor=self.executor, log=self.log)
        self.done += 1
        if self.on_record:
            self.on_record(rec)
        score = rec["score"]["combined_score"]
        if self.best is None or score > self.best + 1e-12:
            self.best, self.since = score, 0
        else:
            self.since += 1
        return rec

    def should_stop(self) -> bool:
        if self.stop_reason:
            return True
        if self.wall and time.time() - self.t0 > self.wall:
            self.stop_reason = "wall budget"
        elif self.plateau and self.since >= self.plateau:
            self.stop_reason = "plateau"
        elif self.done >= self.n:
            self.stop_reason = "iterations"
        return self.stop_reason is not None

    def result(self) -> dict:
        return {"iterations": self.done, "best_score": self.best, "stopped_by": self.stop_reason}


def run(inst: Instance, run_dir: Path, executor=None, log=None, on_record=None) -> dict:
    backend = inst.backend
    loop = _Loop(inst, run_dir, executor, log, on_record)
    if backend == "smac":
        return _smac(inst, loop)
    if backend == "nsga2":
        return _nsga2(inst, loop)
    rng = random.Random(int((inst.search.get("numeric") or {}).get("seed", 0)))
    decls = grid_declarations(inst, loop.n) if backend == "grid" else None
    for it in range(loop.n):
        if loop.should_stop():
            break
        if decls is not None and it >= len(decls):
            loop.stop_reason = "grid exhausted"
            break
        vals = decls[it] if decls is not None else sample_declaration(inst, rng)
        loop.evaluate(vals, backend)
    return loop.result()


# ------------------------------------------------------------ the search space for the libraries

def _searched(inst: Instance) -> list:
    return [inst.bindings[v.name] for v in inst.searched()]


def _encode(member) -> str:
    """A domain member as the string the libraries carry (a dict or a
    list member is its JSON)."""
    if isinstance(member, (dict, list)):
        return json.dumps(member, sort_keys=True)
    return json.dumps(member)


def _decode(text):
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return text


def _condition(inst: Instance, b) -> tuple:
    """(parent name, parent values) of a searched conditional whose
    parent is searched too, else None."""
    var = b.variable
    if var.when is None:
        return None
    parent = inst.bindings.get(var.when[0])
    if parent is None or parent.time != "search":
        return None
    values = [m for m in parent.domain.members() if var.condition_holds(m)] if parent.domain.finite() else []
    return (var.when[0], values)


def _seed_values(inst: Instance) -> list:
    """The seeds' declarations as the initial design."""
    from ..seeds import seed_programs
    from ..declaration import parse_block
    out = []
    try:
        for name, program in seed_programs(inst):
            d = parse_block(program)
            if d.present:
                out.append(dict(d.vars))
    except BindError:
        pass
    return out


def _cost(inst: Instance, rec: dict):
    """The minimization objectives of a record: the goal values in
    minimize form under a Pareto goal, else the negated score. An
    infeasible or failed candidate takes a penalty."""
    if inst.goal.kind == "pareto":
        out = []
        for (d, _), v in zip(inst.goal.levels, rec.get("goal_values") or []):
            if v is None or rec["hard_fail"] or not rec["feasible"]:
                out.append(1e9)
            else:
                out.append(float(v) if d == "minimize" else -float(v))
        return out
    return [-float(rec["score"]["combined_score"])]


# ------------------------------------------------------------ SMAC3

def _smac(inst: Instance, loop: _Loop) -> dict:
    try:
        from ConfigSpace import (Categorical, Configuration, ConfigurationSpace, Float, ForbiddenAndConjunction,
                                 ForbiddenEqualsClause, ForbiddenInClause, InCondition, Integer)
        from smac import HyperparameterOptimizationFacade, Scenario
    except ImportError:
        raise BindError("search.backend", "smac needs the smac and ConfigSpace packages (pip install smac); "
                                          "random or grid run without them") from None
    numeric = inst.search.get("numeric") or {}
    cs = ConfigurationSpace(seed=int(numeric.get("seed", 0)))
    hps = {}
    for b in _searched(inst):
        dom = b.domain
        name = b.name
        if dom.finite() and (getattr(dom, "kind", "") != "range" or len(dom.members()) <= 256):
            hps[name] = Categorical(name, [_encode(m) for m in dom.members()])
        else:
            j = dom.to_json()
            lo, hi = j.get("lower", j.get("min")), j.get("upper", j.get("max"))
            if j.get("type") in ("uniform_int", "int") or isinstance(lo, int) and isinstance(hi, int) and not j.get("step"):
                hps[name] = Integer(name, (int(lo), int(hi)))
            else:
                hps[name] = Float(name, (float(lo), float(hi)))
    cs.add(list(hps.values()))
    for b in _searched(inst):
        cond = _condition(inst, b)
        if cond and cond[1]:
            parent, values = cond
            cs.add(InCondition(hps[b.name], hps[parent], [_encode(v) for v in values]))
    # a member condition: the member is forbidden together with a disallowed sibling value (a searched
    # sibling), or outright where a fixed or runtime sibling never allows it
    for b in _searched(inst):
        for m, (sib, allowed, _doc) in (b.variable.member_when or {}).items():
            if not b.domain.contains(m) or type(hps[b.name]).__name__ != "CategoricalHyperparameter":
                continue
            member = ForbiddenEqualsClause(hps[b.name], _encode(m))
            sb = inst.bindings.get(sib)
            if sb is not None and sb.time == "search" and sib in hps and sb.domain.finite():
                disallowed = [x for x in sb.domain.members() if not any(x == a for a in allowed)]
                if disallowed:
                    cs.add(ForbiddenAndConjunction(member, ForbiddenInClause(hps[sib], [_encode(x) for x in disallowed])))
            elif _pick(member_exclusions(b.variable, b.domain, binding_lookup(inst.bindings)), m) is not None:
                cs.add(member)

    categorical = {name for name, hp in hps.items() if type(hp).__name__ == "CategoricalHyperparameter"}

    def to_vals(config) -> dict:
        vals = {}
        for name in hps:
            if name not in config or config[name] is None:
                continue
            v = config[name]
            vals[name] = _decode(str(v)) if name in categorical else (int(v) if isinstance(v, (int,)) or float(v).is_integer() and name in hps and type(hps[name]).__name__ == "UniformIntegerHyperparameter" else float(v))
        return _prune(inst, vals)

    objectives = [f"goal.{i + 1}" for i in range(len(inst.goal.levels))] \
        if inst.goal.kind == "pareto" else "cost"
    out = loop.run_dir / "smac"
    scenario = Scenario(cs, name="adir", output_directory=out, deterministic=True,
                        n_trials=loop.n, seed=int(numeric.get("seed", 0)), objectives=objectives,
                        walltime_limit=loop.wall or float("inf"))

    def target(config, seed: int = 0):
        if loop.should_stop():
            raise RuntimeError("stopped")
        rec = loop.evaluate(to_vals(config), "smac")
        c = _cost(inst, rec)
        if inst.goal.kind == "pareto":
            return dict(zip(objectives, c))
        return c[0]

    additional = []
    for vals in _seed_values(inst):
        try:
            additional.append(Configuration(cs, values={k: (_encode(v) if k in categorical else v)
                                                        for k, v in vals.items() if k in hps}))
        except Exception:  # noqa: BLE001
            continue
    init = HyperparameterOptimizationFacade.get_initial_design(
        scenario, n_configs=int(numeric.get("initial_design_size", min(10, max(1, loop.n // 4)))),
        additional_configs=additional)
    facade = HyperparameterOptimizationFacade(scenario, target, initial_design=init, overwrite=True,
                                              logging_level=40)
    try:
        facade.optimize()
    except RuntimeError as e:
        if "stopped" not in str(e):
            raise
    loop.should_stop()
    return loop.result()


# ------------------------------------------------------------ NSGA-II (pymoo)

def _nsga2(inst: Instance, loop: _Loop) -> dict:
    try:
        import numpy as np
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.core.mixed import (MixedVariableDuplicateElimination, MixedVariableMating,
                                      MixedVariableSampling)
        from pymoo.core.population import Population
        from pymoo.core.problem import ElementwiseProblem
        from pymoo.core.variable import Choice, Integer, Real
        from pymoo.optimize import minimize
    except ImportError:
        raise BindError("search.backend", "nsga2 needs the pymoo package (pip install pymoo); "
                                          "random or grid run without it") from None
    numeric = inst.search.get("numeric") or {}
    variables = {}
    for b in _searched(inst):
        dom = b.domain
        if dom.finite() and (getattr(dom, "kind", "") != "range" or len(dom.members()) <= 256):
            variables[b.name] = Choice(options=[_encode(m) for m in dom.members()])
        else:
            j = dom.to_json()
            lo, hi = j.get("lower", j.get("min")), j.get("upper", j.get("max"))
            if isinstance(lo, int) and isinstance(hi, int) and not j.get("step"):
                variables[b.name] = Integer(bounds=(int(lo), int(hi)))
            else:
                variables[b.name] = Real(bounds=(float(lo), float(hi)))
    n_obj = len(inst.goal.levels) if inst.goal.kind == "pareto" else 1

    def to_vals(x: dict) -> dict:
        vals = {k: (_decode(v) if isinstance(variables[k], Choice) else v) for k, v in x.items()}
        return _prune(inst, vals)

    class Problem(ElementwiseProblem):
        def __init__(self):
            super().__init__(vars=variables, n_obj=n_obj, n_ieq_constr=1)

        def _evaluate(self, x, out, *args, **kwargs):
            if loop.should_stop():
                out["F"] = [1e9] * n_obj
                out["G"] = [1.0]
                return
            rec = loop.evaluate(to_vals(x), "nsga2")
            out["F"] = _cost(inst, rec)
            out["G"] = [0.0 if rec["feasible"] else 1.0]

    problem = Problem()
    pop_size = int(numeric.get("population", max(4, min(20, loop.n // 2 or 4))))
    seeds = []
    for vals in _seed_values(inst):
        x = {}
        for k, var in variables.items():
            if k in vals:
                x[k] = _encode(vals[k]) if isinstance(var, Choice) else vals[k]
            else:
                x[k] = var.options[0] if isinstance(var, Choice) else var.bounds[0]
        seeds.append(x)
    sampling = MixedVariableSampling()
    if seeds:
        rest = sampling.do(problem, max(0, pop_size - len(seeds)))
        init = Population.new("X", np.array(seeds + [dict(r.X) for r in rest], dtype=object))
        sampling = init
    algorithm = NSGA2(pop_size=pop_size, sampling=sampling,
                      mating=MixedVariableMating(eliminate_duplicates=MixedVariableDuplicateElimination()),
                      eliminate_duplicates=MixedVariableDuplicateElimination())
    minimize(problem, algorithm, termination=("n_evals", loop.n), seed=int(numeric.get("seed", 0)),
             verbose=False)
    loop.should_stop()
    return loop.result()
