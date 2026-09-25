---
family: mx_microscaling_dot
pin: {scale_encoding: two_level_microexponent}
---
# two_level_microexponent

First-level blocks of 16 elements share an 8-bit power-of-two
exponent, and two-element sub-blocks share a 1-bit microexponent that
conditionally right-shifts the pair during reduction; mantissas of 2,
4 or 7 bits give 4, 6 or 9 average bits per element. The pipeline
multiplies mantissas, applies the sub-block shifts inside the adder
tree, reduces each block, normalizes block results to the largest
exponent, accumulates in fixed point at a precision of at most 25 bits,
and converts to fp32.

It is the pick when fidelity per stored bit decides the design: the
9-bit format sits about 16 dB above FP8 E4M3 and 3.6 dB above MSFP16
in QSNR and trains 1.5B- and 1.9B-parameter models to the FP32 loss,
while the 6-bit and 4-bit formats cost about 2x and 4x less
area-memory than a configurable FP8 dot product. Two-element
sub-blocks under a single microexponent bit are the balance point,
because a second microexponent bit raises cost 30% to 50% for half a
decibel. The 6-bit format may need quantization-aware fine-tuning, and
the single-scale sibling avoids the shift logic in the tree.

The library realizes this choice as a pin of the generated mx_microscaling_dot module (`chialu/targets/rtl/families/dot.py`); the family card names the construction.

## references

rouhani_2023a -> B. Darvish Rouhani, R. Zhao, V. Elango, et al., "With Shared Microexponents, A Little Shifting Goes a Long Way", ISCA, 2023
