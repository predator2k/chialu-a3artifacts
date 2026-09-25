# comparator_digit_selection

Quotient-digit selection by parallel comparison rather than a stored
table: a short estimate of the shifted residual enters a bank of
comparators, each a short subtractor with a sign detector, that test
it against the selection constants m_k or against precomputed divisor
multiples, and a coder turns the vector of signs into the digit.
Radix-4 minimal redundancy needs four comparators on the top eight
remainder bits, and the one-hot digit they produce selects among
candidate residuals computed in parallel, so no further
carry-propagate lies on the path; a decimal recurrence tests a
truncated two-word estimate against ten constants and codes a
sign-magnitude digit.

comparison_bits sizes the bank's estimate; the digit set fixes the
count: four comparators for radix-4 minimal redundancy, nine with
symmetry_folding or eighteen without for a decimal digit set, and ten
for the constants m(-4) through m(5), each over eight remainder bits
or four decimal digits. residual_input decides whether the comparators
see an assimilated estimate, which puts one carry-propagate on the
path before the bank, or the redundant two-word estimate, which each
comparator reduces with a 3:2 stage of its own. The constants are
hardwired (the thresholds of the digit set's overlap intervals; a
decimal recurrence forms divisor multiples at initialization instead).
output_encoding is what the host
recurrence consumes: one-hot drives a candidate multiplexer, and
sign-magnitude with a one-hot magnitude and a BCD-5211 copy serves
the decimal recurrences. speculative_candidate_residuals computes the
next residual for every digit in parallel and lets the digit select
it, and the comparator_adder slot is each comparator's subtractor.

The family replaces qds_table where the table's delay is the problem:
the VFP11 comparator path runs at 15.4 FO4 against 16.0 FO4 for the
F_k path, and the decimal divider with comparison multiples reaches
1332 FO4 for a decimal128 division in 0.18 um against 1733 and 3772
FO4 for the table-driven baseline, with its partial-remainder sign
detectors duplicated outside the iteration's critical path. Ten
decimal comparators cost about 3200 NAND2 for a 22.3 FO4 selection
stage. At any radix, added comparators and divisor-multiple generators
select a digit in one addition cycle from the first three or four
signed digits of the residual, where the simplest signed-digit divider
adds or subtracts the divisor repeatedly. The component is
feed-forward and the host recurrence carries the iteration; the
family has no exhaustive-check choice as qds_table does, and the
constants are set by the digit set's selection intervals.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: 2a comparators per divisor row against the thresholds of the generated table, each the `comparator_adder` family's subtractor over `comparison_bits` of the estimate (assimilated by that adder, or the two residual words through a 3:2 row per comparator under `residual_input`), folded on the estimate's sign under `symmetry_folding`, the passes coded into the binary, one-hot, zero-one-hot or sign-magnitude digit (`output_encoding`); `speculative_candidate_residuals` forms every candidate residual in carry-save form and lets the digit select one). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## design choices

### output_encoding

| member | what it selects |
| --- | --- |
| `binary` | the digit as a signed binary word. |
| `one_hot` | one line per digit value, set when the threshold below it passed and its own did not. |
| `zero_one_hot` | the same lines without one for the zero digit, so a zero digit is the all-clear word. |
| `sign_magnitude` | the sign from the zero threshold and the magnitude from the thresholds passed beyond it. |

### residual_input

| member | what it selects |
| --- | --- |
| `assimilated_estimate` | the comparators read one assimilated estimate of the residual. |
| `redundant_two_word` | the comparators read the carry-save pair itself, which removes the estimate's adder from the recurrence; folding needs the assimilated estimate, so the two forms do not combine. |

## references

burgess_2007 -> N. Burgess, C. N. Hinds, "Design of the ARM VFP11 Divide and Square Root Synthesisable Macrocell", Proc. 18th IEEE Symposium on Computer Arithmetic (ARITH-18), pp. 87-96, 2007.
nikmehr_2006 -> Nikmehr, Phillips, Lim, "Fast Decimal Floating-Point Division", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, 2006
avizienis_1961 -> Avizienis, "Signed-Digit Number Representations for Fast Parallel Arithmetic", IRE Transactions on Electronic Computers, 1961
