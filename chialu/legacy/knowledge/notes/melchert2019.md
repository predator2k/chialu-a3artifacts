---
handle: melchert2019
citation: J. Melchert, S. Behroozi, J. Li, Y. Kim, "SAADI-EC: A Quality-Configurable Approximate Divider for Energy Efficiency", IEEE Transactions on VLSI Systems, vol. 27, no. 11, pp. 2680-2692, 2019
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint32_dividend, uint16_divisor]
authority: incremental
pages_read: 2680–2692 / 13
---

## summary
SAADI-EC performs approximate binary division by multiplying the dividend by an incrementally refined Taylor-series approximation of the divisor reciprocal. A runtime-selected approximation order trades accuracy for latency/energy, while shift-add error compensation reduces the negative error bias. # p.2681–2684

## families
### approximate_functional  (role: proposes)
mechanism: SAADI-EC normalizes and truncates the operands to n bits, generates successive powers of |x| for x=b−1 with a shared n-bit multiplier, and accumulates the first t+1 terms of R̃t(b)=Σ|x|^i. The same multiplier computes a×R̃t(b), and a barrel shifter denormalizes the quotient. A LUT indexed by t supplies shift amount s, so error compensation computes Q̃t+Q̃t/2^s. Reciprocal iterations may terminate early to trade accuracy for latency/energy. # p.2682–2684
choices:
  method: incremental_taylor_series [outside domain]   # p.2682
  bias_correction: true   # p.2682–2683
  runtime_quality_scaling: true   # p.2681, p.2684
new_choices:
  approximation_width_n: n bits; evaluated at n=[4, 6, 8, …, 16] — sets normalized operand/multiplier width and maximum accuracy   # p.2683, p.2686
  approximation_order_t: 1≤t≤n−1 — runtime control for reciprocal terms/latency/accuracy   # p.2684
  compensation_implementation: shift_add_lut — an n−1-entry LUT selects s for Q̃t+Q̃t/2^s   # p.2683
  pipeline_mode: {iterative_shared, replicated_mac_pipeline} — SAADI-EC-P replicates the multiply-accumulate stage for pipelining   # p.2687
slots:
  none
parameters: Evaluation uses 32-bit dividends/16-bit divisors under the 2K/K constraint; n=[4,6,8,…,16]; effective t range is 1≤t≤n−1; latency is at most t multiplications; the iterative implementation shares one normalizer and one multiplier. SAADI-EC-P has three pipeline stages, n−1 multiply-accumulate copies, fixed t=n−1, and II=1 cycle. # p.2684, p.2686–2687
results:
| metric | value | unit | technology / device | baseline | condition | page |
| average accuracy range | 94.2–99.6 | % | NanGate 45-nm CMOS / 2019 | exact division | n=8, 32-bit/16-bit division, t=1…7 | p.2680, p.2691 |
| latency range | 1–7 | cycles | NanGate 45-nm CMOS / 2019 | none | n=8, 32-bit/16-bit division, t=1…7 | p.2691 |
| latency/energy scaling range | 7 | × | NanGate 45-nm CMOS / 2019 | lowest-latency/energy configuration | n=8, 32-bit/16-bit division | p.2680 |
| energy-delay cost reduction | up to 87 | % less | NanGate 45-nm CMOS / 2019 | other approximate binary dividers at the same accuracy | 8-bit approximation of 32-bit/16-bit division | p.2680 |
| energy per division reduction | 75 | % lower | NanGate 45-nm CMOS / 2019 | n=16 SAADI-EC | n=8 versus n=16, 99% accuracy, three cycles | p.2687 |
| SAADI-EC-P MAE | 0.37 | % | NanGate 45-nm CMOS / 2019 | none | n=8, t=n−1 | p.2687 |
| SAADI-EC-P throughput | 1 | result/cycle | NanGate 45-nm CMOS / 2019 | iterative SAADI-EC | n=8, t=n−1 | p.2687 |
| SAADI-EC-P delay | 1.16 | ns | NanGate 45-nm CMOS / 2019 | none | n=8, t=n−1 | p.2687 |
| SAADI-EC-P energy per result | 3.54 | nJ | NanGate 45-nm CMOS / 2019 | SAADI-EC at 5.72 nJ | n=8, t=n−1 | p.2687 |
| multiply-accumulate energy share | 73.5 | % | NanGate 45-nm CMOS / 2019 | total divider energy | n=16, t=1 | p.2688 |
| multiply-accumulate energy share | 93.9 | % | NanGate 45-nm CMOS / 2019 | total divider energy | n=16, t=15 | p.2688 |
| color-quantization SSIM | higher than 90 | % | MATLAB model / 2019 | 32-bit exact-divider output | k=8, n=8, t=2 | p.2688–2689 |
| color-quantization PSNR range | 27.7–33.2 | dB | MATLAB model / 2019 | 32-bit exact-divider output | four benchmark images, n=8, t=7 | p.2689 |
| color-quantization SSIM range | 84.6–98.7 | % | MATLAB model / 2019 | 32-bit exact-divider output | four benchmark images, n=8, t=7 | p.2689 |
errors_and_checks: The design is approximate and reports MAE/error distributions rather than a worst-case correctness bound. Finite Taylor truncation and internal multiplier/accumulator truncation underapproximate the quotient; operand truncation can have either sign. A per-t compensation factor is selected to minimize MAE over a large input sample, and the simplified shift-add implementation moves the error distribution closer to zero. Arithmetic evaluation uses one million uniformly distributed random dividend/divisor combinations. # p.2684–2686
conditions: The evaluated 2K/K inputs require the K MSBs of the dividend to be smaller than the divisor to prevent overflow. Accuracy saturates because multiplication by |x|≤0.5 retires at least one bit per cycle, so increasing t beyond n−1 adds latency without improving accuracy; n=4 saturates at t=2. Narrower n is more energy-efficient when it can meet the required accuracy. Optimal runtime accuracy selection is application-dependent and is outside the paper’s scope. # p.2684, p.2686–2687
evidence: §III-A–D, Fig. 2, Fig. 3, Table I, Fig. 4–7, §IV-A–E, Table II, Table III, Fig. 8–14, Table V, pp.2682–2691

## new_families
none

## space_gaps
* `approximate_functional.method` lacks `incremental_taylor_series`, which SAADI-EC uses instead of the declared methods. # p.2682
* `approximate_functional` lacks choices for approximation width n, runtime order t, and shift-add/LUT error compensation. # p.2683–2684
* `approximate_functional` lacks a reciprocal-computation multiplier slot, although SAADI-EC shares one n-bit multiplier across power generation and quotient multiplication. # p.2683–2684

## open_questions
* The paper specifies a single-cycle n-bit multiplier but does not identify its multiplier microarchitecture. # p.2683, p.2686
* The paper describes a signed-division extension, while the reported 2K/K evaluation does not state that signed inputs were evaluated. # p.2684, p.2686
