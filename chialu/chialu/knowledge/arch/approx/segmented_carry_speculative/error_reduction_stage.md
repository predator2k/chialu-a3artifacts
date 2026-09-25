---
family: segmented_carry_speculative
pin: {correction: error_reduction_stage}
---
# error_reduction_stage

A stage after the speculative sum shrinks a missed carry's magnitude
without another cycle: the ISA's COMP compares the speculated carry
with the preceding carry-out and a mismatch increments or decrements
local low bits, flipping preceding high bits when that overflows;
Kim's stage forces the sums of two consecutive all-propagate blocks
to one; Hu-Qian's mux picks the previous block's generate signal or
its approximate carry; the BCSA ERU repairs the first sum bit off the
critical path.

The stage bounds the error rather than removing it: Kim's reduction
cuts the worst-case magnitude from 2^(n-k) to 2^(n-3k), and the 16-bit
k=4 adder reaches 0.18 per cent error rate at 0.215 pJ in 90 nm
against 5.86 per cent for ETAII, VLCSA-1 and ACA; Hu-Qian's variant
holds the maximal relative error to 1/2^k for every input; the ERU
costs about 2 per cent area and 3 per cent power. Correction
precomputation stays outside the critical path, which holds only the
COMP multiplexers. Against extra_cycle the latency stays fixed but the
result is not exact; against none the cost is a few gates per block.
It is the pick for a fixed-latency adder with a bounded relative
error, paired with propagate_window or carry_select_speculation.

## references

camus2015 -> V. Camus, J. Schlachter, C. Enz, "Energy-Efficient Inexact Speculative Adder with High Performance and Accuracy Control", IEEE International Symposium on Circuits and Systems (ISCAS), pp. 45-48, 2015
kim2013 -> Y. Kim, Y. Zhang, P. Li, "An Energy Efficient Approximate Adder with Carry Skip for Error Resilient Neuromorphic VLSI Systems", IEEE/ACM International Conference on Computer-Aided Design (ICCAD), pp. 130-137, 2013
hu_qian2015 -> J. Hu, W. Qian, "A New Approximate Adder with Low Relative Error and Correct Sign Calculation", Design, Automation and Test in Europe (DATE), pp. 1449-1454, 2015
ebrahimi2020 -> F. Ebrahimi-Azandaryani, O. Akbari, M. Kamal, A. Afzali-Kusha, M. Pedram, "Block-Based Carry Speculative Approximate Adder for Energy-Efficient Applications", IEEE Transactions on Circuits and Systems II, vol. 67, no. 1, pp. 137-141, 2020
mittal2016 -> S. Mittal, "A Survey of Techniques for Approximate Computing", ACM Computing Surveys, vol. 48, no. 4, 2016
