"""The instance (design section 2): the bind order from a run file to a
checked instance, its hashes, and the contexts the domain's hooks
receive."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from . import artifacts as A
from .archive import Archive
from .errors import BindError
from .expr import Expr, ParseError
from .graph import Graph, NodeInst, derive_graph, parse_nodes, root_of, WHEN_ONLY_ROOTS
from .metrics import Constraint, Goal, parse_constraints, parse_goal
from .registry import Elaboration, Template, get_template, TOOLS, PRIORS, PROMPT_SOURCES, TACTIC_SOURCES
from .variables import (Binding, Bindings, Variable, VariableTree, bind_variables, expand_presets,
                        space_json, _topological)
from .yamlfile import check_keys, load as load_yaml

TOP_KEYS = ("module", "run_dir", "variables", "artifacts", "evaluate", "constraints",
            "goal", "knowledge", "task", "role", "search", "archive")
TASK_KEYS = ("context", "script", "author")
ROLE_KEYS = ("file", "script")
TASK_AUTHORS = ("discover",)
PROMPTS_KEYS = ("variants", "sample", "sources", "window", "log", "declarations", "omit_vars")
INSTRUCTION_KEYS = ("enabled", "slot", "seed", "propose", "select", "window", "max_chars")
PROPOSE_KEYS = ("role", "every", "from")
OPERATORS_KEYS = ("override",)
EVAL_KEYS = ("nodes", "feedback", "report")
SEARCH_KEYS = ("backend", "iterations", "parallel", "parallel_nodes", "retries", "diff_mode",
               "max_solution_bytes", "eval_timeout_s", "llm_timeout_s", "max_tokens",
               "checkpoint_interval", "random_seed", "attempts", "database", "numeric", "seeds", "operators", "context",
               "prompts", "tactics", "instructions", "models", "tools", "budget", "stop", "replan",
               "history",
               # A block ADIR never reads, for whatever the project on top of it needs to state
               # per run file. `check_keys` is strict everywhere else, which catches a misspelled
               # key rather than silently ignoring it, so a downstream concept gets one clearly
               # marked place instead of a name in this list that ADIR cannot explain.
               "extensions")
SEED_KEYS = ("generated", "files", "discover", "rank", "discovered")
ARCHIVE_KEYS = ("store", "path", "shared", "query_tool", "keep_transcripts", "report")
LLM_BACKENDS = ("adaevolve", "evox", "topk", "beam_search", "best_of_n", "openevolve", "gepa",
                "shinkaevolve", "claude_code")
NUMERIC_BACKENDS = ("random", "smac", "nsga2", "grid")
BUILTIN_TACTICS = ("unexplored_values", "worst_constraint")
MODEL_KEYS = ("agent", "model", "provider", "small_model", "effort", "weight", "timeout_s", "retries", "work_dir",
              "max_output_tokens")
AGENT_RESOURCES = {"claude": "claude_creds", "codex": "codex_creds", "opencode": "opencode_creds"}


@dataclass
class BindContext:
    """What generators, the seed generator and line-kind checks
    receive."""
    instance: "Instance"
    run_dir: Optional[Path] = None
    candidate: Any = None
    declaration: Any = None

    @property
    def bindings(self) -> dict:
        return self.instance.bindings

    @property
    def elaboration(self) -> Elaboration:
        return self.instance.elaboration

    @property
    def template(self) -> Template:
        return self.instance.template

    def value(self, name: str):
        """The fixed value or the provisioned members of a variable."""
        b = self.instance.bindings.get(name)
        if b is None:
            raise KeyError(name)
        if b.time == "fixed":
            return b.value
        if b.time == "runtime":
            return list(b.members)
        raise KeyError(f"{name} is searched; read it from the declaration")

    def values(self, name: str) -> list:
        """The list form: [value] for fixed, the members for runtime."""
        b = self.instance.bindings.get(name)
        if b is None:
            raise KeyError(name)
        return b.possible_values()

    def has(self, name: str) -> bool:
        return name in self.instance.bindings

    def artifact_text(self, path: str, member: str = "") -> str:
        return self.instance.artifacts[path].texts[member]


class Instance:
    def __init__(self):
        self.path: Path = Path(".")
        self.base_dir: Path = Path(".")
        self.cluster: dict = {}
        self.raw: dict = {}
        self.missing_env: set = set()
        self.template: Template = None
        self.tree: VariableTree = None    # the template variables, materialized lazily into bindings
        self.bindings: dict = {}
        self._space = None
        self._variables_expanded = False
        self.elaboration: Elaboration = Elaboration()
        self.artifacts: dict = {}
        self.nodes: dict = {}
        self.feedback: list = []
        self.report: list = []
        self.constraints: list = []
        self.goal: Goal = None
        self.knowledge: str = ""          # the knowledge base directory, resolved
        self.task_text: str = ""          # the instance's task file
        self.task: dict = {}
        self.role_text: str = ""          # the role file: who the model is, the system text's first section
        self.role: dict = {}
        self.search: dict = {}
        self.archive_cfg: dict = {}
        self.run_dir: Path = Path("run")
        self.graph: Graph = None
        self.hashes: dict = {}
        self.requirements: list = []

    # ---------------------------------------------------------- helpers
    @property
    def variables(self) -> list:
        """Every bound variable, including conditional branches the defaults close.

        Binding remains lazy until enumeration, but enumerating the search space
        must not depend on earlier declarations, lookups, or the backend.
        """
        if self.tree is not None and not self._variables_expanded:
            for var in self.tree.expand_all():
                self.bindings.materialize(var.name)
            self._variables_expanded = True
        return [b.variable for b in self.bindings.values()]

    def variable_order(self) -> list:
        # the complete tree has tens of thousands of variables (fp_alu_cmp: 25,077) and a sampler asks for
        # the order once per draw: sort once, and again only if a later binding adds a variable
        n = len(self.bindings)
        if getattr(self, "_order_cache", None) is None or self._order_cache[0] != n:
            self._order_cache = (n, _topological(self.variables))
        return list(self._order_cache[1])

    @property
    def space(self) -> dict:
        """The complete bound feature model, with conditional activity preserved."""
        if self._space is None:
            self._space = space_json(self.variables, self.bindings)
        return self._space

    @space.setter
    def space(self, value):
        self._space = value

    def searched(self) -> list:
        return [v for v in self.variables if self.bindings[v.name].time == "search"]

    def seed_artifacts(self) -> list:
        return [a for a in self.artifacts.values() if a.role == "seed"]

    @property
    def agent_dir(self) -> Path:
        """The coding agent's directory, `<run>/agent`: the knowledge base
        and the programs of its calls are linked there, and the prompts
        name nothing else (design section 7.7). A run inside a git
        repository keeps it outside (adir.confine)."""
        from .confine import run_agent_root
        return run_agent_root(self.run_dir)

    def ctx(self, run_dir=None, candidate=None, declaration=None) -> BindContext:
        return BindContext(self, run_dir or self.run_dir, candidate, declaration)

    @property
    def backend(self) -> str:
        return self.search.get("backend", "adaevolve")

    @property
    def is_numeric(self) -> bool:
        return self.backend in NUMERIC_BACKENDS

    def hard_constraints(self) -> list:
        return [c for c in self.constraints if c.hard]

    def archive(self, run_dir=None) -> Archive:
        run = Path(run_dir or self.run_dir)
        cfg = self.archive_cfg
        path = Path(cfg.get("path", "results_db.jsonl"))
        if not path.is_absolute():
            path = run / path
        shared = cfg.get("shared")
        if shared and not Path(shared).is_absolute():
            shared = run / shared
        return Archive(cfg.get("store", "jsonl"), path, shared)

    def line_kind_names(self) -> list:
        return [lk.name for lk in self.template.line_kinds]

    def decl_roots(self) -> set:
        roots = set(self.line_kind_names())
        for v in self.searched():
            parts = v.name.split(".")
            for i in range(1, len(parts) + 1):
                roots.add(".".join(parts[:i]))
        return roots


def load(path, env=None, run_dir_override=None, search_override=None) -> Instance:
    """Steps 1 to 5 of the bind order (design section 2.2).
    `search_override` replaces search keys before binding (the CLI's
    --backend)."""
    inst = Instance()
    inst.path = Path(path).resolve()
    inst.base_dir = inst.path.parent
    inst.cluster, adir, inst.missing_env = load_yaml(inst.path, env)
    inst.raw = adir
    check_keys(adir, TOP_KEYS, "adir")
    for key in ("module", "variables", "artifacts", "evaluate", "goal", "search"):
        if key not in adir:
            raise BindError(f"adir.{key}", "required")
    # a domain library beside the run file is importable by its directory name
    import sys
    if str(inst.base_dir) not in sys.path:
        sys.path.insert(0, str(inst.base_dir))
    inst.template = get_template(str(adir["module"]))
    run_dir = run_dir_override or adir.get("run_dir") or f"run/{inst.path.stem}"
    inst.run_dir = Path(run_dir) if Path(run_dir).is_absolute() else (Path.cwd() / run_dir)
    inst.search = dict(adir.get("search") or {})      # the backend decides what an artifact may be
    if search_override:
        inst.search.update(search_override)
        adir = {**adir, "search": inst.search}
    _bind_variables(inst, adir.get("variables") or {})
    _bind_artifacts(inst, adir.get("artifacts") or {})
    _bind_evaluate(inst, adir["evaluate"])
    inst.constraints = parse_constraints(adir.get("constraints"))
    inst.goal = parse_goal(adir["goal"])
    _check_references(inst)
    _derive(inst)
    _bind_search(inst, adir)
    _bind_knowledge_and_task(inst, adir)
    inst.archive_cfg = dict(adir.get("archive") or {})
    check_keys(inst.archive_cfg, ARCHIVE_KEYS, "archive")
    _check_requirements(inst)
    _hashes(inst)
    return inst


# ------------------------------------------------------------- variables

def _bind_variables(inst: Instance, specs: dict):
    tpl = inst.template
    if not isinstance(specs, dict):
        raise BindError("variables", "a mapping")
    specs = expand_presets(specs, tpl.presets, "variables")
    defaults = {name: value for name, value in tpl.binding_defaults.items()
                if not any(_matches(given, name) for given in specs)}
    specs = {**defaults, **specs}
    static = [v for v in tpl.variables if not v.indexed_by]
    # phase 1: the static variables, to feed the elaboration
    phase1 = {k: v for k, v in specs.items()
              if any(_matches(k, var.name) for var in static)}
    pre = bind_variables(static, phase1, "variables")
    elab = Elaboration()
    if tpl.elaborate is not None:
        elab = tpl.elaborate(pre) or Elaboration()
        if not isinstance(elab, Elaboration):
            raise BindError("module", f"{tpl.name}.elaborate must return an Elaboration")
    inst.elaboration = elab
    templates = list(tpl.variables) + list(elab.variables)
    names = [v.name for v in templates]
    # a template default written as a pattern is inert when it names no variable of this instance
    # (a domain that declares its rule variables under one spelling and none under another)
    for name in [n for n in defaults if "*" in n and n in specs and specs[n] is defaults[n]]:
        if not any(_matches(name, n) for n in names) and not any(
                _matches(name, n.split("*", 1)[0] + ix) for n in names if "*" in n
                for ix in elab.index_sets.get(next((v.indexed_by for v in templates if v.name == n), ""), ())):
            specs.pop(name)
    if len(set(names)) != len(names):
        dup = sorted({n for n in names if names.count(n) > 1})
        raise BindError("module", f"{tpl.name} declares variables twice: {dup}")
    # the variables stay templates; the bindings materialize the active ones under the
    # defaults now and any other one when a declaration or a lookup names it
    inst.tree = VariableTree(templates, elab.index_sets, specs, "variables")
    inst.bindings = Bindings(inst.tree)
    inst._variables_expanded = False
    inst._space = None
    inst.bindings.bind_defaults()


def _matches(spec_name: str, var_name: str) -> bool:
    import fnmatch
    return spec_name == var_name or ("*" in spec_name and fnmatch.fnmatchcase(var_name, spec_name))


# ------------------------------------------------------------- artifacts

def _bind_artifacts(inst: Instance, raw: dict):
    if not isinstance(raw, dict):
        raise BindError("artifacts", "a mapping")
    ctx = inst.ctx()
    for path, spec in raw.items():
        a = A.parse_artifact(str(path), spec or {}, str(inst.path))
        A.materialize(a, inst.template, ctx, inst.base_dir, inst.elaboration.index_sets)
        inst.artifacts[a.path] = a
    seeds = inst.seed_artifacts()
    if inst.is_numeric and seeds:
        raise BindError("artifacts", f"a numeric backend ({inst.backend}) mutates declarations "
                                     f"only; {[a.path for a in seeds]} cannot be seed artifacts")
    if not inst.is_numeric and not seeds:
        raise BindError("artifacts", "an LLM backend needs one seed artifact")
    if len(seeds) > 1:
        raise BindError("artifacts", "one seed artifact per instance")
    for a in seeds:
        if a.kind == "text":
            # a family's regions may lie in any of its members: the check reads the members together
            try:
                A.find_regions(a.text, a.evolve, a.language)
            except BindError as e:
                raise BindError(f"artifacts.{a.path}.evolve", e.msg) from None


# -------------------------------------------------------------- evaluate

def _bind_evaluate(inst: Instance, raw: dict):
    check_keys(raw, EVAL_KEYS, "evaluate")
    inst.nodes = parse_nodes(raw.get("nodes") or {}, "evaluate.nodes")
    decl_nodes = [n for n, ni in inst.nodes.items() if ni.node == "adir.declaration"]
    if len(decl_nodes) != 1:
        raise BindError("evaluate.nodes", "exactly one adir.declaration node")
    inst.decl_node = decl_nodes[0]
    inst.feedback = [_expr(x, f"evaluate.feedback[{i}]") for i, x in enumerate(raw.get("feedback") or [])]
    inst.report = [_expr(x, f"evaluate.report[{i}]") for i, x in enumerate(raw.get("report") or [])]


def _expr(text, path) -> Expr:
    if not isinstance(text, str):
        raise BindError(path, "a metric name or expression")
    try:
        return Expr(text)
    except ParseError as e:
        raise BindError(path, str(e)) from None


# ------------------------------------------------------------ references

# the run's own paths a node may take as an input: a node that keeps files of its own (an agent call's
# directory) writes them into the run rather than a temporary directory
RUN_REFS = ("dir", "agent_dir")

def _check_ref(inst: Instance, ref: str, path: str, in_when: bool = False):
    root = root_of(ref)
    parts = ref.split(".")
    if root in WHEN_ONLY_ROOTS:
        if not in_when:
            raise BindError(path, f"{ref}: legal in `when` conditions only")
        if root == "archive":
            if len(parts) < 2:
                raise BindError(path, f"{ref}: archive.<node>.<output> or archive.goal.<level>")
            if parts[1] != "goal":
                _check_ref(inst, ".".join(parts[1:]), path)
        return
    if root == "candidate":
        if len(parts) == 2 and parts[1] == "touched":
            return                       # the members the candidate changed against its parent (section 6.2)
        if len(parts) > 1:
            a = inst.artifacts.get(parts[1])
            if a is None:
                raise BindError(path, f"{ref}: no artifact {parts[1]!r}")
            if len(parts) > 2 and (not a.is_family or parts[2] not in a.members):
                raise BindError(path, f"{ref}: no member {parts[2]!r}")
        return
    if root == "artifacts":
        if len(parts) < 2 or parts[1] not in inst.artifacts:
            raise BindError(path, f"{ref}: no artifact {'.'.join(parts[1:2])!r} "
                                  f"(has: {sorted(inst.artifacts)})")
        a = inst.artifacts[parts[1]]
        if len(parts) > 2 and (not a.is_family or parts[2] not in a.members):
            raise BindError(path, f"{ref}: no member {parts[2]!r}")
        return
    if root == "vars":
        if len(parts) < 2:
            raise BindError(path, f"{ref}: vars.<variable>")
        name = ".".join(parts[1:])
        base = ".".join(parts[1:-1])
        for cand in (name, base):
            if cand in inst.bindings:
                # `vars` reads a bound value; a searched variable has none until a
                # candidate declares one, so the value belongs to `decl` (section 3.7).
                # Without this the reference binds and the node is silently skipped at
                # evaluation time with a TypeError from an unset member list.
                if inst.bindings[cand].time == "search":
                    raise BindError(path, f"{ref}: {cand!r} is searched; read it as "
                                          f"decl.{cand} -- vars reads fixed and runtime bindings")
                return
        raise BindError(path, f"{ref}: no bound variable {name!r}")
    if root == "decl":
        name = ".".join(parts[1:])
        if name in inst.decl_roots():
            return
        raise BindError(path, f"{ref}: {name!r} is neither a searched variable, a family "
                              f"root of one, nor a registered line kind")
    if root == "seed":
        _check_ref(inst, ".".join(parts[1:]), path)
        return
    if root == "run":
        if len(parts) != 2 or parts[1] not in RUN_REFS:
            raise BindError(path, f"{ref}: run.<{'|'.join(RUN_REFS)}>")
        return
    if root in inst.nodes:
        ni = inst.nodes[root]
        if len(parts) < 2:
            raise BindError(path, f"{ref}: <node>.<output>")
        if ni.spec.outputs and parts[1] not in ni.spec.outputs \
                and ni.node not in ("adir.declaration", "adir.instance"):
            raise BindError(path, f"{ref}: {ni.node} documents outputs {ni.spec.outputs}, "
                                  f"not {parts[1]!r}")
        if ni.node == "adir.declaration" and parts[1] not in ("ok", "detail", "decl"):
            raise BindError(path, f"{ref}: adir.declaration outputs ok, detail and decl.*")
        return
    raise BindError(path, f"{ref}: unknown name (nodes: {sorted(inst.nodes)})")


def _check_one_source(inst: Instance):
    """A `map_over` key that names a variable of this unit takes that
    variable, not a list of its own.

    The prompt states the unit from the bindings and the graph runs from
    the node specs, so a concept written down twice can say two things
    and nothing notices. A run file that bound `workload` to one value
    and mapped its cells over four told the agent it was optimizing one
    shape while scoring it on four, and every section of the prompt --
    the unit, the domain card, the task -- described the wrong problem
    while the constraints and the goal described the right one.

    The binding time says which set: `fixed` is one value, `runtime` is
    the set the run measures. Referring to it from `map_over` keeps the
    two readings of the same word identical by construction.
    """
    for n, ni in inst.nodes.items():
        for k, i in (ni.map_over or {}).items():
            if k not in inst.bindings or i.expr is not None:
                continue
            b = inst.bindings[k]
            want = f"vars.{k}"
            raise BindError(f"evaluate.nodes.{n}.map_over.{k}",
                            f"`{k}` is a variable of this unit, bound {b.time}; mapping over a list "
                            f"of its own gives the prompt and the graph two sources for one concept. "
                            f"Map over `{want}` and bind `{k}` with the values the run measures "
                            f"(`runtime: [...]` for a set).")


def _check_references(inst: Instance):
    _check_one_source(inst)
    for n, ni in inst.nodes.items():
        for k, i in list(ni.inputs.items()) + list(ni.map_over.items()):
            for r in i.refs:
                _check_ref(inst, r, f"evaluate.nodes.{n}.inputs.{k}")
        for j, w in enumerate(ni.when):
            for r in w.refs:
                _check_ref(inst, r, f"evaluate.nodes.{n}.when[{j}]", in_when=True)
    for i, c in enumerate(inst.constraints):
        for r in c.refs:
            _check_ref(inst, r, f"constraints[{i}]")
    for i, (_, e) in enumerate(inst.goal.levels):
        for r in e.refs:
            _check_ref(inst, r, f"goal[{i}]")
            if root_of(r) in inst.nodes and inst.nodes[root_of(r)].report_only:
                raise BindError(f"goal[{i}]", f"{r} is a report-only output")
    for i, e in enumerate(inst.feedback):
        for r in e.refs:
            _check_ref(inst, r, f"evaluate.feedback[{i}]")
    for i, e in enumerate(inst.report):
        for r in e.refs:
            _check_ref(inst, r, f"evaluate.report[{i}]")
    # report_only isolation
    for n, ni in inst.nodes.items():
        if not ni.report_only:
            continue
        users = []
        for m, mi in inst.nodes.items():
            if any(root_of(r) == n for r in mi.refs) and m != n:
                users.append(f"node {m}")
        for c in inst.constraints:
            if any(root_of(r) == n for r in c.refs):
                users.append(f"constraint {c.text}")
        for e in inst.feedback:
            if any(root_of(r) == n for r in e.refs):
                users.append(f"feedback {e.text}")
        if users:
            raise BindError(f"evaluate.nodes.{n}", f"report_only, but referenced by {users} "
                                                   f"(report_only_isolation)")


def _derive(inst: Instance):
    roots = []
    for c in inst.constraints:
        roots += [(r, f"constraint {c.text}") for r in c.refs]
    for _, e in inst.goal.levels:
        roots += [(r, f"goal {e.text}") for r in e.refs]
    for e in inst.feedback:
        roots += [(r, f"feedback {e.text}") for r in e.refs]
    for e in inst.report:
        roots += [(r, f"report {e.text}") for r in e.refs]
    roots.append((inst.decl_node, "declaration"))
    for n, ni in inst.nodes.items():
        if ni.report_only and any(root_of(r) == n for e in inst.report for r in e.refs):
            roots.append((n, "report"))
    hard_order = {}
    for c in inst.constraints:
        if c.hard:
            for r in c.refs:
                hard_order.setdefault(root_of(r), c.index)
    inst.graph = derive_graph(inst.nodes, roots, hard_order)
    # resources against the cluster
    provided = set()
    for nt in (inst.cluster.get("available_node_types") or {}).values():
        provided |= set((nt or {}).get("resources") or {})
    if provided:
        for n in inst.graph.active:
            ni = inst.nodes[n]
            need = set(ni.resources) | set(ni.spec.resources)
            if need and not need <= provided:
                raise BindError(f"evaluate.nodes.{n}", f"resources {sorted(need - provided)} are "
                                                       f"provided by no worker type "
                                                       f"(cluster has {sorted(provided)})")


# ---------------------------------------------------------------- search

def _bind_search(inst: Instance, adir: dict):
    s = dict(adir.get("search") or {})
    check_keys(s, SEARCH_KEYS, "search")
    backend = s.get("backend", "adaevolve")
    if backend not in LLM_BACKENDS + NUMERIC_BACKENDS:
        raise BindError("search.backend", f"{backend!r} (LLM: {LLM_BACKENDS}; numeric: {NUMERIC_BACKENDS})")
    seeds = dict(s.get("seeds") or {})
    check_keys(seeds, SEED_KEYS, "search.seeds")
    for name in seeds.get("generated") or []:
        if inst.template.seed_generator is None:
            raise BindError("search.seeds.generated", f"{inst.template.name} registers no seed generator")
        if inst.template.seeds and name not in inst.template.seeds:
            raise BindError("search.seeds.generated", f"{name!r} is not a seed the template accepts "
                                                      f"({list(inst.template.seeds)})")
    for f in seeds.get("files") or []:
        if not A.resolve_file(str(f), inst.base_dir).is_file():
            raise BindError("search.seeds.files", f"no file {f}")
    if (inst.task or {}).get("author") == "discover" and "discover" not in (s.get("models") or {}):
        raise BindError("task.author", "needs the model role `discover`")
    n_disc = seeds.get("discover") or 0
    if isinstance(n_disc, dict):
        from .discover import DISCOVER_KEYS
        check_keys(n_disc, DISCOVER_KEYS, "search.seeds.discover")
        if not isinstance(n_disc.get("keep_families", []), list):
            raise BindError("search.seeds.discover.keep_families", "a list of family names")
        n_disc = n_disc.get("count") or 0
    if not isinstance(n_disc, int) or isinstance(n_disc, bool) or n_disc < 0:
        raise BindError("search.seeds.discover", "a count of plans, 0 or more, or a mapping with `count`, "
                                                 "`sharing_only` and `keep_families`")
    if n_disc:
        if inst.template.plan_seed is None:
            raise BindError("search.seeds.discover", f"{inst.template.name} registers no plan_seed")
        if "discover" not in (s.get("models") or {}):
            raise BindError("search.seeds.discover", "needs the model role `discover`")
    rank = seeds.get("rank")
    if rank:
        if rank.get("prior") and rank["prior"] not in PRIORS:
            raise BindError("search.seeds.rank.prior", f"{rank['prior']!r} is not a registered prior "
                                                       f"(has: {sorted(PRIORS)})")
    check_keys(dict(s.get("prompts") or {}), PROMPTS_KEYS, "search.prompts")
    check_keys(dict(s.get("instructions") or {}), INSTRUCTION_KEYS, "search.instructions")
    ops = s.get("operators")
    if ops is not None:
        if not isinstance(ops, dict):
            raise BindError("search.operators", "a mapping with `override: <file>`; the composer "
                                                "renders the operator sections otherwise")
        check_keys(ops, OPERATORS_KEYS, "search.operators")
        if ops.get("override") and not A.resolve_file(str(ops["override"]), inst.base_dir).is_file():
            raise BindError("search.operators.override", f"no file {ops['override']}")
    models = dict(s.get("models") or {})
    if backend in LLM_BACKENDS and "solution" not in models:
        raise BindError("search.models", "an LLM backend needs the solution role")
    provided = set()
    for nt in (inst.cluster.get("available_node_types") or {}).values():
        provided |= set((nt or {}).get("resources") or {})
    for role, m in models.items():
        if not isinstance(m, dict) or "agent" not in m or "model" not in m:
            raise BindError(f"search.models.{role}", "agent and model are required")
        check_keys(m, MODEL_KEYS, f"search.models.{role}")
        agent = str(m["agent"])
        if agent not in AGENT_RESOURCES:
            raise BindError(f"search.models.{role}.agent", " | ".join(AGENT_RESOURCES))
        for key in ("provider", "small_model"):
            if m.get(key) is not None and agent != "opencode":
                raise BindError(f"search.models.{role}.{key}", f"a setting of the opencode agent (the {agent} CLI "
                                                                f"names its model alone)")
        res = AGENT_RESOURCES[agent]
        if provided and res not in provided:
            raise BindError(f"search.models.{role}.agent",
                            f"the {agent} agent runs on a worker with the resource {res!r}, which no "
                            f"worker type provides (cluster has {sorted(provided)})")
        if m.get("work_dir") and not A.resolve_file(str(m["work_dir"]), inst.base_dir).is_dir():
            raise BindError(f"search.models.{role}.work_dir", f"no directory {m['work_dir']}")
    prompts = dict(s.get("prompts") or {})
    if prompts.get("sample", "uniform") not in ("uniform", "ucb"):
        raise BindError("search.prompts.sample", "uniform | ucb")
    for name in prompts.get("sources") or []:
        if name not in PROMPT_SOURCES:
            raise BindError("search.prompts.sources", f"{name!r} is not a registered PromptSource "
                                                      f"(has: {sorted(PROMPT_SOURCES)})")
    inst.search = s
    from .composer import check_variants
    check_variants(inst)
    ins = dict(s.get("instructions") or {})
    if ins.get("enabled"):
        if ins.get("slot", "guidance") != "guidance":
            raise BindError("search.instructions.slot", "guidance is the only evolved slot")
        prop = dict(ins.get("propose") or {})
        check_keys(prop, PROPOSE_KEYS, "search.instructions.propose")
        role = str(prop.get("role") or "strategy")
        if role not in models:
            raise BindError("search.instructions.propose.role",
                            f"instruction evolution needs the model role {role!r} under search.models")
        for src in prop.get("from") or []:
            if src not in ("feedback", "declarations", "metrics"):
                raise BindError("search.instructions.propose.from", "feedback | declarations | metrics")
        if ins.get("select", "ucb") not in ("ucb", "uniform"):
            raise BindError("search.instructions.select", "ucb | uniform")
    for t in s.get("tools") or []:
        name = t if isinstance(t, str) else (t or {}).get("name")
        if name not in TOOLS and not isinstance(t, dict):
            raise BindError("search.tools", f"{name!r} is not a registered tool (has: {sorted(TOOLS)})")
    for src in (s.get("tactics") or {}).get("sources") or []:
        if src not in BUILTIN_TACTICS and src not in TACTIC_SOURCES:
            raise BindError("search.tactics.sources", f"{src!r} is neither built in "
                                                      f"({BUILTIN_TACTICS}) nor registered")
    inst.search = s


def _check_requirements(inst: Instance):
    satisfied = {c.satisfies for c in inst.constraints if c.satisfies}
    open_reqs = []
    for b in inst.bindings.values():
        var = b.variable
        if not var.requires:
            continue
        vals = b.possible_values() if b.time != "search" else []
        for v in vals:
            for req in var.requires.get(v, []) or []:
                if req not in satisfied:
                    open_reqs.append((var.name, v, req))
    if open_reqs:
        detail = "; ".join(f"{n} = {v!r} requires a constraint with satisfies: {r}"
                           for n, v, r in open_reqs)
        raise BindError("constraints", detail)
    inst.requirements = sorted(satisfied)


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def template_identity(t: Variable) -> list:
    """A template's entry in the space's identity: its name, domain,
    condition and index set; a search domain, per-index domains or
    member conditions join the entry where the template carries them,
    so a template without them keeps its entry (and a narrowed or
    conditioned space is a new one). A member condition's doc is text
    for the reader and is not part of the identity."""
    entry = [t.name, t.domain.to_json(), t.when, t.indexed_by]
    if t.search_domain is not None:
        entry.append({"search_domain": t.search_domain.to_json()})
    if t.index_domains:
        entry.append({"index_domains": {str(ix): d.to_json() for ix, d in t.index_domains.items()}})
    if t.member_when:
        entry.append({"member_when": {str(m): [sib, list(allowed)] for m, (sib, allowed, _doc) in t.member_when.items()}})
    return entry


def _hashes(inst: Instance):
    fixed = {n: b.to_json() for n, b in inst.bindings.items() if b.time in ("fixed", "runtime")}
    # the space's identity: the template variables, the index sets and the specs
    # that bind them (the expansion itself is lazy)
    template_id = template_identity
    space_id = {"templates": [template_id(t) for t in inst.tree.templates],
                "index_sets": inst.tree.index_sets,
                "specs": inst.tree.specs} if inst.tree is not None else {}
    node_hashes = {n: _sha(ni.identity()) for n, ni in inst.nodes.items()}
    inst.hashes = {
        "unit_id": _sha({"template": inst.template.name, "bindings": fixed}),
        "space_hash": _sha(space_id),
        "artifact_hashes": {p: a.sha256 for p, a in inst.artifacts.items()},
        "evaluator_hash": _sha({"nodes": {n: ni.identity() for n, ni in inst.nodes.items()},
                                "feedback": [e.text for e in inst.feedback],
                                "report": [e.text for e in inst.report]}),
        "node_hashes": node_hashes,
        "knowledge_hash": _knowledge_hash(inst),
        "model_hashes": {role: _sha(m) for role, m in (inst.search.get("models") or {}).items()},
    }


def _bind_knowledge_and_task(inst: Instance, adir: dict):
    k = adir.get("knowledge")
    if k is not None:
        if not isinstance(k, str):
            raise BindError("knowledge", "the path of the knowledge base directory (a string)")
        p = Path(k)
        if not p.is_absolute():
            p = inst.base_dir / p if (inst.base_dir / p).is_dir() else Path.cwd() / p
        if not p.is_dir():
            raise BindError("knowledge", f"no directory {k}")
        inst.knowledge = str(p.resolve())
    t = adir.get("task")
    if t is not None:
        if not isinstance(t, dict):
            raise BindError("task", "a mapping with `context: <markdown file>`")
        check_keys(t, TASK_KEYS, "task")
        if t.get("author") is not None and t["author"] not in TASK_AUTHORS:
            raise BindError("task.author", " | ".join(TASK_AUTHORS))
        inst.task = dict(t)
        if t.get("context"):
            f = A.resolve_file(str(t["context"]), inst.base_dir)
            if not f.is_file():
                raise BindError("task.context", f"no file {t['context']}")
            inst.task_text = f.read_text()
        if t.get("script"):
            inst.task["script"] = _resolve_script(str(t["script"]), inst.base_dir, "task.script")
    r = adir.get("role")
    if r is not None:
        if not isinstance(r, dict):
            raise BindError("role", "a mapping with `file: <markdown file>` or `script: <python file | module:function>`")
        check_keys(r, ROLE_KEYS, "role")
        inst.role = dict(r)
        if r.get("file"):
            f = A.resolve_file(str(r["file"]), inst.base_dir)
            if not f.is_file():
                raise BindError("role.file", f"no file {r['file']}")
            inst.role_text = f.read_text()
        if r.get("script"):
            inst.role["script"] = _resolve_script(str(r["script"]), inst.base_dir, "role.script")


def _resolve_script(spec: str, base_dir: Path, key: str) -> str:
    """A prompt script: the path of a Python file that defines
    `render(instance) -> str` (relative to the run file), returned
    absolute, or `module:function`, returned as written."""
    if spec.endswith(".py"):
        f = A.resolve_file(spec, base_dir)
        if not f.is_file():
            raise BindError(key, f"no file {spec}")
        return str(f.resolve())
    if ":" in spec and not spec.startswith(":"):
        return spec
    raise BindError(key, "a Python file `<path>.py` with render(instance) -> str, or `module:function`")


def _knowledge_hash(inst: Instance) -> str:
    if not inst.knowledge:
        return ""
    p = Path(inst.knowledge)
    names = sorted(str(f.relative_to(p)) for f in p.rglob("*.md"))
    return _sha(names)


def contract(inst: Instance) -> dict:
    """The resolved instance for contract.json."""
    return {
        "file": str(inst.path),
        "module": inst.template.name,
        "run_dir": str(inst.run_dir),
        "bindings": {n: b.to_json() for n, b in inst.bindings.items()},
        "index_sets": {k: [str(x) for x in v] for k, v in inst.elaboration.index_sets.items()},
        "artifacts": {p: {"role": a.role, "kind": a.kind, "source": a.source, "language": a.language,
                          "evolve": a.evolve, "members": a.members, "sha256": a.sha256}
                      for p, a in inst.artifacts.items()},
        "nodes": {n: ni.identity() for n, ni in inst.nodes.items()},
        "graph": inst.graph.to_json(),
        "constraints": [{"text": c.text, "hard": c.hard, "satisfies": c.satisfies}
                        for c in inst.constraints],
        "goal": {"kind": inst.goal.kind, "levels": [[d, e.text] for d, e in inst.goal.levels],
                 "score": {"rule": inst.goal.score_rule, "infeasible": inst.goal.infeasible}},
        "requirements": inst.requirements,
        "search": inst.search,
        "knowledge": inst.knowledge,
        "task": {**inst.task, "sha256": _sha(inst.task_text)} if inst.task else {},
        "role": {**inst.role, "sha256": _sha(inst.role_text)} if inst.role else {},
        "archive": inst.archive_cfg,
        "missing_env": sorted(inst.missing_env),
        **inst.hashes,
    }
