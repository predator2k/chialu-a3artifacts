---
family: range_reduction
pin: {reduction_type: additive}
---
# additive

The reduced argument is x* = x - kC for an integer k and a constant C
such as pi/2, pi/4, ln 2 or log 2/32, chosen so that x* falls in a
bounded interval around zero and the function of x follows from the
function of x* and k, often from k mod 4 alone for C = pi/2. Every
additive method is a way of forming x - kC without losing the bits
that cancel: split constants, a windowed product with a multiple of
1/C, or stored residues of the powers of two modulo C.

Its difficulty is cancellation near a multiple of C: naive
machine-precision subtraction can lose almost all accuracy, and the
worst case, found by continued fractions, sets the guard precision at
about 28 to 32 extra bits for binary32 constants and 61 to 67 for
binary64, with the smallest binary64 reduced argument for C = pi/2 at
2^-60.89, so the reduced argument generally needs a wider format or
several machine numbers. The additive methods are the cody_waite,
payne_hanek, modular_mrr and table_augmented values of method, ordered
by argument range; the multiplicative sibling is the pick instead when
C can be a power of the radix, which makes the reduction exact and
free. Additive reduction is the form of the trigonometric and
exponential libraries in the notes and of the modular hardware
reducer.

The library's module for range_reduction realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
daumas_1995 -> M. Daumas, C. Mazenc, X. Merrheim, J.-M. Muller, "Modular Range Reduction: A New Algorithm for Fast and Accurate Computation of the Elementary Functions", Journal of Universal Computer Science, vol. 1, no. 3, pp. 162-175, 1995
tang_1989 -> P. T. P. Tang, "Table-Driven Implementation of the Exponential Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 15, no. 2, pp. 144-157, 1989
markstein_1990 -> Markstein, "Computation of Elementary Functions on the IBM RISC System/6000 Processor", IBM Journal of Research and Development, 1990
