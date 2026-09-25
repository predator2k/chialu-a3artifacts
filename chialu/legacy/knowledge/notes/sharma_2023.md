---
handle: sharma_2023
citation: N. Sharma, R. Jain, M. Pokkuluri, S. Patkar, R. Leupers, R. S. Nikhil, "CLARINET: A Quire-Enabled RISC-V-Based Framework for Posit Arithmetic Empiricism", Journal of Systems Architecture, 2023
actual_citation: Niraj N. Sharma, Riya Jain, Mohana Madhumita Pokkuluri, Sachin B. Patkar, Rainer Leupers, Rishiyur S. Nikhil, Farhad Merchant, "CLARINET: A quire-enabled RISC-V-based framework for posit arithmetic empiricism", Journal of Systems Architecture, 2023
status: ok
kind: paper
unit_classes: [VEC_DOT_ACC, other]
formats: [posit8_0, posit16_1, posit24, posit32_2, fp32, fp64]
authority: incremental
pages_read: 16 / 16
---

## summary
Clarinet integrates the parameterized Melodica posit unit and a quire accumulator into an RV32 RISC-V processor while retaining an independent fp32 unit (p.4–5). Melodica supports fused posit multiply/divide accumulation/subtraction, bidirectional posit/fp32 conversion, and quire initialization/readout (p.4–6). FPGA/RTL and application studies quantify resource, latency, and accuracy trade-offs across posit widths (p.8–15).

## families
### posit_quire_mac  (role: proposes)
mechanism: Melodica accumulates fused posit products or quotients into a fixed-point quire sized as N²/2 bits, without intermediate rounding (p.2, p.5–6). The quire is divided into 32-bit segments and updated by a pipelined segmented adder; aligned increment segments enter four-entry FIFOs, and segment zero flags provide fixed-latency leading-zero detection for readout (p.6–7). Quire-writing instructions respond immediately and queue in the pipeline, while a quire read waits for preceding accumulations (p.10, p.14–15).
choices:
  quire_width_bits: [32 [outside domain], 128, 512]   # p.2, p.5
  organization: segmented_pipelined_cpa [outside domain]   # p.7
  op_set: fused_ops_general   # p.4–6
new_choices:
  posit_width_N: [8, 16, 32] — parameter controlling posit and quire widths   # p.5
  exponent_size_es: [0, 1, 2] — maximum posit exponent-field width   # p.5
  quire_segment_width_bits: 32 — width of each pipelined accumulator segment   # p.7
  increment_fifo_entries: 4 — queued increments accepted before a stall   # p.7
slots: none
parameters: N/es configurations (8,0), (16,1), and (32,2); quire widths 32, 128, and 512 bits; 32-bit segments; accumulation depths 1, 4, and 16 stages; FMA.P latencies 6, 9, and 19 cycles respectively; multiplier/divider extraction stage 1 cycle   # p.5–6, p.10–11
results:
| metric | value | unit | technology / device | baseline | condition | page |
| LUT utilization | 12,599 | LUTs | Xilinx KC705 xc7vx485tffg1761-2; 2023 | PERCIVAL PAU: 15,743 LUTs | Clarinet-P32.2-DIV including PRF/decode, 100 MHz target | p.14 |
| FF utilization | 3342 | FFs | Xilinx KC705 xc7vx485tffg1761-2; 2023 | PERCIVAL PAU: 4057 FFs | Clarinet-P32.2-DIV including PRF/decode | p.14 |
| synthesis frequency | 100 | MHz | Xilinx KC705 xc7vx485tffg1761-2; 2023 | PERCIVAL PAU: 50 MHz | timing met with +0.99 ns slack; baseline slack +0.177 ns | p.14 |
| FMA.P latency, posit8 | 6 | cycles | UNKNOWN; 2023 | FMADD.S: 12 cycles | accumulation result remains in quire | p.10 |
| FMA.P latency, posit16 | 9 | cycles | UNKNOWN; 2023 | FMADD.S: 12 cycles | accumulation result remains in quire | p.10 |
| FMA.P latency, posit32 | 19 | cycles | UNKNOWN; 2023 | FMADD.S: 12 cycles | accumulation result remains in quire | p.10 |
| application speedup | up to 1.5x | speedup | Xilinx FPGA, device UNKNOWN; 2023 | Flute floating-point implementation | quire pipeline used effectively | p.15 |
| xGivens accuracy, q32 | 8.8 | accurate decimal digits | UNKNOWN; 2023 | fGivens: 6.79 digits | SoftPosit study | p.8–9 |
| optical-flow RMS error | 1.3415103400712E−09 | RMS error | UNKNOWN; 2023 | f32: 1.9613096794474E−09 | p32-q32-norm, Rubik’s cube dataset | p.12 |
| optical-flow execution | 25.6 million | cycles | Verilator RTL, device UNKNOWN; 2023 | f32: 21 million cycles | three 240 × 240 images, 5 × 5 kernel | p.12 |
errors_and_checks: The quire accumulates without intermediate rounding, and posit readout/conversions use round-to-nearest-even (p.2, p.4–6). The document reports numerical error against fp64 references but no fault model/detection coverage/false-alarm behavior (p.8–9, p.12).
conditions: Long uninterrupted accumulation sequences hide Melodica pipeline latency, while frequent quire reads reduce the advantage (p.10–11). The 32-bit quire pipeline needs 16 accumulation stages and is less tolerant of short accumulation sequences (p.11). The iterative divider has variable data-dependent latency and is not pipelined, so its worst-case latency may outweigh queued-accumulation benefits (p.10). Quire resource use grows quadratically in FFs and approaches O(N³) in LUTs (p.13). Saving the quire through posit conversion during a context switch loses accuracy (p.5).
evidence: §2.1.1; §3.2.1; §3.3; §4; §4.1; Tables 3, 6, and 7; Figs. 3, 4, and 13–15.

