---
family: nonuniform
pin: {addressing: power_of_two_cascade}
---
# power_of_two_cascade

Segment addressing for widths that grow or shrink by factors of two
or more: cascaded OR and AND prefix circuits count the leading zeros
or ones of the input, selected taps of the cascade mark the
boundaries in use, and an adder turns the tap hits into the segment
address. An 8-bit illustrative circuit yields up to 14 addresses, and
uniform outer intervals may contain nonuniform inner segments built
the same way.

The cascade approximates arbitrary boundary placement with a circuit
that is little more than leading-digit detection, which is why it is
the pick on FPGAs where a comparator_tree over stored breakpoints
would cost a comparator per boundary. Its limit is that boundaries
fall only on the power-of-two grid the taps expose, so the
segmentation is less free than a comparator tree allows; within that
grid it still cut sqrt(-ln x) to 59 segments where a uniform split
would need 617 million at the same 0.031 absolute error.

The library's module for nonuniform realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

lee_2003 -> D.-U. Lee, W. Luk, J. Villasenor, P. Y. K. Cheung, "Non-Uniform Segmentation for Hardware Function Evaluation", Field-Programmable Logic and Applications (FPL), LNCS 2778, pp. 796-807, 2003
