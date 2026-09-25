# operand_rounding

Approximate multiplication by rounding the operands: each operand A is
rounded to Ar, its nearest power of two, the product is rewritten as
(Ar - A)(Br - B) + ArB + BrA - ArBr, and the residual cross term (Ar -
A)(Br - B) is omitted. The three surviving terms are shifts of an
operand because Ar and Br are powers of two, so the datapath is three
barrel shifters feeding an adder and a simplified subtractor, with no
partial-product array. Signed operands are handled on absolute values
with the sign restored at the output, and the result is exact whenever
the magnitude of either operand is a power of two.

The rounding choice decides whether the residual cross term is dropped
or retained, which trades the shifter-only datapath against the error
that term carries. With it dropped the relative error is (Ar - A)(Br -
B)/(AB), a signed quantity that may fall on either side of the exact
result with a maximum of about 11.1 percent, which is the error a bias
correction targets. The sign-handling variants trade hardware against
accuracy: the unsigned form removes sign detection and restoration
entirely, the signed form performs exact two's complement negation, and
the approximate-signed form omits the increment during negation and so
reaches 100 percent error when an operand is -1 unless a bypass detects
that case. In the signed forms the shifters dominate delay, power and
area.

The family targets error-resilient DSP where a bounded relative error
is acceptable: image sharpening and smoothing with the approximate
products stay above about 40 dB PSNR against exact multiplication, and
almost all 32-bit outputs land below 10 percent relative error. No
fault checker is provided. Against an exact Baugh-Wooley multiplier at
32 bits in NanGate 45 nm, the signed form costs about 3 percent more
delay for roughly 45 percent less energy and a third less area. It
loses on accuracy to dynamic-segment multipliers such as DSM8, which
beat it on error while it beats them on delay and energy, and in Pareto
sweeps it shows a large standalone error and worse delay than the
accurate compressor-based multiplier. The datapath is feed-forward.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/approx.py`: each operand rounded to its nearest power of two; the product of the two powers, or the RoBA form a 2^kb + b 2^ka - 2^(ka+kb) by shifts, with the mean residual added under bias_correction); the ArithmeticError gate governs.

## design choices

### rounding

| member | what it selects |
| --- | --- |
| `nearest_pow2` | each operand is rounded to the nearest power of two and the product is the product of the two powers. |
| `pow2_plus_residual` | the RoBA form: the rounded power of two plus the residual, which recovers the first-order term. |

## references

zendegani2017 -> R. Zendegani, M. Kamal, M. Bahadori, A. Afzali-Kusha, M. Pedram, "RoBA Multiplier: A Rounding-Based Approximate Multiplier for High-Speed yet Energy-Efficient Digital Signal Processing", IEEE Transactions on VLSI Systems, vol. 25, no. 2, pp. 393-401, 2017
leon2018b -> V. Leon, G. Zervakis, S. Xydis, D. Soudris, K. Pekmestzi, "Walking Through the Energy-Error Pareto Frontier of Approximate Multipliers", IEEE Micro, vol. 38, no. 4, pp. 40-49, 2018
