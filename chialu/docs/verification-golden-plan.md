# One Python golden for the family library

This specifies four changes that make every module the family library
generates verifiable against one Python reference, and make the set of
verified points the same set the synthesis database measures. The four
are ordered: each stands on the one before it.

## What is true today

The Python reference exists and is complete over formats.
`chialu/verify/ops.py` exports `int_ref(op, fmt, a_bits, b_bits,
out_fmt)`, `fp_ref(op, fmt, a_bits, b_bits, rounding, out_fmt)`,
`sfu_ref(fn, fmt, x_bits, rounding, daz, ftz)`, `sfu_vector_ref`,
`dot_ref(elem_fmt, acc_fmt, a_lanes, b_lanes, c_bits)` and `cvt_ref`.
Its SFU functions are correctly rounded through adaptive-precision
mpmath. The ALU seed is verified against it: `chialu/verify/harness.py`
writes `vectors.hex` and `expected.hex` from it, and the testbench only
compares.

The family library is not verified against it. Four spaces use four
different references:

| space | reference | where it lives |
| --- | --- | --- |
| integer families (adder, multiplier, divider, shifter, comparator, count, bcd, redundant) | a SystemVerilog expression written inside each testbench function | `chialu/targets/rtl/families/selftest.py`, e.g. `ref = "$signed(a) * $signed(b)"` at line 124, `exp = {1'b0, a} + {1'b0, b} + cin` at line 713 |
| float families | the engine, emitted as a SystemVerilog package | `chialu/targets/rtl/engine.py`, driven by `chialu/targets/rtl/families/fptest.py` |
| dot and posit families | the same engine | `chialu/targets/rtl/families/dottest.py`, `posittest.py` |
| SFU families | `chialu/verify/sfu_ref.py` through `reference_bits` | `chialu/targets/rtl/families/sfu.py:4193` |

Within one space the reference is shared, so `tb_mul` serves every
multiplier family and the engine serves every float family. Across
layers it is not: the family library compares against a SystemVerilog
expression or against the engine, the ALU seed compares against
`chialu/verify/`, and nothing checks those against each other. The
engine is validated only where a seed happens to exercise it.

The verified set is also much smaller than the measured set. The
selftest cases are hand-written lists rather than an enumeration of the
spaces. At width 16:

| selftest case group | kind | cases |
| --- | --- | --- |
| `adder_cases` + `adder_ext_cases` + `prefix_cases` | adder | 213 |
| `mul_cases` + `mul_ext_cases` + `subword_cases` | multiplier | 202 |
| `approx_cases` | adder and multiplier | 66 |
| `redundant_cases` | sd_adder, rns_* | 79 |
| `bcd_cases` | bcd_* | 35 |
| `div_cases` | divider | 33 |
| `count_cases` | lzc, bitcount | 33 |
| `shifter_cases` | shifter | 24 |
| `cmp_cases` | comparator | 18 |
| `sqrt_cases` | fp_sqrt | 14 |
| `incr_cases` | incrementer | 5 |
| `logic_cases` | logic | 2 |
| total | | 724 |

`python3 -m chialu.synthdb` enumerates 5,057 points at width 16 and
31,531 over every kind at every width of the dense grid, including 807
multiplier points against 202 cases and 507 divider points against 33.
About six of every seven points the database synthesizes have never been
simulated. One consequence already found: the `parity_prediction_adder`
checker fails synthesis outright, and no test covers it.

One reference is circular. `chialu/targets/rtl/families/sfu.py:3899`
fills the `direct_lut` table with `reference_bits(fn, fmt, b)`, and line
4247 checks the result of the same call. For a table family the check is
an identity over the table's contents; it tests the module's addressing
and read-out path and nothing about the values.

## 1. A port-and-op adapter per kind

Write `chialu/verify/family_ref.py`. It maps a library module to a call
on `chialu/verify/ops.py`.

The entry point is

```python
def golden(kind: str, family: str, pins: dict, width: int) -> Adapter | None
```

where `Adapter` carries

* `ports`: the module's port names with their directions and widths, in
  the order the module declares them.
* `stimulus(n, seed)`: `[{port: int}]`, the input patterns, which are
  the corner patterns of the kind followed by `n` pseudo-random ones
  from `seed`.
* `expect(inputs)`: `{port: int}` for every output port, computed by
  `ops.py` alone.
* `tolerance`: `None` for a bit-exact family, or the error bound a
  family with an approximate contract is held to (`max_err`,
  `mean_err`, the same quantities `tb_mul_bound` and `tb_add_bound`
  carry today).

`golden` returns `None` for a (kind, family, pins) whose contract
`ops.py` does not express. Every such return must be listed in a module
constant `NO_GOLDEN` with the reason, so the gap is enumerable rather
than silent. The known cases to start from:

* a prefix adder's flag output `s1`, which is `s + 1` under `cin == 0`
  and has no op in `ops.py`.
* the redundant and signed-digit representations, whose ports carry a
  carry-save or borrow-save pair rather than a binary word.
* the RNS channel modules, whose ports carry residues under a modulus
  set.
* the intermediate structures with no ALU-level op: `rounder`,
  `unpacker`, `incrementer` where it is not `int_ref("add", …, 1)`.

