# flagged_prefix

Rounding fused into the significand addition: a flagged prefix adder carries a row of group-propagate flags beside its prefix tree, so a late carry-in (the rounding increment) and two inversion enables (all-bit inversion for the absolute difference after a negative true subtraction, complementation near the LSBs for subtraction) are applied after the carries are known, and sum, sum+1 and the complemented difference come out of one adder. All four IEEE modes are realized in the add stage.

modes and position follow the rounding slot: with prenormalization rounding the increment is applied before normalization, which is exact because the round position is known from the exponent difference on the far path and a near-path difference-1 result is exact and needs no rounding; the LZA distance then normalizes, and a final stage corrects a one-bit LZA overestimate or a rounded overflow. unified_add_sub_cases is natural here, since the same flag row serves the true-subtraction complement and the increment. The scheme gave a 3-cycle adder in 0.5 um silicon and a 2-cycle architecture that costs more hardware; its limit is that the combined ADD/ROUND delay is too long for one short pipeline stage, which pushes designs at extreme clock rates toward compound_adder_select with a separate selection. The same adder rounds a signed-digit SRT quotient, absorbing the complementation and a 0.5 to 2 ulp adjustment before an optional one-bit normalize shift.

Pick flagged_prefix to save the increment stage and the second adder of a compound scheme in an area-constrained adder; pick compound_adder_select when the cycle budget cannot hold the flag row's extra logic depth.

## references

beaumont_smith1999 -> A. Beaumont-Smith, N. Burgess, S. Lefrere, C.-C. Lim, "Reduced Latency IEEE Floating-Point Standard Adder Architectures", 14th IEEE Symposium on Computer Arithmetic (ARITH-14), 1999.
burgess2005 -> N. Burgess, "Prenormalization Rounding in IEEE Floating-Point Operations Using a Flagged Prefix Adder", IEEE Transactions on VLSI Systems, 2005.
