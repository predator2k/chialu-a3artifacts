# mixed_precision_cascade_fma

Fused multiply-add whose product operands are a narrow format and
whose addend and result are a wider one: the narrow product is exact
in the wide format (q >= 2p + 2), so it is added without intermediate
rounding to the wide addend and the result gets one wide-format
rounding. The datapath is anchored on the product; the addend is
shifted into a register of about 3q bits, a post-multiplier shifter
of up to 2p bits normalizes products of subnormal narrow operands,
and the adder and leading-zero logic size to about 2q + 6 and q + 3
bits, between a narrow and a wide homogeneous FMA. The dot-product
form adds two narrow products and one wide accumulator with one
normalization and rounding.

Preserving the exact product is what the family sells: no conversion
instructions, wide-accumulation accuracy for narrow products, and a
bit-identical match to the C99/IEEE mixed-precision accumulation. The
cost is an intermediate of q + 2p + 5 bits, which puts the unit at
about one third more area than the narrow-format FMA (MPFMA32 versus
FMA32, 28 nm) and well below the wide one; full normalization of
subnormal products is what widens the addition datapath, and a
subnormal wide addend needs nothing extra. Supporting the narrow FMA
and the wide addition on the same datapath costs only multiplexing and
exponent logic, so those auxiliary modes are nearly free. No exemplar
emits a two-term expansion: each returns one rounded wide result, so
exactness holds inside one operation and not across a sequence of
them.

Fusing two products with the accumulator beats two cascaded
mixed-precision FMAs by about 30 percent in area and critical path
(12 nm) and removes their double rounding and addition-order
sensitivity; packing four 8-to-16-bit or two 16-to-32-bit operations
into one wide interface doubles peak throughput over expanding FMAs,
and the FP8-to-FP16 accumulation error at 2000 terms falls from about
1.2e-2 for the cascade to 3.9e-3 for the fused unit. The family wins
for low-precision training and GEMM accumulation (16-to-32, 32-to-64,
64-to-128 bit pairings) and loses to the classic FMA when both formats
coincide. Execution is feed-forward and pipelined at initiation
interval one, with three to six stages in the exemplars.

A half-to-single implementation shows what the anchoring costs in
hardware. The half-precision product needs 22 bits and is padded to 32
on the right, and the single-precision accumulator is placed two bits
to the left of the carry-save product, so the accumulation cannot
overflow and the accumulator's alignment is a right shift alone,
through a 58-bit shifter. The low 32 bits of the aligned accumulator
join the carry-save product in one carry-propagate adder, the high
part is incremented, and the adder's carry-out selects between the two
before an anticipator and a leading-zero count give the normalization
shift. That unit runs three stages at a 3-cycle latency and one
operation per cycle, and in STM 90 nm at a 0.8 ns period it measures
42,710.90 um2 and 14.07 mW, which is 4.6 percent more area and 3.5
percent more power than a floating-point-only multiply-accumulate of
the same shape. Its critical path is in the first stage, where the
multiplier and the alignment shifter sit.

The seed instantiates the library's generated module for this family (`chialu/targets/rtl/families/dot.py`: the library's fp multiplier and a two-path fp adder generated for the exact product's width, so the narrow product enters the wider destination exactly (`exact_product_preserved`); otherwise the product is rounded to d first; the error-term output the `two_term_expansion_output` pins describe has no port on the dot unit). `python3 -m chialu.targets.rtl.families.dot --fab <format> --fc <format> --fd <format> --n <elements> --family <family> --pins k=v,...` emits it for a rewrite.

## design choices

### error_term_normalization

| member | what it selects |
| --- | --- |
| `dedicated` | the error term has a normalizer of its own. |
| `on_demand_copy` | the error term borrows the main normalizer. |

### error_term_ops

| member | what it selects |
| --- | --- |
| `addition` | the error term is kept for the addition alone. |
| `multiplication` | the error term is kept for the multiplication alone. |
| `both` | the error term is kept for both. |

## references

muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
brunie_2011 -> N. Brunie, F. de Dinechin, B. de Dinechin, "Mixed-Precision Fused Multiply and Add", 45th Asilomar Conference on Signals, Systems and Computers, 2011
brunie_2017 -> N. Brunie, "Modified Fused Multiply and Add for Exact Low Precision Product Accumulation", ARITH-24, pp. 106-113, 2017
bertaccini_2022 -> L. Bertaccini, G. Paulin, T. Fischer, S. Mach, L. Benini, "MiniFloat-NN and ExSdotp: An ISA Extension and a Modular Open Hardware Unit for Low-Precision Training on RISC-V Cores", ARITH, 2022
zhang_2018 -> H. Zhang, H. J. Lee, S.-B. Ko, "Efficient Fixed/Floating-Point Merged Mixed-Precision Multiply-Accumulate Unit for Deep Learning Processors", ISCAS 2018