For these, express the contract as a Python function in
`family_ref.py` itself rather than in a testbench, so every reference
stays on one side of the language boundary.

Acceptance: `golden` returns an adapter or a listed `NO_GOLDEN` reason
for every point of `synthdb.points(kind, width)`, over every kind and
every width of `synthdb.DENSE_WIDTHS`. A test asserts that, and prints
the count per kind.

## 2. The cases come from the database's enumeration

`chialu/targets/rtl/families/selftest.py` builds its jobs from
hand-written `*_cases(w)` functions. Replace that with the same
enumeration the database uses, so the verified set and the measured set
cannot drift apart.

* The point list is `chialu.synthdb.points(kind, width)`, which returns
  `[(family, pins, label)]` with `pins` binding every slot of the family
  and of every family bound under it.
* The module is `chialu.characterize.realize(kind, family, pins,
  width)`, which returns a `FAM.Module` with `.name`, `.params` and
  `.text`, or `None` where the library does not realize the point.
* `run_case(lib, name, tb, work, extra)` stays as it is: it closes the
  library over the testbench text, converts through the yosys frontend and runs
  verilator and the model.

Keep the existing `*_cases(w)` functions under a `--cases curated` flag
for one release, so a regression between the two sets is visible, and
make `--cases space` the default.

The full set is 31,531 points, which does not fit one run. Add
`--sample N` (a deterministic sample per kind, seeded), `--kinds`,
`--widths` and `--jobs`, and make the default run the baseline point of
every family at every width plus a sample of the slot points. A nightly
invocation runs the whole set.

Acceptance: `python3 -m chialu.targets.rtl.families.selftest --cases
space --kinds adder,multiplier,shifter,comparator,lzc,bitcount
--widths 8,16` passes, and its case count matches
`sum(len(synthdb.points(k, w)))` over those kinds and widths minus the
points `realize` returns `None` for and the points listed in
`NO_GOLDEN`.

## 3. The stimulus and the expected values are written by Python

Today a testbench computes the expected value in SystemVerilog. Move
that out: Python writes the vectors and the expected values, and the
testbench only compares.

* `family_ref.Adapter.stimulus` and `.expect` produce the two files,
  written in the format `chialu/verify/harness.py` already uses
  (`tb_gen.write_hex`, see `harness.py:325`).
* The testbench becomes one generated module per kind that reads
  `vectors.hex` and `expected.hex` with `$readmemh`, drives the ports in
  declaration order, compares, and prints `PASS` or `FAIL <n>`. One
  testbench generator serves every kind; the per-kind part is the port
  list, which the adapter carries.
* A family with a tolerance compares against the bound rather than the
  pattern, and the bound comes from the adapter rather than from a
  string substitution on the testbench text (which is what
  `selftest.py` does today at the `approx_cases` call site).

Delete every `ref = "..."` and `exp = ...` SystemVerilog expression from
`selftest.py` as its kind moves over. The float, dot and posit harnesses
keep the engine for now; item 4 covers the check that the engine and
`ops.py` agree.

Acceptance: `grep -n 'exp = ' chialu/targets/rtl/families/selftest.py`
returns nothing, and the run of item 2 still passes.

## 4. The engine and the tables against an independent source

Two references remain that are not `ops.py`.

**The engine.** `chialu/targets/rtl/engine.py` emits the SystemVerilog
the float, dot and posit harnesses compare against, and the seed's units
are built from it, so an error in the engine hides from both. Add
`chialu/verify/engine_selftest.py`: for every format the repository
uses (`fp16`, `bf16`, `fp8e4m3`, `fp32`, `posit8_0`, `posit16_1`,
`posit32_2`) and every engine function (`unpack`, `add`, `mul`, `lt`,
`eq`, `pack` under every rounding mode), simulate the engine package
alone against `fp_ref` and `cvt_ref` over every pattern of a format up
to 16 bits and a seeded sample above. This is the check that ties the
two references together.

**The tables.** `sfu.py:3899` fills `direct_lut` and `compressed_lut`
from `reference_bits`, which line 4247 then checks against. Give the
table a source independent of the checker: compute the entries at a
working precision at least twice the format's, round once into the
format, and keep `reference_bits` for the check alone. The two must
agree for a correctly rounded table; the point is that the agreement
becomes a result rather than an identity.

Acceptance: `python3 -m chialu.verify.engine_selftest` passes over every
format and function, and a deliberate one-ulp perturbation of the
engine's rounding makes it fail. The SFU table test fails when the
table's working precision is dropped to the format's own.

## Constraints

* The writing style of `CLAUDE.md` applies to every comment, docstring
  and document this work produces.
* No change to the row schema of `chialu/synthdb.py`. This work reads
  `points()` and `characterize.realize`; it does not alter them.
* `chialu/verify/ops.py` is the frozen reference semantics. Extend it
  only by adding a function for a contract it does not express, never by
  changing an existing one, and say in the commit what the new function
  is the reference for.
* Verilator are the simulation path, as `run_case` already uses
  them. A module the converter cannot carry is reported as a skipped
  case with its size, not as a pass.
* Every step keeps `python3 -m chialu.targets.rtl.families.fptest`,
  `dottest`, `posittest` and `sfutest` passing.
