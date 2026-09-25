---
family: bridge_fma
pin: {composition_style: cascade_mul_then_add}
---
# cascade_mul_then_add

Separate floating-point multiplier and adder datapaths joined by an
internal selectable bus from the multiplier output to one adder
input: the product is rounded in the multiplier and then added, and
the same link serves one fp64, two parallel fp32, one 53-bit integer
or two parallel 24-bit integer multiply-add operations in the
multi-mode FPGA block, with a carry-lookahead final adder, a
leading-zero count after the add and increment rounding.

The cascade is the pick when the fused single-rounding contract is
not required and the unit must switch modes: the internal link
avoids external routing delay and keeps both datapaths independent
with no bridge logic. Its cost is accuracy, since the product is
rounded before the addition and the accumulated rounding error can
exceed that of a dedicated floating-point multiply-accumulate. Bridge
reuse is the sibling when the operation must round once, and the
monolithic fused unit when fused latency dominates.

Keeping the two pipelines apart is what shortens the dependent path.
Aligning after the multiply holds the aligner, adder and normalizer at
about 48 bits for single precision against about 72 for a fused
datapath, and the aligner swaps its two inputs by which significand
carries the smaller exponent. The accumulation latency is then about
half the multiply-add latency, where a fused unit's two latencies are
equal, and only one of the addition's close and far paths need be
clocked. At the same 3.2 GFlops single-precision point in 90 nm the
cascade matches the fused unit's 0.036 mm2/GFlops and 0.046 W/GFlops
and takes 12 cycles against its 10, and in a 45 nm generator study the
cascade holds the latency frontier at pipeline depths of 5 to 12 and
16. Rounding in the unit's active IEEE-754 mode makes the intermediate
product IEEE-754 compliant and the exceptions precise, so the SPARC64
form suppresses the addition when the multiply raises an exception and
delivers a 7-cycle latency at one instruction per cycle in 0.15 um.
The unoverlapped chained form of the same composition is the one that
matches a sequential FMPY followed by an FADD. Its fused latency is
the sum of the two latencies, and its area is the smallest of the
organizations compared, because the adder and the multiplier are
optimized separately.

The library realizes this choice as a pin of the generated bridge_fma module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

chong_2009 -> Y. J. Chong, S. Parameswaran, "Flexible Multi-Mode Embedded Floating-Point Unit for Field Programmable Gate Arrays", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2009
galal_2011 -> S. Galal, M. Horowitz, "Energy-Efficient Floating-Point Unit Design", IEEE Transactions on Computers, vol. 60, no. 7, 2011
galal_2013 -> S. Galal, O. Shacham, J. S. Brunhaver, J. Pu, A. Vassiliev, M. Horowitz, "FPU Generator for Design Space Exploration", ARITH-21, 2013
naini_2001 -> A. Naini, A. Dhablania, W. James, D. Das Sarma, "1-GHz HAL SPARC64 Dual Floating Point Unit with RAS Features", ARITH-15, 2001
quach_1991 -> N. Quach, M. Flynn, "Suggestions for Implementing a Fast IEEE Multiply-Add-Fused Instruction", Stanford CSL-TR-91-483, 1991
