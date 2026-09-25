# end_around_carry

Addition whose carry-out re-enters as the carry-in, which yields
ones'-complement sums and modulo 2^n-1 or 2^n+1 residues: the
most-significant carry returns to the least-significant position as a
+1, and for modulo 2^n+1 in diminished-one representation the
complement of the carry-out re-enters instead. A parallel-prefix core
breaks the direct carry-in-to-carry-out path, which in a plain adder
forms a combinational loop that can oscillate, and re-propagates the
carry-out either in one extra prefix level that acts as a
carry-controlled incrementer or by wrapping the prefix equations
around inside every level so the depth stays at log2 n.

The modulus choice sets the feedback polarity and the zero policy.
Modulo 2^n-1 feeds the carry-out back directly and admits either a
double representation of zero, which the ones'-complement machines
tolerate by testing both patterns, or a single zero bought with a
group-propagate OR that also forces the all-ones sum to zero. Modulo
2^n+1 in diminished-one form inverts the feedback, lets the zero bit
pattern stand for 1, and needs conversion logic at the channel
boundary plus a small check for the false zero that complementary
inputs produce; in an RNS base of 2^n-1, 2^n and 2^n+1 this channel
dictates the addition delay.

The recirculation choice trades a second pass against prefix
hardware. A serial adder re-transmits the carry in another pass, while
a parallel ripple adder pays no extra propagation because the returned
carry cannot travel beyond its originating order. The extra prefix
level costs n more black nodes, which in unit gates is 3/2 n log n + 7n
area at 2 log n + 5 delay against 3/2 n log n + 4n at 2 log n + 3 for
the integer adder, and a final re-entry stage puts a fanout of n on
the reentering carry; wrapping the carry at every level removes both
the level and the fanout for about 3/2 n log n operators. Select-based
recirculation forms two tentative sums and lets a short carry pick
one, which replaces a full-length end-around addition by an m-bit one
in byte-organized residue checking and, in the POWER6 128-bit adder,
lets four 32-bit groups with wrapped carry equations feed conditional
sums into a transmission-gate multiplexer.

The topology choice is the integer prefix adder's, with Sklansky and
Kogge-Stone the usual pins, and algorithm-generated cyclic trees with per-row valencies and a repeated
chain stride distribute the cyclic carry across the network at the
price of more long wires. The family is the terminal adder of
ones'-complement floating-point significand paths, the minus-one
channels of RNS datapaths, and the residue generators and mod-15
checkers of concurrent error detection; a two's-complement adder
avoids both the second pass and the dual tentative sums. A 161-bit
ones'-complement CPA inside a fused multiply-add is picked for that path
because converting its result back to sign-magnitude is easy. That adder
corrects the end-around carry in one pass, feeding the incrementer's
propagate and the lookahead adder's group identifier back to the carry-in
rather than closing a loop.

The seed instantiates the library's module for this family
(`chialu/targets/rtl/families/adder_ext.py`: modulo 2^W - 1 in the double-zero convention (the ones'-complement lane's reference), modulo 2^W + 1 in diminished-one coding, or a generic modulus p with a complete ladder of aligned conditional subtractions over the full binary input sum; recirculation as a two-pass prefix adder with a prefix-AND incrementer pass, the Kogge-Stone cyclic recurrence (every level wraps around) or the select of both candidates by the carry-out; a ones'-complement mode's add class runs on it).

For diminished-one `cyclic_prefix_level`, the selected topology now builds
one generate/propagate graph. An extra carry row feeds the complement of
its whole-word generate into each prefix group. That row drives the sum;
the external `cin` then passes through the selected incrementer. The
all-propagate case needs a zero-code correction when `cin` is one. This
replaces the previous disconnected cyclic network and separate wide
addition/subtraction implementation. `diminished_cyclic_selftest` checks
the modular result, carry output and every actual prefix group against
integer arithmetic, and requires a feedback mutation to fail.

RNS raw-binary consumers and the multiplier netlist's CPA call sites
install an explicit decoder around the selected native EAC. This restores
ordinary `{cout,s}=a+b+cin` without replacing the chosen modular circuit.
Generic-p decoding uses the input quotients and remainders together with
the selected native remainder. The native family and ones'-complement
lane retain their original modular contracts. Other consumers must state
which arithmetic interface they require rather than assuming that equal
port widths imply equal semantics.

## design choices

### recirculation

| member | what it selects |
| --- | --- |
| `two_pass_prefix` | a first prefix adder produces the sum and its carry-out, and a second pass re-enters that carry. |
| `cyclic_prefix_level` | the recirculation is one extra prefix level inside the graph. |
| `select_based` | both candidate sums are computed and the carry-out selects between them. |

### topology

| member | what it selects |
| --- | --- |
| `sklansky` | the minimum-depth prefix graph with doubling fanout. |
| `kogge_stone` | the minimum-depth graph at unit fanout and maximal wiring. |
| `brent_kung` | a regular constant-track graph that spends an extra log depth. |
| `ladner_fischer` | the depth and wiring point between Sklansky and Kogge-Stone. |
| `han_carlson` | a Brent-Kung skeleton over a Kogge-Stone core. |
| `knowles_mixed` | the Knowles continuum, whose fanout vector names the point. |
| `harris` | the taxonomy's (l, f) point, which fixes the extra levels and the fanout cap. |

## realization

| claim | pins | the module header matches |
| --- | --- | --- |
| the carry out of the top re-enters at the bottom | - | `the carry-out re-enters as the carry-in` |

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
thornton_1970 -> J. E. Thornton, "Design of a Computer: The Control Data 6600", Scott, Foresman and Co., 1970
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
zimmermann1999 -> R. Zimmermann, "Efficient VLSI Implementation of Modulo (2^n +/- 1) Addition and Multiplication", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999
vergos2002 -> H. T. Vergos, C. Efstathiou, D. Nikolos, "Diminished-One Modulo 2^n + 1 Adder Design", IEEE Transactions on Computers, vol. 51, no. 12, pp. 1389-1399, 2002
efstathiou2004 -> C. Efstathiou, H. T. Vergos, D. Nikolos, "Fast Parallel-Prefix Modulo 2^n + 1 Adders", IEEE Transactions on Computers, 2004
avizienis_1985 -> A. Avizienis, "Arithmetic Algorithms for Operands Encoded in Two-Dimensional Low-Cost Arithmetic Error Codes", Proc. ARITH-7, pp. 285-292, 1985
yu_2006 -> X. Y. Yu, Y.-H. Chan, M. Kelly, E. Schwarz, B. Curran, B. Fleischer, "A 5GHz+ 128-bit Binary Floating-Point Adder for the POWER6 Processor", 32nd European Solid-State Circuits Conference (ESSCIRC), 2006
jessani_1996 -> R. M. Jessani, C. H. Olson, "The Floating-Point Unit of the PowerPC 603e Microprocessor", IBM Journal of Research and Development, vol. 40, no. 5, 1996
