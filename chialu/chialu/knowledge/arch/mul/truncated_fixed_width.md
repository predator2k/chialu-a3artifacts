# truncated_fixed_width

An n x n multiplier that forms only the n+k most-significant partial-
product columns and returns an n-bit product: the omitted n-k columns
contribute a negative reduction error, discarding the product bits
below the output adds a rounding error, and a correction added inside
the retained columns compensates both. The correction is a constant
(the representable value closest to the inverse of the expected total
error), a data-dependent value formed from the partial products of the
first omitted column and fed into the carry inputs of column n+k, or a
quantized linear function of those input-correction bits chosen to
minimize mean-square or maximum error.

The extra columns kept trade error against savings: with k above
log2(n) the normalized mean-square error stays below 0.09 and the
maximum error below one unit, and the family saves 25% to 35% of a
conventional rounded parallel multiplier, or about half the area when
no extra column is kept. The correction scheme trades error statistics
against matrix height: a constant is the easiest for tree reduction,
because a variable correction can raise the matrix height, while
variable correction is readily built into an array, centres the error
distribution on zero and roughly halves its spread for a few extra
gates, and is the pick when minimum error or maximum SNR matters or
several products accumulate on one sample. The minimum-mean-square
linear correction, with h major columns retained, gives 42% less area
and 47% less power than a full-rounded multiplier in 0.18 um with an
error comparable to it, and the min-max form lowers the maximum
absolute error further and extends to a multiply-accumulate. Booth
forms estimate the omitted carry from the encoder outputs. Output
rounding to nearest adds a bit at the round position and halves the
error contribution of the product; the kept tree may be a carry-save
tree or 4:2 compressors, and truncation shortens the final adder but
does not shorten the critical path much.

The contract is statistical, so the ArithmeticError gate governs: the
error rate is near 100%, the mean error is zero or bounded by
2^(-n-k-1) after correction, the relative error grows when inputs are
small, and a faithful result follows when the total error stays below
2^k, without IEEE compliance. The family applies when only the n most
significant product bits are consumed, in DSP and multimedia
datapaths and in polynomial evaluators whose following addition
truncates the product in any case; on FPGAs a DSP tile that crosses the
truncation line yields its otherwise discarded bits as free
compensation, so a double-precision significand multiplier needs 5 DSPs
against 6 with about half the LUTs and registers on a Virtex-5.
Execution is feed-forward.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/mul_ext.py`: the top n + k columns kept (`extra_columns_kept`) and reduced by the `kept_tree` slot's family, the omitted columns compensated by a constant, by the first omitted column's bits carried into the kept lsb (data_dependent) or by the first two omitted columns' bits with a constant fitted as the mean residual at generation (variable_mmse), the output truncated, rounded or jammed; the low product half is zero, so the ArithmeticError gate governs).

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: the exact family's truncated module under the correction ladder: constant, data_dependent, the fitted constant for variable_stat and linear_regression, the constant halving the residual for min_max, the data-dependent term for incremental_approximate_mean_offset); the ArithmeticError gate governs.

## design choices

The canonical native interface returns a **2n-bit word with n low zeros**:
the retained high half still has weight `2^n`. It is verified through
`family_ref.Adapter.algorithm` using the independent integer contract in
`verify/truncated_multiplier_ref.py`; the original exact multiply and
mathematical tolerance remain a separate gate. A circuit may match its
algorithm and fail that tolerance. The literature error figures above do
not certify every generated pin combination, particularly combinations
whose compensated 2n-bit sum wraps.

Explicit `extra_columns_kept=k` must satisfy `0 <= k <= 4` and `k <= n`.
The native generator rejects a too-small operand width instead of
clipping k. The geometry planner uses at least `k+3` bits for constant or
paired-data MMSE correction, so the omitted triangle can activate the
selected correction; legal smaller cases remain available but do not
serve as witnesses for an ineffective correction. At k=0, truncate and
nearest are algebraically equivalent because the retained sum already
has n low zeros. One-bit jamming is the constant two-bit pattern `10`.

The legacy `correction` path and unmodeled nested approximate/nonbinary
arithmetic remain explicit uncovered contracts. The canonical algorithm
model is not silently applied to those different constructions.

Compensation means and fitted residuals are evaluated with exact rational
and integer arithmetic before the constant is rounded. At n=53, k=2,
the constant is `round(12.5 + 2^-53) = 13`; a binary-float accumulator lost
the positive tail and previously emitted 12. The regression includes the
neighboring half boundaries and a real FP64 normal-significand Dot input
whose retained product changes by two output ULPs at this boundary.

### correction_scheme

| member | what it selects |
| --- | --- |
| `none` | the dropped columns are simply absent. |
| `constant` | a constant compensates their mean. |
| `data_dependent` | the compensation is computed from the operands. |
| `variable_mmse` | the compensation follows a minimum mean-square-error fit over the dropped columns. |

### output_rounding

| member | what it selects |
| --- | --- |
| `truncate` | the kept product is truncated. |
| `round_to_nearest` | the kept product is rounded to nearest. |
| `force_lsb_one_jamming` | the lowest kept bit is forced to one, which is jamming. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the low columns are dropped, and the module states how many partial-product bits go | - | `\d+ partial-product bits omitted` |

## references

schulte1993 -> M. J. Schulte, E. E. Swartzlander, "Truncated Multiplication with Correction Constant", VLSI Signal Processing VI, pp. 388-396, 1993
kidambi1996 -> S. S. Kidambi, F. El-Guibaly, A. Antoniou, "Area-Efficient Multipliers for Digital Signal Processing Applications", IEEE Transactions on Circuits and Systems II, vol. 43, no. 2, pp. 90-95, 1996
king1997 -> E. J. King, E. E. Swartzlander, "Data-Dependent Truncation Scheme for Parallel Multipliers", 31st Asilomar Conference on Signals, Systems and Computers, pp. 1178-1182, 1997
jou1999 -> J. M. Jou, S. R. Kuang, R. D. Chen, "Design of Low-Error Fixed-Width Multipliers for DSP Applications", IEEE Transactions on Circuits and Systems II, vol. 46, pp. 836-842, 1999
petra2010 -> N. Petra, D. De Caro, V. Garofalo, E. Napoli, A. G. M. Strollo, "Truncated Binary Multipliers with Variable Correction and Minimum Mean Square Error", IEEE Transactions on Circuits and Systems I, vol. 57, no. 6, pp. 1312-1325, 2010
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
decaro2013 -> D. De Caro, N. Petra, A. G. M. Strollo, F. Tessitore, E. Napoli, "Fixed-Width Multipliers and Multipliers-Accumulators with Min-Max Approximation Error", IEEE Transactions on Circuits and Systems I, vol. 60, no. 9, pp. 2375-2388, 2013
jiang2020 -> H. Jiang, F. J. H. Santiago, H. Mo, L. Liu, J. Han, "Approximate Arithmetic Circuits: A Survey, Characterization, and Recent Applications", Proceedings of the IEEE, vol. 108, no. 12, pp. 2108-2135, 2020
