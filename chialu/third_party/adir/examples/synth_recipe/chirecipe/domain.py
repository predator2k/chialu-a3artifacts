"""The two templates of chirecipe.

* `chirecipe.SynthRecipe`: the recipe text is the seed artifact an LLM
  backend rewrites; `abc.script_family` is the candidate's declared
  family of ABC passes.
* `chirecipe.RecipeGrid`: the recipe is rendered by
  `chirecipe.nodes.render_recipe` from four searched variables, so a
  numeric backend (grid, random) explores it with no seed artifact."""
from adir import Bool, Enum, Range, Template, Variable

BLOCKS = ("alu_mixed32",)
PDKS = ("nangate45", "asap7", "sky130hd")
FAMILIES = ("resyn2", "compress2rs", "dch", "custom")


def _fixed():
    return [
        Variable("block", Enum(BLOCKS), {"fixed"},
                 doc="the RTL block under rtl/<block>.sv; its top module carries the same name"),
        Variable("pdk", Enum(PDKS), {"fixed"},
                 doc="the PDK descriptor (chiALU's pdk/<name>.yaml names the liberty file)"),
        Variable("clock_ps", Range(100, 20000), {"fixed"},
                 doc="the delay target handed to the mapper, in ps"),
    ]


SYNTH_RECIPE = Template(
    name="chirecipe.SynthRecipe",
    variables=_fixed() + [
        Variable("abc.script_family", Enum(FAMILIES), {"fixed", "search"},
                 doc="the family of the recipe's ABC optimization passes: resyn2 (balance, "
                     "rewrite, refactor rounds), compress2rs (resubstitution-heavy), dch "
                     "(structural choices before mapping), custom (anything else)"),
    ],
    comment_syntax={"yosys_script": "#"},
    doc="A Yosys script the synth node runs unchanged after substituting {rtl}, {liberty}, "
        "{top} and {clock_ps}; the node appends the area statistics and the netlist write, "
        "so the numbers come from the script's own run. The mapped netlist is proven "
        "equivalent to the RTL before it counts.",
)


def _grid_seed(ctx, name):
    return {"abc.script_family": "resyn2", "abc.map_effort": 1, "yosys.opt_full": False,
            "yosys.share": False}


RECIPE_GRID = Template(
    name="chirecipe.RecipeGrid",
    variables=_fixed() + [
        Variable("abc.script_family", Enum(("none",) + FAMILIES[:3]), {"fixed", "search"},
                 doc="the ABC optimization passes before mapping"),
        Variable("abc.map_effort", Range(1, 3), {"fixed", "search"},
                 doc="1: &nf at its defaults; 2: &nf -C 32 -F 8 -p; 3: &dch -f before the "
                     "level-2 mapping"),
        Variable("yosys.opt_full", Bool(), {"fixed", "search"}, doc="opt -full after synth"),
        Variable("yosys.share", Bool(), {"fixed", "search"},
                 doc="keep yosys's SAT-based SHARE pass in synth"),
    ],
    seed_generator=_grid_seed,
    seeds=("default",),
    doc="The recipe is rendered from the declaration by chirecipe.nodes.render_recipe.",
)
