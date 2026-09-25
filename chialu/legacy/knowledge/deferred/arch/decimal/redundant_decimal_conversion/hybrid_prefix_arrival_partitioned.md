---
family: redundant_decimal_conversion
pin: {borrow_network: hybrid_prefix_arrival_partitioned}
---
# hybrid_prefix_arrival_partitioned

The borrow network for signed-digit to BCD conversion built from
several small prefix networks, Ladner-Fischer, 2-bit carry-lookahead
and Han-Carlson, joined according to the arrival times of the
partial-product-reduction digits. A negative digit generates the
borrow, a zero digit propagates it, the network computes the
interdigit negative carries, and a conditional constant adder selects
S, S-1, S+10 or S+9 per digit from the adjacent carry states.

The pick when the converter closes a parallel multiplier tree whose
columns settle at different times: a uniform prefix tree waits for
the last column, while the partitioned hybrid lets the early columns
resolve in their own sub-networks and joins them where the late
columns arrive, which gives a 410 ps converter tail, covering
generate/propagate, prefix tree and selection, at 90 nm for the 16 by
16 digit multiplier. Ripple and plain carry look-ahead are the
siblings for a converter whose inputs arrive together, and the
digitwise constant scheme applies only to the BCD to RBCD direction.
The partition follows the arrival profile of one reduction tree, so a
different tree needs its own partition.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

han_2013 -> Han, Ko, "High-Speed Parallel Decimal Multiplication with Redundant Internal Encodings", IEEE Transactions on Computers, 2013
