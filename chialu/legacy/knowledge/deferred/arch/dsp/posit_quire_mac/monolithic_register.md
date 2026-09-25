---
family: posit_quire_mac
pin: {organization: monolithic_register}
---
# monolithic_register

One wide two's-complement register and one wide adder: every exact
product is shifted by its scale factor into the full quire width and
added in a single carry-propagate operation, so the register always
holds the resolved sum and a read needs no pending-carry resolution
before the leading-zero count, shift and rounding that produce the
posit. PERCIVAL keeps one internal 512-bit quire of this kind for
posit32; the Deep Positron accumulator sizes its quire from n, es and
the product count k.

It is the pick when the accumulation sequence is short, the read must
be immediate, or the width is small enough for the wide adder to meet
timing: a 512-bit unsegmented adder runs at 8.85 ns on a Kintex-7
against a 3 ns target, so segmented_carry_save takes over at high
frequency by delaying carries into 32- or 64-bit segments and paying
one final carry propagation before conversion. The monolithic register
also fixes the software model: PERCIVAL's quire cannot be loaded or
stored, so independent accumulations cannot interleave and a context
switch cannot save it without a lossy posit conversion. Its latency is
two cycles per multiply-add and one for the rounding read, and the
quire is about half the posit unit's area.

The quire family has no library module (an accumulator register across operations in a unit without an accumulate op), so this variant stays behavioral in a seed that declares it (`posit.EXCEPTIONS`).

## references

mallasen_2022 -> D. Mallasén, R. Murillo, A. A. Del Barrio, G. Botella, L. Piñuel, M. Prieto-Matías, "PERCIVAL: Open-Source Posit RISC-V Core With Quire Capability", IEEE Transactions on Emerging Topics in Computing, 2022
carmichael_2019 -> Z. Carmichael, H. F. Langroudi, C. Khazanov, J. Lillie, J. L. Gustafson, D. Kudithipudi, "Deep Positron: A Deep Neural Network Using the Posit Number System", Design, Automation and Test in Europe (DATE), 2019
uguen_2019 -> Y. Uguen, L. Forget, F. de Dinechin, "Evaluating the Hardware Cost of the Posit Number System", International Conference on Field Programmable Logic and Applications (FPL), 2019
