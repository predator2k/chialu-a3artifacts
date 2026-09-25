# rns_montgomery_crypto

Montgomery multiplication carried out in residue arithmetic over two
relatively prime RNS bases: the operands live in n parallel channels
per base with no carries between channels, the reduction multiplies
the product's first-base residues by the precomputed inverse of the
modulus, extends that quotient estimate to the second base,
subtracts the multiple of the modulus, divides exactly by the first
base's product through modular inverses, and extends the result
back, so one multiplication costs n parallel modular
multiply-accumulates plus two base extensions. In the Cox-Rower form n Rower units compute the residue outputs
while a small Cox unit steers the approximate extension.

Channel count and width set the dynamic range and the parallelism:
33 channels of 32 bits cover 1024-bit exponentiation with a 7-bit
Cox adder, 5 to 15 channels of 33 to 36 bits cover 160- to 512-bit
elliptic curves, and the ring design suggests moderately sized 9- to
10-bit moduli in about 80 channels with table-lookup channel
operations. The base extension is the cost: the extensions take
2n(n+2) modular multiplications per Montgomery multiplication
against 5n for everything else. Kawamura's approximate extension is
error-free under its bounds on the base products and may return t or
t+B in the first pass, either of which preserves the congruence;
the mixed-radix extension overlaps the RNS-to-MRS conversion with the
modular operations on a nearest-neighbour processor ring at a
latency of 4n-1 cycles and an initiation interval of 3n; and
iterated approximations keep the reduction correct when the
extension is off by one base product, at two extensions per
reduction against four for the relaxed-residuum method. Rowers can
be time-multiplexed onto fewer processors with utilization between
62.5 and 100 percent.

The family is a fixed-iteration modular multiplier that wins for
large operands: a 1024-bit exponentiation at 100 MHz is estimated at
890 kbit/s (1.1 Mbps with 4-bit windows), a 160-bit scalar
multiplication takes 0.32 ms on a 90 nm Stratix II at 165.5 MHz and
5896 ALMs for general primes, the RNS point multiplier uses less than
half the area of earlier designs, and base randomization gives
side-channel protection at no overhead. It loses the forward and
reverse conversions only when both parties share the RNS
parameters, no comparison against a similarly pipelined high-radix
implementation is available, and the output stays below 2N so that
repeated multiplication needs no correction.

The family's defining structure is a Montgomery multiplication in two residue bases, a cryptographic kernel rather than an ALU op, so the library has no combinational module for it; a core that declares it stays behavioral and the family is listed as an exception (`redundant.EXCEPTIONS`).

## references

kawamura_2000 -> Kawamura, Koike, Sano, Shimbo, "Cox-Rower Architecture for Fast Parallel Montgomery Multiplication", EUROCRYPT (LNCS 1807), 2000
bajard_1998 -> Bajard, Didier, Kornerup, "An RNS Montgomery Modular Multiplication Algorithm", IEEE Transactions on Computers, 1998
posch_posch_1995 -> Posch, Posch, "Modulo Reduction in Residue Number Systems", IEEE Transactions on Parallel and Distributed Systems, 1995
guillermin_2010 -> Guillermin, "A High Speed Coprocessor for Elliptic Curve Scalar Multiplications over F_p", CHES (LNCS 6225), 2010
chang_2015 -> Chang, Molahosseini, Zarandi, Tay, "Residue Number Systems: A New Paradigm to Datapath Optimization for Low-Power and High-Performance Digital Signal Processing Applications", IEEE Circuits and Systems Magazine, 2015
