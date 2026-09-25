---
family: correct_rounding_strategy
pin: {strategy: single_pass_worst_case_precision}
---
# single_pass_worst_case_precision

One fixed-precision evaluation with no retry: the minimum non-zero
distance between any function result and a rounding breakpoint is
computed in advance, and the working precision is set above it, so
every prerounded result rounds correctly in one pass. The worst cases
come from an offline search, exhaustive for short formats or a
polynomial filter with a Euclidean grid test for double; hardware
also adjusts stored coefficients per subinterval until each result
rounds to the exact value.

It is the pick for hardware and for fixed-latency datapaths, where a
retry cannot be scheduled: exactly rounded reciprocal, square root,
2^x and log2 units at 16 and 24 bits are tuned in under an hour for
24 bits, and double-precision exp and ln need 2^-113 and 2^-118 from
the published searches, which took years of workstation time and
cover only exp, ln, 2^x and log2 over the full range. It loses where
the worst case is unknown or the format is wider than the search
reaches, where the two-phase retry is the only proven option, and to
interval synthesis when the target format can be validated
exhaustively and the polynomial can absorb the rounding constraints.

The library's module for correct_rounding_strategy realizes this variant by its pin (`chialu/targets/rtl/families/sfu.py`).

## references

lefevre_2001 -> V. Lefevre, J.-M. Muller, "Worst Cases for Correct Rounding of the Elementary Functions in Double Precision", 15th IEEE Symposium on Computer Arithmetic (ARITH-15), pp. 111-118, 2001
schulte_1994 -> M. J. Schulte, E. E. Swartzlander, "Hardware Designs for Exactly Rounded Elementary Functions", IEEE Transactions on Computers, vol. 43, no. 8, pp. 964-973, 1994
muller_2018 -> J.-M. Muller, N. Brunie, F. de Dinechin, C.-P. Jeannerod, M. Joldes, V. Lefevre, G. Melquiond, N. Revol, S. Torres, "Handbook of Floating-Point Arithmetic", 2nd ed., Birkhauser, 2018
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
