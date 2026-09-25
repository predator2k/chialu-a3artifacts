# exp10, first K=10 iterations (all runs reached >= 10); common reference per target

| target | method | best delay @ area<=B (ps) | best area @ delay<=B (µm²) | HV (norm. to B box) | min delay any | min area any |
|---|---|---|---|---|---|---|
| fp_alu_cmp | adaevolve | 3597 ± 266 | 6381 ± 412 | 0.122 ± 0.028 | 3597 ± 266 | 6368 ± 395 |
| fp_alu_cmp | beam_search | n/a (4272, nan, 4561) | 7263 ± 30 | 0.073 ± 0.009 | 3912 ± 237 | 7249 ± 46 |
| fp_alu_cmp | best_of_n | 4215 ± 93 | 7200 ± 13 | 0.066 ± 0.006 | 4133 ± 155 | 7200 ± 13 |
| fp_alu_cmp | chialu | 3624 ± 0 | 5859 ± 36 | 0.135 ± 0.001 | 3503 ± 0 | 5859 ± 36 |
| fp_alu_cmp | plain | 3623 ± 370 | 6849 ± 450 | 0.109 ± 0.031 | 3488 ± 252 | 6849 ± 450 |
| fp_alu_cmp_hf | adaevolve | 3851 ± 307 | 5954 ± 369 | 0.097 ± 0.027 | 3851 ± 307 | 5954 ± 369 |
| fp_alu_cmp_hf | beam_search | 3549 ± 274 | 5704 ± 432 | 0.125 ± 0.031 | 3518 ± 231 | 5704 ± 432 |
| fp_alu_cmp_hf | best_of_n | 4036 ± 336 | 6037 ± 395 | 0.089 ± 0.031 | 3975 ± 298 | 6037 ± 395 |
| fp_alu_cmp_hf | chialu | 3644 ± 0 | 5123 ± 17 | 0.147 ± 0.001 | 3455 ± 42 | 4958 ± 0 |
| fp_alu_cmp_hf | plain | 3374 ± 45 | 5525 ± 160 | 0.140 ± 0.009 | 3374 ± 45 | 5525 ± 160 |
| fpnew | hand_adaevolve | 3658 ± 18 | n/a (6182, nan, 6179) | 0.060 ± 0.003 | 3658 ± 18 | 6004 ± 126 |
| hardfloat | hand_adaevolve | 2674 ± 208 | 5379 ± 57 | 0.068 ± 0.013 | 2650 ± 186 | 5262 ± 117 |
| int_subword_alu | adaevolve | 1406 ± 115 | 4668 ± 244 | 0.145 ± 0.021 | 1380 ± 102 | 4668 ± 244 |
| int_subword_alu | beam_search | 1385 ± 92 | 5110 ± 434 | 0.129 ± 0.031 | 1371 ± 71 | 5110 ± 434 |
| int_subword_alu | best_of_n | 1452 ± 37 | 4730 ± 121 | 0.135 ± 0.010 | 1452 ± 37 | 4730 ± 121 |
| int_subword_alu | chialu | 1521 ± 0 | 4956 ± 0 | 0.142 ± 0.000 | 1381 ± 0 | 3871 ± 0 |
| int_subword_alu | plain | 1395 ± 54 | 4039 ± 130 | 0.175 ± 0.012 | 1395 ± 54 | 4039 ± 130 |
| transdot | hand_adaevolve | 3755 ± 199 | 4286 ± 77 | 0.079 ± 0.013 | 3755 ± 199 | 4286 ± 77 |

B (area/delay): int_subword_alu 5744/1783; fp_alu_cmp 7284/4385; fp_alu_cmp_hf 6350/4521; fpnew 6194/3682; hardfloat 5420/2801; transdot 4476/4136
