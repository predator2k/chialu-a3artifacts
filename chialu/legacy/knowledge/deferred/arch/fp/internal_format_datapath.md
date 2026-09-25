# internal_format_datapath

One wide internal representation carries every architected format
through an inherited datapath: input converters after the operand
registers translate each architected operand (three HFP and three BFP
formats in the S/390 G5) into a 56-bit hexadecimal-based fraction with
a 14-bit exponent, the existing hexadecimal alignment, arithmetic and
normalization macros perform the add, multiply, divide, square root and
store computation, and sticky logic with one final binary rounder
converts the result back, handles five rounding modes and special
values, and preserves the inherited HFP critical paths.

The four choices set the width of the bridge. internal_radix with
internal_fraction_bits and internal_exponent_bits fix the internal
format the core executes; the G5 point is a hexadecimal-based 56-bit
fraction with a 14-bit exponent, and the ranges bracket that point.
architected_formats states which format sets the converters accept;
the evidenced value is hfp_and_bfp, where BFP operands are converted
to the internal format after the Areg/Breg operand registers, all
arithmetic runs in the HFP form, and results are converted and rounded
to BFP before the Creg result register, with the 32-, 64- and 128-bit
formats and special-case operands handled in hardware without
millicode.

The family wins when an existing datapath must gain a second
architected format at low design cost: the inherited critical paths
are untouched, so the native format keeps its timing (one HFP result
per cycle at 3-cycle latency on the G5 in IBM CMOS 6X), and the
non-native format pays for the two boundary conversions (two cycles per
BFP result at 5-cycle latency) while running about 100 times faster
than a software BFP implementation. It loses to a native datapath per
format when the non-native format dominates the workload, since the
conversion cycles and the single shared rounder cap its throughput.
The core_add, core_mul and core_div slots are the inherited datapath
families and the round slot is the one binary rounder;
widen_internal_exponent grows the internal exponent,
add_boundary_converters is the retrofit move, and
unify_datapaths_over_shared_core is the same structure that the
posit_ieee_interop family reaches with boundary converters. Execution
is feed-forward around the slot cores.

## the library's module

The seed instantiates the library's generated float module for this family
(`chialu/targets/rtl/families/fp.py`, value-exact against the engine: the source decoded into the engine's wide internal value, the target's rounder at the boundary).
The choices and the component families (round) select its sub-structures
from the library.

## references

schwarz_1999 -> E. M. Schwarz and C. A. Krygowski, "The S/390 G5 Floating-Point Unit", IBM Journal of Research and Development, 1999
slegel_1999 -> T. J. Slegel et al., "IBM's S/390 G5 Microprocessor Design", IEEE Micro, vol. 19, no. 2, pp. 12-23, 1999
