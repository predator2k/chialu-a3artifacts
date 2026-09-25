---
family: carry_lookahead
pin: {block_sizing: dp_optimized}
---
# dp_optimized

Variable-size block carry-lookahead: the block sizes are chosen by a
multidimensional dynamic program that fills an m-input lookahead
generator recursively from its least-significant position, keeping
five delay/load components per complete adder and eight per partial
block so that the extra carry-input loading a subadder sees inside a
larger block is accounted for, and pruning by upper bounds and
dominance to reach minimum-latency configurations.

Variable block sizes balance path delays because smaller blocks
reduce fan-in and fan-out delay despite adding logic levels, and the
optimized adders cut worst-case carry delay 15 to 25 percent against
equal-block-size adders in a 1992 ASIC CMOS standard-cell library
with gate fan-in restricted to 4. The variant is the pick when
latency dominates and layout regularity does not: the result is less
modular, uses more levels with smaller fan-ins, and the delay model
excludes wire-length effects. Uniform blocks stay the choice for a
regular layout or when the optimization run is not affordable.

## references

chan1992 -> P. K. Chan, M. D. F. Schlag, C. D. Thomborson, V. G. Oklobdzija, "Delay Optimization of Carry-Skip Adders and Block Carry-Lookahead Adders Using Multidimensional Dynamic Programming", IEEE Transactions on Computers, vol. 41, no. 8, pp. 920-930, 1992.
