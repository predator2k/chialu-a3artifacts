---
handle: vahdat2019
citation: S. Vahdat, M. Kamal, A. Afzali-Kusha, M. Pedram, "TOSAM: An Energy-Efficient Truncation- and Rounding-Based Scalable Approximate Multiplier", IEEE Transactions on VLSI Systems, vol. 27, no. 5, pp. 1161-1173, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [int8, int16, int32]
authority: incremental
pages_read: 13 / 13
---

## summary
TOSAM truncates operands relative to their leading-one positions and rounds the reduced fractional operands to odd midpoints before a small fixed-width multiplication. The design supports signed/unsigned multiplication and configurable accuracy modes while keeping its arithmetic core nearly independent of the original operand width. Reported 32-bit unsigned implementations improve delay, area, and energy by up to 41%, 89%, and 98% against an exact Wallace multiplier. # p.1, p.3–4, p.8

## families
### dynamic_segment  (role: proposes)
mechanism: Each operand is factored as \(N=2^kX\), with \(Y=X-1\). TOSAM retains \(t\) bits of each \(Y\), approximates each multiplicative \(Y\) term with an \(h+1\)-bit midpoint obtained by retaining \(h\) bits and appending “1,” computes \(1+(Y_A)_t+(Y_B)_t+(Y_A)_{APX}(Y_B)_{APX}\), and shifts the result by \(k_A+k_B\). Signed operation uses approximate absolute values followed by sign restoration. # p.3–4
choices:
  segment_select: dynamic_leading_one_rounded # p.3
  unbiasing: round_and_correct # p.3
new_choices:
  truncation_width_t: positive integer — number of retained bits in the additive truncated operands \((Y_A)_t\) and \((Y_B)_t\) # p.3
  rounding_width_h: positive integer — number of retained bits before appending “1” to form each \(h+1\)-bit odd midpoint # p.3
  sign_handling: {unsigned_direct, approximate_absolute_then_sign_restore} — unsigned hardware omits the Approximate Absolute Unit; signed hardware restores the output sign # p.3–4
slots:
  core_multiplier: behavioral_star [operand_width=h+1] [outside domain] # p.3–4
parameters: unsigned/signed 8-, 16-, and 32-bit operands; evaluated TOSAM configurations include (h,t)=(0,2), (0,3), (1,5), (2,6), (3,7), (4,8), and (5,9); \(t=h+4\) is selected for \(h>0\), while \(t=3\) is selected for \(h=0\) # p.5–9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| partial products retained | 31 | partial products | UNKNOWN; 2019 | exact 16-bit multiplier: 256 partial products | TOSAM(3,7), approximately 88% reduction | p.3 |
| absolute relative error | 0.99 | % | UNKNOWN; 2019 | exact product 29 190 802 | 16-bit TOSAM(3,7), A=11761, B=2482 | p.4 |
| MARE range | 11%–0.3% | % | 45-nm Nangate; 2019 | exact multiplier | evaluated TOSAM configurations | p.1 |
| delay improvement | up to 32% | % | 45-nm Nangate; 2019 | exact unsigned 8-bit multiplier | unsigned 8-bit TOSAM | p.6 |
| area improvement | up to 56% | % | 45-nm Nangate; 2019 | exact unsigned 8-bit multiplier | unsigned 8-bit TOSAM | p.6 |
| energy improvement | up to 77% | % | 45-nm Nangate; 2019 | exact unsigned 8-bit multiplier | unsigned 8-bit TOSAM | p.6 |
| speed improvement | up to 39% | % | 45-nm Nangate; 2019 | exact unsigned 16-bit Wallace multiplier | unsigned 16-bit TOSAM | p.7 |
| area improvement | up to 81% | % | 45-nm Nangate; 2019 | exact unsigned 16-bit Wallace multiplier | unsigned 16-bit TOSAM | p.7 |
| energy improvement | up to 95% | % | 45-nm Nangate; 2019 | exact unsigned 16-bit Wallace multiplier | unsigned 16-bit TOSAM | p.7 |
| delay improvement | 41% | % | 45-nm Nangate; 2019 | exact unsigned 32-bit Wallace multiplier | TOSAM(0,2) | p.8 |
| power improvement | 97% | % | 45-nm Nangate; 2019 | exact unsigned 32-bit Wallace multiplier | TOSAM(0,2) | p.8 |
| area improvement | 89% | % | 45-nm Nangate; 2019 | exact unsigned 32-bit Wallace multiplier | TOSAM(0,2) | p.8 |
| energy improvement | 98% | % | 45-nm Nangate; 2019 | exact unsigned 32-bit Wallace multiplier | TOSAM(0,2) | p.8 |
| average energy improvement | 95% | % | 45-nm Nangate; 2019 | exact unsigned 32-bit Wallace multiplier | TOSAM(0,2) through TOSAM(5,9) | p.8 |
| average area improvement | 85% | % | 45-nm Nangate; 2019 | exact unsigned 32-bit Wallace multiplier | TOSAM(0,2) through TOSAM(5,9) | p.8 |
| JPEG PSNR reduction | 1.39 | dB | 45-nm Nangate; 2019 | exact signed 16-bit multiplier | maximum reported reduction, Lena with TOSAM(0,2) | p.10 |
| JPEG SSIM reduction | 0.012 | SSIM | 45-nm Nangate; 2019 | exact signed 16-bit multiplier | maximum reported reduction, Baboon with TOSAM(0,2) | p.10 |
| DCT energy improvement | up to 77% | % | 45-nm Nangate; 2019 | exact signed 16-bit multiplier | JPEG encoder | p.10–11 |
| classifier energy improvement | up to 77% | % | 45-nm Nangate; 2019 | exact signed 16-bit multiplier | 50-hidden-neuron MNIST network | p.11 |
errors_and_checks: RE is \((P_{app}-P)/P\); ARE is \(|RE|\). TOSAM exhibits an almost normal error distribution with near-zero MRE. Accuracy is reported with maxARE, MRE, MARE, VARE, max_NED, and NED; one million uniform random input pairs are used except for exhaustive 65 536-input evaluation at 8 bits. # p.5–6
conditions: Accuracy depends strongly on \(h\), with MARE almost halved when \(h\) increases by one, and weakly on operand width. Increasing \(t\) has diminishing accuracy benefit after \(t=h+4\) for \(h>0\). Hardware gains increase with operand width because the TOSAM calculation core remains unchanged for a fixed accuracy level while exact partial-product count grows quadratically. Signed operation requires approximate absolute-value generation, which may reduce speed. The intended uses are error-resilient image processing/classification workloads. # p.3, p.5–6, p.9–11
evidence: §III–V; Figs. 1–8; Tables I–II; §VI.A–B; Tables III–VIII and X–XII # p.3–11

