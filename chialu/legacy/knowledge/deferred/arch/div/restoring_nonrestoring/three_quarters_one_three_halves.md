---
family: restoring_nonrestoring
pin: {divisor_multiple_set: three_quarters_one_three_halves}
---
# three_quarters_one_three_halves

The multiple set {3/4 D, D, 3/2 D} of a normalized divisor for a
divider that shifts over quotient runs: after each subtraction or
addition the leading equal bits of the partial remainder are decoded,
the remainder shifts across the run of quotient ones or zeros, and the
multiple nearest the remainder is selected so the next run is as long
as possible. Stretch produced 48 quotient bits in thirteen cycles this
way, about 3.7 bits per subtraction.

It is the pick when the average shift per cycle is worth two extra
multiple generators and a selection decode: MacSorley's comparison
gives 3.57 bits per cycle for this set with optimum selection against
2.74 for {1/2 D, D, 2 D} with coded selection and 2.54 for the plain
divisor with a five-bit decode, and the double-adder selection reaches
3.51 with the same multiples. The set needs the divisor normalized,
and a shifter limit of 4 pulls the best methods back to about 3.08
bits per shift cycle from 3.82 unlimited. The plain divisor is the
sibling when the multiple generators and the decode are not
affordable, and {1/2 D, D, 2 D} when the multiples must stay shifts.

## references

bloch_1959 -> E. Bloch, "The Engineering Design of the Stretch Computer", Proc. Eastern Joint Computer Conference, pp. 48-58, 1959.
macsorley1961 -> O. L. MacSorley, "High-Speed Arithmetic in Binary Computers", Proceedings of the IRE, vol. 49, no. 1, pp. 67-91, 1961
