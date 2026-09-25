---
handle: zervakis2016
citation: G. Zervakis, K. Tsoumanis, S. Xydis, D. Soudris, K. Pekmestzi, "Design-Efficient Approximate Multiplication Circuits Through Partial Product Perforation", IEEE Transactions on VLSI Systems, vol. 24, no. 10, pp. 3105-3117, 2016
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU]
formats: [uint16, uint32, uint64, uint128, Q0.32]
authority: landmark
pages_read: 1-13 / 13
---

## summary
The document proposes partial product perforation, which omits \(k\) successive partial products starting at position \(j\) in SPP- or MBE-based multipliers. The document derives bounded error expressions, adds two operand-swapping correction methods, and explores 1376 configurations across 16 multiplier architectures. Perforation reduces power by up to 50%, area by 45%, and critical delay by 35% at NMED below \(10^{-3}\). # p.2, p.3, p.7, p.8

## families
### pp_perforation  (role: proposes)
mechanism: The multiplier omits generation and accumulation of \(k\) successive partial products beginning with partial product \(j\). Each omitted SPP removes \(n\) full adders, while the reduced operand count can also reduce tree depth. The notation D[j,k,c] identifies the reduction architecture, first omitted row, omitted-row count, and SPP/MBE generation. Two optional corrections swap operands after comparing either the perforated \(k\)-bit fields \(x_A,x_B\) or the complete operands \(A,B\). # p.3, p.5-p.6
choices:
  perforated_rows: 1..min(n-j,n-1) [outside domain]   # p.3
  cell: exact_and   # p.3
  correction: {none, compare_xA_xB_swap [outside domain], compare_A_B_swap [outside domain]}   # p.5-p.6
new_choices:
  first_perforated_row: Int[0..n-1] — \(j\) is the order of the first omitted partial product.   # p.3
  partial_product_generation: {SPP, MBE} — \(c=s\) selects simple partial products and \(c=m\) selects modified Booth encoding.   # p.3
slots:
  none
parameters: \(j\in[0,n-1]\); \(k\in[1,\min(n-j,n-1)]\); 16-bit unsigned implementations; 16 architectures and 1376 configurations; 2 ns relaxed synthesis period; width-scaling study from 16 to 128 bits.   # p.3, p.7, p.11
results:
| metric | value | unit | technology / device | baseline | condition | page |
| power reduction | up to 50 | % | TSMC 65-nm / 2016 | respective exact design | 16-bit, NMED < \(10^{-3}\) | p.8 |
| area reduction | up to 45 | % | TSMC 65-nm / 2016 | respective exact design | 16-bit, NMED < \(10^{-3}\) | p.8 |
| critical-delay reduction | up to 35 | % | TSMC 65-nm / 2016 | respective exact design | 16-bit, NMED < \(10^{-3}\) | p.8 |
| power saving | up to 49 | % | TSMC 65-nm / 2016 | exact Dadda 4:2 | selected SPP configurations with Method 1 | p.8 |
| area reduction | up to 40 | % | TSMC 65-nm / 2016 | exact Dadda 4:2 | selected SPP configurations with Method 1 | p.8 |
| NMED | at most \(6.5\times10^{-4}\) | ratio | TSMC 65-nm / 2016 | exact product | selected SPP configurations with Method 1 | p.8 |
| MRED | up to \(1.1\times10^{-2}\) | ratio | TSMC 65-nm / 2016 | exact product | selected SPP configurations with Method 1 | p.8 |
| power saving | up to 47 | % | TSMC 65-nm / 2016 | exact Dadda 4:2 | selected MBE configurations with Method 1 | p.8 |
| area reduction | up to 38 | % | TSMC 65-nm / 2016 | exact Dadda 4:2 | selected MBE configurations with Method 1 | p.8 |
| NMED | \(1.8\times10^{-3}\) | ratio | TSMC 65-nm / 2016 | exact product | selected MBE configurations with Method 1 | p.8 |
| MRED | \(2.5\times10^{-2}\) | ratio | TSMC 65-nm / 2016 | exact product | selected MBE configurations with Method 1 | p.8 |
| power reduction | 21 | % | TSMC 65-nm / 2016 | exact 16-bit Dadda 4:2 | NMED ≤ \(10^{-4}\) | p.11 |
| area reduction | 31 | % | TSMC 65-nm / 2016 | exact 16-bit Dadda 4:2 | NMED ≤ \(10^{-4}\) | p.11 |
| power reduction | 74 | % | TSMC 65-nm / 2016 | exact 128-bit Dadda 4:2 | NMED ≤ \(10^{-4}\) | p.11 |
| area reduction | 91 | % | TSMC 65-nm / 2016 | exact 128-bit Dadda 4:2 | NMED ≤ \(10^{-4}\) | p.11 |
| NMED | \(1.95\times10^{-3}\) | ratio | TSMC 65-nm / 2016 | exact product | 16-bit, 50% power saving | p.11 |
| MRED | \(2.61\times10^{-2}\) | ratio | TSMC 65-nm / 2016 | exact product | 16-bit, 50% power saving | p.11 |
| NMED | \(1.73\times10^{-18}\) | ratio | TSMC 65-nm / 2016 | exact product | 128-bit, 50% power saving | p.11 |
| MRED | \(2.05\times10^{-16}\) | ratio | TSMC 65-nm / 2016 | exact product | 128-bit, 50% power saving | p.11 |
| geometric-mean PSNR | 85.95 | dB | TSMC 65-nm / 2016 | accurate multiplier output | Dadda4:2[1,5,s], no correction | p.10 |
| detected edges | 91.04 | % | TSMC 65-nm / 2016 | accurate multiplier output | Canny, Dadda4:2[1,5,s], no correction | p.10 |
| geometric-mean PSNR | 89.93 | dB | TSMC 65-nm / 2016 | accurate multiplier output | Dadda4:2[3,4,s], no correction | p.10 |
| detected edges | 84.79 | % | TSMC 65-nm / 2016 | accurate multiplier output | Canny, Dadda4:2[3,4,s], no correction | p.10 |
errors_and_checks: For SPP, \(ED(A,B)=A2^j x_B\), \(x_B=\lfloor B/2^j\rfloor\bmod 2^k\), and under uniform inputs \(NMED=2^j(2^k-1)/(4(2^n-1))\). The error is bounded and predictable from \(j,k\) and the operand PDFs; no fault checker is provided.   # p.4
conditions: The optimal \(j,k\) pair depends on the error constraint and operand distribution; correlated audio inputs produce Pareto points with \(j=0,2,6,15\), while uniform inputs produce points with \(j=0,1\). Signed multiplication is handled similarly, except the last partial product is not perforated. Larger widths provide greater savings for the same NMED. Correction by swapping cannot improve squaring because both multiplicands are equal.   # p.4-p.5, p.7, p.11
evidence: §III-A-B, Fig. 1-Fig. 4, §IV, Fig. 5-Fig. 7, §V, Fig. 8-Fig. 12, Table II.   # p.3-p.11

