# redundant_high_radix_cordic

CORDIC with the iteration additions in redundant form: the x, y and
angle recurrences keep their operands as carry-save or signed-digit
vectors, so each microrotation costs a constant time independent of the
word length, and the rotation direction is chosen from a truncated
prefix of the scaled residual rather than its full sign. Reading only a
few digits forces a zero direction into the digit set, which makes the
scale factor K data-dependent, so each member adds a mechanism that
restores a constant or computable scale: double rotations, a correcting
iteration every m steps, an on-the-fly 1/K, branching on both
directions, a differential reformulation, or a per-angle scale at radix
4.

The residual arithmetic sets the selection error and the cell:
signed-digit truncation after one fractional digit errs by at most a
half, carry-save by up to one, and a signed-digit residual is preferred
where absolute values are negated, since carry-save negation needs a
deferred correction; a conventional carry-propagate residual at radix 4
halves the gate count for 1.3x the delay of the carry-save form. The
radix trades microrotations against selection and scale work: radix 4
with directions in -2 to 2 and powers-of-four shifts needs n/2
microrotations for n bits, half the radix-2 count, selects after
assimilating five or six bits, and pays with a scale factor between 1.0
and 2.52 that is evaluated per angle from a small table plus shift-adds
and applied by a linear-CORDIC multiplication, in circular rotation
mode only. The scale handling is the family's open question. Double
rotation keeps K constant at a larger value with a wider convergence
interval; a correcting iteration every m steps is cheap but variable;
restricting the directions to -1/+1 by branching runs two conventional
modules in parallel and keeps K constant at about twice the area; zero
directions that adjust the vector length in the middle iterations and
freeze it late take about (9n-3)/8 iterations against at least 3n/2 for
repeated iterations, a 25 percent gain in latency and area; and the
differential form encodes the sign sequence so every conventional
microrotation is retained, 3.5N+1 full-adder delays against 3.75N with
N rather than 1.5N stages, at the cost of more latches. A coarse-table
plus fine-rotation split is the hybrid the structure offers.

The execution is fixed-iteration and the family wins in spatial or
pipelined arrays where the iteration time, not the count, bounds
throughput; zero skipping removes about a fifth of the average
iterations, and known angles allow stored, zero-rich direction
sequences with the angle path removed. Accuracy matches conventional
CORDIC with about log2 N guard digits plus one for the redundant
representation; no concurrent check is reported.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: the unrolled rotations with the angle residual in carry-save or signed-digit form, the direction from a window estimate with the {-1, 0, 1} digit set, `scale_handling` double_rotation or correcting_iterations, `coarse_fine_hybrid` a rotation table before the fine iterations; radix 4 and the other scale handlings fall back to the radix-2 recurrence with correcting iterations). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family redundant_high_radix_cordic --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### residual_arithmetic

| member | what it selects |
| --- | --- |
| `carry_save` | the residual is a sum and carry pair. |
| `signed_digit` | the residual is a signed-digit pair. |
| `conventional_cpa` | the residual is assimilated every iteration, which is the non-redundant recurrence. |

### scale_handling

| member | what it selects |
| --- | --- |
| `double_rotation` | every step rotates twice, which makes the gain a constant the schedule fixes. |
| `correcting_iterations` | extra correcting iterations are inserted into the schedule. |
| `digit_set_restriction` | the digit set is restricted so the gain stays constant; the module's header records that correcting iterations stand in its place. |
| `online_scale_computation` | the scale is computed alongside the iterations; the header records the same substitution. |
| `virtually_scaling_free` | a schedule whose gain is one by construction; the header records the same substitution. |
| `differential_constant_scale` | the gain is held constant by a differential schedule; the header records the same substitution. |

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
duprat_1993 -> J. Duprat, J.-M. Muller, "The CORDIC Algorithm: New Results for Fast VLSI Implementation", IEEE Transactions on Computers, vol. 42, no. 2, pp. 168-178, 1993
dawid_1996 -> H. Dawid, H. Meyr, "The Differential CORDIC Algorithm: Constant Scale Factor Redundant Implementation without Correcting Iterations", IEEE Transactions on Computers, vol. 45, no. 3, pp. 307-318, 1996
timmermann_1992 -> D. Timmermann, H. Hahn, B. J. Hosticka, "Low Latency Time CORDIC Algorithms", IEEE Transactions on Computers, vol. 41, no. 8, pp. 1010-1015, 1992
antelo_1997 -> E. Antelo, J. Villalba, J. D. Bruguera, E. L. Zapata, "High Performance Rotation Architectures Based on the Radix-4 CORDIC Algorithm", IEEE Transactions on Computers, vol. 46, no. 8, pp. 855-870, 1997
