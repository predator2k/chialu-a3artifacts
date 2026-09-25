# twin_precision_subword

One partial-product matrix gated into either one full-width product
or several concurrent narrow ones: each narrow multiplication is
mapped onto a region of the matrix that no other lane touches (the
two halves or the four quarters), and control signals zero the
partial products between regions, so the shared reduction tree and
final carry-propagate adder deliver the separate results with no
carry crossing a lane boundary, whether because the mapping leaves
no path for one or because carry kills segment the tree and adder
there. Signed lanes add selectable Baugh-Wooley inversions and sign
bits, or mode-dependent Booth recoding and sign-extension patterns
with two extra tree inputs.

The lane set the gating supports is the unit's mode set, which the
realization receives as the lane widths: halves give two N/2 products and
quarters four, and a recursive decomposition applies the same split inside
each lane so a 9-bit block yields one, two or four products. One array
serves three precisions the same way, as one 113 by 113 product, as two 53
by 53 products or as four 24 by 24 products, with the off-diagonal regions
of the matrix forced to zero. The matrix is the Baugh-Wooley form, whose
mode control is simpler and whose delay and power are better than the
modified-Booth form's; the Booth form's recoded matrix is smaller and
holds the area overhead at 3% against 11% for Baugh-Wooley at 32 bits in
65 nm, and it is not realized in this version
(`docs/deferred-families.md`), since the zero-region mapping that needs no
boundary carry-kill logic applies only to matrices that are not Booth
encoded. A Booth-recoded matrix isolates its lanes at the encoder instead:
the zero select of the Booth cells clears the cross quadrants, and the
carry spill between lanes is stopped by the two-bit shift between Booth 2
partial products, or under Booth 3 by an explicit carry kill or by zero
padding. Gating a Booth 2 Wallace multiplier that way costs 5 to 10% power
and area over a double-precision-only multiplier of the same tree in TSMC
45nm, and the Booth 3 form costs 10 to 20%, so the zero padding earns its
complexity only while the partial product it adds leaves the tree depth
alone. per_lane_signed decides whether each operand's sign mode is a
run-time control per lane or one global setting. The lanes need not be
square: a 60 by 60 mantissa array also runs four signed 8 by 16 SIMD
graphics products. lane_cpa is segmented by kills at the lane boundaries
and has been a Kogge-Stone prefix adder, a 4-bit-group lookahead adder and
a sparse prefix hybrid in the designs on file.

The price of the gating in full-width mode is 5 to 8% power, 8 to 11%
area and about 10% delay over a conventional tree multiplier, and the
return comes only from narrow work: two concurrent half-width
products cost about 59% less energy per operation than the
full-width multiplier, so the break-even fraction of narrow
operations is 5 to 7% in 130 nm and 15 to 18% in 65 nm. Holding
throughput constant while the lane count rises lets frequency and
supply fall together, which is how four 4-bit lanes at 125 MHz and
0.75 V save more than 95% of the energy of a fixed 16-bit multiplier
at 500 MHz. Unpartitioned array multipliers reach the same modes by
activating cell diagonals, either summing the subword products apart
or together, at 10 to 18% area overhead. Sharing by segmenting one
carry-killed structure beats building mode-specific subtrees and a
final mode multiplexer, and its advantage grows with width and mode
count. Every mode is exact; the family is feed-forward.

The seed realizes this family by construction: the seed's multiplier unit instantiates one gated partial-product matrix over the served packings (`families/subword.py`: the cross-lane products gated off by the mode select, Baugh-Wooley per lane and mode, the carry-save carries killed at the lane boundaries, a lane-partitioned final adder of the `lane_cpa` family; per_lane_signed False keeps the matrix unsigned and handles each lane's sign outside it: the lanes' magnitudes in, the products negated back by the operand signs); each lane reads its product slice of the packed bus.

## design choices

### per_lane_signed

| member | what it selects |
| --- | --- |
| `True` | each lane's sign mode is a run-time control, and the matrix carries the Baugh-Wooley inversions and sign bits per lane. |
| `False` | one global setting: the lanes' magnitudes go through an unsigned matrix and each lane's product is negated back by the operand signs. |

## references

sjalander2009 -> M. Sjalander, P. Larsson-Edefors, "Multiplication Acceleration Through Twin Precision", IEEE Transactions on Very Large Scale Integration (VLSI) Systems, vol. 17, no. 9, pp. 1233-1246, 2009
sjalander_2004 -> M. Sjalander, H. Eriksson, P. Larsson-Edefors, "An Efficient Twin-Precision Multiplier", Proc. IEEE ICCD, pp. 30-33, 2004
krithivasan2003 -> S. Krithivasan, M. J. Schulte, "Multiplier Architectures for Media Processing", 37th Asilomar Conference on Signals, Systems and Computers, pp. 2193-2197, 2003
danysh_2005 -> A. Danysh, D. Tan, "Architecture and Implementation of a Vector/SIMD Multiply-Accumulate Unit", IEEE Transactions on Computers, vol. 54, no. 3, pp. 284-293, 2005
camus2019 -> V. Camus, L. Mei, C. Enz, M. Verhelst, "Review and Benchmarking of Precision-Scalable Multiply-Accumulate Unit Architectures for Embedded Neural-Network Processing", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 9, no. 4, pp. 697-711, 2019
moons2017 -> B. Moons, R. Uytterhoeven, W. Dehaene, M. Verhelst, "DVAFS: Trading Computational Accuracy for Energy Through Dynamic-Voltage-Accuracy-Frequency-Scaling", Design, Automation and Test in Europe (DATE), pp. 488-493, 2017
rasoulinezhad_2019 -> S. Rasoulinezhad, H. Zhou, L. Wang, P. H. W. Leong, "PIR-DSP: An FPGA DSP Block Architecture for Multi-Precision Deep Neural Networks", IEEE Symposium on Field-Programmable Custom Computing Machines (FCCM), 2019
galal_2013 -> S. Galal, O. Shacham, J. S. Brunhaver, J. Pu, A. Vassiliev, M. Horowitz, "FPU Generator for Design Space Exploration", ARITH-21, 2013
manolopoulos_2016 -> K. Manolopoulos, D. Reisis, V. A. Chouliaras, "An Efficient Multiple Precision Floating-Point Multiply-Add Fused Unit", Microelectronics Journal, vol. 49, 2016
naini_2001 -> A. Naini, A. Dhablania, W. James, D. Das Sarma, "1-GHz HAL SPARC64 Dual Floating Point Unit with RAS Features", ARITH-15, 2001
