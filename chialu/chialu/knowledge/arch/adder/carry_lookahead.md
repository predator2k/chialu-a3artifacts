# carry_lookahead

Carry-propagate addition with carries precomputed from
generate/propagate terms: each carry is expanded
as an AND/OR function of generation at its own order and propagation
through every intervening lower order, so all carries become
available substantially simultaneously. Because a full-width
expansion needs a large amount of switching beyond a few orders, the
carries are formed inside groups of a few bits, group
generate/propagate signals feed a lookahead level that produces the
group carries, further levels (sections, supergroups) repeat the
construction up to the word width, and each sum is one XOR behind its
carry. The standard 4-bit CLA is a 4-bit Brent-Kung prefix
architecture.

Group size trades gate fan-in against level count: four-bit grouping
is the compromise among speed, fan-in and fan-out that Stretch, the
Model 91, ILLIAC IV and the ETH cell-based designs share, five-bit
groups with 25-bit sections serve 50- and 100-bit adders, and at 64
bits a group-of-4 hierarchy needs 5 gate delays against 8 for
group-of-2. Levels are forced by circuit fan-in/fan-out limits rather
than chosen freely, so 60- and 64-bit adders stack three of them.
Intergroup carry sets the shape above the groups: full lookahead
between groups is fastest, rippling the group carries keeps every
lookahead cell independent, and a carry-select stage above lookahead
blocks matches pure CLA unit-gate speed at substantially higher gate
count. Block sizing is uniform for modularity or optimized by dynamic
programming, which balances path delays with smaller blocks at more
levels and cuts worst-case carry delay 15 to 25 percent in a 1992
CMOS standard-cell library.

The family delivers O(log n) delay at O(n log n) hardware relative to
ripple carry; at 50 bits full lookahead takes 12 logical levels and
636 logical units against 100 levels and 400 units for ripple. The
standard CLA sits with Brent-Kung in the linear-area
logarithmic-delay class, below Sklansky and Kogge-Stone, which buy
depth with n log n area, and it is about 50 percent slower than
conditional-sum under a gate model with delay independent of fan-in
while using slightly fewer gates. On an FPGA it maps poorly because
it uses general routing and gives little speed over ripple carry
except at very wide widths, at more than twice the area, unless the
fabric supplies lookahead blocks itself.

Conversions to a prefix tree or to Ling pseudo-carries keep the
group hierarchy and change the operator: Ling H/I terms lower the
first-level stack, and the distant-carry and prefix readings show the
CLA as one point on the depth/fan-in/area continuum. The structure
also serves as the final CPA of parallel multipliers, accepts
mode-dependent kill terms that break carries at SIMD lane boundaries
without lengthening the critical path, and supports concurrent error
detection through duplicated or rippled check carries. Where part of the sum is
already assimilated, that part of the adder becomes an incrementer: a
161-bit multiply-add CPA whose low 26 product bits were added in an
earlier cycle builds only an 88-bit carry-lookahead adder and takes
carry-lookahead incrementers for the remaining sections, which are
smaller and faster than adders of the same width, with the section
carry-ins formed as Cin_c = P_b + G and Cin_d = P_c + P_b + G.

## references

weinberger_smith1958 -> A. Weinberger, J. L. Smith, "A Logic for High-Speed Addition", National Bureau of Standards Circular 591, pp. 3-12, 1958.
richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
macsorley1961 -> O. L. MacSorley, "High-Speed Arithmetic in Binary Computers", Proceedings of the IRE, vol. 49, no. 1, pp. 67-91, 1961
chan1992 -> P. K. Chan, M. D. F. Schlag, C. D. Thomborson, V. G. Oklobdzija, "Delay Optimization of Carry-Skip Adders and Block Carry-Lookahead Adders Using Multidimensional Dynamic Programming", IEEE Transactions on Computers, vol. 41, no. 8, pp. 920-930, 1992.
sklansky1960b -> J. Sklansky, "An Evaluation of Several Two-Summand Binary Adders", IRE Transactions on Electronic Computers, vol. EC-9, no. 2, pp. 213-226, 1960.
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
naffziger1996 -> S. Naffziger, "A Sub-Nanosecond 0.5 um 64 b Adder Design", IEEE International Solid-State Circuits Conference (ISSCC), pp. 362-363, 1996.
jessani_1996 -> R. M. Jessani, C. H. Olson, "The Floating-Point Unit of the PowerPC 603e Microprocessor", IBM Journal of Research and Development, vol. 40, no. 5, 1996
