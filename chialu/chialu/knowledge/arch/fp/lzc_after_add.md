# lzc_after_add

Exact leading-zero count on the completed significand result: the counter slot (a recursive-doubling detector or a prefix-formulated counter) reads the adder output and drives the normalizer, so the count is always right and needs no correction stage, at the cost of placing count, normalize and round in series after the carry propagation.

It is the pick where that series is affordable or already hidden: a single-path adder chosen for area rather than speed, a close path whose bounded pre-alignment lets the result arrive early enough for counting without an LZA, a mainframe pipeline that adds in one stage and counts and normalizes in the next, a multiplier that counts the product's leading zeros for subnormal normalization in parallel with the multiplication, and a conversion path that shares the count with int-to-FP. The dual-path close path still contains subtraction, count and shift in series unless anticipation overlaps the count with the subtraction, and close subtraction makes post-add counting and normalization a dominant delay, which is the case for the lza sibling. A conventional adder without anticipation has lower area and power than an LZA scheme, and the counter itself is a measurable, separately optimizable fraction of FP-add energy.

The mutation replace_lzc_with_lza is the standard latency move; keep the counter when the adder output is early, when the result sign is not known in advance, or when exactness must not depend on a correction path.

## references

pillai_1997 -> R. V. K. Pillai, D. Al-Khalili, A. J. Al-Khalili, "A Low Power Approach to Floating Point Adder Design", IEEE International Conference on Computer Design (ICCD), 1997
gerwig_2004 -> G. Gerwig, H. Wetter, E. M. Schwarz, J. Haess, C. A. Krygowski, B. M. Fleischer, M. Kroener, "The IBM eServer z990 Floating-Point Unit", IBM Journal of Research and Development, 2004
schwarz_1999 -> E. M. Schwarz and C. A. Krygowski, "The S/390 G5 Floating-Point Unit", IBM Journal of Research and Development, 1999
suzuki_1996 -> H. Suzuki, H. Morinaka, H. Makino, Y. Nakase, K. Mashiko, T. Sumi, "Leading-Zero Anticipatory Logic for High-Speed Floating Point Addition", IEEE Journal of Solid-State Circuits, 1996
seidel_2003 -> P.-M. Seidel, "Multiple Path IEEE Floating-Point Fused Multiply-Add", IEEE MWSCAS, 2003
oklobdzija_1994 -> V. G. Oklobdzija, "An Algorithmic and Novel Design of a Leading Zero Detector Circuit: Comparison with Logic Synthesis", IEEE Transactions on VLSI Systems, 1994
chong_2009 -> Y. J. Chong, S. Parameswaran, "Flexible Multi-Mode Embedded Floating-Point Unit for Field Programmable Gate Arrays", ACM/SIGDA International Symposium on Field-Programmable Gate Arrays (FPGA), 2009
