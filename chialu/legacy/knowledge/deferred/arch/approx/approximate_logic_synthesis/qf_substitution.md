---
family: approximate_logic_synthesis
pin: {method: qf_substitution}
---
# qf_substitution

A quality-constraint circuit joins the original circuit, the current
approximate circuit, and a Boolean Q-function whose one output says
whether the quality constraint holds. The observability don't-cares at
Q become approximation don't-cares, expressed in primary inputs and
installed as external don't-cares, so a synthesis tool simplifies one
output cone per iteration; the approximate circuit is updated after
every output, which keeps Q a tautology.

It is the pick when a hard bound must hold by construction with
off-the-shelf synthesis: the specified error magnitude or relative error
is never transgressed, at 1.1x to 1.85x area and 1.15x to 1.75x power
under a bound below 1% and up to 4.75x area at 20% in IBM 45 nm. The
metric must be expressible as a Boolean function of original and
approximate output bits, and large circuits need the scalability
heuristics, of which Q-function decomposition loses optimization
potential by propagating the worst error across stages. Synthesis time
runs from minutes for adders to hours for a DCT datapath. Signal
substitution is the sibling for iso-delay statistical constraints, and
evolutionary search for Pareto libraries.

## references

venkataramani2012 -> S. Venkataramani, A. Sabne, V. Kozhikkottu, K. Roy, A. Raghunathan, "SALSA: Systematic Logic Synthesis of Approximate Circuits", 49th Design Automation Conference (DAC), pp. 796-801, 2012
mittal2016 -> S. Mittal, "A Survey of Techniques for Approximate Computing", ACM Computing Surveys, vol. 48, no. 4, 2016
