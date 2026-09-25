"""ADIR: the task layer of an agentic hardware-design search.

A domain library registers a Template with Variables (bound at one of
three binding times), generators, a seed generator, line kinds and
presets; a run file binds the variables, wires CHIA nodes into an
evaluation graph, and states constraints and a goal over node outputs.
See docs/design.md."""
from .domains import Bool, Domain, Enum, Range, Set, Struct
from .errors import UNDECIDED, BindError
from .registry import (Elaboration, LineKind, Preset, Prior, PromptSource, TacticSource, Template,
                       Tool, node, get_template)
from .spaces import Family, Space
from .variables import Binding, Variable

IntRange = Range

__all__ = ["Bool", "Domain", "Enum", "Range", "IntRange", "Set", "Struct", "UNDECIDED",
           "BindError", "Elaboration", "LineKind", "Preset", "Prior", "PromptSource", "TacticSource",
           "Template", "Tool", "node", "get_template", "Family", "Space", "Binding", "Variable"]
__version__ = "0.1.0"
