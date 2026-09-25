---
family: vector_lane_masking
pin: {masked_write: merge_preserve_old}
---
# merge_preserve_old

Merging predication: an inactive lane leaves its destination
untouched, so a masked store updates only the selected 8-, 16- or
32-bit components and the unselected memory locations keep their
previous contents. In VIS the mask comes from pixel comparisons or
edge instructions in an integer register and is applied by a
partial-store instruction with one-cycle latency and throughput.

Merging is the pick when the old values are meaningful, which is the
case for image boundaries and for accumulating into a destination
across several masked passes: edge-generated masks with partial
stores remove the branchy boundary code, and the CRAY-1 vector merge
composes two vectors under the mask in the same spirit. It costs a
read-modify-write or a write-enable per lane and a dependency on the
prior destination value, which zeroing predication removes by writing
zeros to the inactive lanes; SVE offers both behaviors and lets the
instruction choose.

## references

tremblay_1996 -> M. Tremblay, J. M. O'Connor, V. Narayanan, L. He, "VIS Speeds New Media Processing", IEEE Micro, vol. 16, no. 4, pp. 10-20, 1996
stephens_2017 -> N. Stephens et al., "The ARM Scalable Vector Extension", IEEE Micro, vol. 37, no. 2, pp. 26-39, 2017
