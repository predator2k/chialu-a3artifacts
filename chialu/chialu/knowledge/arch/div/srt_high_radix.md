# srt_high_radix

Digit-recurrence division at radix beta = 2^k: each iteration computes
R(j+1) = beta R(j) - q_j D with a quotient digit from a redundant
symmetric set {-a..a}, ceil(beta/2) <= a < beta, and retires k
quotient bits, so a p-bit quotient takes about p/k iterations. The
redundancy makes valid-selection regions overlap, so the digit is read
from a small table indexed by a few leading divisor bits and a few
leading bits of the shifted residual, which stays in carry-save form
and is assimilated only over the inspected bits. Radix above 4 is assembled from radix-2 or radix-4 stages,
cascaded or overlapped, with later selection stages replicated for
each possible earlier digit.

Radix trades iteration count against the selection path. Iterations
fall from 27 to 18 to 14 cycles for a 53-bit quotient at radix 4, 8,
and 16, but table delay grows linearly and table area quadratically
with radix, and radix 8 and above need divisor multiples that are not
shifts, so a single stage stays at radix 2 or 4 and higher radix comes
from staging. Two overlapped radix-4 stages give the S-1 Mark IIB its
radix 16 at two to three times the cost of radix-2 nonrestoring
hardware and about four times its speed in the same ECL technology;
radix 8 comes from a radix-4 stage overlapped with a radix-2 stage,
and three overlapped radix-4 iterations retire six bits per cycle at
much more area. Duplicating the remainder computation once nearly
halves cycle time. The practical ceiling is under
10 quotient bits per cycle.

Digit redundancy trades divisor multiples against selection width. The
minimal set needs only d and 2d, so one adder with conditional
doubling suffices; the maximal set needs a precomputed 3d but makes
selection faster and smaller; intermediate sets are the most
practicable for a monolithic higher-radix stage, which the library
builds as radix-4 sub-stages instead. Larger digit sets reduce the divisor and
residual bits the table examines, about 3 log2 r digits in total;
divisor bits are cheaper than residual bits because the divisor is
constant and off the iteration path, and assimilating the residual
before the table halves its inputs at higher radix. Prescaling the
operands so the divisor sits near 1 makes selection depend on residual
bits alone or removes the table.

The final remainder is exact, so rounding needs no back-multiplication
and uses the remainder sign and zero test. Correctness rests on every
table entry keeping the residual inside its bound: the five Pentium
entries that returned 0 instead of +2 left the recurrence unable to
recover, with relative error up to 2^-14. The family is fixed-iteration and wins for
short and extended formats and wherever a multiplier is not available
to share; it loses to multiplier-reusing units on area.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: radix-4 sub-stages with digits -2..2 or -3..3 (`digit_redundancy`) and a carry-save or assimilated residual (`residual_form`), radix 8, 16 and 32 as cascades of radix-4 and radix-2 sub-stages whose selections overlap over `overlapped_stages` (the later selections speculated per candidate digit of the earlier ones, the candidate residuals through the residual adder), the digit from the `digit_select` slot (the generated selection table as a case ROM over the truncated divisor and residual estimate, every cell checked for containment at generation, in its digit encoding and folding; or comparators against its thresholds), the divisor normalized through `norm_lzc` and `norm_shifter`, its non-shift multiples through `residual_adder`, the quotient on the fly or as Q+ minus Q-). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

## design choices

### quotient_conversion

| member | what it selects |
| --- | --- |
| `on_the_fly` | the quotient and its decrement are kept in conversion registers and appended per digit, so no carry-propagate add closes the loop. |
| `separate_positive_negative` | the positive and negative digit weights accumulate in two words subtracted at the end. |

### residual_form

| member | what it selects |
| --- | --- |
| `carry_save` | the residual stays a sum and carry pair, so the recurrence has no carry-propagate adder. |
| `irredundant` | the residual is assimilated every iteration, which shortens the digit estimate at the cost of a carry-propagate add in the loop. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the residual stays redundant and the quotient converts without a final add | - | `the residual carry-save.*quotient by on_the_fly` |

## references

robertson_1958 -> Robertson, "A New Class of Digital Division Methods", IRE Transactions on Electronic Computers, 1958
atkins_1968 -> Atkins, "Higher-Radix Division Using Estimates of the Divisor and Partial Remainders", IEEE Transactions on Computers, 1968
taylor_1985 -> Taylor, "Radix 16 SRT Dividers with Overlapped Quotient Selection Stages", 7th IEEE Symposium on Computer Arithmetic, 1985
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
harris_1997 -> Harris, Oberman, Horowitz, "SRT Division Architectures and Implementations", 13th IEEE Symposium on Computer Arithmetic, 1997
oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
burgess_1995 -> Burgess, Williams, "Choices of Operand Truncation in the SRT Division Algorithm", IEEE Transactions on Computers, 1995
pratt_1995 -> Pratt, "Anatomy of the Pentium Bug", TAPSOFT/CAAP, LNCS 915, 1995
