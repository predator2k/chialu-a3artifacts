# transformer_activation_lut

Transformer nonlinearities (GELU, exp, division, inverse square root)
evaluated by a small fixed datapath. Either the function is replaced
by a
low-degree integer polynomial (i-GELU substitutes a clipped odd
quadratic for erf and evaluates it with precomputed static scales in
integer arithmetic only), or by a learned piecewise-linear table
whose N - 1 breakpoints and N slope/intercept pairs are the weights
of a one-hidden-layer ReLU network trained against the target and
selected by a comparator, or the integer polynomial is serialized
most-significant-digit-first on online adders and multipliers so
dependent operations overlap after their online delays and a result
can exit early.

The method choice trades generality against latency. The integer
polynomial needs no floating point, keeps degree low to limit
overflow and cost, and stays within 0.018 of exact GELU on [-4, 4]
with downstream GLUE scores at or slightly above the FP32 model; it
costs one dedicated unit per function at three to five cycles. The
learned table runs every function on one comparator, lookup,
multiplier, and adder by swapping table contents, 16 entries being
enough in the evaluated models, in two cycles and at under half the
area and a small fraction of the power of the integer-polynomial
unit in 7 nm; its accuracy is only known through operation-wise L1
error and task metrics, and a short calibration on unlabeled
activations with the model frozen recovers most of the lost score.
Learned breakpoints matter most for softmax and layer-norm inputs
with a large dynamic range, and small inverse-square-root inputs
need a power-of-two prescale into the trained range. The serial
MSDF form runs the same integer polynomial at about a 3.6x shorter
clock period and roughly half the area of the parallel unit in 45 nm
but spends 30 cycles per result, so it fits edge accelerators where
latency is secondary.

Operand format and calibration follow the method: integer kernels
compute in int32 (or a dataset-narrowed 18 bits) and requantize to
int8, while learned tables have int32, fp16, and fp32 variants, and
the fit is either an analytic coefficient search or a training run.
The accuracy contract is statistical throughout, since no maximum-ulp
bound is reported for any variant. Execution is feed-forward for the
polynomial and table forms and digit-serial for the MSDF form.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/sfu.py`: one minimax quadratic over a clipped domain (integer_polynomial, the I-BERT line) or an 8-piece table placed by the calibration (learned_lut_pwl)). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family transformer_activation_lut --pins k=v,...` emits the module with its modeled error for a rewrite.

## design choices

### calibration

| member | what it selects |
| --- | --- |
| `analytic_minimax` | the breakpoints and coefficients come from a minimax fit of the function. |
| `learned_from_data` | they are learned from sampled activations. |

### operand_format

| member | what it selects |
| --- | --- |
| `int8` | eight-bit integer operands. |
| `int16` | sixteen-bit integer operands. |
| `fp16` | fp16 operands. |
| `bf16` | bf16 operands; the integer formats are realized on the mode's own format, which the module's header records. |

## references

kim_2021 -> S. Kim, A. Gholami, Z. Yao, M. W. Mahoney, K. Keutzer, "I-BERT: Integer-only BERT Quantization", International Conference on Machine Learning (ICML), PMLR 139, pp. 5506-5518, 2021
yu_2022 -> J. Yu, J. Park, S. Park, M. Kim, S. Lee, D. H. Lee, J. Choi, "NN-LUT: Neural Approximation of Non-Linear Operations for Efficient Transformer Inference", ACM/IEEE Design Automation Conference (DAC), pp. 577-582, 2022
taghavizade_2024 -> A. Taghavizade, D. Rahmati, S. Gorgin, J.-A. Lee, "GELU-MSDF: A Hardware Accelerator for Transformer's GELU Activation Function Using Most Significant Digit First Computation", IEEE International System-on-Chip Conference (SOCC), pp. 1-6, 2024
