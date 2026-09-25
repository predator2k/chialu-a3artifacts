---
handle: weinberger_smith1958
citation: A. Weinberger, J. L. Smith, "A Logic for High-Speed Addition", National Bureau of Standards Circular 591, pp. 3-12, 1958.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [binary53]
authority: landmark
pages_read: 3-12 / 22
---

## summary
The paper develops a parallel binary adder that forms several carries simultaneously and extends the method with two levels of auxiliary carry functions. The resulting 53-bit design completes addition in five clock phases with a stated 1 µsec cycle time using 1-Mc SEAC-type circuitry (p.3, p.8, p.12).

## families
### carry_lookahead  (role: proposes)
mechanism: The adder expands each carry as a Boolean function of augend/addend digits and a lower-order carry. Four successive carries are first generated simultaneously in separate gating stages. X/Y auxiliary carry functions allow later carry groups to depend directly on an earlier carry, and a second Z/W auxiliary level extends the method through C52. Sum digits are generated one clock phase after their corresponding carries (p.5-p.10).
choices:
  group_size: 4   # p.6
  levels: 2   # p.8
  intergroup_carry: lookahead   # p.6-p.10
new_choices:
  circuit_style: dynamic_pulse_or_and_or — multiphase pulse circuitry implemented with three-level OR-AND-OR gating stages   # p.3
slots:
  none
parameters: 53-bit augend/addend and sum; 1-Mc/sec circuitry (p.3); 14-bit and 21-bit examples complete in 4 clock phases (p.7); the 53-bit design completes in 5 clock phases with II=1 addition per 1 µsec cycle (p.8, p.12)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| addition cycle time | 1 | µsec | SEAC-type 1-Mc dynamic pulse circuitry; node UNKNOWN; 1958 | UNKNOWN | 53-bit design, five clock phases | p.12 |
| latency | 5 | clock phases | SEAC-type 1-Mc dynamic pulse circuitry; node UNKNOWN; 1958 | UNKNOWN | 53-bit design | p.12 |
| total gating stages | 238 | stages | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 53-bit variant, maximum load 25 gate-loads | p.10-p.12 |
| tubes | 238 | tubes | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 53-bit variant, maximum load 25 gate-loads | p.12 |
| delay lines | 300 | delay lines | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 53-bit variant, maximum load 25 gate-loads | p.12 |
| maximum load | 25 | gate-loads | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 238-stage variant | p.12 |
| total gating stages | 253 | stages | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 53-bit variant, maximum load 19 gate-loads | p.12 |
| tubes | 253 | tubes | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 53-bit variant, maximum load 19 gate-loads | p.12 |
| delay lines | 250 | delay lines | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 53-bit variant, maximum load 19 gate-loads | p.12 |
| maximum load | 19 | gate-loads | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 253-stage variant | p.12 |
| total gating stages | 285 | stages | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 53-bit variant, maximum load 14 gate-loads | p.12 |
| tubes | 285 | tubes | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 53-bit variant, maximum load 14 gate-loads | p.12 |
| delay lines | 150 | delay lines | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 53-bit variant, maximum load 14 gate-loads | p.12 |
| maximum load | 14 | gate-loads | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | other table 1.4 variants | 285-stage variant | p.12 |
| auxiliary carry logic | 26 | stages | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | 238 total stages | first table 1.4 variant | p.10 |
| non-auxiliary register logic | 212 | stages | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | 238 total stages | augend/addend/carry/sum stages | p.10 |
| diode count | approximately 10,000 | germanium diodes | SEAC-type dynamic pulse circuitry; node UNKNOWN; 1958 | UNKNOWN | each of the three 53-bit versions | p.12 |
errors_and_checks: none
conditions: Each gating stage permits up to 4 AND-gates, and the largest AND-gate permits up to 6 inputs (p.3). Signals crossing clock phases require synchronization with electric delay lines (p.3-p.4). The design targets repetitive multiplication/division use in which shifted sum digits recirculate into an input (p.12). Reduced maximum tube load requires more gating stages and tubes (p.12).
evidence: §§2-5; equations (2)-(9); figures 1.7-1.10; tables 1.2-1.4, p.4-p.12

### ripple_carry  (role: analyzes)
mechanism: Sequential carry generation computes Ck explicitly from Ck-1, so each carry waits for the next lower-order carry. Each sum digit becomes available in the clock phase after its corresponding carry, which makes latency grow with the number of binary digits (p.4-p.5).
choices:
new_choices:
  none
slots:
  none
parameters: n-bit operands; n-1 possible carries; one carry position advanced per clock phase (p.5)
results:
| metric | value | unit | technology / device | baseline | condition | page |
| relative speed | 4 | factor | 4-phase 1-Mc circuitry; node UNKNOWN; 1958 | completely serial adder | four successive sum digits obtained per 1 µsec | p.5 |
errors_and_checks: none
conditions: The factor-of-four comparison assumes a 4-phase, 1-Mc clock (p.5). Sequential dependence on Ck-1 limits carry generation to one position per clock phase (p.5).
evidence: §2, equations (1)-(2), table 1.1, p.4-p.5

## new_families
none

## space_gaps
* carry_lookahead lacks a circuit-style choice for the paper's dynamic pulse OR-AND-OR implementation (p.3).

## open_questions
* The paper does not state whether the 53-bit adder versions were fabricated or whether the 1 µsec cycle time is measured rather than derived from the five-phase timing design.
