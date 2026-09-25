---
family: integer_mac
pin: {accumulation_mode: sum_apart}
---
# sum_apart

In Sum Apart mode the narrow products of the submultipliers bypass the
combination logic and each is accumulated into its own accumulator, so a
MAC that composes k submultipliers delivers k independent low-precision
multiply-accumulates per cycle. The shift-add stage that would weight
and merge the partial products is idle, and the parallel results leave
the unit as separate words.

Sum Apart is the mode that converts precision scaling into throughput:
the two-dimensional divide-and-conquer MAC at symmetric 2b scaling
reaches 14.5x the throughput of a full-precision conventional MAC in 28
nm, for up to 4.4x its area. It applies where the workload has k
independent dot products to fill the parallel accumulators, as the
output channels of a convolution do. Sum Together is the alternative
when the narrow products belong to one dot product, since it reuses the
combination adders to merge them and saves 68 percent energy against
data gating at two scaling levels. Both modes sit on the composable
submultiplier array and differ in whether the combination adders are
bypassed or reused for accumulation. The approximate-MAC
precision_scaling choice carries the same pair of values.

The library realizes this choice as a pin of the generated integer_mac module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

camus2019 -> V. Camus, L. Mei, C. Enz, M. Verhelst, "Review and Benchmarking of Precision-Scalable Multiply-Accumulate Unit Architectures for Embedded Neural-Network Processing", IEEE Journal on Emerging and Selected Topics in Circuits and Systems, vol. 9, no. 4, pp. 697-711, 2019
