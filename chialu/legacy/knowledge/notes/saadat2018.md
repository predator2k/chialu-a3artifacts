---
handle: saadat2018
citation: H. Saadat, H. Bokhari, S. Parameswaran, "Minimally Biased Multipliers for Approximate Integer and Floating-Point Multiplication", IEEE Transactions on Computer-Aided Design, vol. 37, no. 11, pp. 2623-2635, 2018
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint8, uint16, fp32]
authority: incremental
pages_read: 12 / 12
---

## summary
The paper proposes MBM, an error-configurable unsigned logarithmic multiplier that adds one constant error-reduction term before output scaling to minimize error bias. The paper also removes leading-one detection/barrel shifting when MBM/DRUM/SSM/MA operate on normalized FP mantissas and constructs approximate fp32 multipliers from the optimized units.

## families
### logarithmic  (role: proposes)
mechanism: MBM applies Mitchell’s linear log/antilog multiplication, then adds c before scaling: c when x1+x2<1 and c/2 when x1+x2≥1. The analytical mean error is −0.08333×2^(k1+k2); hardware approximates 0.08333 as 0.078125=(0.0001010)2. A 7-bit adder and 4-bit 2x1 mux implement the correction. MBM-t truncates t low fractional-log bits and sets the next bit to 1.   # pp.4-5
choices:
  base: mitchell   # pp.3-4
  correction: near_zero_bias_coefficients   # pp.4-5
  mantissa_adder: exact   # p.5
new_choices:
  correction_position: before_output_scaling — avoids separate scaling hardware for the correction term   # p.4
  correction_constant: 0.078125 — hardware approximation of the analytically derived 0.08333 term   # p.4
  fraction_truncation_t: Int[0..N-8:1] — truncates low approximate-log bits for configurable cost/error   # p.5
slots: none
parameters: unsigned N-bit operands; evaluated at N=8 and N=16; MBM-t evaluated for t=1..8 at N=16; single-cycle; 1 GHz   # pp.5-6
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error bias | 0.05 | % | TSMC 45nm / 2018 | accurate 8-bit multiplier | MBM, exhaustive inputs | p.6 |
| mean error | 2.69 | % | TSMC 45nm / 2018 | accurate 8-bit multiplier | MBM | p.6 |
| peak error | 7.81 | % | TSMC 45nm / 2018 | accurate 8-bit multiplier | MBM | p.6 |
| area | 288.4 | µm2 | TSMC 45nm / 2018 | 445.0 µm2 accurate | 8-bit MBM | p.6 |
| power | 21.6 | µW | TSMC 45nm / 2018 | 35.3 µW accurate | 8-bit MBM | p.6 |
| error bias | –0.09 | % | TSMC 45nm / 2018 | accurate 16-bit multiplier | MBM, Monte Carlo | p.6 |
| mean error | 2.58 | % | TSMC 45nm / 2018 | accurate 16-bit multiplier | MBM | p.6 |
| peak error | 7.81 | % | TSMC 45nm / 2018 | accurate 16-bit multiplier | MBM | p.6 |
| area | 686.3 | µm2 | TSMC 45nm / 2018 | 1900.9 µm2 accurate | 16-bit MBM | p.6 |
| power | 47.9 | µW | TSMC 45nm / 2018 | 182.2 µW accurate | 16-bit MBM | p.6 |
| area reduction | 75.0 | % | TSMC 45nm / 2018 | accurate 16-bit multiplier | MBM-8 | p.6 |
| power reduction | 84.3 | % | TSMC 45nm / 2018 | accurate 16-bit multiplier | MBM-8 | p.6 |
| error bias | –0.08 | % | TSMC 45nm / 2018 | accurate 16-bit multiplier | MBM-8 | p.6 |
| mean error | 2.60 | % | TSMC 45nm / 2018 | accurate 16-bit multiplier | MBM-8 | p.6 |
| peak error | 9.36 | % | TSMC 45nm / 2018 | accurate 16-bit multiplier | MBM-8 | p.6 |
| image-filter PSNR | 43 | dB | TSMC 45nm / 2018 | accurate 16-bit multiplication | MBM-8, 7×7 Gaussian filter | p.10 |
errors_and_checks: Error bias is mean relative error; mean error is mean absolute relative error; peak error is peak absolute relative error. The 16-bit MBM variants maintain −0.09% to −0.08% bias and 2.58% to 2.60% mean error as t increases from 0 to 8.   # p.6
conditions: The standalone MBM is unsigned and single-cycle. MBM-t requires t≤(N−1)−7 so the 7-bit correction remains intact. Output-overflow cases bypass correction, and small k1+k2 cases lose correction bits and require special handling.   # p.5
evidence: §III, Fig. 3, Table I, Figs. 4-5, Fig. 10, pp.3-7 and p.10

