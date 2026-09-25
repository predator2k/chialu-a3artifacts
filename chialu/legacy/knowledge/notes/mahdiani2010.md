---
handle: mahdiani2010
citation: H. R. Mahdiani, A. Ahmadi, S. M. Fakhraie, C. Lucas, "Bio-Inspired Imprecise Computational Blocks for Efficient VLSI Implementation of Soft-Computing Applications", IEEE Transactions on Circuits and Systems I, vol. 57, no. 4, pp. 850-862, 2010
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_DOT_ACC]
formats: [binary_integer]
authority: landmark
pages_read: 850-862 / 13
---

## summary
The paper proposes the Lower-Part-OR Adder (LOA) and Broken-Array Multiplier (BAM), which intentionally approximate binary arithmetic by replacing lower sum logic and omitting multiplier-array cells. The paper reports analytical error behavior and 0.13 CMOS synthesis results, then uses both blocks in a face-recognition neural network and a weighted-plateau-average defuzzifier. The application results preserve the specified output behavior while reducing area/delay relative to precise implementations. 

## families
### lower_part_approximate  (role: proposes)
mechanism: The LOA divides a WL-bit addition into an exact upper part and an approximate LPL-bit lower part. Bitwise OR gates produce the lower result bits. An AND of the two most-significant lower-part input bits supplies the carry into the exact upper sub-adder. The upper sub-adder may use any precise architecture; the synthesized instances use ripple carry. # p.851-853
choices:
  lower_width: LPL; evaluated examples include 1, 2, 4, and 8 [outside domain for nonmultiples of 4]   # p.852-853
  lower_cell: or_gate   # p.852
  carry_to_upper: msb_and   # p.852
new_choices:
  none
slots:
  upper_adder: ripple_carry   # p.853
parameters: WL-bit operands; LPL approximate bits; exact upper width WL-LPL; synthesized across multiple WL/LPL values   # p.851-853
results:
| metric | value | unit | technology / device | baseline | condition | page |
| error probability | about 40 | % | UNKNOWN / 2010 | precise adder of the same WL | LPL=2 | p.852 |
| error probability | about 90 | % | UNKNOWN / 2010 | precise adder of the same WL | LPL=8 | p.852 |
| gate-count reduction | 21 to 31 | gates | 0.13 CMOS / 2010 | precise ripple-carry adder of the same WL | each 1-unit LPL increase, across evaluated WLs | p.853 |
| delay reduction | 0.16 to 0.55 | ns | 0.13 CMOS / 2010 | precise ripple-carry adder of the same WL | each 1-unit LPL increase | p.853 |
errors_and_checks: PE depends on LPL rather than WL. The output error range is nearly symmetric and unbiased, with a slightly negative constant mean error; MSE grows exponentially with LPL. No runtime error detector or correction is provided. # p.852
conditions: Higher LPL reduces area/delay/power but increases imprecision. LOA is unsuitable when the application is sensitive to error frequency regardless of error magnitude. The power reduction is analytical rather than a reported power measurement. # p.852-853
evidence: §III-A; Fig. 1; (1)-(8); Figs. 2-4, p.851-853

### pp_perforation  (role: extends)
mechanism: The BAM starts from a carry-save array multiplier followed by a vector-merging adder. HBL removes cells above a horizontal break, while VBL removes cells to the right of a vertical break; omitted outputs are treated as zero. Signed BAM preserves cells that operate on partial-product sign bits. The same breaking technique is proposed as applicable to Wallace-tree and Booth structures. # p.853-855
choices:
  cell: exact_and   # p.853
  correction: none   # p.853
new_choices:
  horizontal_break_level: integer less than multiplier width — HBL controls the horizontally omitted CSA region and provides coarse area/error tuning   # p.853-854
  vertical_break_level: integer less than multiplier width — VBL controls the right-side omitted CSA region and provides fine area/error tuning   # p.853-854
  sign_cell_policy: {omit_uniformly, preserve_sign_cells} — signed BAM preserves sign-processing cells while unsigned BAM permits their omission   # p.853-854
