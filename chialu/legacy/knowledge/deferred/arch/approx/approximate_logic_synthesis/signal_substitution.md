---
family: approximate_logic_synthesis
pin: {method: signal_substitution}
---
# signal_substitution

A target signal is replaced by a substitute signal that equals it with
high probability; the target's exclusive logic cone is deleted and its
timing-relaxed fanout logic is downsized. An iterative loop scores
candidate pairs by deletion potential, downsizing potential and
difference probability, performs the best substitution, simplifies the
circuit, and retains the last implementation that satisfies the
output-error constraint.

It is the pick for iso-delay area and power reduction under error-rate
or average-error constraints: 15% to 25% area and 10% to 28% power at
an error rate below 0.5%, and 30% to 60% of both below 2%, on ISCAS85
circuits in IBM 45 nm. Substitutions must not create combinational
cycles or touch outputs that cannot tolerate errors, and output error
is estimated separately because a differing internal pair need not
propagate. The contract is statistical over equiprobable inputs with no
formal bound, which separates it from don't-care simplification;
structural substitution pays off on large circuits whose exact
structure approximates a useful inexact one.

## references

venkataramani2013 -> S. Venkataramani, K. Roy, A. Raghunathan, "Substitute-and-Simplify: A Unified Design Paradigm for Approximate and Quality Configurable Circuits", Design, Automation and Test in Europe (DATE), pp. 1367-1372, 2013
scarabottolo2020 -> I. Scarabottolo, G. Ansaloni, G. A. Constantinides, L. Pozzi, S. Reda, "Approximate Logic Synthesis: A Survey", Proceedings of the IEEE, vol. 108, no. 12, pp. 2195-2213, 2020
