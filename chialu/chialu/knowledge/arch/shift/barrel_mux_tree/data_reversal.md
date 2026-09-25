---
family: barrel_mux_tree
pin: {direction_handling: data_reversal}
---
# data_reversal

A single right shifter or rotator handles both directions by reversing
the input word before the mux stages and reversing the output
afterwards for left operations, so the shift amount passes through
unchanged and no complement or preshift enters the control path. The
mux-based form selects shift or rotate per stage; the mask-based form
rotates, then applies generated masks to build the logical and
arithmetic shifts and computes the zero and overflow flags in parallel
with the rotation.

Mask-based data reversal has the lowest delay at every tested width
from 8 to 128 bits because flag detection runs in parallel and no
shift/rotate selection mux is added, and one of the two data-reversal
designs has the lowest area at every width; at 32 bits in the IBM
CU-11 0.11 um library it synthesizes to 6141 gates and 0.94 ns against
8827 gates and 1.19 ns for the mask-based two's-complement amount
transform and 9825 gates and 1.22 ns for the one's-complement one,
with area growing as O(n log n) and delay as O(log n)
(pillmeier_2002). The scheme is the pick for a standalone
bidirectional shifter judged on area and delay; amount_negation wins
when a rotator is already present and the reversal muxes would be the
extra cost, and mirrored_datapath when the two directions belong to
different points of the pipeline.

## references

pillmeier_2002 -> M. R. Pillmeier, M. J. Schulte, E. G. Walters III, "Design Alternatives for Barrel Shifters", Proc. SPIE 4791, Advanced Signal Processing Algorithms, Architectures, and Implementations XII, 2002