### accuracy_configurable  (role: extends)
mechanism: The configurable implementation provisions truncation, shifting, reduction, and final addition for the largest \(h,t\) pair. Mode signals power-gate unused adders/AND gates, force selected final-adder inputs and output bits to zero, and select the partial-product subset for the active accuracy level. # p.4–5
choices:
  mode_count: 3 # p.4
  reconfig_grain: truncation_width # p.4–5
  power_gate_unused: true # p.4–5
new_choices:
  mode_parameter_pairs: {(0,2), (2,6), (5,9)} — T2, T6, and T9 select fixed \((h,t)\) pairs # p.4
slots:
  none
parameters: 32-bit; modes T2/T6/T9; largest hardware dimensions h=5 and t=9; 9-bit final adder # p.4, p.9
results:
| metric | value | unit | technology / device | baseline | condition | page |
| operating modes | 3 | modes | 45-nm HSPICE; 2019 | fixed TOSAM | T2, T6, and T9 | p.9 |
errors_and_checks: Accuracy is selected by the operating mode; no runtime error detector or correction mechanism is reported. # p.4–5
conditions: T2 provides the highest speed and lowest power among the three modes. All units must be sized for the largest desired \(h,t\), so inactive arithmetic is power-gated in lower-accuracy modes. # p.4–5, p.9
evidence: §IV; Fig. 6; §VI.A.4; Table IX # p.4–5, p.9

## new_families
none

## space_gaps
* `dynamic_segment` needs separate `truncation_width_t` and `rounding_width_h` choices because TOSAM uses two independently meaningful retained widths. # p.3
* `dynamic_segment.core_multiplier` admits adder families rather than multiplier families, while TOSAM explicitly uses a small fixed-width multiplication core. # p.3–4
* `accuracy_configurable.reconfig_grain` lacks a value for jointly selecting truncation/rounding widths and partial-product reduction hardware. # p.4–5

## open_questions
* The numeric cells of Tables I–XII are not legible in the supplied transcription, so only values repeated in the surrounding prose are recorded.
* The paper calls the appended-“1” midpoint operation rounding to the nearest odd number, but it does not map that operation explicitly to the vocabulary’s `round_and_correct` term.
