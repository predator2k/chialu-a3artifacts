# table_factor_refinement

The Wong-Goto rectangular-multiplier method: the residual is driven to
0 or 1 by one to three stages, each extracting a short chunk of the
residual, reading a tabulated correction factor addressed by that
chunk, and applying it through a rectangular multiplier while the
remaining error propagates to the next stage; a truncated Taylor series
or a table lookup on the final residual ends the refinement. The
logarithm reuses the reciprocal's K1/K2/K3 factors, the exponential
splits its fixed-point argument into short fields and multiplies
tabulated exponentials, the reciprocal square root applies half-sized
factors, and atan2 and sine/cosine rotate by complex factors of
truncated components.

factor_bits sets the width of the extracted chunk and of the tabulated
factor, and residual_stages sets how many factor stages precede the
tail; together they set the table size and the number of rectangular
multiplications on the path. terminal_correction and tail_degree set
how the final residual is retired, by a truncated series in the
tail_evaluator slot or by a table of squares. multiplier_shape and
rectangular_multiplier_count size the specialized multipliers: the
stated double-precision implementation uses a 16 by 56 multiplier that
runs in slightly more than half a full double multiplication time, and
the peak need is one or two of them depending on the function.
function_set names the operation the stage sequence serves, and
unified_hardware time-shares one datapath across all of them. The
range_reducer supplies the reduced argument in [0, pi/2) for sine and
cosine and the prespecified-base range for the logarithm.

The family wins where several double-precision functions must share
one multiplier-based datapath: the analytical latencies in full
double-multiplication units run from 3.68 for division to 7.06 for
atan2, with the logarithm, the reciprocal square root and sine/cosine
between, and the tables for all functions together fit in high-speed
SRAM. Against lut_plus_poly, which selects the coefficients of one
local polynomial, the stages normalize by whole table-derived factors
and propagate the residual between them; against
digit_recurrence_exp_log, which normalizes over ln(1 +- 2^-i) constants
one shift-add step per digit, each stage retires a whole chunk of the
residual through a multiplier. It loses where a single narrow function
needs no multiplier or where the table set is unaffordable.

The accuracy contract is a relative error within 0.5 ulp for each
function by analytical proof over its supported range, with guard bits
in the denormalization for atan2, and within 1 ulp for the logarithm
once the 56-bit intermediate is rounded to the 53-bit double. The
stages are a fixed unrolled sequence, so the family is feed-forward;
the unified hardware time-shares the stages across functions.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: the Wong-Goto stages, a `factor_bits` seed table and `residual_stages` residual-driven factors through rectangular multipliers, a Taylor or table-square tail of `tail_degree`; reciprocal, roots, the exponential by factor tables and the logarithm by factor stages). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family table_factor_refinement --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### function_set

| member | what it selects |
| --- | --- |
| `division` | the tables and the tail cover division. |
| `logarithm` | they cover the logarithm. |
| `reciprocal_square_root` | they cover the reciprocal square root. |
| `exponential` | they cover the exponential. |
| `atan2` | they cover the two-argument arctangent. |
| `sine_cosine` | they cover the sine and the cosine. |

### multiplier_shape

| member | what it selects |
| --- | --- |
| `rectangular` | the refinement multiplies are rectangular, which is narrower on one operand. |
| `full_square` | they are full-width squares. |

### terminal_correction

| member | what it selects |
| --- | --- |
| `truncated_taylor` | the tail is a truncated Taylor expansion. |
| `table_square` | the tail comes from a table of the squared residual. |

## references

wong_1994 -> W. F. Wong, E. Goto, "Fast Hardware-Based Algorithms for Elementary Function Computations Using Rectangular Multipliers", IEEE Transactions on Computers, vol. 43, no. 3, pp. 278-294, 1994
muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