### error_analysis_quality  (role: extends)
mechanism: The analysis derives ED/MED/NMED/RED/MRED directly from the omitted partial products and the operand PDFs. Closed forms are given for uniform inputs, while equation (6) supports other PDFs. Method 1 compares \(x_A,x_B\); Method 2 compares \(A,B\). # p.4-p.6
choices:
  metric: {nmed, mred, med [outside domain], ed [outside domain], red [outside domain]}   # p.4
  model: analytical_pmf   # p.4
new_choices:
  none
slots:
  none
parameters: Uniform \(n\)-bit operands for closed-form equations; arbitrary operand PDFs through weighted summation.   # p.4
results:
| metric | value | unit | technology / device | baseline | condition | page |
| NMED reduction | 30 | % average | UNKNOWN / 2016 | uncorrected perforation | Method 1, 16-bit, all \(j,k\) | p.6 |
| MRED reduction | 24 | % average | UNKNOWN / 2016 | uncorrected perforation | Method 1, 16-bit, all \(j,k\) | p.6 |
| NMED reduction | 26 | % average | UNKNOWN / 2016 | uncorrected perforation | Method 2, 16-bit, all \(j,k\) | p.6 |
| MRED reduction | 50 | % average | UNKNOWN / 2016 | uncorrected perforation | Method 2, 16-bit, all \(j,k\) | p.6 |
| critical-delay overhead | 13 | % | TSMC 65-nm / 2016 | accurate Dadda 4:2 | Method 1, \(j=1,k=1..8\) | p.6 |
| power saving | 26 | % average | TSMC 65-nm / 2016 | accurate Dadda 4:2 | Method 1, \(j=1,k=1..8\) | p.6 |
| area saving | 20 | % average | TSMC 65-nm / 2016 | accurate Dadda 4:2 | Method 1, \(j=1,k=1..8\) | p.6 |
| critical-delay overhead | 20 | % | TSMC 65-nm / 2016 | accurate Dadda 4:2 | Method 2, \(j=1,k=1..8\) | p.6 |
| power saving | 26 | % average | TSMC 65-nm / 2016 | accurate Dadda 4:2 | Method 2, \(j=1,k=1..8\) | p.6 |
| area saving | 17 | % average | TSMC 65-nm / 2016 | accurate Dadda 4:2 | Method 2, \(j=1,k=1..8\) | p.6 |
errors_and_checks: The equations characterize arithmetic error rather than hardware faults. Method 1 favors NMED and uses a \(k\)-bit comparator; Method 2 favors MRED and uses an \(n\)-bit comparator.   # p.6
conditions: Uniform-input closed forms must be recomputed from equation (6) for application-specific PDFs. Method selection depends on whether absolute or relative error matters.   # p.4, p.6
evidence: §III-B, equations (4)-(30), Fig. 2-Fig. 4.   # p.4-p.6

## new_families
none

## space_gaps
* `pp_perforation.perforated_rows` lacks the first-row position \(j\), although \(j\) materially changes error and Pareto placement.   # p.3-p.5
* `pp_perforation.correction` lacks operand swapping based on \(x_A,x_B\) or complete \(A,B\).   # p.5-p.6
* `pp_perforation` lacks the SPP/MBE partial-product-generation choice.   # p.3
* `error_analysis_quality.metric` lacks ED/MED/RED, which the document analyzes alongside NMED/MRED.   # p.4

## open_questions
* Table II cell values are not legible in the supplied document text, so only application results stated in prose are recorded.
