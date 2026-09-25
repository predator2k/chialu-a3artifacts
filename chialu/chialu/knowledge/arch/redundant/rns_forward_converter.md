# rns_forward_converter

Binary-to-residue conversion, one channel per modulus and every channel
independent of the others: a chunk of input bits addresses a table of
its contribution 2^j mod m and the chunk contributions are summed by
modular adders; a memoryless channel partitions the bits into P(A)
weight classes, where P(A) is the period of 2^j mod A, reduces them in
a carry-save tree whose carries wrap after P(A) positions and finishes
in a cyclic adder plus a ROM or PLA; a cryptographic datapath computes
x mod m_i as the sum of x(j) times the precomputed constant 2^rj mod
m_i on its n Rower multiplier-accumulators in n steps. The converter is
the entry tax paired with rns_reverse_converter.

implementation trades storage against adders. rom_per_chunk converts a
whole chunk in one lookup: one 8K semiconductor ROM per modulus turns a
10-bit word into residues in one lookup cycle, and a 20-bit word split
into two equal parts costs 3N ROMs and two lookup cycles because the
two chunk residues are summed. segmented_rom_modular_add stores partial
sums of the bitwise values 2^j mod p_i in several ROMs, so each residue
needs one modular addition instead of a chain of them, at more ROM (two
4-bit segments at t = 7: 2L ROMs of 16 words). periodic_csa_moma
removes the tables and their exponential growth with the word length
from the channel, and pipelines like any carry-save tree; a 32-bit
generator mod 9 takes 25 full adders plus one half adder, 9 delta and
a 128 x 4 ROM. channel_modular_mac adds no hardware to a
Cox-Rower datapath and spends n^2 modular multiplications. chunk_bits
sets the table size, with 1 the bitwise encoder; moduli_count adds one
channel per modulus; modulus_class decides whether the modular_adder
slot is an end-around-carry adder or, for a generic modulus, a
two's-complement adder followed by the fixed correction 2^L - p;
signed_input treats the chunk holding the sign bit as signed and the
other chunks as unsigned; final_reduction is a modular adder after
tables or a ROM or PLA after the cyclic adder.

The family wins where the residue channels justify their entry: a fixed
word width and fixed moduli favour tables, a wide word or an arbitrary
odd modulus favours the periodic tree, and a datapath that already
holds channel multiplier-accumulators converts without extra hardware.
Against rns_reverse_converter the forward direction is cheap, because no
channel depends on another and no reconstruction modulo M occurs; the
two converters together decide whether an RNS datapath wins overall, so
the moduli set is co-selected with both (the
co_select_moduli_set_with_converter mutation). The column_reducer slot
takes the csa_tree of adder_tree_space for the periodic form, and the
modular_adder slot takes the channel adder. The contract is exact.
Execution is feed-forward; the channel-MAC form runs n steps on n
Rowers.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/redundant.py`: the binary-to-residue conversion of every operand of an `rns_internal` core: chunk tables of (chunk 2^(j i)) mod m of `chunk_bits` summed by modular adders (rom_per_chunk), the same tables reduced per segment first (segmented_rom_modular_add), the periodic folding of the word into n-bit slices for the 2^n +- 1 channels (periodic_csa_moma), or the unrolled chunk Horner chain of modular multiply-adds (channel_modular_mac); `final_reduction` picks the modular adder or a table on the chunk sum; `moduli_count` sizes the set; a signed operand is presented as a magnitude by the lane). `python3 -m chialu.targets.rtl.families.redundant --width 32 --slot channels --kind adder --family rns_forward_converter --pins k=v,...` emits it for a rewrite.

`moduli_count` constructs exactly the requested 3 through 64 channels.
The first three moduli are the classic `(2^n-1, 2^n, 2^n+1)` set; the
fourth and fifth are `2^(n+1)-1` and `2^(n-1)-1`, with even n. Additional
channels take ascending odd candidates that are coprime to every
already-selected modulus. Their widths follow these actual moduli;
this converter has no `channel_width_n` pin. The generator chooses the
first n whose complete set is coprime and has enough capacity for the
operation, including n above 32 when a wide lane needs it. The 4..32
axis belongs only to `rns_channel_arithmetic`. It never clips the channel count. For a 9-bit adder and
count 64, n=4 gives 64 moduli with residue widths from 3 to 9 bits and
a 428-bit combined range; all 64 conversions and channel additions
feed the reverse converter. `rns_geometry_selftest` checks every count
and inspects the actual CPA ports of the largest seed.

## design choices

### final_reduction

| member | what it selects |
| --- | --- |
| `modular_adder` | the chunk tables are summed by a chain of modular adders. |
| `rom` | the chunk tables are summed once and the sum reduced by a table, or by a subtract ladder where the sum is too wide to tabulate. |

## references

jenkins_leon_1977 -> Jenkins, Leon, "The Use of Residue Number Systems in the Design of Finite Impulse Response Digital Filters", IEEE Transactions on Circuits and Systems, 1977
jullien_1978 -> Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
piestrak_1994 -> S. J. Piestrak, "Design of Residue Generators and Multioperand Modular Adders Using Carry-Save Adders", IEEE Transactions on Computers, vol. 43, no. 1, pp. 68-77, 1994
kawamura_2000 -> Kawamura, Koike, Sano, Shimbo, "Cox-Rower Architecture for Fast Parallel Montgomery Multiplication", EUROCRYPT (LNCS 1807), 2000
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
