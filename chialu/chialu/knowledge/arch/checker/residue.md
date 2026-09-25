# residue

Concurrent error detection by modular arithmetic: the checker computes
the operation in a tiny ring (mod 2^k - 1; k=2..4 in practice, IBM
ships mod 15) from residues of the operands, and compares against the
residue of the main result. Addition and multiplication commute with
the residue map, so one k-bit datapath checks a w-bit one — area
overhead of a few percent, single-bit output-error coverage 1.0, and
alias probability ~1/(2^k - 1) for random corruption.

The family is the shipping default for multiply/FMA protection
(parity does not commute through a multiplier). Its limits define its
neighbors: it assumes the EXACT arithmetic relation, so approximate
cores need duplication or reduced-precision replicas instead; logic
and shift operations need parity prediction; and coverage of errors
that alias to a multiple of the modulus is bought with multi-residue
or a wider k.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family: the residues of the operands and of the result mod M by k-bit folding, the prediction with the wrap recovered from the patterns, one compare per lane through the comparator slot (`checker.comparator.family`).

## design choices

### generator_style

| member | what it selects |
| --- | --- |
| `csa_tree` | the chunks are summed in a carry-save tree closed by an end-around-carry adder. |
| `modular_ripple` | the chunks are summed by a chain of end-around-carry adders. |
| `lut` | a table over the chunk pairs, which the generator builds where the index fits in 12 bits. |

## references

garner_1966 -> H. L. Garner, "Error Codes for Arithmetic Operations", IEEE Trans. Electronic Computers, 1966
piestrak_1994 -> S. J. Piestrak, "Design of Residue Generators and Multioperand Modular Adders Using Carry-Save Adders", IEEE Trans. Computers, 1994
lipetz_schwarz_2011 -> D. Lipetz, E. Schwarz, "Self Checking in Current Floating-Point Units", ARITH-20, 2011
