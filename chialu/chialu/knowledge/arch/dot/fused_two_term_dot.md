# fused_two_term_dot

One rounding for a*b + c*d: two multiplier trees form both products
in carry-save form, an exponent comparison aligns the smaller product
to the larger, a 4:2 reduction tree merges the four vectors, and the
FMA tail from the carry-save adder onward, which is the
carry-propagate adder, leading-zero handling, normalization and
rounding, finishes the sum once. The unit is a conventional FP
multiplier or FMA plus a second tree, an aligner and a reduction tree,
and carries one rounding error where two discrete multipliers and an
adder carry three. The Fused AS sibling computes A+B and A-B in
parallel and shares exponent difference, swap and alignment.

The second-op choice sets what the shared tail serves: the dot form
alone, the add/subtract pair alone, or both as the primitives of an
FFT butterfly, where the dot form also selects AB+CD or AB-CD.
Against a conventional parallel dot product in a 45 nm fp32
implementation the fused unit is about 70% of the area and 27% faster,
at 150% of a multiplier's time; the fused add/subtract pair saves
about 22% of cell area against two adders but is about 5% slower,
because subtraction needs a two's complement and the fused circuit
carries heavier loading. The alignment slot can bound the shift and
keep only 26 bits of the smaller significand with round and sticky
formed during alignment, which shrinks the adder; a dual-path adder,
the leading-zero anticipator, the final adder, the rounding scheme
and the multiplier trees are the same slots the FMA exposes.

The accuracy contract is one rounding of the fused sum rather than a
correctly rounded dot product for all inputs: the wide-accumulator
form sorts the two products and the 2w-bit addend by magnitude, adds
them at increasing internal widths, and restores the smallest addend
when an exact-zero detector sees cancellation, which beats sequential
FMAs on relative error but is not claimed correct for every input.
Fused radix-2 and radix-4 butterflies cut worst-case output error from
2 to 1 LSB and from 2.5 to 1.5 LSB.

The family wins in throughput-oriented DSP and low-precision training,
where FP8-to-FP16 and FP16-to-FP32 dot products cut GEMM cycles by up
to 10% against FP16 FMAs in 12 nm FinFET. It loses when addition-only
or multiplication-only use is frequent, since the bypass multiplexers
add one or two multiplexer delays, and when two FMAs with two
roundings are acceptable and already present.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: for a two-element mode, a*b + c*d (+ c) aligned to the largest exponent in one window, or, under `dual_path_add`, through a two-node tree whose node aligns its inputs to the larger exponent; the add_subtract_pair second op needs a sign control the unit has no port for). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## references

saleh_2008 -> H. H. Saleh, E. E. Swartzlander, "A Floating-Point Fused Dot-Product Unit", IEEE ICCD, 2008
swartzlander_2012 -> E. E. Swartzlander, H. H. Saleh, "FFT Implementation with Fused Floating-Point Operations", IEEE Transactions on Computers, vol. 61, no. 2, pp. 284-288, 2012
bertaccini_2022 -> L. Bertaccini, G. Paulin, T. Fischer, S. Mach, L. Benini, "MiniFloat-NN and ExSdotp: An ISA Extension and a Modular Open Hardware Unit for Low-Precision Training on RISC-V Cores", ARITH, 2022
