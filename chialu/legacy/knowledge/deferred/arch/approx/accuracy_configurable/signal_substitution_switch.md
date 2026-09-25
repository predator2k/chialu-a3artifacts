---
family: accuracy_configurable
pin: {reconfig_grain: signal_substitution_switch}
---
# signal_substitution_switch

The quality knob of substitute-and-simplify (SASIMI): every substituted
signal keeps its target logic, and a mode-controlled switch selects the
target signal or its substitute, so the tightest mode is exact.
Substitutions are nested by quality constraint, and a tighter mode
recovers a strict superset of the errors a looser mode recovers. The
grain applies to any synthesized circuit, and the recovery choice adds
difference monitors that extend the clock when a substitution differs.

Recovery sets what accurate mode costs. With error_detection, TS/SS
difference monitors accumulate, and the clock extends by one cycle
either only when a difference fires (selective_extra_cycle) or in
every accurate-mode cycle (universal_extra_cycle); the affected
substitution circuits switch back to their target signals and the
downstream logic recomputes. The two-cycle probability in accurate
mode runs from 0.002% (SAD) to 0.24% (ripple-carry adder) across the
benchmarks in IBM 45 nm, accurate-mode energy saving from 2.69% (RCA)
to 33.3% (multiplier), and approximate-mode energy saving from 14.44%
(SAD) to 40.05% (multiplier) against the accurate original. The grain
differs from carry_chain_switch, whose predicted carry is a fixed
function of the boundary bits: the substitute is another existing
signal of the circuit. It is the pick when the circuit is not an adder
or the modes come from a synthesis flow rather than a datapath
partition.

## references

venkataramani2013 -> S. Venkataramani, K. Roy, A. Raghunathan, "Substitute-and-Simplify: A Unified Design Paradigm for Approximate and Quality Configurable Circuits", Design, Automation and Test in Europe (DATE), pp. 1367-1372, 2013
