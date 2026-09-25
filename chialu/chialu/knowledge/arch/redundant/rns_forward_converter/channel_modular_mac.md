---
family: rns_forward_converter
pin: {implementation: channel_modular_mac}
---
# channel_modular_mac

Conversion on the channel multiplier-accumulators of a Cox-Rower
datapath: a radix-2^r operand x = (x(n-1), ..., x(0)) yields x mod m_i
as the sum over j of x(j) times the precomputed constant 2^rj mod m_i,
computed independently in every residue channel, so the n Rower units
finish in n steps with no table and no tree.

It is the pick when the datapath already holds a modular
multiplier-accumulator per channel, as the RNS Montgomery multiplier of
rns_montgomery_crypto does, because the conversion adds constants
rather than hardware; the cost is n^2 modular multiplications per
conversion and a latency of n steps, against one lookup cycle for a
table and a carry-save tree depth for the periodic form. chunk_bits is
the radix digit width r and moduli_count the number of Rowers. The same
reuse in the reverse direction is the Cox-Rower conversion that
rns_reverse_converter absorbs. Execution is n sequential steps rather
than feed-forward.

The library realizes this implementation as the unrolled Horner chain over the word's chunks, each step a modular multiply-add reduced by the channel's tables (`chialu/targets/rtl/families/redundant.py`).

## references

kawamura_2000 -> Kawamura, Koike, Sano, Shimbo, "Cox-Rower Architecture for Fast Parallel Montgomery Multiplication", EUROCRYPT (LNCS 1807), 2000
