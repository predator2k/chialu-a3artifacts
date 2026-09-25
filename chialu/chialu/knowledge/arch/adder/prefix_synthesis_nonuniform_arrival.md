# prefix_synthesis_nonuniform_arrival

Synthesis of the prefix graph to a per-bit arrival profile rather
than selection of a named topology: every interval generate/propagate
pair is built from the pair of shorter non-overlapping intervals that
minimizes its ready time, serial-prefix regions serve positions whose
timing already tolerates ripple propagation, and parallel-prefix
regions accelerate the late or critical positions, so the multiplier
final adder's V-shaped profile, a late half-word or a single late bit
each gets its own graph. The graph is then reduced from the
required-time side: non-critical nodes are rewired to slower parents
or removed without changing the optimal output delays.

The search method trades optimality guarantees against run cost. The
compression/expansion algorithm starts from a serial-prefix graph,
compresses every column to minimum depth and expands under a depth
bound to reduce size, is correct by construction and runs below 1 s
for several hundred bits on a SPARCstation-10; it reaches the Snir
bound depth plus size of 2n-2 for uniform profiles at depths from
2 log n-3 through n-1. Dynamic programming builds every interval from
its minimum-delay parents in O(n^3) time and O(n^2) space and adds a
required-time backward pass. Exhaustive bottom-up generation with
pruning minimizes node count under level, fanout and wire-length
constraints and keeps several minima for physical evaluation.
Reinforcement learning trains on physical-synthesis rewards and
Pareto-dominates the named topologies, saving up to 30.2 percent area
at 64 bits at equivalent delay in Nangate45, but a 64-bit run took
about 5 days on 192 synthesis workers and 14 GPUs and assumes
uniform arrivals.

The fanout cap trades node count against load: a cap of 2 costs
more nodes than an unconstrained graph but stays below Kogge-Stone,
and a lower cap can improve post-placement timing despite the larger
graph. Region hybridization lets converted regions become ripple,
carry-skip or carry-select circuitry, or lets each arrival group of a
multiplier's result take its own topology, at the price that a
changed partial-product reducer needs a changed prefix graph.

The family wins whenever the arrival profile is known and
non-uniform: synthesized graphs beat Kogge-Stone and Brent-Kung on
delay from last input to last output, by at least 40 percent over
Brent-Kung on monotonically decreasing profiles, though decreasing
profiles need more cells and steep profiles need a per-column node
bound of about log n. It loses to a named topology when the profile
is uniform and the width small, and its graph-level timing degrades
at large widths, where wire delay reaches half the estimated timing
at 32 bits in 0.13 um and analytical-metric training produces graphs
that worsen after physical synthesis.

## the library's module

The seed instantiates the library's prefix module for the declared
`topology` (see the parallel_prefix card: `chialu.targets.rtl.families.prefix`
emits any graph; `--arrival` builds the graph for the `arrival_profile` (uniform, multiplier_vee, lsb_late, msb_late, or per-bit times) with the greedy depth- and size-decreasing construction); a rewrite pastes an edited graph's module in
its place.

## references

zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
liu2003 -> J. Liu, S. Zhou, H. Zhu, C.-K. Cheng, "An Algorithmic Approach for Generic Parallel Adders", International Conference on Computer-Aided Design (ICCAD), 2003.
roy2013 -> S. Roy, M. Choudhury, R. Puri, D. Z. Pan, "Towards Optimal Performance-Area Trade-off in Adders by Synthesis of Parallel Prefix Structures", 50th Design Automation Conference (DAC), 2013; extended in IEEE TCAD, vol. 33, no. 10, pp. 1517-1530, 2014.
roy2021 -> R. Roy, J. Raiman, N. Kant, I. Elkin, R. Kirby, M. Siu, S. Oberman, S. Godil, B. Catanzaro, "PrefixRL: Optimization of Parallel Prefix Circuits using Deep Reinforcement Learning", 58th ACM/IEEE Design Automation Conference (DAC), pp. 853-858, 2021.
