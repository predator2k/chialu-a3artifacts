# Whole-ALU synthesis cost

Local <host> wall seconds including receipt storage; medium / Nangate45 / 300 ps, report=False.
Independent jobs and other host load affect timings. Four internal workers reserve four EDA slots.

| Target | repeats=1 | repeats=5, serial | repeats=5, four workers | serial ratio |
| --- | ---: | ---: | ---: | ---: |
| int_subword_alu | 5.23 | 22.00 | 9.96 | 4.21 |
| fp_alu_cmp | 25.74 | 40.23 | 31.12 | 1.56 |
| fp_alu_cmp_hf | 20.36 | 33.62 | 30.91 | 1.65 |

9,704 integer surrogate labels, using this baseline as the proxy: 59.29 core-hours
(formerly 14.09; extra 45.20), ideally 0.99 hours at 60 cores.
This is synthesis only: generation, feature extraction, simulation and retraining are excluded;
design complexity and memory may change throughput. Use one internal worker with 60 independent jobs.

The existing DB has 16,446 rows (14,074 successful);
15,493 rows record seconds, totalling 163.98 core-hour equivalents.
A conservative fivefold planning estimate is 819.90 core-hour equivalents
or 13.66 hours at 60 cores.
This is a budget estimate, not a measured bound: checkpoint reuse and text deduplication reduce work;
generation cost, unknown timings, host contention, retries and long-tail failed rows can increase it.
No dataset re-labelling or full synthesis DB rebuild was run. Only the isolated one-row DB test was rebuilt.
