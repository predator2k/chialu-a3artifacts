# end_around_carry: proposed changes to the space

* `recirculation` value for direct feedback into a ripple or carry-skip chain (concurrent parallel feedback, automatic end-around carry, cyclic carry-skip distributions with one or two skip layers) — the pre-prefix machines and the carry-skip optimization return the carry through the ordinary chain without a prefix level [richards_1955, bloch_1959, majerski1967]
* `recirculation` value `serial_second_pass` — bit-serial ones'-complement adders re-transmit the carry in another pass through the adder [richards_1955, thornton_1970]
* `recirculation` value `carry_increment_stage` (late-increment feedback) — the flagged prefix adder and PPFCI feed the carry-out or its complement into a separate increment row rather than a cyclic prefix level [burgess2002, efstathiou2004]
* `recirculation` value for carry-lookahead equations that absorb the complemented carry-out at bit or group level — the CLA form of the diminished-one adder recirculates inside one- or two-level lookahead equations [vergos2002]
* `modulus` value `mod_2n_plus_1_normal` — modulo 2^n+1 with normal-binary operands avoids diminished-one converters and special zero handling [zimmermann1999, efstathiou2004]
* `modulus` value or separate choice for floating-point subtraction and sign correction — the ones'-complement floating-point adders use end-around carry for magnitude subtraction rather than for a numeric modulus [anderson1967, hokenek_1990, bloch_1959]
* choice `zero_representation: {single, double, diminished_one, normal_2n_as_zero}` plus a zero-output detection option — the modulo 2^n-1 zero encoding and the false zero of the diminished-one form are design decisions the space does not record [zimmermann1997, zimmermann1999, efstathiou2004, vergos2002]
* `topology` value for algorithm-generated cyclic trees defined by per-row valencies and a repeated-chain stride — the generator's structure is not one of the named topologies [beaumont_smith2001]
* choice `group_partition` — the POWER6 adder wraps four 32-bit group carries rather than the whole word [yu_2006]
* `recirculation` value for a one-pass correction with no closed loop — the incrementer's propagate and the lookahead adder's group identifier are fed back to the carry-in instead of the carry-out being re-propagated [jessani_1996]
