---
handle: shenoy_kumaresan_1989
citation: Shenoy, Kumaresan, "Fast Base Extension Using a Redundant Modulus in RNS", IEEE Transactions on Computers, 1989
actual_citation: same
status: ok
kind: paper
unit_classes: [other]
formats: [rns]
authority: landmark
pages_read: 292-296 / 5
---

## summary
The paper proposes a CRT-based RNS base-extension method that replaces sequential mixed-radix conversion with a parallel tree and a redundant residue channel. The method reduces latency from \(n\) table-lookup cycles to \(\lceil\log_2(n+1)\rceil+1\) cycles and reduces lookup-table hardware for larger bases. (pp.292, 294-296)

## families
### rns_scaling_comparison  (role: proposes)
mechanism: The method carries the residue of \(x\) modulo a relatively prime redundant modulus \(p_{m+1}\) through all arithmetic operations. The CRT expansion bounds the unknown integer \(r_x\) by \(n-1\), so \(r_x\) is recovered modulo \(p_{m+1}\) when \(p_{m+1}\geq n\). Parallel constant multiplications and tree-structured modular additions compute \(r_x\) and the residues for every extension modulus simultaneously, after which \(r_xP\) is subtracted modulo each extension modulus. (pp.294-295)
choices:
  operation: base_extend   # p.292
  method: redundant_modulus   # pp.292, 294
  exactness: exact   # p.294
new_choices:
  redundant_modulus_requirement: relatively prime and \(p_{m+1}\geq n\) — the redundant channel must distinguish every possible \(r_x\) value   # p.294
  stage_implementation: lookup_tables | modulo_adders | combination — successive stages may use any of these implementations   # p.296
  first_stage_table_inputs: single | multiple — the first stage may accept one or multiple operands depending on modulus size   # p.296
slots:
  none
parameters: \(n\) original relatively prime moduli; one redundant modulus \(p_{m+1}\geq n\); one or more extension moduli \(p_{n+1},\ldots,p_m\); example uses \(n=5\), moduli 3/5/7/11/13, redundant modulus 8, extension modulus 17, and \(x=10000\)   # pp.292, 294
results:
| metric | value | unit | technology / device | baseline | condition | page |
| latency | \(\lceil\log_2(n+1)\rceil+1\) | table-lookup cycles | UNKNOWN; year 1989 | Szabo-Tanaka: \(n\) table-lookup cycles | modulo addition and multiplication by a known constant combined in one lookup | p.294 |
| latency | 1 lookup plus \(\lceil\log_2(n+1)\rceil+1\) modular additions | cycles | UNKNOWN; year 1989 | Szabo-Tanaka: \(n\) lookups plus \(n\) modular additions | multiplication and modular addition implemented separately | p.295, Table I |
| lookup tables | \(2n+2\) | tables | UNKNOWN; year 1989 | Szabo-Tanaka: \(\frac{1}{2}n(n+1)-1\) | multiplication and modular addition implemented separately | p.295, Table I |
| lookup tables, \(n=4\) | 8 | tables | UNKNOWN; year 1989 | Szabo-Tanaka: 9 | lookup-table-only implementation | p.296, Table II |
| lookup tables, \(n=5\) | 10 | tables | UNKNOWN; year 1989 | Szabo-Tanaka: 14 | lookup-table-only implementation | p.296, Table II |
| lookup tables, \(n=8\) | 16 | tables | UNKNOWN; year 1989 | Szabo-Tanaka: 35 | lookup-table-only implementation | p.296, Table II |
| lookup tables, \(n=12\) | 24 | tables | UNKNOWN; year 1989 | Szabo-Tanaka: 77 | lookup-table-only implementation | p.296, Table II |
| lookup tables, \(n=16\) | 32 | tables | UNKNOWN; year 1989 | Szabo-Tanaka: 136 | lookup-table-only implementation | p.296, Table II |
| lookup tables, \(n=20\) | 40 | tables | UNKNOWN; year 1989 | Szabo-Tanaka: 209 | lookup-table-only implementation | p.296, Table II |
| latency, \(n=4\) | 4 | table-lookup cycles | UNKNOWN; year 1989 | Szabo-Tanaka: 4 | lookup-table-only implementation | p.296, Table II |
| latency, \(n=5\) | 4 | table-lookup cycles | UNKNOWN; year 1989 | Szabo-Tanaka: 5 | lookup-table-only implementation | p.296, Table II |
| latency, \(n=8\) | 5 | table-lookup cycles | UNKNOWN; year 1989 | Szabo-Tanaka: 8 | lookup-table-only implementation | p.296, Table II |
| latency, \(n=12\) | 5 | table-lookup cycles | UNKNOWN; year 1989 | Szabo-Tanaka: 12 | lookup-table-only implementation | p.296, Table II |
| latency, \(n=16\) | 6 | table-lookup cycles | UNKNOWN; year 1989 | Szabo-Tanaka: 16 | lookup-table-only implementation | p.296, Table II |
| latency, \(n=20\) | 6 | table-lookup cycles | UNKNOWN; year 1989 | Szabo-Tanaka: 20 | lookup-table-only implementation | p.296, Table II |
errors_and_checks: The method computes the exact extended residues. The paper assumes that the redundant residue is available and does not report fault coverage, false alarms, or alias rates.   # pp.294-295
conditions: The method assumes pairwise relatively prime original/extension moduli and a relatively prime redundant modulus \(p_{m+1}\geq n\) whose residue accompanies the data from start to finish. (pp.292, 294) Base extension supports scaling, dynamic-range extension, magnitude comparison, overflow detection, sign determination, and redundant-RNS error correction. (p.292) Reduced latency matters for recursive algorithms such as IIR filters, where base extension lies in the feedback path. (p.292) In fully pipelined applications, latency does not reduce throughput, so the principal benefit is reduced hardware and fewer interstage latches. (p.296) Small moduli keep lookup tables practical, while previously proposed special-modulus methods require moduli considered too large for practical implementation. (p.292)
evidence: Abstract; §§I and IV-V; Figs. 1-3; Tables I-II; pp.292-296.

## new_families
none

## space_gaps
* `rns_scaling_comparison` lacks a choice for the redundant-modulus bound \(p_{m+1}\geq n\), which is required to recover \(r_x\). (p.294)
* `rns_scaling_comparison` lacks a stage-implementation choice covering lookup tables/modulo adders/combinations. (p.296)
* `rns_scaling_comparison` lacks a first-stage fan-in choice covering single-input and multiple-input lookup tables. (p.296)

## open_questions
* The supplied rendering does not preserve the complete modulo-adder count in Table I or the lookup-table size expressions in Table II, so those values remain unrecorded.
