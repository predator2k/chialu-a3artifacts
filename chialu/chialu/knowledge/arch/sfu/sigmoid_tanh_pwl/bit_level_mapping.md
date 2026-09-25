---
family: sigmoid_tanh_pwl
pin: {approximation: bit_level_mapping}
---
# bit_level_mapping

Direct combinational mapping from input bits to output bits: the
fixed-point input and output are truncated to a few bits, each output
bit is minimized as a Boolean sum of products of the input bits, and the
sigmoid is a two-level logic block with no arithmetic. Symmetry lets the
mapping cover only positive or only negative inputs with a z-bit
adder/subtractor for the other half. The posit8 extreme flips the first
bit of the encoding and shifts right by two to get a sigmoid-shaped
function.

Bit-level mapping is the pick for the smallest and fastest activation at
low precision: on an EP2A15 FPGA the s3.3/0.7 positive-only mapping
takes 45 logic elements at 76.4 MHz with 0.17% average and 0.39% maximum
error over [-8, 8), and the s2.3/0.6 mapping 25 logic elements at 94.7
MHz with 0.40% and 0.77% over [-4, 4), better on every quality factor
than the shift-add lines at similar cell counts. Truncation is the only
error source, with worst case 2^-(z+1) for a z-bit output, so precision
is bought with input bits and the logic grows with them. Positive-only
mapping gives the best results. The posit8 bit trick is specific to es =
0 and reports no error figure, but replaces a library sigmoid of over a
hundred cycles.

The library's module for sigmoid_tanh_pwl realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

tommiska_2003 -> M. T. Tommiska, "Efficient Digital Implementation of the Sigmoid Function for Reprogrammable Logic", IEE Proceedings - Computers and Digital Techniques, vol. 150, no. 6, pp. 403-411, 2003
gustafson_2017 -> J. L. Gustafson, I. T. Yonemoto, "Beating Floating Point at its Own Game: Posit Arithmetic", Supercomputing Frontiers and Innovations, vol. 4, no. 2, pp. 71-86, 2017
