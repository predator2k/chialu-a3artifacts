---
handle: metzgen_2004
citation: P. Metzgen, "A High Performance 32-bit ALU for Programmable Logic", Proc. ACM/SIGDA International Symposium on FPGAs, pp. 61-70, 2004
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int32, int16]
authority: incremental
pages_read: 61-70 / 10 pages
---

## summary
The document presents the arithmetic/logic/byte-extraction datapath used in the Altera NIOS 2.0 soft processor and maps the datapath to Apex 20KE Logic Elements. The design combines AdderUnit and LogicUnit results with XOR, retimes their registers, and integrates forwarding logic to reduce area and delay. A two-cycle 32-bit rotate-and-mask barrel shifter reuses the LogicUnit byte rotator.

## families
### fpga_carry_chain  (role: instantiates)
mechanism: The Apex arithmetic-mode LE implements sum and carry functions from the same three inputs, with each carry-out feeding the next LE. The 32-bit AdderUnit uses 32 LEs; synchronous clear forces zero, and synchronous load bypasses addition with OpB.
choices:
  chain_segment_length: 32   # p.63, p.66
  prefix_over_chain: false   # p.66
new_choices:
  register_control_use: synchronous_clear_zero / synchronous_load_OpB_bypass — uses LE register controls to implement AdderUnit functions without extra multiplexers   # p.66
slots:
  none
parameters: 32-bit adder; one LE per bit; 5.0ns estimated adder delay   # p.63, p.66
results:
| metric | value | unit | technology / device | baseline | condition | page |
| adder area | 32 | LEs | Altera Apex 20KE FPGA / 2004 | none | complete 32-bit AdderUnit | p.66 |
| 32-bit adder delay | 5.0 | ns | Altera Apex 20KE FPGA / 2004 | none | approximate longest delay in Table 1 | p.63 |
| ALU critical-path delay | 11.5 | ns | Altera Apex 20KE FPGA / 2004 | none | RB through forwarding and the 32-bit adder | p.67 |
| estimated ALU fmax | 87 | MHz | Altera Apex 20KE FPGA / 2004 | none | 32-bit critical path through the adder | p.67 |
errors_and_checks: none
conditions: The 32-bit ALU crosses MegaLab boundaries because 256 LEs exceed one 160-LE MegaLab, so the timing model assumes 2.5ns inter-MegaLab routing. # p.66-p.67 The 16-bit implementation fits within one MegaLab, which reduces critical routing delay to 1.0ns. # p.68
evidence: §2.3; Table 1; Figures 5, 8, and 10; §3.2-3.4

### barrel_mux_tree  (role: instantiates)
mechanism: A single right rotator implements both directions; a left shift by N rotates right by 32-N. Three stages rotate by 0/2/4/6 bits, then 0/1 bit, then 0/8/16/24 bits. The final stage reuses the LogicUnit byte rotator.
choices:
  stage_radix: mixed 4/2/4 [outside domain]   # p.68
  direction_handling: amount_negation   # p.68
  stage_order: 2/4/6-bit stage, then 1-bit stage, then 8/16/24-bit stage [outside domain]   # p.68
new_choices:
  final_stage_reuse: LogicUnit byte rotator — avoids implementing the final rotation stage as additional logic   # p.68
slots:
  none
parameters: 32-bit bidirectional shifts; three rotation stages; two cycles; 3 LEs per bit of additional logic   # p.68-p.69
results:
| metric | value | unit | technology / device | baseline | condition | page |
| additional barrel-shifter area | 96 | LEs | Altera Apex 20KE FPGA / 2004 | 256-LE ALU datapath | full 32-bit barrel shifting | p.69 |
| barrel-shifter latency | 2 | cycles | Altera Apex 20KE FPGA / 2004 | NIOS 1.1 early-exit shifter used up to 5 cycles | every shift amount | p.68 |
errors_and_checks: none
conditions: Every shift takes two cycles, and the barrel shifter does not reduce processor fmax. # p.68 NIOS 1.1 required separate left/right shifters and used one to five cycles for shifts through 31 bits. # p.68
evidence: Figure 13; §3.5; §5

### masked_merged  (role: instantiates)
mechanism: The first shift cycle constructs a mask and partially rotates OpA. The second cycle reuses the byte rotator, ANDs the fully rotated value with the mask in LogicUnit, and uses AdderUnit for signed-right-shift extension.
choices:
  merge_style: AND mask [outside domain]   # p.68
new_choices:
  sign_extension_source: AdderUnit mask — the same mask supplies signed-right-shift extension when the source sign is negative   # p.68
slots:
  rotator: barrel_mux_tree [stage_radix=mixed 4/2/4 [outside domain]]   # p.68
parameters: 32-bit mask; two-cycle operation; left/right/logical/signed shifts   # p.68
results:
| metric | value | unit | technology / device | baseline | condition | page |
| fmax impact | 0 | none | Altera Apex 20KE FPGA / 2004 | ALU without barrel shifter | paper reports no reduction in processor fmax | p.68 |
errors_and_checks: none
conditions: The second cycle forwards a dummy all-ones AluResult to force the OpA forwarding logic while FirstStageShift supplies the partially rotated operand. # p.68
evidence: Figure 13; §3.5