### posit_ieee_interop  (role: proposes)
mechanism: Clarinet keeps fp32 and posit values as independent types with separate FPR and PRF register files and parallel FPU/Melodica functional units (p.4). FCVT.P.S and FCVT.S.P perform bidirectional RNE conversion, allowing a posit/quire kernel to be inserted between floating-point computations (p.4–5). PMV instructions transfer uninterpreted posit bits between the integer and posit register files because the C compiler lacks a primitive posit type (p.4–5, p.8).
choices:
  interop_style: boundary_converters   # p.4–5
  conversion_direction: bidirectional   # p.4
  quire_present: true   # p.4–5
new_choices:
  register_file_organization: separate_fpr_prf — floating-point and posit values occupy independent register files   # p.4
slots: none
parameters: 32 PRF registers of width N; 32-bit float-width; FCVT.P.S/FCVT.S.P use RNE; RV32IMAFC base processor   # p.4–5
results:
| metric | value | unit | technology / device | baseline | condition | page |
| conversion overhead | 2N | instructions | UNKNOWN; 2023 | native posit data: 0 additional conversions | N-iteration legacy loop with two fp32-to-posit conversions per iteration | p.5 |
errors_and_checks: Conversions use RNE; no conversion-error bound or hardware checker is reported (p.4).
conditions: Interoperation permits selected legacy kernels to use quire accumulation while the surrounding application remains fp32 (p.4–5). Per-iteration conversions are unpipelined and can exceed posit-compute cycles (p.10). Inline assembly prevents compiler backend optimizations, and the current unit lacks posit square root, which forces fp32 conversion in xGivens (p.8, p.10–11).
evidence: §3.1; §3.2.3; §3.2.5–3.2.6; §5.1–5.2; Tables 2 and 5; Figs. 2, 5–7, and 9–10.

## new_families
none

## space_gaps
* `posit_quire_mac.organization` needs `segmented_pipelined_cpa`, because Melodica uses a segmented carry-propagate accumulator rather than the declared organizations (p.6–7).
* `posit_quire_mac.quire_width_bits` excludes the reported 32-bit quire and the N²/2 parameterization (p.2, p.5).
* `posit_quire_mac.op_set` does not explicitly distinguish fused multiply-accumulate from fused divide-accumulate/subtract (p.4–6).
* `posit_ieee_interop` lacks a register-file-organization choice for separate FPR/PRF coexistence (p.4).

## open_questions
* Table 4 names p24-q24 Clarinet synthesis/latency studies, but §4 and Table 8 list hardware configurations only for N/es values (8,0), (16,1), and (32,2).
* The iterative integer divider’s recurrence and radix are not identified, so no divider family can be assigned without guessing (p.6).
* Figs. 13–15 provide additional utilization bars whose exact numeric values are not printed in the document text.
