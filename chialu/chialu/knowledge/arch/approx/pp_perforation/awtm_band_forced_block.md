---
family: pp_perforation
pin: {cell: awtm_band_forced_block}
---
# awtm_band_forced_block

A b x b sub-product block of the bit-width-aware Wallace tree
multiplier: its low b/2 product bits are computed exactly, its next
b/2 bits are forced to one, and its upper bits are computed exactly
with a carry predicted from the tallest partial-product column by a
two-or-more threshold or a simplified OR. The block fills the AH x AL,
AL x AH and AL x AL quadrants of a recursive 2b x 2b decomposition,
AH x AH recurses exactly, and a Wallace tree sums the four quadrant
products.

The accuracy_modes choice sets how many AH x AH sub-multipliers of the
recursion stay exact while the AHH x AHH core always does. At 16 x 16
in Nangate 45 nm the four modes run from 34.49% area and 41.96%
total-power saving at 5.26% mean error to 27.90% area and 37.10%
total-power saving at 0.13% mean error against the accurate
multiplier, and the single-cycle form cuts latency by 23.91%. The
bit-width-aware algorithm sizes the approximate region for the operand
width, so the 4 x 4 and 8 x 8 instances save 55.76% and 51.93% area.
The cell is the pick when the error must fall with the mode rather
than with the row count; it loses to kulkarni_2x2_inaccurate when a
low error rate matters more than mean error, since the band is forced
to one on every input.

## references

bhardwaj2014 -> K. Bhardwaj, P. S. Mane, J. Henkel, "Power- and Area-Efficient Approximate Wallace Tree Multiplier for Error-Resilient Systems", 15th International Symposium on Quality Electronic Design (ISQED), pp. 263-269, 2014
