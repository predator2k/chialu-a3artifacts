---
family: transformer_activation_lut
pin: {method: msdf_online_serial}
---
# msdf_online_serial

The I-BERT second-order integer polynomial is evaluated
most-significant-digit-first on online arithmetic: a binary-to-BSD
converter feeds absolute-value and sign detection, an MSDF
comparator, two serial multipliers, three serial adders and a
sign-controlled posibit/negabit mux. Each dependent operation starts
after its online delay, three cycles for a multiplier and two for an
adder, so the chain overlaps digit by digit and the serial result
lands in a register for parallel consumers.

Against the parallel integer_polynomial unit, the serial form shortens
the clock period about 3.6x (0.68 ns against 2.5 ns in 45 nm) and
needs roughly half the area, but spends 30 cycles per result, so
latency rises despite the faster clock, and power is comparable at
the fastest points. Dataset-derived narrowing lets most intermediates
run at 18 bits while the second addition keeps a 32-bit input, and no
error bound or task accuracy is reported for the narrowed hardware.
It is the pick for resource-constrained edge accelerators where
latency is secondary and a result can be consumed as its leading
digits emerge; learned_lut_pwl stays cheaper per function where a
two-cycle table is acceptable. Execution is digit-serial. In the ADIR
grammar it is `family: transformer_activation_lut` with
`pin: {method: msdf_online_serial}`.

This variant is digit-serial with early termination and stays behavioral (an exception, `sfu.SEQUENTIAL_SFU`).

## references

taghavizade_2024 -> A. Taghavizade, D. Rahmati, S. Gorgin, J.-A. Lee, "GELU-MSDF: A Hardware Accelerator for Transformer's GELU Activation Function Using Most Significant Digit First Computation", IEEE International System-on-Chip Conference (SOCC), pp. 1-6, 2024
kim_2021 -> S. Kim, A. Gholami, Z. Yao, M. W. Mahoney, K. Keutzer, "I-BERT: Integer-only BERT Quantization", International Conference on Machine Learning (ICML), PMLR 139, pp. 5506-5518, 2021
yu_2022 -> J. Yu, J. Park, S. Park, M. Kim, S. Lee, D. H. Lee, J. Choi, "NN-LUT: Neural Approximation of Non-Linear Operations for Efficient Transformer Inference", ACM/IEEE Design Automation Conference (DAC), pp. 577-582, 2022
