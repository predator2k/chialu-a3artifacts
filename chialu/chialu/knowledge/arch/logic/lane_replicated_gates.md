# lane_replicated_gates

One row of and/or/xor/not gates per lane and mode, the float sign ops (fabs, fneg) as per-lane sign-bit manipulation. The generated seed's shape; small, but duplicated once per lane configuration.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/logic.sv`: one gate row per lane and mode (`fam_logic_gate_row`: and, or, xor, not by an op code), instantiated by the integer lane module for its logic ops).

## references
tremblay_1996 -> M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
diefendorff_2000 -> K. Diefendorff, P. K. Dubey, R. Hochsprung, H. Scales, "AltiVec Extension to PowerPC Accelerates Media Processing", IEEE Micro, vol. 20, no. 2, pp. 85-95, 2000
