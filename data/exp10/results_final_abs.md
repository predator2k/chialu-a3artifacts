# exp10, first K=13 iterations (all runs reached >= 13); common reference per target

| target | method | best delay @ area<=B (ps) | best area @ delay<=B (µm²) | HV (norm. to B box) | min delay any | min area any |
|---|---|---|---|---|---|---|
| fp_alu_cmp | adaevolve | 3583 ± 283 | 6378 ± 414 | 0.126 ± 0.025 | 3501 ± 198 | 6366 ± 397 |
| fp_alu_cmp | beam_search | 4078 ± 337 | 7260 ± 28 | 0.073 ± 0.009 | 3912 ± 237 | 7247 ± 45 |
| fp_alu_cmp | best_of_n | 4136 ± 53 | 7109 ± 118 | 0.074 ± 0.006 | 3998 ± 148 | 7109 ± 118 |
| fp_alu_cmp | chialu | 3624 ± 0 | 5859 ± 36 | 0.135 ± 0.001 | 3496 ± 10 | 5859 ± 36 |
| fp_alu_cmp | plain | 3623 ± 370 | 6844 ± 457 | 0.111 ± 0.029 | 3434 ± 188 | 6844 ± 457 |
| fp_alu_cmp_hf | adaevolve | 3781 ± 354 | 5954 ± 369 | 0.100 ± 0.027 | 3773 ± 343 | 5954 ± 369 |
| fp_alu_cmp_hf | beam_search | 3295 ± 94 | 5499 ± 174 | 0.146 ± 0.004 | 3295 ± 94 | 5499 ± 174 |
| fp_alu_cmp_hf | best_of_n | 3915 ± 397 | 6030 ± 391 | 0.095 ± 0.034 | 3858 ± 352 | 6030 ± 391 |
| fp_alu_cmp_hf | chialu | 3624 ± 28 | 5074 ± 79 | 0.148 ± 0.002 | 3455 ± 42 | 4958 ± 0 |
| fp_alu_cmp_hf | plain | 3277 ± 59 | 5525 ± 160 | 0.146 ± 0.011 | 3277 ± 59 | 5525 ± 160 |
| fpnew | hand_adaevolve | 3522 ± 175 | 6022 ± 224 | 0.073 ± 0.013 | 3422 ± 164 | 5932 ± 195 |
| hardfloat | hand_adaevolve | 2674 ± 208 | 5217 ± 286 | 0.074 ± 0.021 | 2650 ± 186 | 5100 ± 233 |
| int_subword_alu | adaevolve | 1404 ± 114 | 4642 ± 217 | 0.147 ± 0.020 | 1378 ± 100 | 4642 ± 217 |
| int_subword_alu | beam_search | 1358 ± 109 | 4826 ± 224 | 0.144 ± 0.022 | 1343 ± 88 | 4735 ± 186 |
| int_subword_alu | best_of_n | 1417 ± 49 | 4730 ± 121 | 0.140 ± 0.013 | 1417 ± 49 | 4730 ± 121 |
| int_subword_alu | chialu | 1521 ± 0 | 4956 ± 0 | 0.142 ± 0.000 | 1381 ± 0 | 3871 ± 0 |
| int_subword_alu | plain | 1390 ± 57 | 3871 ± 125 | 0.182 ± 0.009 | 1390 ± 57 | 3871 ± 125 |
| transdot | hand_adaevolve | 3728 ± 197 | 4286 ± 77 | 0.080 ± 0.013 | 3728 ± 197 | 4286 ± 77 |

B (area/delay): int_subword_alu 5744/1783; fp_alu_cmp 7284/4385; fp_alu_cmp_hf 6350/4521; fpnew 6194/3682; hardfloat 5420/2801; transdot 4476/4136

## LLM budget per method (all exp10 calls up to the stop, 3 targets x 3 reps; hand: 3 refs x 3 reps)

| method | calls | tokens (in+out+reasoning, M) | cost $ |
|---|---|---|---|
| adaevolve | 189 | 26.8 | 9.04 |
| beam_search | 180 | 26.0 | 8.92 |
| best_of_n | 179 | 25.2 | 8.63 |
| chialu | 257 | 30.4 | 8.92 |
| hand_adaevolve | 187 | 27.7 | 9.77 |
| plain | 133 | 30.9 | 11.94 |
| total | 1125 | 167.1 | 57.22 |
