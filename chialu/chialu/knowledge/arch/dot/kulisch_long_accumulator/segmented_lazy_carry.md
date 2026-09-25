---
family: kulisch_long_accumulator
pin: {organization: segmented_lazy_carry}
---
# segmented_lazy_carry

The carry chain is cut into k-bit segments separated by registers, so
each cycle propagates a carry only inside a segment and the carry out
of a segment enters the next one a cycle later. The register holds an
exact partial carry-save form, returned to standard binary by feeding
zeros for enough cycles after the last product or by a pipelined
carry-propagation stage before normalization. Each segment has its own
adder, with latched carry and borrow between segments.

This is the pick when the width is set by the format's exponent range
and the target frequency by the pipeline: with 32-bit segments the
recurrence closes at 400 MHz on Virtex-4 and Stratix II for one extra
register per 32 bits, and a 559-bit two's-complement accumulator with
32-bit or 64-bit segments matches the posit32 quire in LUTs, cycles and
delay on a Kintex 7. Smaller segments raise frequency at more register
cost; the zero-flush exit is free but adds latency, the pipelined exit
costs hardware but exposes the running value. The monolithic sibling is
only competitive at small widths.

The library realizes this choice as a pin of the generated kulisch_long_accumulator module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
uguen_2019 -> Y. Uguen, L. Forget, F. de Dinechin, "Evaluating the Hardware Cost of the Posit Number System", International Conference on Field Programmable Logic and Applications (FPL), 2019
koenig_2017 -> J. Koenig, D. Biancolin, J. Bachrach, K. Asanovic, "A Hardware Accelerator for Computing an Exact Dot Product", ARITH-24, pp. 114-121, 2017
