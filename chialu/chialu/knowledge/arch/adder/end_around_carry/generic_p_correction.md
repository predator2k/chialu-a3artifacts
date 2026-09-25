---
family: end_around_carry
pin: {modulus: generic_p_correction}
---
# generic_p_correction

Modulo-p addition for an arbitrary modulus p below 2^L: a conventional
L-bit two's-complement adder forms the sum, logic detects a forbidden
output state or an overflow, and the fixed constant C_L = 2^L - p is
added when either is detected. The paper calls the correction a
generalized end-around carry and hard-wires it with the adder, so the
re-entered carry bit of the sibling moduli becomes a re-entered
constant.

The native generator accepts every W-bit operand, including values above
p. Its selected prefix adder first computes the complete W+1-bit sum and
binary carry. A descending ladder subtracts aligned multiples of p through
the same prefix topology, retaining a difference only when its carry-out
proves it nonnegative. The result is `s=(a+b+cin)%p`; `cout` is the original
binary carry. A single correction is sufficient only for canonical inputs
and is therefore not the full native interface contract.

Explicit `modulus_value` spans 3 through 4095 and must also be below 2^W.
Recirculation and incrementer selections are inactive for this modulus
and fail if explicitly bound. The full Range regression uses W=12 so no
value is clipped: 4093 moduli, 709641 vectors, and actual reduction-stage
activity checks. A separate joint-instantiation regression covers the six
parameter pairs that collided under the old short module-name hash.

This modulus is the pick for residue channels whose moduli are not of
the 2^n±1 form, such as the {16, 13, 11, 9, 7} set of the paper's FIR
filter, and it is the member that rns_channel_arithmetic with
modulus_form=generic and rns_forward_converter with
modulus_class=generic place in their modular_adder slot. Against
mod_2n_minus_1 and mod_2n_plus_1_diminished_one it pays detection
logic and a constant addition in place of one re-entered carry bit,
and the paper gives no gate count or delay for it, so the sibling
moduli stay the pick wherever the moduli set can be chosen to fit
them.

## references

jenkins_leon_1977 -> Jenkins, Leon, "The Use of Residue Number Systems in the Design of Finite Impulse Response Digital Filters", IEEE Transactions on Circuits and Systems, 1977
