# srt_radix2

Digit-recurrence division with the redundant quotient digit set
{-1, 0, 1}: each iteration selects one digit from an estimate of the
shifted partial remainder, forms the next remainder as 2(PR - D),
2PR or 2(PR + D), and needs no divisor bits and no fractional
remainder bits for the selection, so three most-significant residual
positions summed in a short adder classify the remainder, and a
digit of zero covers the interval whose sign cannot be determined
and lets later iterations counterbalance it. The partial remainder
stays in carry-save form so each stage has constant delay and the
full sum is deferred to the last stage.

The residual form trades recurrence delay against storage: carry-save
residuals give a constant-delay stage but double the residual
registers, complicate selection and need a final assimilation when
the remainder is required, while a two's-complement residual keeps
one register at a full carry-propagate delay per iteration. The
estimate width is fixed by the remainder bound, since three
inspected digits are necessary and sufficient; trimming the
remainder path and short adder from 4 to 3 bits with modified
selection equations and a force-next-digit flag for the aliased sign
gains about 5 percent. Quotient prediction overlaps the selection,
the remainder formation, both, or only the critical high-order
remainder bits across cascaded stages; three speculative
carry-propagate branches per stage buy 40 percent over the
sequential arrangement, and overlap beyond three stages is limited
by exponential growth of the selection blocks. The digit-select
slot holds the table, which at radix 2 is the smallest of any radix,
or an equivalent set of selection equations.

The family is a fixed-iteration divider at one bit per stage:
reasonable implementations cost 4 to 5 FO4 per bit and about 6000
transistors per bit per cycle in 1 um CMOS, dual-rail domino runs
1.7 times faster at 1.6 times the area of static, the Pentium 4
double-pumps two quotient or square-root bits per clock with a
typical divide latency of about 60 clocks, and a fully unrolled
combinatorial array reaches O(n) delay at O(n^2) area. Radix 2 wins
on selection simplicity and ring area; overlapped radix 4 was
estimated faster (150 against 160 ns for 54 bits in 1.2 um) but
needs five larger carry-propagate branches instead of three and
about 18 against 10 mm2. Rounding uses a guard digit and the final
remainder sign, and a negative remainder may need restoration.

The seed instantiates the library's generated divider for this family
(`chialu/targets/rtl/families/div.py`: the unrolled radix-2 recurrence with a carry-save or assimilated residual (`residual_form`), the digit from the `digit_select` slot (the generated table over the residual estimate in its encoding and folding, or comparators against its thresholds through the comparator adder), the divisor normalized through `norm_lzc` and `norm_shifter` and the dividend scaled with it, the quotient on the fly or as Q+ minus Q- (`quotient_conversion`); as a square root the same recurrence in the halved residual form). `python3 -m chialu.targets.rtl.families.div --width 32 --family <family> --pins k=v,...` emits it for a rewrite (`--sqrt` for the square root).

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
| `twos_complement_cpa` | the residual is assimilated every iteration into one two's complement word. |

## references

oberman_1997 -> Oberman, Flynn, "Division Algorithms and Implementations", IEEE Transactions on Computers, 1997
harris_1997 -> Harris, Oberman, Horowitz, "SRT Division Architectures and Implementations", 13th IEEE Symposium on Computer Arithmetic, 1997
williams_1991 -> Williams, Horowitz, "A Zero-Overhead Self-Timed 160-ns 54-b CMOS Divider", IEEE Journal of Solid-State Circuits, 1991
zuras1986 -> D. Zuras, W. H. McAllister, "Balanced Delay Trees and Combinatorial Division in VLSI", IEEE Journal of Solid-State Circuits, vol. 21, 1986
burgess_1995 -> Burgess, Williams, "Choices of Operand Truncation in the SRT Division Algorithm", IEEE Transactions on Computers, 1995
noll_1991 -> Noll, "Carry-Save Architectures for High-Speed Digital Signal Processing", Journal of VLSI Signal Processing, 1991
hinton_2001 -> G. Hinton, D. Sager, M. Upton, D. Boggs, D. Carmean, A. Kyker, P. Roussel, "The Microarchitecture of the Pentium 4 Processor", Intel Technology Journal, Q1, 2001.
