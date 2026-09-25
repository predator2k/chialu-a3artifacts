---
family: rns_dsp_datapath
pin: {kernel: iir}
---
# iir

The residue recursive section: a second-order canonic section performs
its five multiplications and four additions in the residue channels and
shares one scaling operation at the central node, so the feedback loop
stays inside the dynamic range. Fixed coefficients and adjacent
operations are combined in ROM tables, and latching each lookup-cycle
result pipelines the section and lets one set of tables serve several
multiplexed sections.

This is the pick when the kernel is recursive and the additions and
multiplications still far outnumber the scaling, sign and magnitude
operations: arithmetic before the scaling is extended precision without
roundoff, the single scaling injects one noise source whose variance
ratio against a standard implementation is F/(3 + 2F), and a pipelined
multiplexed section takes an input rate over 11 MHz from 90 ns ROMs.
The scaling and normalizing factors must satisfy the coefficient and
data worst-case bounds to prevent overflow, which the FIR sibling
avoids entirely by scaling only at the output.

The kernel is not an ALU op; the family is an exception (`redundant.EXCEPTIONS`).

## references

jullien_1978 -> Jullien, "Residue Number Scaling and Other Operations Using ROM Arrays", IEEE Transactions on Computers, 1978
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
