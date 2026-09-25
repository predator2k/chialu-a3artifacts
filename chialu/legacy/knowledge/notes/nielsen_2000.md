---
handle: nielsen_2000
citation: A. M. Nielsen, D. W. Matula, C. N. Lyu, G. Even, "An IEEE Compliant Floating-Point Adder that Conforms with the Pipelined Packet-Forwarding Paradigm", IEEE Transactions on Computers, 2000
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [IEEE_754_double_extended_binary]
authority: landmark
pages_read: 33-47 / 15
---

## summary
The document proposes a four-stage IEEE 754 floating-point adder that forwards a redundant principal significand packet after two cycles and supplies its carry-round packet one cycle later (pp.33-35). The design uses parallel exponent-difference paths and borrow-save 3:2/4:2 additions so dependent operations avoid full-width nonredundant addition until retirement (pp.35, 39-45).

## families
### two_path  (role: extends)
mechanism: Two parallel datapaths distinguish small and large exponent differences. The small-difference path handles -1 <= e1-e2 <= 4, performs possible cancellation normalization using leading-zero anticipation on a partially compressed borrow-save sum, and adds the late carry-round packet during cycle two. The large-difference path handles e1-e2 >= 5 or e2-e1 >= 2, shifts only the operand with the smaller exponent, and directs the late carry-round packet to one of two fixed locations. Both paths feed common rounding stages. (pp.39-44)
choices:
  close_path_trigger: exp_diff_only   # pp.35, 39
  path_select_point: early_exponent_compare   # pp.35, 39, 42
  shared_rounding: true   # pp.35, 45
new_choices:
  path_partition: asymmetric_small_range_-1_to_4 — The packet operand and standard operand have different widths/arrival schedules, so the close-path interval is directional rather than an absolute exponent-difference threshold.   # pp.39, 42
slots:
  round: UNKNOWN   # pp.34-35
  far_align: full_align   # pp.42-44
  near_lz: lza   # pp.40-41
parameters: small path -1 <= e1-e2 <= 4; large path e1-e2 >= 5 or e2-e1 >= 2; alignment magnitude limited to 66 positions; four pipeline stages; first two stages perform addition and last two perform rounding   # pp.35, 39, 42
results: none
errors_and_checks: The two paths produce an input to the rounding phase that is not necessarily the exact sum but rounds to the same IEEE 754 value as the exact sum.   # p.35
conditions: The small path permits a potentially long normalization shift, while the large path requires at most a one-position normalization shift.   # pp.39-44
evidence: Fig. 2 and §§1.4, 3, 3.1, 4, 4.1; Figs. 9-11; pp.35, 39-44

### carry_save_datapath  (role: extends)
mechanism: Borrow-save significands remain redundant across forwarded dependent additions. P/N recodings partially compress the representation before leading-zero anticipation, while ppm/mmp cells implement 3:2 and cascaded 4:2 additions. The first two cycles contain only redundant significand additions. A full-width nonredundant compression occurs in the fourth stage when a standard result retires. (pp.34-35, 37-45)
choices:
  compressor: {3_2, 4_2} [outside domain]   # p.45
  assimilation_point: end_of_chain   # p.45
  accumulator_redundant: true   # pp.34-35, 45
new_choices:
  redundant_encoding: borrow_save — Each digit is encoded as positive and negative bits representing a value in {-1, 0, 1}.   # pp.36-38
  partial_compression_recoding: P_N_ppm_mmp — Half-adder-like P/N recodings and full-adder-like ppm/mmp recodings constrain fraction ranges without complete compression.   # pp.37-39, 45
slots:
  assimilator: UNKNOWN   # pp.35, 45
parameters: 64-digit principal part packet; two-digit carry-round packet restricted to {-2, -1, 0, 1, 2}; 132-digit borrow-save input to the rounding unit; one full-width nonredundant addition in pipeline stage four   # pp.34-36, 45
results: none
errors_and_checks: Partial-compression bounds prove that leading-zero anticipation and constant-width carry-round additions preserve the required normalization ranges.   # pp.41-44
conditions: The carry-round packet arrives at cycle two, so the small path adds it to four low digits and the large path directs it to one of two fixed positions using constant-width adders.   # pp.41-44
evidence: §§1.3, 2.1-2.4, 3.1, 4.2, 5 and Appendix B; Figs. 3, 6-8, 12-13; pp.34-45

## new_families
### packet_forwarding_fp_adder  (domain: fp, closest: two_path, why_not: The two_path family describes exponent-difference datapaths but does not represent split-cycle forwarding of a redundant result or deferred assimilation across dependent operations.)
mechanism: One operand arrives in standard IEEE 754 format. The other arrives as a packet containing sign/exponent, a borrow-save principal significand part, and a late two-digit carry-round part. The pipeline outputs the result sign/exponent/principal part after cycle two and the carry-round packet after cycle three, which permits a dependent operation to start every two cycles. Stage four compresses the redundant value and produces the standard IEEE 754 result. Each intermediate operation remains IEEE rounded even though full-width nonredundant addition is deferred until retirement. (pp.33-35, 37, 45)
choices: operand_interface: {standard_plus_packet}; forwarded_result_delivery: {principal_cycle_2_carry_round_cycle_3}; retirement_format: {IEEE_754_cycle_4}; dependency_interval_cycles: Int[2..2:1]; exception_forwarding_policy: {UNKNOWN}
results:
| metric | value | unit | technology / device | baseline | condition | page |
| effective dependent-operation latency | 2 | cycles | UNKNOWN / 2000 | UNKNOWN | packet result forwarded to the adder or a cooperating multiplier | pp.33, 37 |
| standard-format result latency | 4 | cycles | UNKNOWN / 2000 | UNKNOWN | IEEE 754 result retired to a register | pp.33, 35 |
| estimated stage depth | roughly 15 | logic levels per cycle | UNKNOWN / 2000 | UNKNOWN | four-stage design | pp.34, 45 |
| estimated effective forwarding depth | roughly 30 | logic levels | UNKNOWN / 2000 | UNKNOWN | two-cycle dependent-operation latency | p.34 |
evidence: Abstract, §§1.3-1.4, 2.2, 5; Figs. 2, 4-5; pp.33-37, 45

## space_gaps
* The `two_path.sig_adder` slot cannot name `carry_save_datapath`, although the proposed significand datapaths use borrow-save 3:2/4:2 additions rather than a carry-propagate family.   # pp.34-35, 45
* The `carry_save_datapath.compressor` choice cannot express one design that uses both `3_2` and `4_2` compressors.   # p.45
* The vocabulary lacks a rounding component for a split principal-part/carry-round packet with late nonredundant assimilation.   # pp.34-35, 45-46
* The `two_path.path_threshold` choice cannot express the directional small-path interval -1 <= e1-e2 <= 4.   # pp.39, 42

## open_questions
* The document details only the first two pipeline stages and defers the exact two-stage rounding-unit implementation to reference [8], so the `round` slot remains `UNKNOWN`.   # pp.34-35
* The document reports no fabricated technology, device, area, power, or measured timing result; its timing values are logic-level estimates.   # pp.34, 45
* IEEE exception detection and handling are not addressed, and forwarding may need to be disabled for overflow or underflow.   # p.45
