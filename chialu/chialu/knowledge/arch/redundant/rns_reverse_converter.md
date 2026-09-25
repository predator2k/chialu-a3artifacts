# rns_reverse_converter

This family declares `moduli_count`, but no channel-width axis. Its
derived n follows the lane width and requested count and may exceed 32;
the `channel_width_n` range of `rns_channel_arithmetic` does not apply.

In the generated `adder_based` CRT boundary, constant products use
shift-add logic. The generator expands the constant's CSD digits or
the narrow operand's binary digits, whichever needs fewer terms;
every addition uses the selected channel CPA. It reduces each product
by a descending sequence of aligned modulus subtractions through that
same CPA, using carry-out to select the nonnegative difference. The
largest possible canonical operand bounds the first subtraction.
This preserves arithmetic conversion when many channels make CRT
constants hundreds of bits wide, without constructing a large table
for every slice of the product. These changes apply to `adder_based`;
the ROM variant is a separate implementation. The final sum of canonical CRT terms is
reduced below the product of the moduli as before.

Residue-to-binary reconstruction of the weighted integer from all
channels: the Chinese remainder theorem forms X as the sum over
channels of x_i times the constant s_i |1/s_i|_{m_i}, with s_i =
M/m_i, reduced modulo M; mixed-radix conversion first derives mixed-
radix digits and then sums each digit's weighted binary contribution;
the new CRT-I rewrites the CRT so that the final modulus shrinks and,
for special sets such as {2^n-1, 2^n, 2^n+1}, the conversion collapses
to additions of rearranged and complemented residue fields in end-
around-carry adders. The converter decides whether RNS wins overall,
so the algorithm and the moduli set are co-selected.

The algorithm trades the shape of the final reduction against
sequential depth. The CRT needs multiplication by large constants and
a modulo-M step, which a filter absorbs by premultiplying the constants
into its coefficients and accumulating ROM outputs in a mod-M
adder-shifter, and which a quotient/remainder split reduces to one or
two extra additions with a conditional subtraction of M. Mixed-radix
conversion is strictly sequential unless every residue addresses
tables for its projection's digits and the triangular digit array is
summed by column, which takes two clock cycles instead of n-1 for up to
15 moduli (50 ns against 350 ns in ECL) at n(n+1)/2 half-size tables
plus n comparator/subtractors. For the three-moduli special set the
CRT form needs two carry-save stages with end-around carry and one
2n-bit one's-complement adder, and the new CRT-I form either halves
that hardware with a single 2n-bit adder or doubles the speed with four
n-bit carry-lookahead adders. The moduli count grows the converter,
special moduli permit bit selection, reshuffling and modular carry-save
addition, and arbitrary moduli generally need lookup tables that are
hard to pipeline.

The implementation choice follows the input width: a ROM converter is
practical when the width and moduli are fixed, an 8-bit conversion over
moduli 15 and 17 fits one 4K table and the memory-side neural
accelerator pays under 6% for both conversions, whereas adder-based
converters are memoryless and pipelineable. A cryptographic RNS datapath
reuses its modular multipliers, either expanding the CRT into radix-2^r
rows accumulated in the Rower units at 2n^2+n modular multiplications,
or extracting one radix word per step through a channel fixed at 2^r at
under 0.3% of a scalar multiplication. The contract is exact within the
dynamic range; decoding scaled by one modulus shortens the words at a
bounded quantization error, signed output comes from a circular shift
by M/2, and a NAND in the end-around-carry path forces a single zero
representation. Execution is feed-forward.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/redundant.py`: the residue-to-binary conversion of every result of an `rns_internal` core: the Chinese remainder theorem with constant multipliers as shift-adds over CSD digits or weighted operand bits, folded below M (adder_based) or per-channel tables (rom) and a ladder of conditional subtractions below M, the mixed-radix chain of modular subtract-and-multiply steps, and Wang's New CRT-I and New CRT-II with their smaller final modulus (`algorithm`, `implementation`, `moduli_count`); the generator derives canonical intermediate bounds and rejects unsupported selectors). `python3 -m chialu.targets.rtl.families.redundant --width 32 --slot channels --kind adder --family rns_reverse_converter --pins k=v,...` emits it for a rewrite.

The ROM implementation uses complete case tables with at most eight address
bits per bank for every nontrivial modular constant product. Selected
channel CPAs merge their canonical outputs. Mixed-radix steps, CRT-I
reconstruction and both CRT-II subgroups honor this choice. A wide ROM
choice never substitutes CSD multiplication. The arithmetic implementation
uses selected CPA constant products and bounded conditional subtraction.
Canonical residue inputs and an output wide enough for the full product
of the moduli are required.

`rns_reverse_selftest` checks all 24 algorithm/implementation/channel-count
bindings and directed unequal, unordered and wide modulus sets: 52 cases,
41,156 independent integer-reconstruction vectors. The elaborated
hierarchies and activity probes distinguish the 168 actual ROM banks and
1,095 selected CPAs in those fixtures. These fixtures fix the child CPA
pins; they do not certify every nested CPA algorithm.

## design choices

### algorithm

| member | what it selects |
| --- | --- |
| `crt` | the Chinese remainder theorem sum of the residues weighted by M / m_i, reduced modulo M. |
| `mixed_radix` | mixed-radix conversion: the digits are extracted channel by channel, so no reduction modulo M is needed. |
| `new_crt_i` | the New CRT-I recurrence, which carries the difference of successive residues through constant multiplies. |
| `new_crt_ii` | New CRT-II: the moduli split in halves, each half converted by the CRT, and the halves joined by X_A + M_A |k (X_B - X_A)|_{M_B}; three channels use a real 1+2 split, four use 2+2, and five use 2+3. |

## references

jenkins_leon_1977 -> Jenkins, Leon, "The Use of Residue Number Systems in the Design of Finite Impulse Response Digital Filters", IEEE Transactions on Circuits and Systems, 1977
jullien_1978 -> Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
huang_1983 -> Huang, "A Fully Parallel Mixed-Radix Conversion Algorithm for Residue Number Applications", IEEE Transactions on Computers, 1983
vu_1985 -> Vu, "Efficient Implementations of the Chinese Remainder Theorem for Sign Detection and Residue Decoding", IEEE Transactions on Computers, 1985
piestrak_1995 -> Piestrak, "A High-Speed Realization of a Residue to Binary Number System Converter", IEEE Transactions on Circuits and Systems II, 1995
kawamura_2000 -> Kawamura, Koike, Sano, Shimbo, "Cox-Rower Architecture for Fast Parallel Montgomery Multiplication", EUROCRYPT (LNCS 1807), 2000
wang_2002 -> Wang, Song, Aboulhamid, Shen, "Adder Based Residue to Binary Number Converters for (2^n-1, 2^n, 2^n+1)", IEEE Transactions on Signal Processing, 2002
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
