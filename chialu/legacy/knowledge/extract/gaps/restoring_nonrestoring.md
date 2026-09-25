# restoring_nonrestoring: proposed changes to the space

* bits_per_cycle admits a variable 1..x_j value tied to shift_over_zeros — remainder normalization into [0.5, 1) every iteration produces a data-dependent number of quotient bits per iteration. [freiman_1961]
* choice divisor_multiple_set (e.g. {1.0D}, {0.75D, 1.0D, 1.5D}, {0.625D, 1.0D, 1.25D}) — the available divisor multiples control the average shift length and thus the iteration rate. [freiman_1961]
* choice quotient_generation_correction (add_01_and_invert_next_bit) — a sign change after subtracting 0.75D with a shorter-than-encoded normalization shift needs a quotient correction. [freiman_1961]
* bits_per_cycle range extended to 3, 4, and 8 (replicated_steps) — a three-bit nonrestoring merged div/sqrt and 4-bit/8-bit replicated restoring baselines are implemented. [kim_2025, mach_2020]
* function coverage extended to square root — the same restoring or nonrestoring radix-2 recurrence performs extended-precision and merged square root. [schwarz_1999, mach_2020, kim_2025]
* choice remainder_selection (subtract_result_or_old_remainder) — nonperforming discards the negative subtraction result rather than restoring it. [davis_1969]
* choice parallel_trial_multiples (3) — three parallel subtractors try 1X/2X/3X and end-around-borrow signals select the largest success for two bits per iteration. [thornton_1970__s06]
* choices initial_magnitude_test (subtract_shifted_divisor) and final_remainder_policy {discard, restore, reconstruct} — the divisor magnitude is verified against the dividend first and the remainder is discarded, restored, or reconstructed after quotient generation. [richards_1955__s06]
* choice iteration_override (fewer_than_correctly_rounded) — the iteration count can be reduced below the correctly rounded count for an accuracy/throughput trade. [mach_2020]
