# rns_channel_arithmetic

Arithmetic in independent residue channels: an integer is
represented by its residues over N pairwise relatively prime moduli
whose product M is the dynamic range, and addition, subtraction and
multiplication execute channel by channel with no carry between
channels, so every channel is a narrow modular adder or multiplier.
Moduli of the forms 2^n, 2^n-1 and 2^n+1 give the structure: the 2^n
channel discards its carry-out, the 2^n-1 channel is an
end-around-carry adder, and the 2^n+1 channel uses a diminished-1
encoding so that its adder and multiplier reduce by inverting and
feeding back one bit; generic moduli need a table or a general
modular correction.

The modulus form trades channel balance against operator
simplicity. Arbitrary moduli give flexible, balanced channel widths,
which the early filters exploit with heterogeneous sets such as {16,
13, 11, 9, 7} in 4-bit channels and the cryptographic units with 32-bit
channels near 2^32 or pseudo-Mersenne 2^r - epsilon channels that
fold the high product part; the special forms give the identities
that simplify operators and converters, and a set may be chosen
exhaustively for minimum area-delay product from per-modulus stage
costs. Channel width sets the table size for lookup channels and the
adder depth for logic channels. The diminished-1 encoding of the
2^n+1 channel makes its residue reduction two fixed carry-save stages
whose delay is independent of n.

The multiplier reduction is a table, a folded tree, or Booth. ROM
channels of at most 5 bits address a 10-bit table and fold a chain of
fixed operations into one lookup: a 16 x 16 signed product in seven
8K ROMs at 55 ns against about 115 ns with 4-bit multipliers and
lookahead adders. The folded tree rotates modulo-reduced
partial products into an end-around carry-save tree and one modulo
carry-propagate adder, and costs about the same area as an integer
multiplier and about 7% to 10% more delay at 8 to 32 bits in 0.25 um,
with the 2^n+1 form slightly larger for its correction terms; Booth
halves the partial products but does not always reduce area or tree
delay. Radix-4 Booth with 4:2 compression and a Sklansky merge adder
gives a 19-bit RNS multiplier 4.62x lower energy and 2.1x lower delay
than a 16-bit binary one in 45 nm, while the RNS and binary adders
stay near parity.

The family is feed-forward and wins on workloads dominated by
addition and multiplication, such as FIR filters, DNN
multiply-accumulates and Montgomery multiplication, where results are
roundoff-free inside the range and errors stay localized to their
channel, so a faulty channel can be dropped if the remaining moduli
keep the range. It loses on conversion, which is expensive both ways,
and on sign detection, comparison, overflow, division and scaling,
which need inter-channel work.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/redundant.py`: the adder, multiplier and comparator of an `rns_internal` core: the moduli set follows `modulus_form` ({2^n - 1, 2^n, 2^n + 1}, pairwise coprime 2^a - 1, or odd generic moduli) with n fixed by an explicit `channel_width_n`, the channel adders per modulus form (end-around carry, the low bits, the normal or diminished-one adder of 2^n + 1 by `pow2_plus_1_encoding`, add and conditional subtract), and the channel multipliers by `multiplier_reduction` (a table, the rotated rows of 2^n +- 1 summed and folded, Booth rows with the modular correction of the negative ones, or the unrolled carry-save recurrence with the quotient digit estimated from `remainder_estimate_digits` top bits); the multi-operand adder and its final converter serve the forward converter's chunk sums). `python3 -m chialu.targets.rtl.families.redundant --width 32 --slot channels --kind adder --family rns_channel_arithmetic --pins k=v,...` emits it for a rewrite.

Here `channel_width_n` is the classic set's base exponent, the first
exponent of the Mersenne sequence, or the maximum residue width of the
generic set. It does not require every channel to have the same width:
the classic set has widths `(n, n, n+1)`, and the Mersenne exponents grow
until three pairwise-coprime moduli have been selected. The generic
moduli stay below `2^n`. An explicit n is never raised to accommodate
the lane; insufficient capacity is an error.

For W-bit ports the represented maximum is `2^(W+1)-1` for the adder,
`(2^W-1)^2` for unsigned multiplication, `2^(2W-2)` for multiplication
of signed magnitudes, and `2^W-1` for comparison. The product M of the
moduli must exceed that maximum. For example, the classic n=4 set has
M=4080 and accepts the unsigned 6-bit maximum product 3969, even
though M is below `2^12`. The signed multiplier zero-extends its
reconstructed magnitude to the full output width before applying the
sign; its magnitude may need fewer than 2W bits. When n is unspecified,
the generator chooses a set satisfying the same capacity check within
the declared 4..32 range, or reports that no legal default exists.

## design choices

### modulus_form

| member | what it selects |
| --- | --- |
| `pow2_minus_1` | Mersenne-like moduli 2^a - 1 with pairwise coprime exponents, whose channel adder is end-around carry. |
| `pow2` | the classic set {2^n - 1, 2^n, 2^n + 1}, extended by 2^(n+1) - 1 and 2^(n-1) - 1 where more channels are needed. |
| `pow2_plus_1` | the same set with the 2^n + 1 channel in the diminished-one encoding available. |
| `generic` | odd moduli below 2^n chosen pairwise coprime, which costs a general modular reduction per channel. |

### multiplier_reduction

| member | what it selects |
| --- | --- |
| `rom` | the channel product is reduced by a table. |
| `csa_with_periodic_folding` | the partial products are folded on the modulus's period in a carry-save tree. |
| `booth_modular` | the rows are Booth-recoded and reduced modulo the channel's modulus. |
| `iterative_carry_save_msd_estimate` | an unrolled recurrence r = 2r + a b_j - q m whose quotient digit comes from the top remainder bits, closed by one subtraction. |

## references

zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
zimmermann1999 -> R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
jenkins_leon_1977 -> Jenkins, Leon, "The Use of Residue Number Systems in the Design of Finite Impulse Response Digital Filters", IEEE Transactions on Circuits and Systems, 1977
jullien_1978 -> Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
ma_1998 -> Ma, "A Simplified Architecture for Modulo (2^n + 1) Multiplication", IEEE Transactions on Computers, 1998
conway_nelson_2004 -> Conway, Nelson, "Improved RNS FIR Filter Architectures", IEEE Transactions on Circuits and Systems II, 2004
samimi_2020 -> Samimi, Kamal, Afzali-Kusha, Pedram, "Res-DNN: A Residue Number System-Based DNN Accelerator Unit", IEEE Transactions on Circuits and Systems I, 2020
