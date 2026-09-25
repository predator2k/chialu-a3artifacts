# exp10 results within the first K=10 iterations (runs keep going; min iterations over all runs = 10)

| target | method | runs | start (area/delay) | best delay @ area<=start | best area @ delay<=start | ΔHV vs start (%) | designs dominating start |
|---|---|---|---|---|---|---|---|
| fp_alu_cmp | adaevolve | 3 | 7284/4385 | -18.0% ± 6.1 | -12.4% ± 5.7 | +547.3 ± 257.7 | 8.0 |
| fp_alu_cmp | beam_search | 3 | 7284/4385 | -0.9% ± 1.2 | -0.3% ± 0.4 | +103.2 ± 44.9 | 1.0 |
| fp_alu_cmp | best_of_n | 3 | 7284/4385 | -3.9% ± 2.1 | -1.2% ± 0.2 | +70.6 ± 36.1 | 4.0 |
| fp_alu_cmp | chialu | 3 | 7745/3503 | +0.0% ± 0.0 | +0.0% ± 0.0 | +1.0 ± 1.0 | 0.7 |
| fp_alu_cmp | plain | 3 | 7284/4385 | -17.4% ± 8.4 | -6.0% ± 6.2 | +407.3 ± 295.7 | 4.3 |
| fp_alu_cmp_hf | adaevolve | 3 | 6350/4521 | -14.8% ± 6.8 | -6.2% ± 5.8 | +323.1 ± 238.1 | 6.3 |
| fp_alu_cmp_hf | beam_search | 3 | 6350/4521 | -21.5% ± 6.1 | -10.2% ± 6.8 | +570.4 ± 293.1 | 6.3 |
| fp_alu_cmp_hf | best_of_n | 3 | 6350/4521 | -10.7% ± 7.4 | -4.9% ± 6.2 | +265.5 ± 264.3 | 3.3 |
| fp_alu_cmp_hf | chialu | 3 | 6855/3485 | -0.1% ± 0.1 | -0.7% ± 1.0 | +0.9 ± 1.0 | 0.7 |
| fp_alu_cmp_hf | plain | 3 | 6350/4521 | -25.4% ± 1.0 | -13.0% ± 2.5 | +706.9 ± 95.2 | 7.7 |
| fpnew | hand_adaevolve | 3 | 6194/3682 | -0.7% ± 0.5 | -0.1% ± 0.1 | +35.3 ± 15.5 | 0.7 |
| hardfloat | hand_adaevolve | 3 | 5421/2801 | -5.4% ± 6.7 | -0.8% ± 1.0 | +82.2 ± 86.5 | 1.3 |
| int_subword_alu | adaevolve | 3 | 5743/1783 | -21.2% ± 6.5 | -18.7% ± 4.2 | +721.9 ± 165.2 | 7.7 |
| int_subword_alu | beam_search | 3 | 5743/1783 | -22.3% ± 5.1 | -11.0% ± 7.6 | +590.9 ± 307.5 | 6.3 |
| int_subword_alu | best_of_n | 3 | 5743/1783 | -18.5% ± 2.1 | -17.6% ± 2.1 | +655.2 ± 90.9 | 8.0 |
| int_subword_alu | chialu | 3 | 6955/1381 | +0.0% ± 0.0 | +0.0% ± 0.0 | +0.2 ± 0.2 | 0.0 |
| int_subword_alu | plain | 3 | 5743/1783 | -21.8% ± 3.0 | -29.7% ± 2.3 | +1023.5 ± 107.7 | 9.3 |
| transdot | hand_adaevolve | 3 | 4475/4136 | -9.2% ± 4.8 | -4.2% ± 1.7 | +168.3 ± 89.0 | 8.0 |
