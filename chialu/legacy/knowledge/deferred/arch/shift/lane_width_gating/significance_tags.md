---
family: lane_width_gating
pin: {detection: significance_tags}
---
# significance_tags

Each 32-bit value carries extension bits that record whether each
upper byte is significant or a sign extension, with the low byte
always represented. The bits live with the values in caches and
registers, flow through the pipeline, control byte-bank accesses and
ALU activity, and gate pipeline latches. Serial organizations process
only the significant bytes over several cycles; semi-parallel and
byte-parallel organizations instantiate more byte lanes and disable
the unneeded ones.

With 8-bit significance compression on a 32-bit MIPS-like in-order
pipeline, Mediabench activity falls by 33.2% in the ALU, 46.5% on
register-file reads and 42.2% in the pipeline latches, the three-bit
encoding adds 9% metadata and the two-bit alternative 6%, and the
byte-serial organization costs 79% CPI, semi-parallel 24%,
byte-parallel compressed 6% and byte-parallel skewed with bypasses 2%
(canal_2000). Activity reduction stands in for dynamic energy, and the
full-width organizations need extra latches, forwarding paths or
control. The tags are the pick when narrowness should be known before
a value is read, so that storage as well as the datapath is gated;
msb_zero_detect recomputes the width at each result, and static_mode
fixes it per operating mode.

## references

canal_2000 -> R. Canal, A. Gonzalez, J. E. Smith, "Very Low Power Pipelines Using Significance Compression", Proc. MICRO-33, pp. 181-190, 2000
