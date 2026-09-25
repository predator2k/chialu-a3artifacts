# Task

An L1D prefetcher ensemble steered by hints, one per load PC, held in a
table in main memory and cached on chip by a small buffer. The hardware
is the design of PF-LLM (Xu et al., ASPLOS '26): a router that looks a
load up in the buffer, a multiplexer that hands the load and its hint to
one member of the ensemble, and an orchestrator that applies the degree
and the filter. That hardware is fixed here.

What you write is the program that fills the table. For every load PC of
a binary you are given the disassembly -- the instruction, the 128 lines
either side, and the whole listing if you need a def-use walk -- and you
decide three things:

* **selection**: which member of the ensemble may issue prefetches for
  this load, or `none`;
* **degree**: 1, 2 or 3, mapping to the first quartile, the median and
  the third quartile of that member's own native degree range;
* **filter**: a member that must not see this load's demand request, so
  its tables are not trained by an access it cannot predict.

You also declare the hardware the program runs on: which of the three
hint fields the orchestrator applies (`SDF`, `SD`, `S`), the ensemble
(every member, or the four a generator selects most often), the buffer
size, and the policy used while a buffer miss is served.

The original design trained a model to make this decision. This task
asks whether the decision can be written down instead, as an analysis of
the code, with no training at all.

## How it is measured

Every candidate is compiled into its hint tables and simulated in
ChampSim on three workloads; the geomean IPC across them is the score. A
fourth workload is simulated only at report time and is never scored
against, so it is the one number no candidate was optimized for.

Two references come from one sweep, run once: every (member, degree)
pair on every workload, recording each load PC's L1D demand misses.

* **best_single** is the strongest one-size-fits-all choice per workload.
  Beating it is the whole point of deciding per PC.
* **oracle** takes, for each PC, the pair with the fewest misses, builds
  that table and actually runs it. It is the ceiling any static per-PC
  hint table reaches on this hardware.

`gap.closed_pct` is how much of the room between the two a candidate
took. It is reported, not optimized: the goal is absolute IPC, so a
candidate cannot look good by choosing a weak ensemble with a low
ceiling.

## What is not allowed

The generator sees the binary and nothing else. Reading a trace, reading
any measurement it is scored by, or carrying a table of PC constants
instead of an analysis all fail the lint. Every load PC must get a
decision, and the same binary must produce the same hints twice.
