---
family: posit_adder_multiplier
pin: {internal_representation: twos_complement}
---
# twos_complement

The representation the format itself prescribes: a negative posit is
the two's complement of its positive counterpart, so the decoder
two's-complements a negative input before the regime, exponent and
fraction are read, and the intermediate significand can likewise be
a two's-complement number, as in the posit intermediate format with
its NaR flag, biased exponent, round bit and sticky bit.

Two's complement is the pick when the operator is built as a
single-path adder on a signed intermediate, where subtraction needs
no separate magnitude comparison and the mutual exclusion of large
alignment and normalization shifts keeps widths down, and it is the
representation of the standard-following generators. It pays one
conversion at each decode and encode, which a sign-magnitude
datapath skips by carrying the sign separately; the PERCIVAL authors
note that newer two's-complement decoding may reduce their
sign-separated unit's cost, so the choice is open in either
direction.

The library realizes this variant as the decoder that reads the raw two's complement pattern without a negation stage (the scale of a negative posit is the bitwise complement of the raw scale, the significand the two's complement word {s, ~s, f}, negated narrow into the sign-magnitude X at the end) and as the encoder that negates the field word first with the sticky as its borrow, builds the regime of the complemented scale and rounds to nearest even in the two's complement domain, so no final negation exists (`internal_representation: twos_complement`). The decoder therefore follows the newer two's-complement decoding the PERCIVAL note refers to rather than the negate-then-decode order described above, which is the sign_magnitude realization.

## references

gustafson_2017 -> J. L. Gustafson, I. T. Yonemoto, "Beating Floating Point at its Own Game: Posit Arithmetic", Supercomputing Frontiers and Innovations, vol. 4, no. 2, pp. 71-86, 2017
chaurasiya_2018 -> R. Chaurasiya, J. Gustafson, R. Shrestha, et al., "Parameterized Posit Arithmetic Hardware Generator", IEEE International Conference on Computer Design (ICCD), 2018
uguen_2019 -> Y. Uguen, L. Forget, F. de Dinechin, "Evaluating the Hardware Cost of the Posit Number System", International Conference on Field Programmable Logic and Applications (FPL), 2019
mallasen_2022 -> D. Mallasén, R. Murillo, A. A. Del Barrio, G. Botella, L. Piñuel, M. Prieto-Matías, "PERCIVAL: Open-Source Posit RISC-V Core With Quire Capability", IEEE Transactions on Emerging Topics in Computing, 2022
