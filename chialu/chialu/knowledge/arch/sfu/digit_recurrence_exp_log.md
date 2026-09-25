# digit_recurrence_exp_log

Exponential and logarithm by digit recurrence over the constants ln(1 +
d r^-i): a logarithmic residual and an exponential state advance
together, the state multiplied by (1 + d_i r^-i), which is a shift and
an add, while the residual has the tabulated ln(1 + d_i r^-i)
subtracted. Digits driving the residual to zero yield exp of the
argument; digits driving the state to one, with the constants
accumulated, yield log, which is multiplicative normalization of the
argument. Restoring variants pick digits 0/1 by comparison, one bit per
step; redundant variants use signed digits, a signed-digit or
carry-save residual, and select each digit by rounding a short prefix
of the scaled residual.

The radix sets the iteration count, about n/k iterations in radix 2^k,
against table and selection cost: the radix-16 algorithm with digits in
-10 to 10 takes roughly 1.5x the hardware and 3x the ROM of radix 2 for
about 4/3 the average performance, so the efficiency is about equal,
and in the high-radix units radices 32 to 128 are the efficient range,
since table area grows exponentially with radix. A high radix also
breaks the first iteration, where the selection intervals do not cover
the residual, so that step starts at n=2 with a small convergence
domain, uses a special correction factor, or takes its digit from a
table. The normalization is multiplicative for the logarithm and
additive for the exponential in the units that compute both, with the
result formed from the same continued-product factors. The digit set
trades a constant-time step against the selection logic: a nonredundant
restoring step compares the full word, a signed-digit or carry-save
residual removes the carry but needs overlapping selection regions and
a four-digit prefix or a small table to pick the digit, and a full-word
comparison would give the speed back. Selection by rounding holds from
the third iteration on. Two accelerations skip iterations:
data-dependent bit skipping advances the index by the leading-zero
count and ends with a linear extrapolation, averaging 6.2 iterations
for 24 bits, and Baker's prediction takes a block of digits from the
residual's binary expansion with one correction per block.

