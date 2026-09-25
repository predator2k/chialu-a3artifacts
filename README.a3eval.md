# chialu-a3eval

The evaluation of chiALU against LLM-driven RTL optimization and against
hand-designed floating-point units, as `3rdparty/chialu/docs/evaluation-plan.md`
lays it out: one synthesis flow, one conformance gate and one set of clock
targets for every unit that enters a table. This repository holds what the
plan needs beside chiALU itself: the reference designs as submodules, their
wrappers and numerical models, the clock sweeps, the TestFloat harness, the
run scripts and the tables.

## Layout

* `3rdparty/chialu`: chiALU on its `accuracy-ctl` branch, with ADIR nested
  under `third_party/adir`; every flow (rendering, conformance, synthesis,
  the search) runs from it
* `3rdparty/cvfpu`: FPnew / CVFPU (`develop`)
* `3rdparty/berkeley-hardfloat`: Berkeley HardFloat (Chisel), with SoftFloat
  and TestFloat as its own submodules
* `3rdparty/transdot`: TransDot (`develop`), FPnew extended with the
  transprecision dot-product mode
* `baselines/<name>/`: one directory per reference design: the wrapper that
  presents chiALU's `alu_core` interface, the file list for sv2v, the script
  that regenerates it, the numerical model of the design's contract and the
  conformance verdict
* `sweeps/`: the tier-2 clock sweep (the plan's section 3) over the seeds,
  the hand plans and the numeric front points
* `harness/`: the TestFloat harness for chiALU's fp16 units and the plain agent
  loop of Table A (`harness/plain_loop.py`; `harness/README.md` documents both)
* `tables/`: the tables and the figure from real archives
* `docs/plan.md`: the prerequisite checklist and what each item found
* `docs/handoff.md`: the handoff (in Chinese) a session on a new server follows to
  prepare the environment, build the synthesis database and run every experiment

## Working copy

```
git clone --recurse-submodules --shallow-submodules git@github.com:predator2k/chialu-a3eval.git
```

Every measurement runs on the EDA host (`3rdparty/chialu/docs/verification-decisions.md`);
the scripts here take the chiALU checkout as `CHIALU=3rdparty/chialu`.
