# wide_gate_row

Bitwise operations do not depend on lane boundaries, so one full-width gate row serves 1 x 32, 2 x 16 and 4 x 8 (and every other packing) unchanged; not is xor with ones; fabs and fneg become and/xor with a mode-selected sign mask. The packed-logic operations of SIMD media ISAs are built this way.

The seed realizes this family by construction: the seed's logic unit instantiates one `fam_logic_gate_row` over the whole word and every served packing reads it (the bitwise ops are lane-agnostic); the float sign ops keep their lane path.

## references
tremblay_1996 -> M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
