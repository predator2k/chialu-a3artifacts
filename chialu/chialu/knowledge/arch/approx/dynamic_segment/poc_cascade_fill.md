---
family: dynamic_segment
pin: {segment_select: static_msb_or_lsb, unbiasing: poc_cascade_fill}
---
# poc_cascade_fill

The error-tolerant multiplier's low half: under static_msb_or_lsb each
operand splits into a high part and a low part, a conventional
parallel multiplier computes the high product bits, and cascading POC cells fill the low product
bits without partial products. The cells scan the two low operand
halves from MSB to LSB; the first position where either low operand
bit is 1 sets that product bit and every lower product bit to 1, and
preceding 00 positions produce 0, so the low half has no carry
path.

The fill replaces the LSB half rather than unbiasing a window, so the
product keeps its full width while the low half costs neither partial
products nor adders. The 12-bit instance with two 6-bit parts occupies
491 um2 against 1028 um2 for the conventional multiplier in Chartered
0.18 um and draws 50% to 96% less power, with the saving depending on
input switching activity; the reported accuracies run from 94% to 100%
over the sampled operand pairs. The small_operand_fallback choice adds
a control block and a multiplexer that route operand pairs whose high
halves are both zero to a conventional half-width multiplier, so small
operands are exact. The value is the pick when the low half must be
cheap and the contract is per-operand accuracy rather than a bounded
window error; lsb_set_to_one keeps the segment error near zero mean
where accumulation follows.

## references

kyaw2010 -> K. Y. Kyaw, W. L. Goh, K. S. Yeo, "Low-Power High-Speed Multiplier for Error-Tolerant Application", IEEE International Conference of Electron Devices and Solid-State Circuits (EDSSC), 2010
