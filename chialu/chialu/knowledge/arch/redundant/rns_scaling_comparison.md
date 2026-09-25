# rns_scaling_comparison

RNS operations needing positional information without a full reverse conversion: scale, sign, compare, and base-extend each reconstruct part of the integer the residues encode. rom_mrc scales by a product of S moduli through iterated division by multiplicative inverses and a partial mixed-radix conversion. crt_fraction_estimate turns each CRT summand into a scaled binary fraction whose sum carries the wanted bit, the sign relative to M/2 or a scaled estimate with bounded error. redundant_modulus carries one extra residue mod p >= n so the unknown CRT multiple is recovered at one lookup depth. diagonal_function sums the residues mod SQ into a value whose order is the integer order.

operation sets what must be reconstructed. Scaling avoids overflow at some loss of output precision and is cheapest when the factor is a product of moduli or one modulus of a special set; sign detection asks only whether the value lies in the lower or upper half of M; comparison is a modular subtraction followed by sign detection or a direct order-preserving map; base extension underlies all of them. method trades table count against depth and against an extra channel. rom_mrc finishes in at most N lookup cycles with parallel two-input ROMs. crt_fraction_estimate needs one lookup and one ordinary binary addition, with enough stored precision that truncation cannot cross the sign boundary. redundant_modulus replaces the n-cycle Szabo-Tanaka chain by a tree of depth about log2(n + 1) + 1 and 2n + 2 tables, which for n = 8 is 16 tables and 5 lookup cycles against 35 and 8, but the redundant residue must accompany the data through every arithmetic operation. diagonal_function needs no redundant modulus and no iterative core, at the cost of a modulo-SQ summation network that grows with the modulus count; grouping moduli into virtual moduli shrinks SQ but needs a fast mixed-radix conversion inside each group.

exactness is the accuracy contract. Exact division and exact base extension return the true residues; the estimate form of scaling bounds its error by (S + 1)/2 with a round-down or round-off option. relax_to_approximate_scaling_with_bounded_error goes one step further, accepting an off-by-one extension uncorrected where the consuming reduction tolerates it, and a DNN accelerator built this way loses at most 1.15% inference accuracy against fp32. Special moduli sets of the form {2^n - 1, 2^(n+x), 2^n + 1}, optionally with a fourth modulus, fold division by 2^n into rotations, end-around-carry CSAs, and modulo CPAs, for up to 57% area-delay-product improvement over a converter-based scaler in 90-nm CMOS. The family is the RNS tax: a binary comparator at the same point costs 11.8x less energy and 2.9x less area in 45 nm, so they are kept rare.

The seed instantiates this family's comparator for an `rns_internal`
core, including when the ordinary binary-comparator slot is absent.
All three methods implement both exactness selections. The exact mixed-radix
path compares complete digits. Its approximate path compares two high
digits, then resolves ties with the remaining low digits. The diagonal
path uses an exact integer floor-sum identity; its approximate path compares
high diagonal bits, then corrects with the low bits and a residue tie key.
The CRT fractional path either uses its full precision or a coarse estimate
whose nearby results select the exact comparison. Unknown methods fail
instead of substituting mixed-radix logic. Scaling and base extension are
not ALU operations.

Approximate-with-correction targets must activate both stages. With the
default three-modulus set, mixed-radix and diagonal fixtures need at least
six operand bits; the fractional estimate needs seven. Smaller widths
are rejected because their coarse key is constant or their correction
is always selected. `rns_correction_selftest` probes every internal key
and decision against independent integer arithmetic, checks signed and
unsigned ordering, and corrupts each fractional decision path separately
to establish its contribution to the public result.


## design choices

### exactness

| member | what it selects |
| --- | --- |
| `exact` | the compare reconstructs enough positional information to order every pair. |
| `approximate_with_correction` | the compare works from an estimate and an exact correction, which the module header records. |

## references

jullien_1978 -> Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
shenoy_kumaresan_1989 -> Shenoy, Kumaresan, "Fast Base Extension Using a Redundant Modulus in RNS", IEEE Transactions on Computers, 1989
vu_1985 -> Vu, "Efficient Implementations of the Chinese Remainder Theorem for Sign Detection and Residue Decoding", IEEE Transactions on Computers, 1985
dimauro_1993 -> Dimauro, Impedovo, Pirlo, "A New Technique for Fast Number Comparison in the Residue Number System", IEEE Transactions on Computers, 1993
sousa_2015 -> Sousa, "2^n RNS Scalers for Extended 4-Moduli Sets", IEEE Transactions on Computers, 2015
posch_posch_1995 -> Posch, Posch, "Modulo Reduction in Residue Number Systems", IEEE Transactions on Parallel and Distributed Systems, 1995
samimi_2020 -> Samimi, Kamal, Afzali-Kusha, Pedram, "Res-DNN: A Residue Number System-Based DNN Accelerator Unit", IEEE Transactions on Circuits and Systems I, 2020
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
