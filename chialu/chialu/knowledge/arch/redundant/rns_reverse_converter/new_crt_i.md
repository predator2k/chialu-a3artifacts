---
family: rns_reverse_converter
pin: {algorithm: new_crt_i}
---
# new_crt_i

The CRT rewritten with constants precomputed from the moduli alone, so
the final modulus shrinks; for {2^n-1, 2^n, 2^n+1} the conversion
reduces to additions of rearranged and complemented residue fields.
Converter I combines carry-save intermediates in one 2n-bit
one's-complement adder and concatenates the remaining residue field;
Converter II uses four parallel n-bit carry-lookahead adders with
carry-dependent selection; Converter III swaps two of them for
incrementers.

It is the pick for the three-moduli special set when the converter
must beat 2n-bit-adder CRT designs: Converter I needs about half their
hardware, Converter II is about twice as fast at similar hardware
because its selector adds no delay once the carries are available, and
Converter III is faster still at more hardware. All three are
memoryless and combinational. Algebraically the constants are the
mixed-radix representations of s_i |1/s_i|, so the method is the second
form of the CRT rather than a new algorithm, and the same rewriting
extends to four-moduli sets with wider dynamic range.

The library realizes this algorithm as x_1 + m_1 times the reduced sum of the k_i-weighted residue differences modulo m_2 ... m_k (`chialu/targets/rtl/families/redundant.py`).

## references

wang_2002 -> Wang, Song, Aboulhamid, Shen, "Adder Based Residue to Binary Number Converters for (2^n-1, 2^n, 2^n+1)", IEEE Transactions on Signal Processing, 2002
