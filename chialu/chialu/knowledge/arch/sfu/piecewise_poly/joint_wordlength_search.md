---
family: piecewise_poly
pin: {coefficient_optimization: joint_wordlength_search}
---
# joint_wordlength_search

The finite-wordlength coefficients are chosen by an optimization that
sees quantization: Pineiro's three minimax passes compensate the
rounding of C1, C2 and C0 in turn; Strollo and De Caro solve a
linear program for real coefficients and a mixed-integer program for
integer ones under continuity constraints at each segment-pair
midpoint; De Caro's integer linear program bounds approximation,
quantization, arithmetic and output-rounding errors together and
minimizes total coefficient wordlength.

The joint search is the pick whenever coefficient memory dominates,
because it beats rounding a real minimax polynomial by a wide margin:
sharing constrained coefficients across adjacent segments cuts ROM by
30 to 50 percent at equal accuracy over 12 to 42 bits, 40 percent for
the SFU that shares the constant and linear coefficients of each pair,
and the ILP reaches 111 Kbit for four exactly rounded 15-bit functions
against 156 K, with 32 or 64 quadratic segments where the reference
needs 256. Pineiro's four-function unit holds about 22.2 Kbit of
tables at 1 ulp with a bias found by exhaustive simulation, so it is
unsuitable beyond single precision, and the ILP grows impractical
above 24 input bits or degree 2. Lee's MiniBit assigns widths
analytically for a faithful 1-ulp result. Rounded Remez is the cheap
sibling with no such search.

The library's module for piecewise_poly realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

pineiro_2005 -> J.-A. Pineiro, S. F. Oberman, J.-M. Muller, J. D. Bruguera, "High-Speed Function Approximation Using a Minimax Quadratic Interpolator", IEEE Transactions on Computers, vol. 54, no. 3, pp. 304-318, 2005
strollo_2011 -> A. G. M. Strollo, D. De Caro, N. Petra, "Elementary Functions Hardware Implementation Using Constrained Piecewise-Polynomial Approximations", IEEE Transactions on Computers, vol. 60, no. 3, pp. 418-432, 2011
decaro_2017 -> D. De Caro, E. Napoli, D. Esposito, G. Castellano, N. Petra, A. G. M. Strollo, "Minimizing Coefficients Wordlength for Piecewise-Polynomial Hardware Function Evaluation With Exact or Faithful Rounding", IEEE Transactions on Circuits and Systems I, vol. 64, no. 5, pp. 1187-1200, 2017
decaro_2009 -> D. De Caro, N. Petra, A. G. M. Strollo, "High-Performance Special Function Unit for Programmable 3-D Graphics Processors", IEEE Transactions on Circuits and Systems I, vol. 56, no. 9, pp. 1968-1978, 2009
lee_2009 -> D.-U. Lee, R. C. C. Cheung, W. Luk, J. D. Villasenor, "Hierarchical Segmentation for Hardware Function Evaluation", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 1, pp. 103-116, 2009
