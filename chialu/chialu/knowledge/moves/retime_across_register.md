---
id: retime_across_register
tier: structural
applies_to: [adder, mul, fp, sfu, dot]
preserves: latency_neutral
check: tb
effect: delay-
sources: [muller_2018]
---
# Move logic across a pipeline register

pattern: a stage with a long path next to a stage with slack

rewrite: move the register boundary (retime) so the critical path is split evenly; the latency contract is unchanged, only which cycle does what

when: pipelined units where synthesis reports one stage far above the others
