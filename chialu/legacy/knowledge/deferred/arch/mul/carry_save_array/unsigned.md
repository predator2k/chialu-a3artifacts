---
family: carry_save_array
pin: {signed_scheme: unsigned}
---
# unsigned

The plain array: the multiplicand is gated by every multiplier bit to
form all partial products at once, and rows of full adders in carry-save
form sum them, each row passing its sum vertically and its carry
diagonally to the next, until a final carry-propagate row forms the
product. No sign handling exists anywhere in the array, so every cell is
an AND gate plus a full adder and the product is the sum of n positive
partial products, n + m bits wide for n by m operands.

Unsigned is the pick when operands are magnitudes or when the array is a
component of a wider structure that handles sign elsewhere: the uniform
cell is what makes bit-level pipelining regular, as in the 8 by 8 array
with registered full-adder rows and a registered half-adder final row
that runs at 70 MHz in 2.5 um CMOS, 16 stages deep, at about 4.4 times
the unpipelined area. The array is the fastest structure of its era at
the cost of a large amount of hardware, and a conservative delay bound
follows the longest conceivable signal path. Signed two's-complement
operands are added later with the Baugh-Wooley reorganization, which
keeps the array and changes only a few inversions and constant bits, and
the Pezaris form, which treats the sign bits as negative weights.

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
hatamian1986 -> M. Hatamian, G. L. Cash, "A 70-MHz 8-bit x 8-bit Parallel Pipelined Multiplier in 2.5-um CMOS", IEEE Journal of Solid-State Circuits, vol. SC-21, no. 4, pp. 505-513, 1986
bewick1994 -> G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