slots:
  none
parameters: demonstrated 6×6 structure; synthesized 10×10 unsigned BAM; HBL/VBL are zero for a precise array and must be less than operand width for the reported equations; vector-merging adder is ripple carry in synthesis   # p.853-855
results:
| metric | value | unit | technology / device | baseline | condition | page |
| correct results | 100 | % | UNKNOWN / 2010 | precise array multiplier | HBL=0 and VBL=0 | p.854 |
| mean relative error | less than 1 | % | UNKNOWN / 2010 | precise result | HBL=1 or HBL=2 across evaluated WLs | p.854 |
errors_and_checks: BAM always produces a result no greater than the precise product. HBL affects PE/mean error more than VBL. No runtime detection or correction is provided. # p.854
conditions: Higher HBL/VBL reduce area and delay while increasing error. HBL is the coarse control and VBL is the fine control. Signed BAM realizes smaller savings because sign-related cells remain present. BAM power reduction is argued analytically; experimental power results are not reported. # p.853-855
evidence: §III-B; Figs. 5-9; (9)-(15), p.853-855

### approximate_mac_nn  (role: instantiates)
mechanism: A fully sequential three-layer face-recognition network reuses one hardware neuron. The precise datapath contains an array multiplier and ripple-carry adder, while the imprecise datapath substitutes BAM and LOA. Chip-in-the-loop back-propagation adapts weights to the component imprecision. # p.855-858
choices:
  retraining: true   # p.855
new_choices:
  none
slots:
  none
parameters: 32×30 grayscale inputs; eight hidden neurons with 960 inputs each; nine output neurons; WL=9 selected for the smallest precise implementation that recognizes every pattern; one multiplier and one adder on the datapath/critical path   # p.855-857
results:
| metric | value | unit | technology / device | baseline | condition | page |
| delay excess | 30 | % | 0.13 CMOS / 2010 | BIC#1 | precise model, WL=9, both recognize correctly | p.857-858 |
| area excess | 54 | % | 0.13 CMOS / 2010 | BIC#1 | precise model, WL=9, both recognize correctly | p.857-858 |
| area-delay-product excess | 101 | % | 0.13 CMOS / 2010 | BIC#1 | precise model, WL=9, both recognize correctly | p.857-858 |
| critical-path-delay excess | about 20 | % | 0.13 CMOS / 2010 | BIC#2 | precise model, WL=9 | p.858 |
| gate-count excess | 43 | % | 0.13 CMOS / 2010 | BIC#2 | precise model, WL=9 | p.858 |
| area-delay-product excess | 72 | % | 0.13 CMOS / 2010 | BIC#2 | precise model, WL=9 | p.858 |
errors_and_checks: Correct operation requires correct values from all nine output neurons for every training/testing pattern. At WL=9, isolated acceptable bounds are LPL≤4, HBL≤2, and VBL≤6, but the parameters interact and require concurrent simulation. # p.856-857
conditions: The reported efficiency depends on application-level tolerance and chip-in-the-loop training. Increasing one imprecision parameter reduces the allowable values of the others. # p.855-858
evidence: §IV; Table I; Figs. 10-14, p.855-858

## new_families
none

## space_gaps
* `lower_part_approximate.lower_width` excludes documented LPL values such as 1 and 2, although these values are central to the reported tradeoffs. # p.852-853
* `pp_perforation` lacks independent horizontal/vertical cell-break choices and a signed-cell preservation policy needed to describe BAM. # p.853-854
* The vocabulary has no component-composition entry for the LOA/BAM weighted-average defuzzifier, whose datapath contains a multiplier, two adders, and a divider. # p.858-861

## open_questions
* The supplied text omits the rendered contents of several equations, so the exact PE/ME/MSE/MAX/MIN formulas cannot be transcribed.
* The supplied text does not expose the numeric cells of Tables I and II, so the exact BIC#1/BIC#2/BIC#3 parameter combinations and absolute synthesis values remain UNKNOWN.
