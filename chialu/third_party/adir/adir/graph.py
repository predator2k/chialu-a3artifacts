"""The evaluation graph (design sections 6.1 to 6.9): node instances,
input references, the derived graph, scheduling, `when`, `map_over`,
pins and report-only nodes."""
from __future__ import annotations

import itertools
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .errors import UNDECIDED, BindError
from .expr import Expr, ParseError, as_value, condition_slack, evaluate, parse, references, to_json
from .nodes import NodeSpec, resolve_node
from .yamlfile import check_keys

NODE_KEYS = ("node", "inputs", "map_over", "when", "report_only", "pin", "resources",
             "rollback", "giveup")
REF_ROOTS = ("candidate", "artifacts", "seed", "archive", "goal", "decl", "vars", "run")
WHEN_ONLY_ROOTS = ("archive", "goal")


@dataclass
class Input:
    key: str
    expr: Optional[Expr]      # None for a literal
    literal: Any = None
    nested: dict = field(default_factory=dict)   # path tuple -> Expr, for expression leaves of a mapping or list literal

    @property
    def refs(self):
        out = list(self.expr.refs) if self.expr else []
        for e in self.nested.values():
            out += e.refs
        return out


@dataclass
class NodeInst:
    name: str
    node: str
    spec: NodeSpec
    inputs: dict = field(default_factory=dict)     # key -> Input
    map_over: dict = field(default_factory=dict)   # key -> Input
    when: list = field(default_factory=list)       # [Expr]
    report_only: bool = False
    pin: bool = False
    resources: dict = field(default_factory=dict)
    order: int = 0
    rollback: bool = False        # a violated hard row over this node retracts the call's history
    giveup: dict = field(default_factory=dict)     # {sigma, min_samples}: a mapped node's tail

    @property
    def refs(self) -> list:
        out = []
        for i in list(self.inputs.values()) + list(self.map_over.values()):
            out += i.refs
        for w in self.when:
            out += w.refs
        return out

    @property
    def data_refs(self) -> list:
        out = []
        for i in list(self.inputs.values()) + list(self.map_over.values()):
            out += i.refs
        return out

    def literal_inputs(self) -> dict:
        return {k: i.literal for k, i in self.inputs.items() if i.expr is None}

    def identity(self) -> dict:
        return {"node": self.node,
                "inputs": {k: (i.expr.text if i.expr else i.literal) for k, i in self.inputs.items()},
                "map_over": {k: (i.expr.text if i.expr else i.literal) for k, i in self.map_over.items()},
                "rollback": self.rollback, "giveup": dict(self.giveup),
                "when": [w.text for w in self.when], "report_only": self.report_only,
                "pin": self.pin, "resources": self.resources}


def root_of(ref: str) -> str:
    return ref.split(".", 1)[0]


