---
family: reduced_precision
pin: {bound_type: absolute}
---
# absolute

The error-control block compares the main result with the narrow
replica against one fixed threshold. In Shim's reduced precision
redundancy the threshold is the maximum error-free difference, which
bounds the difference caused only by replica truncation: the main
output is selected within it and the replica output substituted
outside it. In Seetharam's multiplier checker the reduced product
AhighBhigh is compared with the upper 2X+1 bits of the full product
and differences up to 7 are accepted.

An absolute bound is the pick when one constant separates truncation
from error: under the truncation assumptions the rule guarantees no
false alarm when the main output is error-free, detected errors are
corrected by replica substitution, and undetected errors remain
residual noise. The demonstrated contract preserves the required
output SNR at error rates of 0.09/sample for the FIR and 0.06/sample
for the FFT, at 60% energy and 44% power savings in 0.25 um CMOS; an
RNS FIR with the same redundancy saves 62% more energy than a
conventional filter with under 2 dB SNR loss. With a
7-bit checker mantissa the accepted difference of 7 lets an undetected
error reach about 5.5% of the maximum mantissa value, and checking is
disabled for infinity, NaN and denormal cases. Against relative_ulp it
needs no adjustment unit. In the ADIR grammar it is
`family: reduced_precision` with `pin: {bound_type: absolute}`.

The generated checker realizes this variant (`checker.bound_type: absolute`): the bound at the operands' scale.

## references

shim_2004 -> B. Shim, S. R. Sridhara, N. R. Shanbhag, "Reliable Low-Power Digital Signal Processing via Reduced Precision Redundancy", IEEE Transactions on VLSI Systems, vol. 12, no. 5, pp. 497-510, 2004
seetharam_2013 -> Seetharam, Keh, Nathan, Sorin, "Applying Reduced Precision Arithmetic to Detect Errors in Floating Point Multiplication", Proc. PRDC 2013, pp. 232-235, 2013
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
