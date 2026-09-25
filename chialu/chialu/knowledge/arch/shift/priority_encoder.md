# priority_encoder

An N-input fixed-priority encoder asserts only the output that
corresponds to the highest-priority asserted request, and its delay
is the kill chain that carries priority status from cell to cell.
Priority lookahead partitions the chain into four-bit segments, each
with a precharged lookahead line that any asserted request in the
segment discharges, so priority status jumps across a segment instead
of rippling through it; cascaded modules add intermodule discharge
and precharge circuitry, and further lookahead levels connect pairs
of 4-bit cells and pairs of 8-bit macro cells so that the one-hot
tokens are updated through a tree rather than a sequential chain.

The lookahead group and the number of levels set the delay against
the transistor count and fanout. One level of four-bit lookahead cuts
the worst-case delay of a 32-bit encoder from 11.4 ns to 4.4 ns in
1 um CMOS, about 2.6x, for a transistor count of 16N + 6(N/4) against
15N + 4(N/4), about 9% more; the four-bit segment is the compromise
between fanout and delay, and the worst case is the first and last
requests asserted with everything between deasserted. Three levels,
with four outputs per first-level signal and two more levels of
pairing, give a 32-bit encoder about 65% more speed, 20% less layout
area and 30% less power than a conventional single-lookahead design
in 0.6 um CMOS, though part of that gain comes from layout and
sizing rather than the structure.

The output form decides whether the one-hot result is encoded to a
binary index in a following stage or used directly; the reported
encoders stop at the one-hot output. The circuit style is dynamic in
every reported design: precharged pass-transistor lines, or NP domino
gates connected in parallel for speed or in series for lower
switching activity, the latter needing a lookahead-controlled pMOS
correction to resolve the race between cascaded n-type gates.

The family is feed-forward, is the leading-one detector of shifters
and normalizers, and wins over a standard-gate cascade, which needs
many more transistors for little gain; a static fixed priority is set
by wiring, so a configurable priority needs another structure.

## design choices

### output_form

| member | what it selects |
| --- | --- |
| `one_hot_then_encode` | a one-hot vector is formed and then encoded. |
| `direct_binary` | the position is resolved directly into binary. |

## references

delgado_frias_2000 -> J. G. Delgado-Frias, J. Nyathi, "A High-Performance Encoder with Priority Lookahead", IEEE Transactions on Circuits and Systems I, vol. 47, no. 9, pp. 1390-1393, 2000
wang_2000 -> J.-S. Wang, C.-H. Huang, "High-Speed and Low-Power CMOS Priority Encoders", IEEE Journal of Solid-State Circuits, vol. 35, no. 10, pp. 1511-1514, 2000
