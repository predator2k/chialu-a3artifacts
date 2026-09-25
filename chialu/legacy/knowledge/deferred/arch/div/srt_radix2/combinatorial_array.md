---
family: srt_radix2
pin: {implementation_topology: combinatorial_array}
---
# combinatorial_array

The recurrence unrolled in space: n copies of the quotient-selection
and remainder cell, one per quotient bit, connected as a purely
combinational array with no clocked stage between them and ending in
one redundant-to-binary converter that delivers the quotient. Each row
receives the previous row's residual, selects its digit, and passes
the next residual down.

It is the pick when the latency of one division matters more than
area and the residual form keeps each row at constant delay: with
signed-digit residuals the 64-bit array runs in 396 gate delays at
110k transistors, against 938 gate delays and 120k transistors for the
array built from SRT cells in the same 1987 CMOS process, so the delay
is about 42 percent of the baseline at about 90 percent of the
transistors. The reused clocked stage is the sibling when n rows are
not affordable or the divider is shared across operations; the array
has no iteration control and no registers between rows, and its
converter is the only carry-propagating structure.

## references

kuninobu_1987 -> Kuninobu, Nishiyama, Edamatsu, Taniguchi, Takagi, "Design of High Speed MOS Multiplier and Divider Using Redundant Binary Representation", 8th IEEE Symposium on Computer Arithmetic, 1987
