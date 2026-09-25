# Family verification

The complete Cartesian-product scope is tracked separately in [Complete variant coverage](full-variant-verification.md). The database enumeration described below remains the acceptance scope of the original four-step plan.

`chialu.targets.rtl.families.selftest` selects the points that `chialu.synthdb.points()` enumerates.

* The default run selects the first point of every family at every dense width and eight additional points per kind and width.
* An explicit `--kinds` or `--widths` scope selects every point within that scope unless `--sample` limits the additional points.
* `--sample N --seed S` retains every family baseline and selects N additional points per kind and width deterministically.
* `--jobs N` limits concurrent simulations. Space workers run in separate processes so each worker has its own mpmath precision context.
* `--vectors N` sets the random vector count for exact points. Approximate points retain at least 1,500 random vectors because their contracts include a mean error.
* `--cases curated` retains the previous case lists for one release.

The nightly invocation covers the full enumeration:

```sh
python3 -m chialu.targets.rtl.families.selftest --cases space --all --jobs 8
```

The acceptance scope covers six kinds at two widths:

```sh
python3 -m chialu.targets.rtl.families.selftest --cases space \
  --kinds adder,multiplier,shifter,comparator,lzc,bitcount --widths 8,16
```

`results.jsonl` records each selected point's pins and status in the reported work directory. Converter failures and converter timeouts have status `skipped` and include the source size in bytes. Unrealized points and declared reference gaps have separate counts. Simulation failures make the command fail.

`chialu.verify.family_ref` defines each adapter's ports, input domain and expected output patterns. `NO_GOLDEN` declares the contracts absent from the format-level reference. Internal float, posit, dot and SFU representations retain their existing harnesses. A modular arithmetic component inside a binary arithmetic slot has no matching binary operation contract. An approximate component inside another arithmetic module needs a bound for the composed error.

`Tolerance` records maximum and mean error. Absolute error is divided by `scale`. Relative error is divided by the magnitude of the exact result. `minimum` restricts a relative contract to its specified result range. Block boundaries determine the scale of segmented adders. The omitted partial-product region determines the bounds of truncated multipliers. Wider approximate regions have correspondingly weaker numerical guarantees.

The enumeration checks run independently of simulation:

```sh
python3 -m chialu.verify.family_ref_selftest
python3 -m chialu.verify.family_space_selftest
```

The float and posit harnesses allow 7,200 seconds per simulation. Their division and square-root cases can exceed the previous 900-second limit when suites run concurrently. The limit does not change their vectors or comparisons.

`family_tb` writes `vectors.hex` and `expected.hex` with `tb_gen.write_hex`. The first declared input or output occupies the most significant bits of its respective file word. The generated bench writes `actual.hex` for diagnosis. Every exact output is compared, including the shifter's sticky bit and the prefix flags.

The maximum-error comparison uses integer cross multiplication. The mean-error comparison accumulates conservative fixed-point errors with 32 fractional bits. Corner vectors contribute to the maximum check. Seeded random vectors contribute to both checks, so the mean describes the random distribution rather than the frequency of selected corner patterns.

The comparator checks include corruption of an expected value at 8, 64 and 512 bits:

```sh
python3 -m chialu.verify.family_tb_selftest
```

The engine check covers all seven requested formats. Every format through 16 bits supplies every input pattern. Larger formats supply seeded samples. Binary operands use a permutation and a Cartesian product of corner patterns. The add function is checked with both subtraction-control values. Packing probes include exact values and values below, at and above rounding midpoints. Every engine rounding code is exercised. Posit modes follow the frozen pattern rules, including their RTZ behavior; the SR word has no effect on posit rounding.

```sh
python3 -m chialu.verify.engine_selftest
python3 -m chialu.verify.sfu_table_selftest
```

Both commands test a deliberate mutation. The engine mutation adds one ulp during packing. The table mutation evaluates sigmoid at the format's significand precision. Each command requires its mutation to fail. The mutations can also run directly and return a failing exit status:

```sh
python3 -m chialu.verify.engine_selftest --formats fp8e4m3 --mutate-rounding
python3 -m chialu.verify.sfu_table_selftest --formats fp8e4m3 --functions sigmoid --working-precision format
```

GELU's negative tail uses `erfc(-x / sqrt(2))` to avoid cancellation in `1 + erf(x / sqrt(2))`. At `posit8_0` input `0x85`, which represents -14, the reference returns `0xff`. A regression checks both `ops.sfu_ref` and the table checker at that input. This approved GELU correction is the only change to `ops.py`.

The engine check compares result patterns and unpacked fields. Exception flags beyond the unpacker's denormal flag remain under the family harnesses because `ops.py` does not return those flags.

Pattern tables use adapters for the scalar contracts that `ops.py` expresses. The reciprocal adapter applies the input's zero sign through `fneg`, because the scalar SFU reference omits that sign.

The unpacker adapter checks both stored and normalized significands. The integer dot adapter calls `dot_ref` with the module's wide accumulator format. Approximate dividers remain `NO_GOLDEN` because their remainder ports lack an error contract. The curated divider bench retains its quotient-only bound for the compatibility release. Other outputs outside a tolerance are compared exactly.

The completed acceptance runs cover 56,517 enumerated points and 2,280 eligible simulations in the six-kind scope. The engine run checks 2,523,924 vectors across all seven formats. Additional space runs check 45 unpacker cases and 361 integer-dot cases. The table test checks and simulates all 60 direct/compressed tables. Both mutation tests reject the deliberate error.

The existing harnesses pass with 133 float cases, 263 dot cases, 68 posit cases and 516 SFU modules built. `synthdb.py`, `characterize.py`, the format definitions and the integer-family `run_case` remain unchanged.
