---
family: approximate_compressor_tree
pin: {compressor: akbari_dual_quality}
---
# akbari_dual_quality

Four dual-quality cells (DQ4:2C1 to DQ4:2C4) that combine an
approximate part with supplementary exact-mode circuitry: approximate
mode power-gates the supplement, exact mode reuses most of the
approximate circuitry and activates it. C1 connects carry* to x4 and sum* to x1
and omits Cout, C2 also connects Cout to x3, C3 improves sum*
accuracy and C4 improves carry* accuracy, and a mixed tree places C1
in the low columns and C4 in the high columns.

The dual-quality cells are the pick when accuracy must be selectable
at run time: the 32-bit Dadda multipliers average 46 percent less
delay and 68 percent less power than the prior approximate
compressors in approximate mode, and 49.3 percent less delay and
83.7 percent less power than the exact multiplier, in 45 nm CMOS.
The costs are the highest per-cell error rates of the family (62.5
percent for C1 and C2, 50 for C3, 31.25 for C4), a 22 to 26 ps mode
transition with invalid outputs, and a small exact-mode overhead from
the tristate isolation, so a fixed-accuracy design picks the Yang or
extended cells instead.

## references

akbari2017 -> O. Akbari, M. Kamal, A. Afzali-Kusha, M. Pedram, "Dual-Quality 4:2 Compressors for Utilizing in Dynamic Accuracy Configurable Multipliers", IEEE Transactions on VLSI Systems, vol. 25, no. 4, pp. 1352-1361, 2017
strollo2020 -> A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, G. Di Meo, "Comparison and Extension of Approximate 4-2 Compressors for Low-Power Approximate Multipliers", IEEE Transactions on Circuits and Systems I, vol. 67, no. 9, pp. 3021-3034, 2020
