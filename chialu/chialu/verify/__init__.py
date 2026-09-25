"""chialu.verify — the golden verification layer (design rev: instruction 9).

The layer is parameterized by FUNCTIONAL parameters only (formats, op
sets, lanes, rounding, error budgets, checker contracts) — exactly what
an elaborated ADIR module exposes — and never by architecture choices,
so one implementation covers every parameter combination of the three
unit classes and stays microarchitecture-independent.

Composition:
  formats.py   number formats as composable objects (int encodings, BCD,
               generic IEEE-like floats incl. fp8/fp4, posit, scaled
               accumulators): decode/encode/round/corners/sample/ulp
  ops.py       frozen exact reference semantics for every op of the
               three templates, defined over formats
  stimulus.py  corner x corner + op-aware directed + seeded random
               vector plans, with a reproducibility freeze hash
  errors.py    numerical error model: ulp/abs/rel + approximate-
               computing metrics (error_rate, med, nmed, mred,
               error_bias) and budget verdicts from ADIR constraints
  faults.py    error-checking model: false-alarm and detection
               expectations at the core/checker interface seam
  tb_gen.py    interface-driven SV testbench emission (self-check or
               dump mode; fault-injection harness)
  harness.py   one call from an elaborated Module (or explicit spec)
               to {vectors, tb, expected, check()}
"""

from chialu.verify.formats import make_format          # noqa: F401

try:  # harness needs the full layer; formats alone must stay importable
    from chialu.verify.harness import build_verification   # noqa: F401
except ImportError:  # pragma: no cover
    pass
