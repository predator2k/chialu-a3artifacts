"""A toy domain library: a `toy.Box` template whose nodes are pure
Python, so every path of ADIR runs without EDA tools."""
from adir import (Bool, Elaboration, Enum, LineKind, Preset, PromptSource, Range, Set, Template,
                  Variable)


def elaborate(bindings):
    lanes = bindings["lanes"].value
    return Elaboration(index_sets={"lanes": [f"l{i}" for i in range(lanes)]},
                       info={"interface": f"{lanes} lanes of 8 bits"})


def parse_note(tokens):
    return {"text": " ".join(tokens)}


def check_note(ctx, entries):
    return (all(e["text"] for e in entries), "empty NOTE" if not all(e["text"] for e in entries) else "ok")


PROGRAMS = {
    "baseline": ("fast", 2, "def compute(x):\n    y = helper(x)\n    return y * 2 + 1\n"),
    "small": ("small", None, "def compute(x):\n    return helper(x)\n"),
    "fast": ("fast", 4, "def compute(x):\n    y = helper(x)\n    z = y * 4\n    return z + 3\n"),
}


def seed_generator(ctx, name):
    algo, k, body = PROGRAMS[name]
    text = "# toy program\n\ndef helper(x):\n    return x + 1\n\n\n" + body
    # one VAR per active searched variable: the seed's own plan where it
    # has one, a default otherwise
    defaults = {"algo": algo, "algo.k": k if k is not None else 2, "lanes_outer": 1}
    vars_ = {}
    for var in ctx.instance.variable_order():
        b = ctx.instance.bindings.get(var.name)
        if b is None or b.time != "search":
            continue
        if var.when is not None:
            parent = var.when[0]
            pv = vars_.get(parent) if parent in vars_ else (ctx.value(parent) if ctx.has(parent) else None)
            if not var.condition_holds(pv):
                continue
        if var.name in defaults:
            vars_[var.name] = defaults[var.name]
        elif var.name.startswith("lane."):
            vars_[var.name] = "x"
    return text, vars_, [("NOTE", ["seed", name])]


PLAN_DOC = """A plan is `{"algo": "fast" | "small", "k": <int 1..8>}`; `k` only under fast."""


def plan_seed(ctx, name, plan):
    """A discovered plan as a seed: the fast or the small body with the
    plan's k."""
    algo = plan.get("algo", "fast")
    if algo not in ("fast", "small"):
        raise ValueError(f"algo {algo!r}")
    k = int(plan.get("k", 2))
    body = PROGRAMS["fast" if algo == "fast" else "small"][2]
    text = "# toy program\n\ndef helper(x):\n    return x + 1\n\n\n" + body
    vars_ = {"algo": algo} if algo != "fast" else {"algo": "fast", "algo.k": k}
    return text, vars_, [("NOTE", ["plan", name])]


def replan(ctx, decl, parent_decl):
    """A NOTE line `replan` regenerates the body for the declared algo
    and keeps nothing from the parent."""
    notes = [t for k, t in decl.lines if k == "NOTE"]
    if not any(t and t[0] == "replan" for t in notes):
        return None
    text, vars_, lines = plan_seed(ctx, "replan", {"algo": decl.vars.get("algo", "fast"),
                                                   "k": decl.vars.get("algo.k", 2)})
    return text, dict(decl.vars), [("NOTE", ["replanned"])], []


def gen_harness(ctx):
    return f"print('harness for {ctx.value('lanes')} lanes')\n"


NOTES = PromptSource("toy_notes", lambda inst, archive, parent: "## Toy notes\n\nA lane is a byte.\n",
                     static=True)
PLAN = PromptSource("toy_plan", lambda inst, archive, parent:
                    "## Plan of the parent\n\n" + ("k=" + str((parent.get("declarations") or {}).get("vars", {}).get("algo.k"))
                                                   if parent else "(no parent)") + "\n")


