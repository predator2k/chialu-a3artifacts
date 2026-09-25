# sig_div_then_round: proposed changes to the space

* choices `signed_round_information: signed_round_and_sticky_digits` and a prenormalization adjustment range — rounding a signed-digit SRT quotient needs signed round/sticky polarities and a 0.5 to 2 ulp adjustment [burgess2005]
* `round` slot value for final rounding performed by the ambient mode of the last `fma` — the software division sequences have no separate rounding circuit [harrison_2000]
* choice `optimization_target: {latency, throughput}` — separate algorithm variants exist for dependency latency and independent-operation throughput [harrison_2000]
* a square-root wrapper family corresponding to `sig_div_then_round` — the textbook treats square root as a second potentially infinite exact result with its own algorithm families [muller_2018#s07]
* choice `significand_algorithm: {digit_recurrence, functional_iteration, polynomial_approximation}` — the three algorithm families differ in exactness, iteration count and rounding proof, and the slot enum mixes them without that axis [muller_2018#s07]
* choice for deliberately biased preset rounding — the CDC 6600 preset one-third rounding is a distinct rounding contract [thornton_1970#s06]
* `subnormal` value for an optional non-IEEE hardware flush mode alongside full hardware support [asprey_1993]
