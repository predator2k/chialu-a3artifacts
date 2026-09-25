# alu_pg_fused

The adder's first stage already forms generate (a and b) and propagate (a xor b) for every bit; and, xor and or (p or g) are taken from those signals through the result mux, so the logic class costs a few muxes on the shared adder instead of a gate row. The 74181-style ALU organization; it ties the logic ops to the adder's timing and to its lane gating.

The seed realizes this family by construction: the integer lane computes and as the operands' generate, xor as their propagate and or as their or (the 74181 form), the same expressions the adder's first stage forms, which the synthesizer shares within the lane.

## references
tremblay_1996 -> M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