### speculative_variable_latency  (role: proposes)
mechanism: The proposed adder splits the 32-bit carry chain into lower and upper 16-bit adders. Scheme #3 guesses the carry between the halves and stalls to correct AluResult only when the guess is wrong.
choices:
  speculation_window: 16   # p.69
  recovery: extra_cycle_correction   # p.69
new_choices:
  boundary_carry_prediction: predicted carry between lower and upper 16-bit adders — determines whether correction is required   # p.69
slots:
  base_adder: fpga_carry_chain [chain_segment_length=16]   # p.69
parameters: two 16-bit adder halves; projected 9.0ns critical path; variable correction latency   # p.69
results:
| metric | value | unit | technology / device | baseline | condition | page |
| projected critical-path delay | 9.0 | ns | Altera Apex 20KE FPGA / 2004 | 11.5ns unsplit path | split 32-bit adder | p.69 |
| projected fmax | 111 | MHz | Altera Apex 20KE FPGA / 2004 | 87MHz unsplit ALU | split 32-bit adder before correction overhead | p.69 |
| projected fmax | 110 | MHz | Altera Apex 20KE FPGA / 2004 | 87MHz unsplit ALU | conclusion’s summary of the three split-adder schemes | p.69 |
errors_and_checks: Mispredicted boundary carries are detected and corrected by stalling; no error rate or false-alarm rate is reported. # p.69
conditions: Subtractions often produce a boundary carry of 1, so the paper requires generalized carry-bit speculation rather than always predicting zero. # p.69 Loop counters and array pointers that remain below 65536 are expected qualitatively to make carry prediction close to 100% accurate. # p.69 The schemes are further work rather than implemented results. # p.69
evidence: §4; §5

## new_families
### retimed_xor_merged_alu  (domain: other, closest: masked_merged, why_not: masked_merged covers rotate/mask functions rather than fusion of arithmetic, logic, extraction, registers, and forwarding)
mechanism: AdderUnit and LogicUnit operate together, and AluResult is their XOR rather than a multiplexed unit output. Registers are retimed before the XOR, and copies of the XOR are placed at forwarding-multiplexer inputs. Byte selection, operand complementation/zeroing, synchronous register controls, and the adder jointly implement arithmetic/logical/extraction/sign-extension instructions.
choices:
  result_combination: XOR   # p.64
  output_registering: retimed_before_XOR   # p.65
  forwarding_fusion: XOR_replicated_at_forwarding_inputs   # p.65
  opb_forwarding: parameterized_enabled_or_disabled   # p.69
  extraction_granularity: byte_and_16_bit_word   # p.64-p.65
results:
| metric | value | unit | technology / device | baseline | condition | page |
| datapath area | 256 | LEs | Altera Apex 20KE FPGA / 2004 | none | 32-bit ALU without barrel-shifter addition | p.66 |
| achieved fmax | 90 | MHz | Altera Apex 20KE FPGA / 2004 | 87MHz timing estimate | real place-and-route | p.67 |
| optimized full ALU area | 320 | LEs | Altera Apex 20KE FPGA / 2004 | none | full barrel shifter with OpB forwarding removed | p.69 |
| optimized full ALU fmax | 91 | MHz | Altera Apex 20KE FPGA / 2004 | 87MHz before OpB-forwarding removal | 11.0ns critical path | p.69 |
| 16-bit ALU area | 128 | LEs | Altera Apex 20KE FPGA / 2004 | none | fits within one 160-LE MegaLab | p.68 |
| achieved 16-bit processor fmax | 120 | MHz | Altera Apex 20KE FPGA / 2004 | 150MHz ALU timing estimate | program-control unit limits the processor | p.68 |
| NIOS 2.0 processor area | 1200 | LEs | Altera Apex 20KE FPGA / 2004 | NIOS 1.1: 2400 LEs; 50% size reduction | entire 32-bit processor | p.61 |
| NIOS 2.0 processor fmax | 85 | MHz | Altera Apex 20KE FPGA / 2004 | NIOS 1.1: 50MHz; 70% improvement | entire 32-bit processor | p.61 |
evidence: Figures 6-8 and 14; Table 2; §3.1-3.3; §3.6-3.7; §5

## space_gaps
* `barrel_mux_tree.stage_radix` and `stage_order` cannot represent the mixed 4/2/4 stage sequence used by the design. # p.68
* `masked_merged.merge_style` lacks a rotate-then-AND-mask value with AdderUnit-based sign extension. # p.68
* `fpga_carry_chain` lacks choices for synchronous-clear/load reuse and mapping sum/carry functions within one FPGA LE. # p.66
* The vocabulary lacks an ALU-level family for XOR-merging arithmetic/logic/extraction outputs and retiming that merge into forwarding logic. # p.64-p.66

## open_questions
* The merge pass must distinguish the 256-LE base datapath achieving 90MHz from the 320-LE barrel-shifter configuration reported at 91MHz. # p.67, p.69
* The document does not quantify the extra NOP rate caused by disabling OpB forwarding. # p.69
