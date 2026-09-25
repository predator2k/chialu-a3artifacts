---
family: integer_mac
pin: {accumulation_mode: sum_together}
---
# sum_together

In Sum Together mode the combination adders that normally weight and
merge the submultiplier outputs into a full-precision product instead
accumulate the narrow products into one result, so a MAC composed of k
submultipliers finishes k terms of one dot product per cycle. The shift-
add logic is reused rather than bypassed, and one accumulator receives
the merged sum.

Sum Together is the energy mode of the divide-and-conquer MAC: the two-
dimensional design with two levels of symmetric 2b scaling saves 68
percent energy against a data-gated conventional MAC in 28 nm, and a
two-level one-dimensional design covering the weight-only case saves 15
percent with 5 percent of operations at 8b. It fits a dot product whose
terms all narrow together, because the merged accumulation needs one
accumulator and one output word. Sum Apart is the throughput
alternative, keeping k separate accumulators and reaching 14.5x the
full-precision throughput at symmetric 2b for up to 4.4x area. Both
modes sit on the composable submultiplier array and differ in what the
combination adders do, and the scalability_levels choice sets how far
the narrowing goes. A merged fixed/floating unit takes the same mode
for its fixed-point path, summing the two packed 8-bit products in a
(4,2) CSA into one 32-bit two's complement accumulator that needs
neither inversion nor alignment.

The library realizes this choice as a pin of the generated integer_mac module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

camus2019 -> V. Camus, L. Mei, C. Enz, M. Verhelst, "Review and Benchmarking of Precision-Scalable Multiply-Accumulate Unit Architectures for Embedded Neural-Network Processing", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 9, no. 4, pp. 697-711, 2019
zhang_2018 -> H. Zhang, H. J. Lee, S.-B. Ko, "Efficient Fixed/Floating-Point Merged Mixed-Precision Multiply-Accumulate Unit for Deep Learning Processors", ISCAS 2018