def elaborate_cond(bindings):
    """Two index sets: `lanes` for every lane, `narrow` for every lane
    but the last, so the last lane's `tail` has no sibling."""
    lanes = bindings["lanes"].value
    return Elaboration(index_sets={"lanes": [f"l{i}" for i in range(lanes)],
                                   "narrow": [f"l{i}" for i in range(max(lanes - 1, 0))]},
                       info={"interface": f"{lanes} lanes with member conditions"})


def cond_seed(ctx, name):
    text = "# toy program\n\ndef helper(x):\n    return x + 1\n\n\ndef compute(x):\n    return helper(x)\n"
    return text, {}, [("NOTE", ["seed", name])]


COND = Template(
    name="toy.Cond",
    variables=[
        Variable("lanes", Range(1, 4), {"fixed"}, doc="lane count"),
        Variable("mode", Enum(("x", "y")), {"fixed", "runtime"}, doc="the mode port"),
        Variable("mul", Enum(("separate", "fused")), {"fixed", "search"}, doc="the multiplier organization"),
        Variable("unpack", Enum(("in_unpack", "in_datapath")), {"fixed", "search"},
                 member_when={"in_datapath": ("mul", ("fused",), "a separate multiplier needs normalized operands")},
                 doc="where a subnormal operand is normalized"),
        Variable("first", Enum(("cond", "plain")), {"fixed", "search"}, member_when={"cond": ("mul", ("fused",))},
                 doc="a variable whose first member is conditioned"),
        Variable("pack", Enum(("a", "b")), {"fixed", "search"}, member_when={"b": ("mode", ("x",))},
                 doc="a member conditioned on the run-time mode"),
        Variable("lane.*.order", Enum(("swap", "each")), {"fixed", "search"}, indexed_by="lanes"),
        Variable("lane.*.lz", Enum(("single", "dual")), {"fixed", "search"}, indexed_by="lanes",
                 member_when={"dual": ("lane.*.order", ("each",))}),
        Variable("lane.*.split", Enum(("sign", "count")), {"fixed", "search"}, indexed_by="lanes",
                 when=("lane.*.lz", ("dual",))),
        Variable("lane.*.tail", Enum(("none", "wide")), {"fixed", "search"}, indexed_by="lanes",
                 member_when={"wide": ("narrow.*.width", ("w",))}),
        Variable("narrow.*.width", Enum(("n", "w")), {"fixed", "search"}, indexed_by="narrow"),
    ],
    elaborate=elaborate_cond,
    generators={"program": lambda ctx: cond_seed(ctx, "base")[0]},
    seed_generator=cond_seed,
    seeds=("base",),
    line_kinds=[LineKind("NOTE", parse_note, check_note)],
    doc="a toy unit with member conditions",
)


BOX = Template(
    name="toy.Box",
    variables=[
        Variable("lanes", Range(1, 4), {"fixed"}, doc="lane count"),
        Variable("lanes_outer", Range(1, 4), {"fixed", "search"}, doc="a lane count an outer search decides"),
        Variable("mode", Enum(("a", "b", "c")), {"fixed", "runtime"}, doc="the mode port"),
        Variable("algo", Enum(("fast", "small")), {"fixed", "search"}, doc="the algorithm"),
        Variable("algo.k", Range(1, 8), {"fixed", "search"}, when=("algo", "fast"),
                 doc="unroll factor of the fast algorithm"),
        Variable("lane.*.style", Enum(("x", "y")), {"fixed", "search"}, indexed_by="lanes"),
        Variable("cfg.a", Range(0, 9), {"fixed"}),
        Variable("cfg.b", Bool(), {"fixed"}),
        Variable("accuracy", Enum(("exact", "approximate")), {"fixed"},
                 requires={"approximate": ["error_bound"]}),
    ],
    elaborate=elaborate,
    generators={"harness": gen_harness,
                "program": lambda ctx: seed_generator(ctx, "baseline")[0]},
    seed_generator=seed_generator,
    plan_doc=PLAN_DOC,
    plan_seed=plan_seed,
    replan=replan,
    seeds=tuple(PROGRAMS),
    line_kinds=[LineKind("NOTE", parse_note, check_note)],
    presets={"std": Preset("cfg", {"a": 3, "b": True})},
    doc="a toy unit",
)