The execution is fixed-iteration, about n steps for n bits at radix 2
and the same order as CORDIC, without CORDIC's scale factor when the
complex BKM form is used. The family composes: log, a left-to-right
multiplication and exp give powering in one overlapped sequential
datapath, at about 100 tau and 5964 full-adder units for 32-bit fixed
point against 120 tau and about 6000 for a high-radix CORDIC. The
accuracy contract is a relative error below 2^-n+1 for exp and an
absolute error of the same size for log before rounding, or a
faithfully rounded result once guard bits are sized; no concurrent
check is reported.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: the unrolled multiplicative normalization over ln(1 + d radix^-i) constants with the `digit_set` and `selection`, `termination` linear_extrapolation after half the stages). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family digit_recurrence_exp_log --pins k=v,...` emits the module with its modeled error for a rewrite.

The real implementation distinguishes the two digit sets in both cores.
For logarithm with `nonredundant`, the centred significand `m` is folded
to `r=m/2` when `m>1`, otherwise `r=m`, and the logarithm accumulator
receives the corresponding integer offset. Thus `r` starts in `[1/2,1]`
and every selected digit belongs to `0..radix-1`. The threshold selector
takes the largest digit whose multiplicative update stays at or below
one. Rounded selection uses the scaled residual and corrects an unsafe
digit by one before updating the state. The signed variant keeps its
centred input and signed digit set. Negative log constants are rounded
with the same nearest-integer rule as positive constants.

`chialu.verify.digit_recurrence_ref` provides an independent integer
contract. It recomputes every log constant using rational series bounds
and does not invoke `Net` callbacks. The fixture command below checks
the result and every selected digit for all 256 input patterns over the
48 combinations of core, radix, digit set, selection and termination;
two further cases check 64 output fraction bits.

```
python -m chialu.verify.digit_recurrence_selftest --wide --error-bounds
```

`error_enclosure` enumerates the entire contracted **core** input domain
and bounds the true exponential/logarithm with rational series. It returns
an explicit incomplete result when the requested enumeration limit is
exceeded. These bounds do not include whole-seed range reduction,
reconstruction, special values or approximate child arithmetic. The
survey's accuracy claims above are not a proof for every generated pin
combination or an automatic substitute for the user's target contract.

## design choices

### normalization

| member | what it selects |
| --- | --- |
| `multiplicative` | retain the one-centered state and multiply it by the selected normalization factor. |
| `additive` | store the zero-centered delta and add its digit-weighted correction with a separate digit bias. |

The [additive contract](digit_recurrence_exp_log/additive.md) records the
operation-dependent terminology, this project's physical state definition,
and the independent verification scope. Both choices support the real
digit/selector/radix/termination/advancement product. Complex BKM remains
unimplemented.

### index_advance

| member | what it selects |
| --- | --- |
| `sequential` | the iteration index advances by one per step. |
| `leading_bit_skip` | real radix-2/4/16 uses a leading-zero detector, exact threshold correction, a variable factor-table address and a variable shift. Both selectors, both digit sets and both termination choices are implemented. |

`python -m chialu.verify.digit_recurrence_selftest --skip-only --wide --error-bounds`
checks physical indices and digits against an independent scan of the exact
digit conditions. It reconstructs the sequential schedule and checks that
each omitted digit is zero. The full family entry test checks skip/sequential
RTL equivalence; its scope does not include an independent whole-seed golden.
The radix-4/16 checks include partial final stages whose quantized log factor
is zero while the selected digit is nonzero. Such a digit still changes the
other recurrence state and cannot be removed as a zero update.
Rounded residual selection uses a variable left shift, nearest-integer
selection, digit clamping and the algorithm's one-digit safety correction.
Its zero residual selects no digit, including partial final stages.
For signed rounded selection, positive and negative half-step thresholds
differ: ties round toward positive infinity, so a positive half-step
selects +1 while a negative half-step initially selects zero. The skip
schedule preserves this asymmetry and the next negative digit.
Signed table lookup retains the ceiling of adjacent exponential-factor
midpoints and exact reciprocal-midpoint comparisons for logarithms. Its
reference compares doubled residuals or exact integer products instead of
replaying the RTL threshold construction. Directed vectors distinguish a
floor midpoint from the required ceiling; changing one RTL table entry to
the floor is rejected by the independent test.

### selection

| member | what it selects |
| --- | --- |
| `table_lookup` | the digit comes from a table over the residual estimate. |
| `rounding_of_scaled_residual` | the digit is the rounded scaled residual, which needs no table. |

### state_domain

| member | what it selects |
| --- | --- |
| `real` | the recurrence runs on a real residual. |
| `complex_bkm` | not yet implemented; explicit requests fail rather than using the real recurrence. |

### termination

| member | what it selects |
| --- | --- |
| `iterate_to_full_precision` | the recurrence runs until the residual reaches the target precision. |
| `linear_extrapolation` | the last bits come from a linear extrapolation rather than further iterations. |

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
ercegovac_1973 -> M. D. Ercegovac, "Radix-16 Evaluation of Certain Elementary Functions", IEEE Transactions on Computers, vol. C-22, no. 6, pp. 561-566, 1973
chen_1972 -> T. C. Chen, "Automatic Computation of Exponentials, Logarithms, Ratios and Square Roots", IBM Journal of Research and Development, vol. 16, no. 4, pp. 380-388, 1972
bajard_1994 -> J.-C. Bajard, S. Kla, J.-M. Muller, "BKM: A New Hardware Algorithm for Complex Elementary Functions", IEEE Transactions on Computers, vol. 43, no. 8, pp. 955-963, 1994
pineiro_2004 -> J.-A. Pineiro, M. D. Ercegovac, J. D. Bruguera, "Algorithm and Architecture for Logarithm, Exponential, and Powering Computation", IEEE Transactions on Computers, vol. 53, no. 9, pp. 1085-1096, 2004
vazquez_2013 -> A. Vazquez, J. D. Bruguera, "Iterative Algorithm and Architecture for Exponential, Logarithm, Powering, and Root Extraction", IEEE Transactions on Computers, vol. 62, no. 9, pp. 1721-1731, 2013
