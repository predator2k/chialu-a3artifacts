---
family: booth_recoded_parallel
pin: {sign_extension: prevention_constant}
---
# prevention_constant

Instead of extending each partial product's sign to the full product
width, the leading-one triangle that the complemented rows would
contribute is summed once into fixed constants, and conditional S
terms clear those constants for positive rows, so each row carries one
sign-handling bit. Signed multiplication sign-extends the multiplicand
before complementing it and controls the clearing with an
EXCLUSIVE-NOR of the multiplicand sign and the high-order selection
bit.

The summed construction is exactly equivalent to explicit
two's-complement leading-one strings, combining the top row's S term
with its two leading ones lowers the maximum column height by one, and
signed multiplication drops one partial product (bewick1994). Tree
designs adopt it to keep the array rectangular: the 54x54 regularly
structured tree multiplier corrects each row's sign in a Ph unit
without extending it through the 107th bit (goto1992), and a dual-mode
53x53 tree that holds two 24-bit partial-product sets in opposite
corners relies on it with a three-bit separation so that the two
products do not contaminate each other (chong_2009). A 60-bit folded array adds two extension bits to each
recoded row, which gives a 63-bit partial product, and adds the Booth
sign Pbs into that row (naini_2001). It is the pick
whenever the reduction is a tree with fixed columns; roorda_compact
goes further and removes the full adders whose inputs the extension
had fixed, which matters in an array.

## references

bewick1994 -> G. W. Bewick, "Fast Multiplication: Algorithms and Implementation", PhD dissertation, Stanford University, CSL-TR-94-617, 1994
goto1992 -> G. Goto, T. Sato, M. Nakajima, T. Sukemura, "A 54x54-b Regularly Structured Tree Multiplier", IEEE Journal of Solid-State Circuits, vol. 27, 1992
chong_2009 -> Y. J. Chong, S. Parameswaran, "Flexible Multi-Mode Embedded Floating-Point Unit for Field Programmable Gate Arrays", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2009
naini_2001 -> A. Naini, A. Dhablania, W. James, D. Das Sarma, "1-GHz HAL SPARC64 Dual Floating Point Unit with RAS Features", ARITH-15, 2001
