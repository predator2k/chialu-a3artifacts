"""chirecipe: a Yosys/ABC synthesis recipe for one fixed RTL block as an
ADIR domain library (examples/synth_recipe). `chirecipe.domain`
registers the templates; `chirecipe.nodes` holds the CHIA nodes."""
from chirecipe.domain import RECIPE_GRID, SYNTH_RECIPE  # noqa: F401

__all__ = ["SYNTH_RECIPE", "RECIPE_GRID"]
