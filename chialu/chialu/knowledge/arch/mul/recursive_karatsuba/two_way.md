---
family: recursive_karatsuba
pin: {split_kind: two_way}
---
# two_way

The Karatsuba-Ofman split: multiplication becomes addition and
squaring through ab = [(a+b)^2 - (a-b)^2]/4, a 2m-digit squaring
reduces to three m-digit squarings plus additions and
multiplications by powers of two, and recursive application gives
m^(log2 3) digit operations at log m depth. In the FPGA form the two
halves give P00, P11 and the subtractive cross term (X0-X1)(Y0-Y1),
so a 34x34 product takes 3 DSPs instead of 4.

Two-way splitting is the pick when one saved multiplier is worth a
pre-subtraction of about 6k LUTs and the operands split into equal
signed halves that fill the embedded multiplier: the 34x34 design
runs at 317 MHz in 3 cycles on Virtex-4, and two levels of recursion
give 51x51 with 6 DSPs against 9. Deeper recursion shrinks the
chunks and lengthens the critical path, so the direct three- and
four-part forms are the siblings for wider products, and the
rectangular split is the sibling when the DSP tile is not square.

## references

karatsuba1962 -> A. Karatsuba, Yu. Ofman, "Multiplication of Multidigit Numbers on Automata", Doklady Akademii Nauk SSSR, vol. 145, no. 2, pp. 293-294, 1962 (Engl. transl. Soviet Physics-Doklady, vol. 7, pp. 595-596, 1963)
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