### sig_mul_then_round  (role: extends)
mechanism: Each fp32 design retains accurate exponent addition and exception logic while replacing the 24-bit mantissa multiplier with optimized MBM/DRUM/SSM/MA. Normalization fixes each mantissa leading one at the MSB, so leading-one detectors/input barrel shifters are removed. In optimized MBM, the characteristic addition is removed and the output barrel shifter becomes 2x1 muxes. The evaluated designs deliberately omit rounding and subnormal support.   # pp.7-9
choices: none
new_choices:
  fixed_hidden_one_optimization: Bool — removes leading-one detection and general shifts for normalized mantissas   # pp.7-8
slots:
  sig_mul: logarithmic [base=mitchell, correction=near_zero_bias_coefficients] [outside slot domain]   # pp.8-9
  exp: exponent_path   # p.8
parameters: fp32; 24-bit significands including hidden bit; 8-bit exponent; single-cycle; 1 GHz; AFMB-t truncation evaluated through t=20   # pp.8-11
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power improvement | 16.1 | × | TSMC 45nm / 2018 | FPM-R fp32 multiplier | AFMB base model | p.9 |
| area improvement | 11.7 | × | TSMC 45nm / 2018 | FPM-R fp32 multiplier | AFMB base model | p.9 |
| power improvement | 57 | × | TSMC 45nm / 2018 | FPM-R fp32 multiplier | maximum AFMB-t design point | p.10 |
| area improvement | 28 | × | TSMC 45nm / 2018 | FPM-R fp32 multiplier | maximum AFMB-t design point | p.10 |
| JPEG PSNR | 27.73 | dB | TSMC 45nm / 2018 | IEEE fp32 PSNR 29.12 dB | AFMB, t=15 | p.11 |
| power improvement | 30.35 | × | TSMC 45nm / 2018 | IEEE fp32 multiplier | AFMB, t=15, JPEG | p.11 |
| area improvement | 19.27 | × | TSMC 45nm / 2018 | IEEE fp32 multiplier | AFMB, t=15, JPEG | p.11 |
| Top-1 error | 41.8 | % | TSMC 45nm / 2018 | fp32 AlexNet 42.8% | AFMB, t=20 | p.11 |
| Top-5 error | 20.2 | % | TSMC 45nm / 2018 | fp32 AlexNet 19.6% | AFMB, t=20 | p.11 |
errors_and_checks: The full FP design space reaches less than 25% peak relative error, 7% mean error, and 4% error bias at up to 57× power and 28× area improvement. Relative error is measured against single-precision output.   # pp.1,9
conditions: Rounding is omitted, subnormals are unsupported, exponent addition remains accurate, and exception logic is unchanged. The method is stated to apply to half/double precision, but only fp32 is implemented.   # pp.8,10
evidence: §V-VII, Figs. 6-9 and 11, Table II, pp.7-11

## new_families
none

## space_gaps
* The logarithmic family needs explicit values for pre-scaling constant correction and normalized-input removal of LOD/barrel-shifter hardware.   # pp.4,7-8
* The sig_mul_then_round.sig_mul slot does not admit the approximate logarithmic family used by AFMB.   # p.8
* The FP family vocabulary lacks values for omitted rounding and unsupported subnormals.   # p.8

## open_questions
* Section III-C says overflow occurs when k1=k2=N, although the earlier leading-one definition bounds k by N−1.   # pp.3,5
* The exact small-(k1+k2) corner-case correction circuit is not specified.   # p.5
