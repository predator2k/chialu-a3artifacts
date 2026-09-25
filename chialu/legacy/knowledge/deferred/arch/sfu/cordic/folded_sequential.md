---
family: cordic
pin: {topology: folded_sequential}
---
# folded_sequential

One set of adder-subtractors and shift registers reused for every
iteration: Volder's machine is three shift registers with three
adder-subtractors, an operation taking as many word times as the word
is long, and Walther's processor is three parallel arithmetic units,
each a 64-bit register, an 8-bit adder-subtracter and an 8-out-of-48
multiplex shifter, fed by a 512 by 48-bit ROM of constants at 200
nanoseconds a cycle. Radix 2 yields one digit per iteration.

The folded core is the area pick, the multiplierless low-area
long-latency option of the FPGA comparisons: a 16-bit 8-iteration
iterative processor fits 21 CLBs of a Xilinx 4000E at about 1.5
microseconds per result, and a bit-serial 7-iteration vector-magnitude
core takes about 20 percent of an Atmel 6005 at a 125 MHz bit clock,
three and a half times the time of the much larger bit-parallel
solution. Its cost is the variable shifter, whose fan-in maps poorly
to FPGA logic, and the angle table; the FloPoCo comparison shows a
32-cycle LogiCore sine/cosine at 3812 LUTs and 296 MHz against
polynomial units of 16 cycles and about 800 LUTs plus DSPs and
memory, and several parallel radix-2 cores with FIFOs and a
floating-point adder exceed 61 cycles of latency for exp. The
unrolled pipeline trades that area for one result per clock.

The library realizes the family's unrolled topology alone; this variant reuses one stage over the cycles and stays behavioral (an exception, `sfu.SEQUENTIAL_SFU`).

## references

volder_1959 -> J. E. Volder, "The CORDIC Trigonometric Computing Technique", IRE Transactions on Electronic Computers, vol. EC-8, no. 3, pp. 330-334, 1959
walther_1971 -> J. S. Walther, "A Unified Algorithm for Elementary Functions", AFIPS Spring Joint Computer Conference, pp. 379-385, 1971
andraka_1998 -> R. Andraka, "A Survey of CORDIC Algorithms for FPGA Based Computers", ACM/SIGDA International Symposium on FPGAs, pp. 191-200, 1998
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
