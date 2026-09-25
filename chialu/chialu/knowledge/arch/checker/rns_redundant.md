# rns_redundant

Computation in a residue number system with r redundant moduli: an
integer is held as residues modulo n pairwise-prime information moduli
and r redundant ones, add/subtract/multiply act digit-wise so a failing
channel corrupts one residue digit, and a legitimate value lies in [0,
M), M being the information product. A digit error moves the value into
the illegitimate range [M, M m_R), which a reverse conversion or a
base-extension consistency check exposes; up to r digit errors are
detectable and floor(r/2) correctable, and the faulty digit is located
by projections (drop one modulus, test legitimacy) or by base-extension
discrepancies that index a correction table.

The redundant_moduli and correction choices are one trade: one
redundant modulus larger than every other modulus detects any single
digit error, and unambiguous correction of every single digit error
needs the redundant product m_R to exceed max(m_i m_j), a bound that is
necessary and sufficient and that the earlier base-extension scheme
overshoots by up to 2x. Restricting the guaranteed class to selected
errors (single-bit encoding errors under a Hamming-distance-constrained
residue encoding) shrinks m_R from 273 to 161 to 69 for the same M =
2992, at the price that an uncovered error in the redundant digit can
be miscorrected. Correction is priced in modular operations, 2(n+r) - 1
per projection plus 2(r+1) for the magnitude test, and the decoder can
be a legitimate-range test, iterative channel exclusion or
maximum-likelihood selection.

The base_moduli_count sets dynamic range against digit width: residues
are ordinarily 5 to 10 bits, and an exemplar four-plus-two set uses
moduli near 200 to 500. The check arithmetic can reuse the information
channels in time or run in separate modules, and the whole machine
lands near a 2x hardware factor against 3x for triple modular
redundancy before voter cost.

The family wins where errors must stay channel-local and the workload
is add/multiply heavy: arithmetic, storage, transmission and
residue-domain DSP, with a zero fault-missing rate reported for
single-event upsets in FIR filters. It loses on division and square
root, which cost more time than in binary, and its contract assumes at
most r wrong digits with no error during the consistency check itself.
Execution is feed-forward, with detection as a reverse conversion at
the domain exit.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family: the residue check under base_moduli_count plus redundant_moduli low-cost moduli 2^a - 1 (a the first primes), the per-channel disagreements as the syndrome; with correction the syndrome names the faulty channel, and the verdict stays any disagreement because the interface carries no corrected result.

## references

watson_hastings_1966 -> R. W. Watson, C. W. Hastings, "Self-Checked Computation Using Residue Arithmetic", Proceedings of the IEEE, vol. 54, no. 12, pp. 1920-1931, 1966
barsi_maestrini_1973 -> F. Barsi, P. Maestrini, "Error Correcting Properties of Redundant Residue Number Systems", IEEE Transactions on Computers, vol. C-22, pp. 307-315, 1973
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
