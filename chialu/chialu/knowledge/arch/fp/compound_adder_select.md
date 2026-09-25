# compound_adder_select

Rounding by selection: a compound adder produces sum and sum+1 (and sum+2 for the directed modes) in parallel, and the guard/round/sticky decision, resolved while the addition runs, picks the rounded result, so the serial post-normalize increment leaves the critical path. position says where the selection sits: after the normalizer, before it on a far path whose normalization is at most one bit, or before a fine normalization with candidates at each possible rounding location.

modes sets how many candidates the decision needs: round-to-nearest needs sum and sum+1, the directed modes need sum+2 for the overflow case (a half-adder row above the significand adder), and RNE needs a tie fix that forces the LSB to zero. speculative_locations covers a result spanning two binades: the QTF scheme injects a prediction bit and selects over a two-way compound adder, the YZ scheme keeps a short carry-save buffer and selects normalized candidates, and a far path can precompute +1 and +2 with three adders. unified_add_sub_cases merges the addition and subtraction rounding cases so one selection serves both. Normalizing before the addition halves the adder width and fixes the rounding positions, which is how the dual-adder FMAs make the combined add/round a 53-bit block; an overflow pre-shift keeps its input below 11.XXX.

The scheme is the production default for adders and multipliers because it costs one extra adder and a mux and removes a pipeline stage; increment_adder is cheaper where latency is not critical, injection replaces the mode logic by constants when a compound prefix adder already exists, and flagged_prefix fuses the increment into the adder itself. The selection is exact under all IEEE modes; only the decision logic differs between schemes.

## references

oberman_1996 -> S. F. Oberman and M. J. Flynn, "A Variable Latency Pipelined Floating-Point Adder", Euro-Par'96 Parallel Processing (LNCS 1124), Springer, 1996
even_2000 -> G. Even and P.-M. Seidel, "A Comparison of Three Rounding Algorithms for IEEE Floating-Point Multiplication", IEEE Transactions on Computers, 2000
lang_2004 -> T. Lang, J. D. Bruguera, "Floating-Point Multiply-Add-Fused with Reduced Latency", IEEE Transactions on Computers, vol. 53, pp. 988-1003, 2004
sohn_2016 -> J. Sohn, E. E. Swartzlander, "A Fused Floating-Point Four-Term Dot Product Unit", IEEE TCAS-I, vol. 63, no. 3, pp. 370-378, 2016
seidel_2004 -> P.-M. Seidel and G. Even, "Delay-Optimized Implementation of IEEE Floating-Point Addition", IEEE Transactions on Computers, 2004
santoro_1989 -> M. R. Santoro, G. Bewick, M. A. Horowitz, "Rounding Algorithms for IEEE Multipliers", 9th IEEE Symposium on Computer Arithmetic, 1989
quach_2004 -> N. T. Quach, N. Takagi, M. J. Flynn, "Systematic IEEE Rounding Method for High-Speed Floating-Point Multipliers", IEEE Transactions on VLSI Systems, 2004
pillai_1997 -> R. V. K. Pillai, D. Al-Khalili, A. J. Al-Khalili, "A Low Power Approach to Floating Point Adder Design", IEEE International Conference on Computer Design (ICCD), 1997
