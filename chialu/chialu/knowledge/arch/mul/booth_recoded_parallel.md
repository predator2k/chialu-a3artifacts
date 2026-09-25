# booth_recoded_parallel

Parallel multiplication with recoded partial products: the multiplier
operand is recoded (radix-4 Booth halves the partial-product count;
radix-8 needs a hard 3x multiple), the partial products are reduced by
a carry-save tree, and one final carry-propagate adder resolves the
redundant sum. Signed operands come for free from the recoding; the
sign-extension rows collapse into constant correction bits.

The three components move independently: recoding radix (partial
products vs multiple generation cost), reduction geometry (Wallace
reduces early, Dadda reduces late with fewest counters, TDM assigns
wires by arrival time; 4:2 compressors regularize layout), and the
final CPA, whose non-uniform input arrival profile rewards a hybrid
adder over any textbook prefix tree. The family is the default for
width >= 8 exact multiplication; array multipliers beat it only under
tight regularity/low-power constraints at small width, and truncated /
logarithmic families apply only once the accuracy contract is
statistical rather than exact.

The radix decision weighs rows against multiple generation and against
the tree's level count. An analytic model counted in CSA units gives
radix-4 Booth the lowest delay at most widths, radix-8 about 10% less
area and energy at large n, and radix-16 only a marginal area gain over
radix-8 at twice the wire tracks; moving the mux XNOR from the selected
output onto the multiplicand and sharing the term with the neighbouring
mux takes 0.5 CSA gate delay off the Booth path at no extra area. A
60-bit unit rejected radix 8 because the +-3 multiple adds delay and
both radices need four 4:2 levels at that width, so the higher radix
saves no level there.

Row count is cut further at the edges of the matrix. Sign-extension
embedding that leaves the most significant row non-negative sends 13
rather than 14 rows into the tree and removes one 3:2 stage, a reduced
left-edge banded matrix gives a 57-bit first row and 56-bit remaining
rows, and the hot one of a negative row is appended as b'01' to the low end
of the row two positions to its left. The array itself need not be built at
full width: a half-size array that splits the multiplier operand into a
28-bit and a 25-bit part double-pumps a double-precision product, feeds
the first pass's sum and carry back into free tree inputs and defers the
last first-pass hot one to the second pass, for about half the area of
the single-pass array, 2.5 mm2 against 5.1 mm2 in the same process. A
quad-precision unit recodes 18 multiplier bits per cycle into 9 partial
products and retires 18 bits of its 226-bit sum and carry vectors per
cycle, which fits an area and power budget rather than a latency target.
One control signal can switch the same partial-product generate logic
between unsigned and signed rows, which a merged fixed and
floating-point unit needs.

## the library's module

The seed instantiates the library's generated multiplier for this family
(`chialu/targets/rtl/families/mul.py`: radix-4, radix-8 or radix-16 Booth rows over the signed extension of the operands; the hard multiples 3a, 5a and 7a through the `hard_multiple_adder` slot's adder, as short adders whose tile carries join the tree (partially_redundant) or through a lookahead specialized to a + 2^k a (specialized_3m_cpa); the negative rows as ones' complement plus a bit or as multiples precomputed through the `negation_incrementer` slot; the sign extension in full, as ~s plus a folded constant, or as Roorda's compact pattern); the reduction and the final adder follow the `reduction.*` choices (the counter tree in five geometries over 3:2, 4:2, 5:2 or 7:3 counters, the compressor tree, or the tiled CPA tree; any adder family for the final add, or the arrival-driven regions of `hybrid_arrival_driven`). `python3 -m chialu.targets.rtl.families.mul
--width 32 --family booth_recoded_parallel --signed --sv mul32.sv` emits it for a rewrite.

## design choices

### sign_extension

| member | what it selects |
| --- | --- |
| `prevention_constant` | the sign extension is replaced by a constant added once, which is the standard prevention trick. |
| `full_extension` | every row is sign-extended to the product width. |
| `roorda_compact` | Roorda's compact encoding of the extension bits. |

## references

booth1951 -> A. D. Booth, "A Signed Binary Multiplication Technique", Quart. J. Mech. Appl. Math., 1951
macsorley1961 -> O. L. MacSorley, "High-Speed Arithmetic in Binary Computers", Proc. IRE, 1961
wallace1964 -> C. S. Wallace, "A Suggestion for a Fast Multiplier", IEEE Trans. Electronic Computers, 1964
dadda1965 -> L. Dadda, "Some Schemes for Parallel Multipliers", Alta Frequenza, 1965
galal_2013 -> S. Galal, O. Shacham, J. S. Brunhaver, J. Pu, A. Vassiliev, M. Horowitz, "FPU Generator for Design Space Exploration", ARITH-21, 2013
jessani_1998 -> R. M. Jessani, M. Putrino, "Comparison of Single- and Dual-Pass Multiply-Add Fused Floating-Point Units", IEEE Transactions on Computers, vol. 47, no. 9, 1998
lichtenau_2016 -> C. Lichtenau, S. Carlough, S. M. Mueller, "Quad Precision Floating Point on the IBM z13", ARITH-23, 2016
naini_2001 -> A. Naini, A. Dhablania, W. James, D. Das Sarma, "1-GHz HAL SPARC64 Dual Floating Point Unit with RAS Features", ARITH-15, 2001
oh_2006 -> H.-J. Oh et al., "A Fully Pipelined Single-Precision Floating-Point Unit in the Synergistic Processor Element of a CELL Processor", IEEE Journal of Solid-State Circuits, vol. 41, no. 4, 2006
zhang_2018 -> H. Zhang, H. J. Lee, S.-B. Ko, "Efficient Fixed/Floating-Point Merged Mixed-Precision Multiply-Accumulate Unit for Deep Learning Processors", ISCAS 2018
