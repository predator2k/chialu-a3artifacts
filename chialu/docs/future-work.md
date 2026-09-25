# Future work

This document records the two subjects a later version of chiALU takes
up. Neither is a deferred family: `docs/deferred-families.md` lists the
families, choice values and spaces this version does not realize, and
each of them waits on one of the two subjects below. Each section states
the scope of the version, what the repository already carries for it,
and what the version has to build.

## 1. Registered and multi-cycle units

### Scope

A unit whose result arrives in a cycle later than the one its operands
enter, either after a fixed number of cycles or after a number the data
decides. The current scope is one operation per vector through
combinational logic, which the README and section 1 of
`docs/formats-and-options.md` state, so a structure that reuses a
datapath over cycles has no place to be realized.

### What the repository already carries

* **The spec fields**: `latency_cycles` and `variable_latency_max` are
  optional fields of every verify spec (`chialu/verify/harness.py`). No
  unit template sets them.
* **The testbench protocols**: `chialu/verify/tb_gen.py` emits three.
  The combinational protocol applies a vector, settles and samples. The
  fixed-latency protocol clocks one vector at a time and samples `L`
  cycles later. The variable protocol drives `in_valid`, waits for
  `out_valid`, and writes `TIMEOUT` into the dump when the response
  arrives later than `variable_latency_max` cycles.
* **The checker gate**: the fault harness drives the checker beside the
  datapath in the same cycle, which a registered unit changes.

### What the version has to build

* **A protocol variable on the unit templates**, which binds the latency
  or the valid handshake and reaches the seed and the verify spec
  together, so the testbench protocol and the generated registers agree.
* **Registers in the seed**, which the templates place at the boundary
  the protocol variable names rather than inside a family's own
  structure.
* **A timing metric of cycle time times cycles, or of throughput**. The
  current metric is ABC's combinational delay and the mapped area
  (`chialu/synthdb.py`), and a unit that answers in `n` cycles is not
  comparable to a combinational one under it.
* **The pipelined configurations of the evaluation's baselines**.
  TransDot's `NumPipeRegs` is set to 0 for the comparison
  (`docs/evaluation-plan.md` section 2), and the paper's own numbers use
  three pipeline registers, so a pipelined comparison needs both the
  baseline's parameter and chiALU's own protocol.
* **A checker contract across cycles**, since a concurrent checker of a
  registered unit compares a result against a prediction that has to be
  delayed with it.

### What returns with it

| Group | Count | Where it is recorded |
| --- | --- | --- |
| Sequential families | 10 | the first table of `docs/deferred-families.md` |
| Sequential choice values | 9 | the choice-value table of the same document |
| The on-line group | 4 families of `online_space` | `legacy/knowledge/deferred/spaces_deferred.py` |
| The on-line core families | `online_msdf_core`, `merged_mul_div` | `chialu/modules/alu.py` before 2026-09-12 |

The sequential families are `speculative_variable_latency`,
`digit_serial_adder`, `sequential_shift_add`, `serial_serial_parallel`,
`iterative_reuse`, `self_timed_variable_latency`, the fp adder's
`variable_latency`, `iterative_decimal_multiplication`, `time_redundancy`
and `lane_width_gating`. The nine choice values are `trap_to_software`,
`shared_multiplier`, `microcoded_fpu_sequence`, `folded_sequential`,
`msdf_online_serial`, `sequential_reuse`, `bit_serial_composable`,
`compensated_two_sum` and `ordered_fp_loop_lookahead`.

## 2. Decimal floating point

### Scope

A unit whose modes are the IEEE 754-2019 decimal formats, which is
decimal32, decimal64 and decimal128 in either encoding. The current
decimal scope is the BCD integer modes, so a decimal floating-point
family has no mode to be realized under.

### What the repository already carries

* **The BCD integer formats**: `bcd<D>` is a format of the verify layer
  (`chialu/verify/formats.py`), and `bcd_8421` is a coding a structure
  can name.
* **The decimal integer families**: the library realizes the
  `bcd_adder`, `bcd_multiplier` and `bcd_divider` kinds, whose families
  are `bcd_direct_addition`, `speculative_decimal_addition`,
  `redundant_decimal_addition`, `decimal_multioperand_addition`,
  `parallel_decimal_multiplication`, `decimal_digit_recurrence` and
  `decimal_newton`. The synthesis database carries their rows.
* **The cards and the space text**: the nine families' cards are under
  `legacy/knowledge/deferred/arch/decimal/`, and `decimal_misc_space` is
  kept verbatim in `legacy/knowledge/deferred/spaces_deferred.py`.

### What the version has to build

* **The formats in the verify layer**: decimal32, decimal64 and
  decimal128 as format descriptors, with the densely packed decimal
  (DPD) and the binary integer decimal (BID) encodings of IEEE 754-2019
  clause 3.5, since the two encodings put the same value in different
  bit patterns and a conformance judge compares bit patterns.
* **The cohort and preferred-exponent rules of IEEE 754-2019 clause 5**,
  which decide the exponent of a result whose value several
  representations carry, so the reference produces the representation
  the standard requires rather than any member of the cohort.
* **A unit template with decimal floating-point modes**, which opens the
  slots the nine families fill and carries the decimal rounding modes,
  including the two decimal-only ones.
* **The reference and the stimulus**: a decimal reference in
  `chialu/verify` that computes in the decimal format rather than in
  binary, and vectors that reach the cohort and preferred-exponent
  cases.

### The families that return

`decimal_fp_addition`, `bid_fp_addition`, `decimal_fma`,
`decimal_fp_multiplication`, `decimal_encoding_codec`,
`binary_decimal_conversion`, `redundant_decimal_conversion`,
`decimal_cordic_transcendental` and `commercial_decimal_fpu`.
`iterative_decimal_multiplication` returns with subject 1 rather than
with this one, since cycles rather than the format defer it.
