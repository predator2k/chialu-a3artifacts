---
family: generalized_signed_digit
pin: {final_conversion: cpa}
---
# cpa

One carry-propagate addition at the end: the signed-digit result is
the difference of its positive and negative bit vectors, so a
carry-lookahead adder converts it to two's complement in time
proportional to log n. In the fabricated 16-bit redundant-binary
multiplier the conversion adds 8 gates to an 18-gate tree path. A
sign-select form converts blocks under both sign assumptions in
parallel and lets the most-significant nonzero block pick the
result, at 8 to 13 gate delays from 8 to 64 bits.

It is the pick when the result leaves the redundant domain once,
after a multiplier tree or a long sequence of redundant operations,
and when a conventional remainder value is needed, which on-the-fly
conversion cannot supply. The sign-select converter is 14 to 30%
faster than lookahead or carry-select adders above 32 bits for about
50% more transistors than binary lookahead. It loses to on_the_fly
when the digits arrive most-significant-first over time, where the
conditional-form registers absorb each digit with no propagation at
all.

The library's signed-digit adder realizes this conversion as P - N over the positive and negative digit words through the lane's adder family (`chialu/targets/rtl/families/redundant.py`).

## references

takagi_1985 -> Takagi, Yasuura, Yajima, "High-Speed VLSI Multiplication Algorithm with a Redundant Binary Addition Tree", IEEE Transactions on Computers, 1985
harata_1987 -> Harata, Nakamura, Nagase, Takigawa, Takagi, "A High-Speed Multiplier Using a Redundant Binary Adder Tree", IEEE Journal of Solid-State Circuits, 1987
kuninobu_1987 -> Kuninobu, Nishiyama, Edamatsu, Taniguchi, Takagi, "Design of High Speed MOS Multiplier and Divider Using Redundant Binary Representation", 8th IEEE Symposium on Computer Arithmetic, 1987
srinivas_parhi_1992 -> Srinivas, Parhi, "A Fast VLSI Adder Architecture", IEEE Journal of Solid-State Circuits, 1992
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
