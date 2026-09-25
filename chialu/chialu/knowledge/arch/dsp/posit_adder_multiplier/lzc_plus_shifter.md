---
family: posit_adder_multiplier
pin: {regime_decode: lzc_plus_shifter}
---
# lzc_plus_shifter

Regime decoding by one leading-digit counter and one shifter: the
counter measures the run of identical regime bits, which gives the
scale contribution useed^k, and the shifter removes the run so the
exponent and fraction fields land at fixed positions in the
intermediate format. In the integrated form a single leading-zero-or
-one counter with shifter handles both regime polarities without
separate detectors or operand inversion.

This is the decoder of every posit generator on record, from the
parameterized ICCD generator through PACoGen and the FloPoCo posit
operators, because the regime length must be determined before the
exponent and fraction can be decoded and a counter plus shifter is
the direct realization; the same pair, run in reverse, is the
encoder. Its cost is the extraction latency that an equal-width
IEEE operator does not pay, which is why posit adders stay slower
than their float counterparts, and a two-stage masked decode that
detects zeros and ones concurrently and overlaps detection with a
preshift is the sibling for a latency-critical multiplier.

The library decoder realizes this variant with the library's leading-zero counter over the body xored with its first bit and the library's shifter that exposes the exponent and fraction fields (`posit.decode_sv`, `regime_decode: lzc_plus_shifter`); the encoder builds the regime and shifts the fields below it through the same shifter family.

## references

chaurasiya_2018 -> R. Chaurasiya, J. Gustafson, R. Shrestha, et al., "Parameterized Posit Arithmetic Hardware Generator", IEEE International Conference on Computer Design (ICCD), 2018
podobas_2018 -> A. Podobas, S. Matsuoka, "Hardware Implementation of POSITs and Their Application in FPGAs", IEEE International Parallel and Distributed Processing Symposium Workshops (IPDPSW), 2018
uguen_2019 -> Y. Uguen, L. Forget, F. de Dinechin, "Evaluating the Hardware Cost of the Posit Number System", International Conference on Field Programmable Logic and Applications (FPL), 2019
murillo_2020 -> R. Murillo, A. A. Del Barrio, G. Botella, "Customized Posit Adders and Multipliers Using the FloPoCo Core Generator", IEEE International Symposium on Circuits and Systems (ISCAS), 2020
