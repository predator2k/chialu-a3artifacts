---
family: segmented_carry_speculative
pin: {correction: extra_cycle}
---
# extra_cycle

A detector flags a segment whose predicted carry disagrees with the
true one, and the exact result is restored in an additional cycle
rather than inside the approximate path: the ACA detects a segment
error from its carry-in and an all-one lower result and adds
compensation with an incrementor, GeAr's correction path restores
the exact output, a speculative final adder stalls the multiplier and
adds 1, and DSEC accumulates ignored carries and adjusts the
accumulator in a correction cycle.

The approximate path keeps its short clock and the correction is paid
only when needed: the 16-bit ACA at k=4 in TSMC 65GP passes 94.0 per
cent of random cycles and gains 22.3 per cent throughput over a CLA
with the recovery overhead included, and its EDC costs 28 per cent
area against 75 per cent for Lu's adder and 15 per cent for ETAIIM.
For k below N/4 one correction stage cannot restore full accuracy in
one clock, so several stages are needed. Against
error_reduction_stage, which only shrinks the error in place,
extra_cycle yields an exact result at variable latency; against none
it adds detection logic and a stall. It is the pick when the consumer
tolerates variable latency and the error rate keeps recovery cycles
rare.

## references

kahng_kang2012 -> A. B. Kahng, S. Kang, "Accuracy-Configurable Adder for Approximate Arithmetic Designs", 49th Design Automation Conference (DAC), pp. 820-825, 2012
shafique2015 -> M. Shafique, W. Ahmad, R. Hafiz, J. Henkel, "A Low Latency Generic Accuracy Configurable Adder", 52nd Design Automation Conference (DAC), 2015
lin2013 -> C.-H. Lin, I.-C. Lin, "High Accuracy Approximate Multiplier with Error Correction", IEEE International Conference on Computer Design (ICCD), pp. 33-38, 2013
venkatesan2011 -> R. Venkatesan, A. Agarwal, K. Roy, A. Raghunathan, "MACACO: Modeling and Analysis of Circuits for Approximate Computing", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 667-673, 2011
