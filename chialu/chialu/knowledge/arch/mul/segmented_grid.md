# segmented_grid

Multiplication as a rectangular grid of fixed-size segment blocks: each
operand is split into num_seg segments of seg_w bits, one block per
segment pair forms the segment product, and the blocks exchange partial
results with their left, right, top and bottom neighbours over
dedicated connections, so a grid of m by n blocks computes any (seg_w *
m)-bit by (seg_w * n)-bit product. Only the blocks in the final column
use their output adders, and the segment partial products are merged by
a carry-propagate adder chosen from the adder space. Configuration bits
per block mark the signed most-significant segment and the operand
boundaries, so one block serves signed and unsigned operands.

The segment width and segment count trade block granularity against
interconnect: a 4x4 flexible block needs 36 dedicated inter-block
connections, half again as many as Hwang's reconfigurable partial-array
modules, and that interconnect is what lowers the delay growth from
O(N^2) to O(N) in the operand size, comparable to a fixed-size
Baugh-Wooley array. The merge_adder slot picks the carry-propagate
adder that resolves the final column, and any adder family applies. The
regular connection pattern scales to other block sizes, and the grid
avoids general reconfigurable routing between blocks.

The family wins when the multiplier size must be reconfigurable and the
blocks are embedded in an FPGA: the estimated embedded-block
implementation takes about 50 times less silicon than the same
multiplier configured from conventional FPGA resources, while its gate
count exceeds Hwang's scheme by about 3 percent. It loses to a
fixed-size tree multiplier once the size is fixed, since the cost of
reconfigurability is about 50 percent more gates than a fixed
Baugh-Wooley or Wallace/Dadda design and the delay grows linearly
rather than logarithmically. The datapath is feed-forward.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/mul_ext.py`: square or rectangular segment products through the `segment` slot's multiplier, a segmented grid again while `recursion_depth` is above one, the top segment of a signed operand signed, merged by a chain or a shift-add tree of `merge_adder` instances or by the `merge_tree` reduction; the runtime lane mode is the subword slot's and the temporal composition a later version's).

## design choices

### merge_form

| member | what it selects |
| --- | --- |
| `cpa` | the segment products are merged by a carry-propagate chain of merge adders. |
| `carry_save_tree` | they are merged by a reduction over the product bits. |
| `shift_add_tree` | they are merged by a shift-add tree of merge adders. |

## references

haynes_1998 -> S. D. Haynes, P. Y. K. Cheung, "Configurable Multiplier Blocks for Embedding in FPGAs", Electronics Letters, 1998
