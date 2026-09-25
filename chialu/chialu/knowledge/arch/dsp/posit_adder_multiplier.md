# posit_adder_multiplier

Add and multiply on posit<n,es> operands, each carrying a sign, a
variable-length regime run, up to es exponent bits and the remaining
fraction bits, so precision tapers with magnitude. A decoder
two's-complements a negative input or separates its sign, counts the
regime run with a leading-digit counter, shifts it out,
and extracts exponent and fraction into a fixed-field intermediate
with scale useed^k times 2^e and significand 1.f. The adder aligns
the smaller significand by the scale difference, adds or subtracts,
normalizes with a leading-one detector and recomputes the regime; the
multiplier adds the scales and multiplies the significands. An
encoder rounds once, to nearest even.

The es choice moves cost between the two operators: the adder's
components depend mainly on n, so its resources barely change with
es, while the multiplier's fraction narrows as es grows, which cuts
its logic and, on an FPGA, its DSP count. The regime decode choice
sets the decoder's latency, since the regime length must be known
before the exponent and fraction can be placed, and an integrated
leading-zero-or-one counter with shifter handles both regime
polarities in one component; the internal representation decides
whether negative operands are two's-complemented before decoding or
carried as sign and magnitude, which skips the conversion. The
logarithmic approximation replaces the fraction multiplier by an
addition of fractions, removing the fixed-point multiplier for a
maximum relative error of 11.1 percent that is independent of the
exponent, and cuts area by 69 to 73 percent against the exact posit
multiplier in TSMC 45 nm while keeping inference accuracy within
about half a percent of exact posit<16,1>.

Against IEEE at equal width the honest comparisons put posit
operators at comparable area and latency for similar effort, with
the multiplier paying for a slightly wider internal significand and
both paying for field extraction and packing that fixed-field
formats omit: a pipelined 32-bit posit adder takes 738 LUTs and 22
cycles against 425 LUTs and 14 cycles for IEEE on a Kintex-7, and a
posit<32,2> unit without quire is 1.32x the area and 1.38x the power
of an fp32 FPU in TSMC 45 nm. The family wins where the tapered
precision buys accuracy, as in 8-bit and 16-bit training and
inference, and where a single rounding at encode simplifies the
core; a single-path adder that exploits the mutual exclusion of large
alignment and normalization shifts keeps the intermediate widths
down. The sig_datapath slot is the adder inside the aligned
significand addition; the significand multiplier is a separate
integer multiplier whose regions can be gated by the regime.

The seed instantiates the library's generated posit unit for this family (`chialu/targets/rtl/families/posit.py`): the decoder (`regime_decode`: the run from a leading-zero counter over the body xored with its first bit and a shifter, or the two-stage masked decode's prefix-or thermometer, one-hot terminator and and-or field matrix; `internal_representation`: the pattern negated first with the sign carried separately, or the raw two's complement pattern decoded with the complemented scale and the significand negated narrow at the end), the encoder in the matching rounding domain, the unit's adder on X through the float library's single-path adder with the `sig_datapath` slot's significand adder, its exact multiplier, and under `operator_set: add_mul_div` its divider and square root from the `sig_div` slot; `approximation: logarithmic_fraction` is the PLAM module, which the seed uses only under an approximate contract. `python3 -m chialu.targets.rtl.families.posit --format posit16_1 --kind unit --pins k=v,...` emits it for a rewrite.

## design choices

### approximation

| member | what it selects |
| --- | --- |
| `none` | the fraction multiply is exact. |
| `logarithmic_fraction` | the PLAM form: the fraction multiply is a Mitchell add of the fractions, which the seed takes only under an approximate accuracy contract. |

### operator_set

| member | what it selects |
| --- | --- |
| `add_mul` | the unit's X adder and multiplier alone. |
| `add_mul_div` | the divider and the square root as well, through the significand division slot. |

### regime_decode

| member | what it selects |
| --- | --- |
| `lzc_plus_shifter` | the run length from a leading-zero count of the body xored with its first bit, and the fields from a shift past the run. |
| `two_stage_masked_decode` | a prefix-or thermometer of that xored body and a one-hot terminator, whose and-or matrix selects the fields without a shifter. |

## references

gustafson_2017 -> J. L. Gustafson, I. T. Yonemoto, "Beating Floating Point at its Own Game: Posit Arithmetic", Supercomputing Frontiers and Innovations, vol. 4, no. 2, pp. 71-86, 2017
chaurasiya_2018 -> R. Chaurasiya, J. Gustafson, R. Shrestha, et al., "Parameterized Posit Arithmetic Hardware Generator", IEEE International Conference on Computer Design (ICCD), 2018
jaiswal_2019 -> M. K. Jaiswal, H. K.-H. So, "PACoGen: A Hardware Posit Arithmetic Core Generator", IEEE Access, 2019
murillo_2020 -> R. Murillo, A. A. Del Barrio, G. Botella, "Customized Posit Adders and Multipliers Using the FloPoCo Core Generator", IEEE International Symposium on Circuits and Systems (ISCAS), 2020
uguen_2019 -> Y. Uguen, L. Forget, F. de Dinechin, "Evaluating the Hardware Cost of the Posit Number System", International Conference on Field Programmable Logic and Applications (FPL), 2019
dedinechin_2019b -> F. de Dinechin, L. Forget, J.-M. Muller, Y. Uguen, "Posits: The Good, the Bad and the Ugly", Conference for Next Generation Arithmetic (CoNGA), 2019
murillo_2022 -> R. Murillo, A. A. Del Barrio, G. Botella, M. S. Kim, H. Kim, N. Bagherzadeh, "PLAM: A Posit Logarithm-Approximate Multiplier", IEEE Transactions on Emerging Topics in Computing, 2022
mallasen_2022 -> D. Mallasén, R. Murillo, A. A. Del Barrio, G. Botella, L. Piñuel, M. Prieto-Matías, "PERCIVAL: Open-Source Posit RISC-V Core With Quire Capability", IEEE Transactions on Emerging Topics in Computing, 2022
