---
family: approximate_compressor_tree
pin: {compressor: momeni_d1_d2}
---
# momeni_d1_d2

Two truth-table simplifications of the 4:2 compressor: Design 1
sets the carry equal to cin and simplifies sum and cout to reduce
error distance and logic, at 28 transistors against 52 for the exact
cell and a 37.5 percent error rate; Design 2 interchanges the carry
and cout roles and removes both cin and cout because cin is zero in
the first reduction stage, at 26 transistors and a 25 percent error
rate. The cells go either throughout the Dadda tree or only in
the n-1 least-significant columns.

The Momeni cells are the pick when cell cost dominates and the
workload tolerates the largest per-cell error: Design 2 reaches
24.44 ps and 9 aJ against 47.59 ps and 45 aJ for the exact
compressor in 16 nm, and the full-tree multipliers cut delay by up
to 26.52 percent and power by up to 58.58 percent in 32 nm at an
average NED near 5e-2. The column-bounded multipliers keep NED below
1e-3 and image PSNR near 54 dB but gain no delay. Both cells emit a
nonzero output for all-zero inputs, which gives large relative errors
for small operands unless a zero detector is added, so the Yang and
Lin cells are the siblings for a precision-first pick.

## references

momeni2015 -> A. Momeni, J. Han, P. Montuschi, F. Lombardi, "Design and Analysis of Approximate Compressors for Multiplication", IEEE Transactions on Computers, vol. 64, no. 4, pp. 984-994, 2015
strollo2020 -> A. G. M. Strollo, E. Napoli, D. De Caro, N. Petra, G. Di Meo, "Comparison and Extension of Approximate 4-2 Compressors for Low-Power Approximate Multipliers", IEEE Transactions on Circuits and Systems I, vol. 67, no. 9, pp. 3021-3034, 2020
jiang2017 -> H. Jiang, C. Liu, L. Liu, F. Lombardi, J. Han, "A Review, Classification, and Comparative Evaluation of Approximate Arithmetic Circuits", ACM Journal on Emerging Technologies in Computing Systems, vol. 13, no. 4, 2017
