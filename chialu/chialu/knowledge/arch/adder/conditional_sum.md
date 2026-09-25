# conditional_sum

Carry-select recursively doubled to its limit: every bit computes its
sum and carry for both carry-in values, and a binary hierarchy of
two-input multiplexers, each controlled by the carry out of the
lower-significance group, selects the valid results. Group sizes start
at one bit and double at every level, so an n-bit adder has log2 n
selection levels, both candidate results are generated only at level
one, and later levels duplicate only multiplexers. The select pattern
is the Sklansky prefix tree, and one select signal can drive up to n/2
multiplexers.

The family is the fastest carry-propagate adder in the unit-gate model,
at 2 log2 n gate delays for 3n log2 n gates in abstract units, but its
area grows as n log n and its select fanout is unbounded, so wiring and
fanout degrade post-layout speed and its area-delay and power-delay
products fall behind the Brent-Kung and Kogge-Stone prefix adders of
the same delay class. The base block width trades selection levels
against ripple inside the block: a 4-bit block with ripple carry-merge
logic and 2:1 selection serves as a noncritical sum generator in the
65-nm Pentium 4 integer unit, where it takes a 60 percent
transistor-size reduction because it sits off the carry path. The mux
style sets the cost of each level: transmission-gate cells and
multiplexers give a path of 1+log2 n series transistors and about 30
percent lower latency than carry-select adders in 2.5-µm CMOS, at the
price of cascaded CMOS buffers on the select signals and more area.
Binary selection, in which each level resolves two carry candidates,
is the setting every reported design uses.

Fanout is the recurring cost. The RS/6000 floating-point adder keeps
it bounded by placing progressively larger buffers in the otherwise
unused evaluation locations of each recursive section, which retains
logarithmic delay at widths above 100 bits where carry-skip is no
longer competitive. The family wins for latency-critical additions
with a regular layout at arbitrary word length, such as resolving the
carry-save output of a multiplier, and loses to carry-select once area
matters and to prefix adders once wiring and fanout dominate; the
convert_to_sklansky_prefix mutation re-expresses the same select
pattern as a prefix tree. Two hybrids reuse the structure: a compound
adder forms A+B and A+B+1 with one duplicated carry chain and selects
by rounding logic rather than by a carry-in, and a multiplier final
adder synthesized from the tree's per-bit arrival times uses
conditional-carry sections for the early bits and a conditional-sum
block only for the last, latest-arriving group.

## references

sklansky1960b -> J. Sklansky, "An Evaluation of Several Two-Summand Binary Adders", IRE Transactions on Electronic Computers, vol. EC-9, no. 2, pp. 213-226, 1960.
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
rothermel1989 -> A. Rothermel, B. J. Hosticka, G. Troester, J. Arndt, "Realization of Transmission-Gate Conditional-Sum (TGCS) Adders with Low Latency Time", IEEE Journal of Solid-State Circuits, vol. 24, no. 3, pp. 558-561, 1989.
montoye_1990 -> R. K. Montoye, E. Hokenek, S. L. Runyon, "Design of the IBM RISC System/6000 Floating-Point Execution Unit", IBM Journal of Research and Development, 1990
wijeratne_2007 -> S. B. Wijeratne, et al., "A 9-GHz 65-nm Intel Pentium 4 Processor Integer Execution Unit", IEEE Journal of Solid-State Circuits, vol. 42, no. 1, pp. 26-37, 2007.
santoro_1989 -> M. R. Santoro, G. Bewick, M. A. Horowitz, "Rounding Algorithms for IEEE Multipliers", 9th IEEE Symposium on Computer Arithmetic, 1989
yehjen2000 -> W.-C. Yeh, C.-W. Jen, "High-Speed Booth Encoded Parallel Multiplier Design", IEEE Transactions on Computers, vol. 49, no. 7, pp. 692-701, 2000
