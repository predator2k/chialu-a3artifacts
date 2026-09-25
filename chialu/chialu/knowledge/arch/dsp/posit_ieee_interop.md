# posit_ieee_interop

Interoperation between posit and IEEE-754 operands, either through
converters at the memory or instruction boundary or through one
datapath that decodes both formats. A boundary converter extracts sign,
exponent, regime, and mantissa from the source word, prenormalizes IEEE
subnormals, derives the regime and exponent from the unbiased IEEE
exponent, or removes the variable-length regime with a leading-one
detector and a dynamic shift, and repacks the fields. A unified
datapath decodes each operand into shared sign, scale-factor, and
fraction vectors, runs one arithmetic core, and encodes the result into
the configured format. A quire adds an exact wide accumulator on the
posit side.

The interop style trades hardware against what can run at once.
Boundary converters are the cheapest: posit8 and posit16 map exactly
into fp32 and posit32 into fp64, so posits keep their memory density
while established IEEE arithmetic and libraries do the computing, and
a converter is well below the operator it wraps, about 90 LUTs and 6
cycles for posit16-to-fp32 against 367 LUTs and 12 cycles for an fp32
add on a Kintex-7, amortized over a whole pipeline. Exact input
conversion still does not guarantee standard posit results, because
converting back after IEEE computation can double-round; IEEE
subnormals become the smallest posit, posits never decode as
subnormals, and NaN detection is dropped when the posit format has
none. A unified dual-format datapath selects the format of every
operand and of the result independently and takes the posit exponent
size at runtime, so mixed-format operations and conversions run on one
core at the cost of per-format decode, encode, and exception stages.
Replacing the float ISA keeps the RISC-V F encodings and register
state and needs the fewest compiler changes but excludes simultaneous
IEEE use; coexistence through a separate posit accelerator with its own
register file, or through separate parallel datapaths with their own
register file, scoreboard, and issue paths, restores simultaneous
support at extra decode and interconnect cost, which raised a CVA6 core
from about 29 k to about 45 k LUTs on a Kintex-7 once a quire-equipped
posit unit was added.

Bidirectional conversion with round-to-nearest-even lets a posit or
quire kernel sit between fp32 phases of a legacy application, but
per-iteration conversions that are not pipelined can exceed the posit
compute cycles. The quire gives the posit
side exact accumulation; the replacement proposal makes bitwise
identical results depend on mandated correct rounding and no covert
extra precision.

The family is feed-forward. Converters win when the surrounding
application stays IEEE and only selected kernels want posit range or
the quire; the unified datapath wins for transprecision vector MAC
units that must mix formats; the ISA replacement wins only when IEEE
compatibility can be given up.

The seed instantiates the library's decoder and encoder of the posit mode for this family (`chialu/targets/rtl/families/posit.py`); under `interop_style: boundary_converters` it adds one dedicated converter module per lane and target in the directions `conversion_direction` names (a decoded posit value into a float target through the float rounder datapath, into a posit target through the posit encoder, and a float lane's decoded value into the posit format through the posit encoder), while the unified datapath and the ISA replacement leave the conversions on the lane's shared X datapath and pack functions. `python3 -m chialu.targets.rtl.families.posit --format posit16_1 --kind cvt --target fp16` emits a converter for a rewrite.

## design choices

### conversion_direction

| member | what it selects |
| --- | --- |
| `posit_to_ieee` | converters from the posit lane into a float target alone. |
| `ieee_to_posit` | converters from a float lane into a posit target alone. |
| `bidirectional` | a converter in each direction, which is what a unit mixing posit and float modes needs. |

### internal_representation

| member | what it selects |
| --- | --- |
| `sign_magnitude` | a negative pattern is two's-complemented at the decoder and the sign is carried beside the magnitude. |
| `twos_complement` | the body stays in two's complement, so the encoder negates the field word and rounds in that domain rather than at the end. |

### regime_decode

| member | what it selects |
| --- | --- |
| `lzc_plus_shifter` | the run length from a leading-zero count of the body xored with its first bit, and the fields from a shift past the run. |
| `two_stage_masked_decode` | a prefix-or thermometer of that xored body and a one-hot terminator, whose and-or matrix selects the fields without a shifter. |

## references

dedinechin_2019b -> F. de Dinechin, L. Forget, J.-M. Muller, Y. Uguen, "Posits: The Good, the Bad and the Ugly", Conference for Next Generation Arithmetic (CoNGA), 2019
jaiswal_2018 -> M. K. Jaiswal, H. K.-H. So, "Universal Number Posit Arithmetic Generator on FPGA", Design, Automation and Test in Europe (DATE), 2018
crespo_2022 -> L. Crespo, P. Tomás, N. Roma, N. Neves, "Unified Posit/IEEE-754 Vector MAC Unit for Transprecision Computing", IEEE Transactions on Circuits and Systems II: Express Briefs, 2022
tiwari_2021 -> S. Tiwari, N. Gala, C. Rebeiro, V. Kamakoti, "PERI: A Configurable Posit Enabled RISC-V Core", ACM Transactions on Architecture and Code Optimization, 2021
mallasen_2022 -> D. Mallasén, R. Murillo, A. A. Del Barrio, G. Botella, L. Piñuel, M. Prieto-Matías, "PERCIVAL: Open-Source Posit RISC-V Core With Quire Capability", IEEE Transactions on Emerging Topics in Computing, 2022
sharma_2023 -> N. Sharma, R. Jain, M. Pokkuluri, S. Patkar, R. Leupers, R. S. Nikhil, "CLARINET: A Quire-Enabled RISC-V-Based Framework for Posit Arithmetic Empiricism", Journal of Systems Architecture, 2023
gustafson_2017 -> J. L. Gustafson, I. T. Yonemoto, "Beating Floating Point at its Own Game: Posit Arithmetic", Supercomputing Frontiers and Innovations, vol. 4, no. 2, pp. 71-86, 2017
