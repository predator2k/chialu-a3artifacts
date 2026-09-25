# cordic

Shift-add digit recurrence for rotations: each iteration adds or
subtracts a shifted copy of the working vector, steering by the residual
angle, and converges one bit per iteration; a constant scale factor is
folded into initialization. Circular, linear, and hyperbolic modes
cover sin/cos/atan, multiply/divide, and sinh/exp/log with the same
datapath, which is the family's whole appeal: no multiplier, no tables
beyond the arctan constants.

It is the canonical ITERATIVE SFU: latency is ~n cycles at 1 bit/cycle
(the execution contract is fixed_iteration or variable-latency), so it
loses to table/polynomial families whenever II=1 is required, and wins
where area is scarce, latency is tolerable, or the function mix leans
on rotations. Redundant high-radix variants retire several bits per
iteration at the cost of sign-detection complexity and a variable scale
factor.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: `iterations` unrolled micro-rotations in the circular, hyperbolic or linear coordinate set the function needs, rotation or vectoring, the scale by a constant multiplier, scaling iterations or a pre-scaled start). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family cordic --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### mode

| member | what it selects |
| --- | --- |
| `rotation` | the angle drives the iterations. |
| `vectoring` | the y residual drives them. |
| `both` | the unit serves either, the mode selecting the residual the iterations follow. |

### topology

| member | what it selects |
| --- | --- |
| `unrolled_combinational` | every micro-rotation is a stage of one combinational chain, so the whole evaluation settles in a cycle and the iteration count sets the delay. |

The pipelined topology is deferred: it needs the latency and clock
contract the VecSFU interface does not define, and
`UNSUPPORTED_SFU_CHOICES` in `chialu/spaces/sfu_spaces.py` keeps the
member machine-readable so an old selection fails with that reason. Its
card is under `legacy/knowledge/deferred/arch/sfu/cordic/`.

### scale_compensation

| member | what it selects |
| --- | --- |
| `constant_multiplier` | the gain is removed by one constant multiply. |
| `scaling_iterations` | the gain is removed by shift-add iterations folded into the schedule. |
| `none` | the gain is folded into the initial x value instead. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the evaluation is shift-add rotations whose count and scale compensation the module states | - | `\d+ iterations, scale \w+` |

## references

volder_1959 -> J. E. Volder, "The CORDIC Trigonometric Computing Technique", IRE Trans. Electronic Computers, 1959
walther_1971 -> J. S. Walther, "A Unified Algorithm for Elementary Functions", AFIPS SJCC, 1971
