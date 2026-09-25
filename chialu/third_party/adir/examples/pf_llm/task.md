# Task

An L1D prefetcher ensemble steered by hints a language model wrote
offline (PF-LLM, Xu et al., ASPLOS '26). For every load PC of a
binary the model read the 128 assembly lines on either side of the
load and answered with a JSON hint: the sub-prefetcher that may issue
prefetches for the load; a degree of 1, 2 or 3, which maps to the
first quartile, the median and the third quartile of that
sub-prefetcher's native degree range; and, optionally, a
sub-prefetcher that must not see the load's demand request. The hints
are packed to 8 bits per PC (4 for the selection, 2 for the degree, 2
for the filter) into the Prefetch Hint Table in main memory. A
256-entry Prefetch Hint Buffer caches them on chip, and a reserved
entry holds the policy used while a buffer miss is served.

The candidate is the `lmhint` struct: the router that looks a load up
in the buffer, the multiplexer that hands the load and its hint to one
sub-prefetcher, and the orchestrator that applies the degree and the
filter. Its declaration names the hint fields it applies (S, SD or
SDF), the ensemble (the twelve sub-prefetchers of the paper's Table 2,
or the four the model selects most often), the buffer size and the
default policy. The sub-prefetchers, the buffer and the table loader
are fixed. A hint reaches the router only through the buffer lookup:
reading the table directly, or anything outside the documented
ChampSim API, fails the lint, and the router's state together with the
buffer must fit the accounting budget.

The model is fine-tuned once per run from the ground truth: for each
training binary, one ChampSim run per (sub-prefetcher, degree), the
average memory access time of every load PC, the best pair as the
label and the worst sub-prefetcher as the filter. Hints for the test
binaries are generated under vLLM with the JSON schema restricted to
the declared ensemble, so a reduced ensemble needs no retraining.
Every candidate is simulated on six SPEC 2017 workloads with its own
hint tables; the geomean IPC across them, relative to the seed, is the
score. The other six workloads are simulated at report time only. The
seed is the paper's LMHint-SDF: all three fields, the full ensemble,
256 buffer entries.
