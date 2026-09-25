# trailing_zero

Count or locate the lowest set bit of a word by one of three routes:
bit-reverse the operand by wiring and feed it to a leading-zero
detector, so the detector's 2-bit valid/position cells or its
carry-lookahead flag equations serve unchanged; isolate the lowest
set bit, by x AND -x or by a ripple kill chain, and encode the
resulting one-hot with a priority encoder or a leading-zero detector;
or isolate the bit, multiply by a de Bruijn constant, and index a
2^k-entry table. Every route is combinational and feed-forward.

The strategy decides what is reused. Reversal costs only wiring and
redirects an existing leading-zero detector to trailing-zero duty,
which is the structure-reuse move of this domain, so its depth and
energy are those of the detector: modular 2-bit cells composed to 32
or 64 bits beat flat synthesis, and the carry-lookahead formulation
lowers energy per count against the cell tree. Isolate-then-encode
builds a dedicated unit whose delay is set by the encoder's
priority-propagate chain; lookahead groups or tree folding shorten
that chain, and a 32-bit priority-lookahead encoder gains about 2.5x
speed for roughly 10% more transistors than the ripple version. The
de Bruijn route replaces the encoder with a small constant multiplier
and a table; it is the branch-free software ctz that a hardware unit
has to beat.

The `lzd` slot names the detector the reversed word feeds and the
`negation_incrementer` slot the incrementer of the two's-complement
isolate. The isolate circuit trades the two's-complement AND, which reuses
arithmetic already present, against a ripple kill chain, which is the
same chain the priority encoder is built from and shares its
group-size lever: group size trades logic depth against fan-in and
select decode across the whole domain. The family wins as a reversal
whenever the datapath already carries a leading-zero detector, as it
does for normalization, and as a dedicated isolate-and-encode unit
where only the trailing count is wanted and the detector is absent.

## design choices

### isolate_circuit

| member | what it selects |
| --- | --- |
| `twos_complement_and` | the lowest set bit as a & -a, with the negation through the incrementer slot. |
| `ripple_kill_chain` | the lowest set bit from a kill chain that clears every position above the first one. |

### strategy

| member | what it selects |
| --- | --- |
| `reverse_then_lzd` | the word is bit-reversed into the leading-zero detector slot. |
| `isolate_then_encode` | the lowest one is isolated and encoded to its index by an OR network. |
| `debruijn_multiply_index` | the isolated one is multiplied by a de Bruijn constant and its top bits index a table. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the count comes from the leading-zero detector on the reversed word | - | `the word reversed into the leading-zero detector` |

## references

leiserson_1998 -> C. E. Leiserson, H. Prokop, K. H. Randall, "Using de Bruijn Sequences to Index a 1 in a Computer Word", MIT LCS technical memo, 1998
oklobdzija_1994 -> V. G. Oklobdzija, "An Algorithmic and Novel Design of a Leading Zero Detector Circuit: Comparison with Logic Synthesis", IEEE Transactions on VLSI Systems, vol. 2, no. 1, pp. 124-128, 1994
dimitrakopoulos_2008 -> G. Dimitrakopoulos et al., "Low-Power Leading-Zero Counting and Anticipation Logic for High-Speed Floating Point Units", IEEE Transactions on VLSI Systems, vol. 16, no. 7, 2008
delgado_frias_2000 -> J. G. Delgado-Frias, J. Nyathi, "A High-Performance Encoder with Priority Lookahead", IEEE Transactions on Circuits and Systems I, vol. 47, no. 9, pp. 1390-1393, 2000
wang_2000 -> J.-S. Wang, C.-H. Huang, "High-Speed and Low-Power CMOS Priority Encoders", IEEE Journal of Solid-State Circuits, vol. 35, no. 10, pp. 1511-1514, 2000
