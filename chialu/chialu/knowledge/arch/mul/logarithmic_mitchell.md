# logarithmic_mitchell

Multiplication through binary logarithms without a table: a
leading-one detector gives the characteristic of each operand, the
bits below the leading one are read directly as the fractional
logarithm, which is a straight-line approximation of log2 between
powers of two, the two approximate logarithms are added (subtracted
for division), and the antilog is decoded by shifting the fraction by
the characteristic, so a multiply costs two leading-one detections,
one addition and one shift. The product is always low, by up to 11.1
percent when both mantissas are one half and by nothing at powers of
two; the correction schemes add back an estimate of the missing
cross term of the two fractions.

correction_scheme buys accuracy with a second pass. Mitchell's own
correction adds a scaled approximation of the product of the two
fractions (or of their complements after a mantissa carry) through a
second logarithmic operation, which cuts the maximum error to about a
quarter, but successive operations of the same kind compound the error
because every error has the same sign, and too many corrections
remove the advantage over an iterative multiplier. Operand
decomposition rewrites X times Y as C times D plus A times B with the
four operands formed by bitwise OR, XOR and complement, runs two
Mitchell multiplications and one binary addition, and lowers the
probability of a 1 in the decomposed operands from a half to a
quarter, so average error falls by 44.7 percent; it combines with a
divided-approximation correction on a few mantissa bits at under 2
percent extra hardware, while a table of correction values or the
Mitchell correction adds about half again. The parallel form nearly
doubles the area and power of a bare Mitchell multiplier, still under
a third of a 32-bit array multiplier's power in 0.7 um, and the
sequential form reuses one datapath, doubling delay for a few percent
area. correction_table_bits and exact_msb_hybrid are the other two
routes: a small table indexed by the leading fraction bits, or an
exact small multiplier on the most significant bits.

The family wins where a multiplier array is unaffordable and the
workload tolerates a biased, statistically characterized error, which
is why it is revived for neural workloads; the antilog_shifter slot
carries most of the datapath. It loses wherever the error contract is
a bound per operation, since division errs high by up to 12.5 percent
and chains of multiplications drift low, and to truncated or
perforated multipliers when the required accuracy is within a few
percent.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/mul_ext.py`: leading-one detection through the `lod` slot, the operands normalized through the `normalize_shifter` slot, the fractions added through the `log_adder` slot, the antilog shift through the `antilog_shifter` slot; Combet's cross term from a small table (before and after a mantissa carry), operand decomposition as two Mitchell products and an add, nearest-one rounding with a signed fraction on the same line, and the exact top-half product through the `exact` slot under `exact_msb_hybrid`).

## design choices

### correction_scheme

| member | what it selects |
| --- | --- |
| `none` | the logarithm stands uncorrected. |
| `combet_error_terms` | Combet's piecewise error terms are added. |
| `operand_decomposition` | the operands are decomposed and the parts multiplied separately. |
| `nearest_one_rounding` | the significand is rounded to the nearest power of two rather than truncated toward it. |

## references

mitchell1962 -> J. N. Mitchell, "Computer Multiplication and Division Using Binary Logarithms", IRE Transactions on Electronic Computers, vol. EC-11, no. 4, pp. 512-517, 1962
mahalingam2006 -> V. Mahalingam, N. Ranganathan, "Improving Accuracy in Mitchell's Logarithmic Multiplication Using Operand Decomposition", IEEE Transactions on Computers, vol. 55, no. 12, pp. 1523-1535, 2006
