---
family: rns_forward_converter
pin: {implementation: periodic_csa_moma}
---
# periodic_csa_moma

The memoryless channel: the input bits are partitioned into weight
classes by 2^j mod A, whose period P(A) sets the column count,
full-adder carry-save stages reduce the columns with carries wrapping
end-around after q = min(P(A), m) positions, a cyclic adder reduces the
remaining bits, and a ROM or PLA maps the last P(A)+1 or fewer weighted
bits to the residue. A combinational tree is the high-speed form; one
CSA stage looped through a carry-save register is the cost-effective
form.

It is the pick for an arbitrary odd modulus and a wide word, where a
table converter's ROM grows exponentially with the chunk width and the
periodic tree grows with the bit count: a 32-bit generator mod 9 costs
25 full adders plus one half adder and 9 delta before a 128 x 4 ROM.
The same engine over k residue operands is the multioperand modular
adder of rns_channel_arithmetic, where 8 operands mod 25 take 32 full
adders and 2 half adders at 7 delta plus the ROM in tree form, or 7
full adders and a 14-bit carry-save register at 11 delta plus the ROM
in register form. The tree pipelines like any carry-save reduction; the
register form trades delay for cells. Against rom_per_chunk it spends
adders for the tables it removes, and against channel_modular_mac it
needs no multiplier.

The library realizes this implementation as the folding of the word into n-bit slices summed with the end-around carry (or with alternating signs for 2^n + 1) and one final modular reduction (`chialu/targets/rtl/families/redundant.py`).

## references

piestrak_1994 -> S. J. Piestrak, "Design of Residue Generators and Multioperand Modular Adders Using Carry-Save Adders", IEEE Transactions on Computers, vol. 43, no. 1, pp. 68-77, 1994
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
