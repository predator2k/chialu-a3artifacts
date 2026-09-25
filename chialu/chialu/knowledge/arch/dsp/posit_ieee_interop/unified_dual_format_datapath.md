---
family: posit_ieee_interop
pin: {interop_style: unified_dual_format_datapath}
---
# unified_dual_format_datapath

One arithmetic core for both formats: posit and IEEE-754 operands are
decoded into a shared sign, scale-factor and fraction form
(-1)^s x 2^sf x 1.f, the shared datapath computes, and format-specific
encoders and exception handlers follow. Posit decoding does the
sign-conditioned two's complement, the regime run-length decode and a
runtime exponent extraction; IEEE decoding extracts the fields and
removes the configured bias. Each operand's format and the output
format are set independently.

The unified core is the pick when mixed-format operation and
conversion should be free by-products of the MAC itself: the vector
unit of Crespo et al. handles 32-, 16- and 8-bit posit and IEEE
elements, an 8-bit IEEE-like format with 4 exponent and 3 mantissa
bits, a runtime-selected posit exponent size and a quire, with the
IEEE encoder handling subnormals and choosing between the rounded
result, zero, infinity and a canonical NaN from generated flags. No
area or ulp figure is reported. Boundary converters keep the IEEE
datapath untouched but double round on the way back and cost a
conversion per crossing; PERCIVAL's alternative keeps separate posit
and float datapaths and register files on one core and pays
register-file, decoder, scoreboard and interconnect area, 44693 LUTs
against 28950 for the bare CVA6 with the PAU and no FPU.

Under this variant the seed instantiates the library's decoder and encoder of the posit mode and leaves the conversions on the lane's shared X datapath and pack functions.

## references

crespo_2022 -> L. Crespo, P. Tomás, N. Roma, N. Neves, "Unified Posit/IEEE-754 Vector MAC Unit for Transprecision Computing", IEEE Transactions on Circuits and Systems II: Express Briefs, 2022
dedinechin_2019b -> F. de Dinechin, L. Forget, J.-M. Muller, Y. Uguen, "Posits: The Good, the Bad and the Ugly", Conference for Next Generation Arithmetic (CoNGA), 2019
mallasen_2022 -> D. Mallasén, R. Murillo, A. A. Del Barrio, G. Botella, L. Piñuel, M. Prieto-Matías, "PERCIVAL: Open-Source Posit RISC-V Core With Quire Capability", IEEE Transactions on Emerging Topics in Computing, 2022
