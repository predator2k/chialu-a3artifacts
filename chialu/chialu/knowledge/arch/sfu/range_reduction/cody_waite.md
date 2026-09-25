---
family: range_reduction
pin: {method: cody_waite}
---
# cody_waite

The constant C is split into two or three floating-point terms, the
first with enough trailing zeros that k C1 is exact for every k in
the covered range, and the reduced argument is (x - k C1) - k C2, with
a third term for a wider range; subtracting the terms separately
avoids the accuracy loss of a combined constant. Single precision uses
C1 = 201/64 and C2 = 9.67653589793e-4 for C = pi; double precision
uses C1 = 3217/1024 and C2 = -8.908910206761537356617e-6.

It is the cheapest reduction and it is restricted to small arguments
when last-bit accuracy is required for every input: k must stay small
enough for k C1 to remain exact, which for binary64 and C = pi/256
holds below |x| = 6433 with two terms and up to 13176794 with three.
Tang's exponential rounds X times 32/log 2 to N, splits log 2/32 into
L1 + L2, and keeps the reduced argument as R1 + R2 with error at most
2^-34 in fp32 and 2^-77 in fp64; Itanium's sine and cosine use a
two-term pi/16 constant so that x - N P1 is exact, and the Bfloat16
logarithm library uses a modified form. Beyond its range the
payne_hanek sibling takes over, and the table_augmented sibling covers
the arguments of reasonable size between the two.

The library's module for range_reduction realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
tang_1989 -> P. T. P. Tang, "Table-Driven Implementation of the Exponential Function in IEEE Floating-Point Arithmetic", ACM Transactions on Mathematical Software, vol. 15, no. 2, pp. 144-157, 1989
lim_2021 -> J. P. Lim, M. Aanjaneya, J. Gustafson, S. Nagarakatte, "An Approach to Generate Correctly Rounded Math Libraries for New Floating Point Variants", Proceedings of the ACM on Programming Languages, vol. 5 (POPL), pp. 1-30, 2021
