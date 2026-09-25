---
family: operand_rounding
pin: {rounding: nearest_pow2}
---
# nearest_pow2

The RoBA form of operand rounding: both operands are rounded to their
nearest power of two, the product is split into ArB + BrA - ArBr plus
the residual cross term (Ar - A)(Br - B), and the residual is dropped.
Every surviving term is a shift of one operand, so the datapath is
three barrel shifters, an adder and a simplified subtractor with no
partial-product array, and the result is exact whenever the magnitude
of one operand is a power of two.

Dropping the residual is what makes the multiplier shift-only, and it
is also the whole error: the relative error is (Ar - A)(Br - B)/(AB),
signed, with a maximum of about 11.1 percent, and almost all 32-bit
outputs stay below 10 percent. This is the pick for error-resilient DSP
where energy matters more than worst-case error, since a 32-bit signed
RoBA in NanGate 45 nm spends about 3 percent more delay than a
Baugh-Wooley multiplier for roughly 45 percent less energy, while image
filtering with it stays above about 40 dB PSNR. It loses on accuracy to
dynamic-segment multipliers and on delay to the accurate
compressor-based multiplier; keeping the residual cross term is the
sibling that buys accuracy back at the cost of a real product.

## references

zendegani2017 -> R. Zendegani, M. Kamal, M. Bahadori, A. Afzali-Kusha, M. Pedram, "RoBA Multiplier: A Rounding-Based Approximate Multiplier for High-Speed yet Energy-Efficient Digital Signal Processing", IEEE Transactions on VLSI Systems, vol. 25, no. 2, pp. 393-401, 2017
leon2018b -> V. Leon, G. Zervakis, S. Xydis, D. Soudris, K. Pekmestzi, "Walking Through the Energy-Error Pareto Frontier of Approximate Multipliers", IEEE Micro, vol. 38, no. 4, pp. 40-49, 2018
