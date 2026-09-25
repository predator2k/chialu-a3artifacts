"""The chiALU domain library for ADIR. Importing this module registers
the three unit-class templates (chialu.ALU, chialu.VecSFU,
chialu.VecDotAcc), the priors, the tactic sources and the prompt sources; the nodes live in
chialu.eda and are named by import path in a run file."""
from chialu import eda  # noqa: F401  the nodes
from chialu import priors  # noqa: F401  registers the prior and the tactic sources
from chialu import prompts  # noqa: F401  registers the prompt sources
from chialu.modules.alu import ALU
from chialu.modules.dot import VEC_DOT_ACC
from chialu.modules.sfu import VEC_SFU

TEMPLATES = {t.name: t for t in (ALU, VEC_SFU, VEC_DOT_ACC)}

__all__ = ["ALU", "VEC_SFU", "VEC_DOT_ACC", "TEMPLATES"]