def make_input(key: str, value, node_names, path: str) -> Input:
    """A literal, a reference or an expression. A bare identifier that
    names no known root is a literal string. A mapping or list literal
    may carry expressions at its leaves."""
    if isinstance(value, (dict, list)):
        nested = {}
        _collect_nested(value, (), node_names, path, nested)
        return Input(key, None, value, nested)
    if not isinstance(value, str):
        return Input(key, None, value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return Input(key, None, value[1:-1])        # a quoted string is a literal (a model name with `/` and `-`)
    try:
        ast = parse(value)
    except ParseError:
        return Input(key, None, value)
    refs = references(ast)
    if ast[0] == "ref":
        if root_of(refs[0]) in REF_ROOTS or root_of(refs[0]) in node_names:
            return Input(key, Expr(value))
        return Input(key, None, value)
    if ast[0] == "num":
        return Input(key, None, ast[1])
    unknown = [r for r in refs if root_of(r) not in REF_ROOTS and root_of(r) not in node_names]
    if unknown:
        if not refs or all(r == refs[0] for r in refs) and " " not in value:
            return Input(key, None, value)
        raise BindError(path, f"expression {value!r} references unknown names {unknown}")
    return Input(key, Expr(value))


def _collect_nested(value, at, node_names, path, out):
    if isinstance(value, dict):
        for k, v in value.items():
            _collect_nested(v, at + (k,), node_names, path, out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _collect_nested(v, at + (i,), node_names, path, out)
    elif isinstance(value, str):
        inp = make_input(".".join(str(a) for a in at), value, node_names, path)
        if inp.expr is not None:
            out[at] = inp.expr


def substitute_nested(literal, nested: dict, resolver):
    if not nested:
        return literal
    import copy
    out = copy.deepcopy(literal)
    for at, e in nested.items():
        cur = out
        for k in at[:-1]:
            cur = cur[k]
        cur[at[-1]] = e.value(resolver)
    return out


def parse_nodes(raw: dict, path: str = "evaluate.nodes") -> dict:
    if not isinstance(raw, dict) or not raw:
        raise BindError(path, "a non-empty mapping of node instances")
    names = set(raw)
    out = {}
    for order, (name, spec) in enumerate(raw.items()):
        p = f"{path}.{name}"
        if not isinstance(spec, dict):
            raise BindError(p, "a node instance is a mapping")
        check_keys(spec, NODE_KEYS, p)
        node_name = spec.get("node")
        if not node_name or not isinstance(node_name, str):
            raise BindError(p, "`node` names the node")
        nspec = resolve_node(node_name, f"{p}.node")
        inputs = {}
        for k, v in (spec.get("inputs") or {}).items():
            if not nspec.accepts(k):
                raise BindError(f"{p}.inputs.{k}", f"not a parameter of {node_name} "
                                                   f"(has: {sorted(nspec.params)})")
            inputs[k] = make_input(k, v, names, f"{p}.inputs.{k}")
        map_over = {}
        for k, v in (spec.get("map_over") or {}).items():
            if k in inputs:
                raise BindError(f"{p}.map_over.{k}", "also under inputs")
            if not nspec.accepts(k):
                raise BindError(f"{p}.map_over.{k}", f"not a parameter of {node_name}")
            map_over[k] = make_input(k, v, names, f"{p}.map_over.{k}")
        missing = nspec.required - set(inputs) - set(map_over)
        if missing and node_name not in ("adir.declaration",):
            raise BindError(f"{p}.inputs", f"{node_name} requires {sorted(missing)}")
        when = []
        for i, w in enumerate(spec.get("when") or []):
            if not isinstance(w, str):
                raise BindError(f"{p}.when[{i}]", "a condition is a string")
            try:
                when.append(Expr(w))
            except ParseError as e:
                raise BindError(f"{p}.when[{i}]", str(e)) from None
        giveup = spec.get("giveup") or {}
        if giveup and not map_over:
            raise BindError(f"{p}.giveup", "only a mapped node has members to give up on")
        if giveup and not isinstance(giveup, dict):
            raise BindError(f"{p}.giveup", "a mapping: {sigma, min_samples}")
        out[name] = NodeInst(name, node_name, nspec, inputs=inputs, map_over=map_over, when=when,
                             report_only=bool(spec.get("report_only", False)),
                             pin=bool(spec.get("pin", False)),
                             resources=dict(spec.get("resources") or {}), order=order,
                             rollback=bool(spec.get("rollback", False)),
                             giveup=dict(giveup))
    return out


@dataclass
class Graph:
    nodes: dict
    active: list            # node names that run, in schedule order
    edges: list             # (from, to)
    needed_by: dict         # node -> what references it

    def to_json(self) -> dict:
        return {"order": self.active, "edges": self.edges,
                "nodes": {n: self.nodes[n].identity() for n in self.active},
                "needed_by": self.needed_by}


GIVEUP_STATE = "giveup.json"


def _giveup_counters(run) -> dict:
    """`{node: {member: consecutive give-ups}}` of a run."""
    try:
        return json.loads((Path(run) / GIVEUP_STATE).read_text())
    except Exception:  # noqa: BLE001 -- no file is no give-up yet
        return {}


def _save_giveup(run, state: dict) -> None:
    try:
        (Path(run) / GIVEUP_STATE).write_text(json.dumps(state, indent=1, sort_keys=True))
    except OSError:
        pass


def _await_members(futs: list, rule: dict, run, node: str, log) -> tuple:
    """(results, members given up on) for a mapped node with a tail rule.

    The threshold comes from the members of this same call that have
    already finished, and from nothing else: a member's own past
    durations are no baseline on a machine whose load is not ours, where
    the distribution moves under us between one candidate and the next.
    The siblings ran under the load this call is running under.

    Since members are not alike -- one shape is eight times another's
    work -- a threshold over siblings would give up on the same member
    every time. Each member therefore carries a count of the calls it was
    given up on in a row, and at `max_skips` it is waited for however
    long it takes. A member is never stale by more than that many
    candidates, and nothing has to hold about the shape of the
    distribution for that to be true.
    """
    import statistics
    from concurrent.futures import wait, FIRST_COMPLETED
    sigma = float(rule.get("sigma") or 3.0)
    max_skips = int(rule.get("max_skips") or 2)
    min_done = max(2, int(rule.get("min_done") or 2))
    counters = _giveup_counters(run) if run else {}
    mine = dict(counters.get(node) or {})

    started = time.time()
    pending = {f: key for key, f in futs}
    done_at: dict = {}
    results, gave_up = [], []
    while pending:
        finished, _ = wait(list(pending), timeout=1.0, return_when=FIRST_COMPLETED)
        now = time.time()
        for f in finished:
            key = pending.pop(f)
            done_at[key] = now - started
            results.append((key, f.result()))
            mine[key] = 0
        if not pending:
            break
        if len(done_at) < min_done:
            continue
        xs = list(done_at.values())
        cut = statistics.fmean(xs) + sigma * (statistics.stdev(xs) if len(xs) > 1 else 0.0)
        for f, key in list(pending.items()):
            if now - started <= cut:
                continue
            if int(mine.get(key, 0)) >= max_skips:
                continue                      # its turn to be waited for, whatever it costs
            pending.pop(f)
            mine[key] = int(mine.get(key, 0)) + 1
            gave_up.append(key)
            log(f"{node}: gave up waiting on {key} after {now - started:.0f}s "
                f"(cut {cut:.0f}s, {mine[key]}/{max_skips} in a row)")
    if run:
        counters[node] = mine
        _save_giveup(run, counters)
    return results, gave_up


def holds(v) -> bool:
    """Whether a `when` entry holds.

    The truth a constraint row `eq: true` would accept over the same
    expression, and for the same reason: section 4.5's aggregates return
    numbers, so `min` over a mapping of booleans is `1`, and an identity
    test against `True` refused it. A node conditioned on every member of
    a mapped check then never ran, and the message said only `is 1`.
    Nothing else holds -- `2`, a string and `UNDECIDED` alike -- so a
    numeric expression still has to be compared before it gates a node.
    """
    v = as_value(v)
    if v is True:
        return True
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == 1


def derive_graph(nodes: dict, roots: list, hard_order: dict, path="evaluate") -> Graph:
    """The nodes the goal, the constraints, `feedback`, `report` and the
    `when` conditions reference, plus their transitive inputs, in
    schedule order."""
    needed: dict = {}
    stack = [(root_of(r), src) for r, src in roots if root_of(r) in nodes]
    while stack:
        n, src = stack.pop()
        if n in needed:
            needed[n].add(src)
            continue
        needed[n] = {src}
        for r in nodes[n].refs:
            rn = root_of(r)
            if rn in nodes:
                stack.append((rn, f"node {n}"))
    edges = []
    for n in needed:
        for r in nodes[n].data_refs:
            rn = root_of(r)
            if rn in nodes and rn != n:
                edges.append((rn, n))
            if rn == n:
                raise BindError(f"{path}.nodes.{n}", "a node references itself")
    deps = {n: {a for a, b in edges if b == n} | {root_of(r) for w in nodes[n].when
                                                for r in w.refs if root_of(r) in nodes}
            for n in needed}
    order = []
    remaining = set(needed)
    while remaining:
        ready = [n for n in remaining if deps[n] <= set(order)]
        if not ready:
            raise BindError(f"{path}.nodes", f"a cycle among {sorted(remaining)}")
        ready.sort(key=lambda n: (n != "declaration" and nodes[n].node != "adir.declaration",
                                  hard_order.get(n, 10 ** 6), nodes[n].order))
        order.append(ready[0])
        remaining.discard(ready[0])
    return Graph(nodes, order, edges, {n: sorted(s) for n, s in needed.items()})


class Runner:
    """Runs the graph for one candidate. `resolver` answers every
    reference; `outputs` collects node outputs; `on_node_done` evaluates
    the hard constraints that became decidable."""

    def __init__(self, graph: Graph, executor, resolver, pins: dict, on_node_done=None,
                 mode: str = "evaluate", log=None):
        self.graph = graph
        self.executor = executor
        self.resolver = resolver
        self.pins = pins
        self.on_node_done = on_node_done
        self.mode = mode
        self.outputs: dict = {}
        self.skipped: dict = {}
        self.node_hashes: dict = {}
        self.screen_distance: Optional[float] = None
        self.cancelled = False
        self.gave_up: dict = {}        # node -> [member] the tail rule stopped waiting for
        self.carry_from: dict = {}     # the measurements a given-up member is carried at
        self.run_dir = getattr(resolver, "run", None)   # `run` is this class's own method
        self.log = log or (lambda *a: None)

    def _value(self, inp: Input):
        if inp.expr is None:
            return substitute_nested(inp.literal, inp.nested, self.resolver)
        return inp.expr.value(self.resolver)

    def _deps(self) -> dict:
        """node -> the active nodes it waits for: its data inputs, the
        nodes its `when` conditions read, and, for a `goal.<n>`
        reference, the nodes of that goal level."""
        nodes = self.graph.nodes
        active = set(self.graph.active)
        goal = getattr(self.resolver.instance, "goal", None)
        deps = {}
        for n in self.graph.active:
            d = {a for a, b in self.graph.edges if b == n}
            for w in nodes[n].when:
                for r in w.refs:
                    root = root_of(r)
                    if root in active:
                        d.add(root)
                    elif root == "goal" and goal is not None:
                        parts = r.split(".")
                        lvl = int(parts[1]) - 1 if len(parts) > 1 and parts[1].isdigit() else 0
                        if 0 <= lvl < len(goal.levels):
                            d |= {root_of(g) for g in goal.levels[lvl][1].refs if root_of(g) in active}
            deps[n] = (d & active) - {n}
        return deps

    def run(self):
        """Every node whose dependencies are settled starts at once (on
        the executor's worker threads); a hard failure cancels the nodes
        not yet started and drops the results of the running ones."""
        from concurrent.futures import FIRST_COMPLETED, wait
        nodes = self.graph.nodes
        deps = self._deps()
        pending = list(self.graph.active)
        done: set = set()
        running: dict = {}
        while pending or running:
            if self.cancelled:
                for n in pending:
                    self.skipped[n] = "cancelled by a hard failure"
                pending = []
                for fut in running:
                    fut.cancel()
                break
            started = []
            for n in pending:
                if not deps[n] <= done:
                    continue
                ni = nodes[n]
                started.append(n)
                if ni.report_only and self.mode != "report":
                    self.skipped[n] = "report_only"
                    done.add(n)
                    continue
                if not ni.report_only and self.mode == "report":
                    done.add(n)
                    continue
                prep = self._prepare(ni)
                if prep is None:
                    done.add(n)
                    if self.on_node_done and self.on_node_done(n) is False:
                        self.cancelled = True
                        break
                    continue
                kwargs, grid = prep
                submit = getattr(self.executor, "submit", None)
                if submit is None:
                    self.outputs[n] = self._invoke(ni, kwargs, grid)
                    done.add(n)
                    if self.on_node_done and self.on_node_done(n) is False:
                        self.cancelled = True
                        break
                    continue
                running[submit(self._invoke, ni, kwargs, grid)] = n
            pending = [n for n in pending if n not in started]
            if self.cancelled:
                continue
            if not running:
                for n in pending:
                    self.skipped[n] = "a dependency never ran"
                break
            finished, _ = wait(list(running), return_when=FIRST_COMPLETED)
            for fut in finished:
                n = running.pop(fut)
                try:
                    self.outputs[n] = fut.result()
                except Exception as e:  # noqa: BLE001
                    from .nodes import InfrastructureError, is_infra_error
                    if is_infra_error(e):
                        for f in running:
                            f.cancel()
                        raise e if isinstance(e, InfrastructureError) else InfrastructureError(f"{n}: {type(e).__name__}: {e}")
                    self.skipped[n] = f"failed: {e}"
                    self.outputs[n] = {"ok": False, "detail": f"{type(e).__name__}: {e}"}
                done.add(n)
                if self.on_node_done and not self.cancelled:
                    if self.on_node_done(n) is False:
                        self.cancelled = True
        return self.outputs

    def _prepare(self, ni: NodeInst):
        """None when the node's output is settled here (a `when` that
        does not hold, an undecided input, a builtin node), else the
        (kwargs, map_over grid) the executor runs."""
        name = ni.name
        for w in ni.when:
            try:
                ok = w.value(self.resolver)
            except Exception as e:  # noqa: BLE001
                ok = UNDECIDED
                self.log(f"{name}: when {w.text}: {e}")
            if not holds(ok):
                self.skipped[name] = f"when {w.text} is {as_value(ok)!r}"
                if as_value(ok) is not UNDECIDED:
                    try:
                        self.screen_distance = condition_slack(w.ast, self.resolver)
                    except Exception:  # noqa: BLE001
                        self.screen_distance = 1.0
                self.outputs[name] = UNDECIDED
                return None
        try:
            kwargs = {k: self._value(i) for k, i in ni.inputs.items()}
            grid = {k: self._value(i) for k, i in ni.map_over.items()}
        except Exception as e:  # noqa: BLE001
            self.skipped[name] = f"input: {e}"
            self.outputs[name] = UNDECIDED
            return None
        if any(as_value(v) is UNDECIDED for v in kwargs.values()) or \
                any(as_value(v) is UNDECIDED for v in grid.values()):
            self.skipped[name] = "an input is UNDECIDED"
            self.outputs[name] = UNDECIDED
            return None
        kwargs = {k: to_json(v) for k, v in kwargs.items()}
        if ni.node == "adir.declaration":
            self.outputs[name] = self.resolver.declaration_outputs()
            self.node_hashes[name] = "declaration"
            return None
        if ni.node == "adir.instance":
            from .subinstance import run_subinstance
            self.outputs[name] = run_subinstance(self.resolver.instance, self.resolver.run, kwargs)
            self.node_hashes[name] = "instance"
            return None
        return kwargs, grid

    def _invoke(self, ni: NodeInst, kwargs: dict, grid: dict) -> dict:
        """The node's output dict: one call, or the map_over product
        merged output by output."""
        name = ni.name
        try:
            if grid:
                keys = list(grid)
                lists = []
                for k in keys:
                    v = grid[k]
                    if isinstance(v, dict):
                        v = list(v.values())
                    if not isinstance(v, (list, tuple)):
                        raise RuntimeError(f"map_over {k} is not a list")
                    lists.append(list(v))
                calls = []
                for combo in itertools.product(*lists):
                    kw = dict(kwargs)
                    kw.update({k: to_json(v) for k, v in zip(keys, combo)})
                    calls.append((".".join(str(v) for v in combo), kw))
                # Section 6.8 gives every member its own run, hash and cache entry, so
                # the product is independent work; running it serially made a mapped
                # node the width of one call however wide the executor was.
                submit = getattr(self.executor, "submit_member", None)
                if submit is None:
                    results = [(key, self._call(ni, kw, pin_key=f"{name}.{key}"))
                               for key, kw in calls]
                elif ni.giveup and len(calls) > 1:
                    futs = [(key, submit(self._call, ni, kw, f"{name}.{key}"))
                            for key, kw in calls]
                    results, gave_up = _await_members(futs, ni.giveup, self.run_dir, name, self.log)
                    if gave_up:
                        self.gave_up.setdefault(name, []).extend(gave_up)
                else:
                    futs = [(key, submit(self._call, ni, kw, f"{name}.{key}"))
                            for key, kw in calls]
                    results = [(key, f.result()) for key, f in futs]
                merged: dict = {}
                for key, out in results:
                    for ok_, ov in out.items():
                        merged.setdefault(ok_, {})[key] = ov
                return merged
            return self._call(ni, kwargs)
        except Exception as e:  # noqa: BLE001
            from .nodes import InfrastructureError, is_infra_error
            if is_infra_error(e):
                # ray failed, not the candidate: no output is recorded, the evaluation is repeated
                raise e if isinstance(e, InfrastructureError) else InfrastructureError(f"{name}: {type(e).__name__}: {e}")
            self.skipped[name] = f"failed: {e}"
            self.log(f"{name}: {type(e).__name__}: {e}")
            return {"ok": False, "detail": f"{type(e).__name__}: {e}"}

    def _call(self, ni: NodeInst, kwargs: dict, pin_key: Optional[str] = None) -> dict:
        """`pin_key` is the node name, or `<node>.<member>` for one run of
        a mapped node: section 6.8 gives every member its own hash and
        provenance, and a single key per node would let each member of the
        product overwrite the pin before the next one reads it."""
        from .nodes import content_key
        h = content_key(ni.node, kwargs)
        key = pin_key or ni.name
        self.node_hashes[key] = h
        if ni.pin:
            pinned = self.pins.get(key)
            if pinned and pinned.get("hash") == h:
                return pinned["outputs"]
            out = self.executor.run(ni.spec, kwargs)
            self.pins[key] = {"hash": h, "outputs": out}
            return out
        return self.executor.run(ni.spec, kwargs)
