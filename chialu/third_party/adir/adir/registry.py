"""The registration API (design section 12): what a domain library
registers, and how a yaml's `module:` name reaches its template.

Nodes are CHIA's. A domain adds one by writing a function that takes
keyword inputs and returns a dict, and may document its outputs with
the `node` decorator, which also wraps it as a `@ChiaFunction` when
CHIA is importable. A domain writes no prompt text: it registers
PromptSources (data the composer renders) and TacticSources."""
from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .errors import BindError
from .variables import Variable

TEMPLATES: dict = {}
PRIORS: dict = {}
TACTIC_SOURCES: dict = {}
PROMPT_SOURCES: dict = {}
TOOLS: dict = {}


@dataclass
class Elaboration:
    """What `Template.elaborate(bindings)` returns: the index sets the
    indexed variables expand over, further variables that exist under
    these bindings, and free information the generators read."""
    index_sets: dict = field(default_factory=dict)
    variables: list = field(default_factory=list)
    info: dict = field(default_factory=dict)


@dataclass
class Preset:
    path: str
    bindings: dict
    doc: str = ""


@dataclass
class LineKind:
    """A domain declaration line: `parse(tokens) -> dict` and
    `check(ctx, entries) -> (ok, detail)`."""
    name: str
    parse: Callable
    check: Optional[Callable] = None


@dataclass
class Prior:
    name: str
    predict: Callable      # (declarations: dict) -> (value, lo, hi)

    def __post_init__(self):
        PRIORS[self.name] = self


@dataclass
class TacticSource:
    name: str
    render: Callable       # (instance, archive, parent_record) -> list[str]

    def __post_init__(self):
        TACTIC_SOURCES[self.name] = self


@dataclass
class PromptSource:
    """Domain data the composer renders into a prompt slot (design
    section 7): `render(instance, archive, parent_record) -> markdown`.
    A static source (an interface description) renders once into the
    system text with no parent; the others render per iteration with
    the parent record (a structure table, a plan table, a move menu).
    A run file selects sources by name under `search.prompts.sources`."""
    name: str
    render: Callable
    static: bool = False
    doc: str = ""

    def __post_init__(self):
        PROMPT_SOURCES[self.name] = self


@dataclass
class Tool:
    name: str
    node: str
    work_dir: str = ""
    timeout_seconds: int = 600

    def __post_init__(self):
        TOOLS[self.name] = self


@dataclass
class Template:
    name: str
    variables: list
    elaborate: Optional[Callable] = None          # (bindings) -> Elaboration
    generators: dict = field(default_factory=dict)  # artifact path -> (ctx) -> text | {member: text}
    seed_generator: Optional[Callable] = None     # (ctx, name) -> text | (text, vars, lines)
    seeds: tuple = ()                             # the names the seed generator accepts
    normalize_declaration: Optional[Callable] = None   # (ctx, Declaration) -> Declaration, before the check
    focus_map: Optional[Callable] = None          # (ctx, parent record) -> {region name: [variable names]}
    plan_doc: str = ""                            # the plan grammar the discover role answers in
    plan_seed: Optional[Callable] = None          # (ctx, name, plan dict) -> text | (text, vars, lines)
    replan: Optional[Callable] = None             # (ctx, decl, parent decl) -> None | (texts, vars, lines, keep)
    line_kinds: list = field(default_factory=list)
    presets: dict = field(default_factory=dict)
    comment_syntax: dict = field(default_factory=dict)   # language -> prefix
    doc: str = ""
    binding_defaults: dict = field(default_factory=dict)  # explicit template defaults, overridden by user specs

    def __post_init__(self):
        for v in self.variables:
            if not isinstance(v, Variable):
                raise BindError(self.name, f"variables must be Variable objects (got {v!r})")
        self.line_kinds = list(self.line_kinds)
        TEMPLATES[self.name] = self

    def line_kind(self, name: str) -> Optional[LineKind]:
        for lk in self.line_kinds:
            if lk.name == name:
                return lk
        return None


def get_template(name: str) -> Template:
    """`<library>.<Template>`: import the library (and its `domain`
    module where one exists) so its templates register, then look the
    name up."""
    if name in TEMPLATES:
        return TEMPLATES[name]
    if "." not in name:
        raise BindError("module", f"{name!r} is not <library>.<Template>")
    lib, attr = name.rsplit(".", 1)
    for modname in (lib, f"{lib}.domain"):
        try:
            mod = importlib.import_module(modname)
        except ModuleNotFoundError as e:
            if e.name and (e.name == modname or modname.startswith(e.name)):
                continue
            raise BindError("module", f"importing {modname}: {e}") from e
        if name in TEMPLATES:
            return TEMPLATES[name]
        obj = getattr(mod, attr, None)
        if isinstance(obj, Template):
            TEMPLATES[name] = obj
            return obj
    raise BindError("module", f"no template {name!r} (registered: {sorted(TEMPLATES)})")


def node(outputs=None, resources=None, cache_id=None, transient=None):
    """Document a node's outputs and resources, and wrap it as a
    `@ChiaFunction` when CHIA is importable. `cache_id` is a callable
    taking the node's keyword arguments and returning a string the cache
    key folds in: what the arguments do not carry, such as the liberty
    files and the ABC script a synthesis runs under. `transient` names
    the outputs a downstream node reads but no record keeps: a compiled
    binary, a waveform, a netlist. They travel through the graph and are
    dropped from the archived measurement, which otherwise carries every
    megabyte of them once per candidate."""
    def deco(fn):
        fn.adir_outputs = list(outputs or [])
        fn.adir_resources = dict(resources or {})
        fn.adir_cache_id = cache_id
        fn.adir_transient = list(transient or [])
        try:
            from chia.base.ChiaFunction import ChiaFunction  # type: ignore
        except Exception:  # noqa: BLE001
            return fn
        try:
            wrapped = ChiaFunction(resources=dict(resources or {}))(fn)
        except Exception:  # noqa: BLE001
            return fn
        try:
            wrapped.adir_outputs = fn.adir_outputs
            wrapped.adir_resources = fn.adir_resources
            wrapped.adir_cache_id = fn.adir_cache_id
            wrapped.adir_transient = fn.adir_transient
            wrapped.__wrapped__ = fn
        except Exception:  # noqa: BLE001
            pass
        return wrapped
    return deco


def underlying(fn):
    """The plain Python function behind a decorated node, for signature
    inspection and local calls."""
    seen = set()
    while hasattr(fn, "__wrapped__") and id(fn) not in seen:
        seen.add(id(fn))
        fn = fn.__wrapped__
    for attr in ("func", "fn", "function", "_func", "_fn"):
        inner = getattr(fn, attr, None)
        if callable(inner) and not inspect.isclass(fn):
            return inner
    return fn
