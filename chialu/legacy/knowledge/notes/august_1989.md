---
handle: august_1989
citation: M. C. August, G. M. Brost, C. C. Hsiung, A. J. Schiffleger, "Cray X-MP: The Birth of a Supercomputer", IEEE Computer, vol. 22, no. 1, pp. 45-52, 1989.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, VEC_SFU, other]
formats: ["Cray-1-compatible 64-bit floating point", "64-bit word", "24-bit address arithmetic"]
authority: landmark
pages_read: 45-52 / 8
---

## summary
The paper establishes the Cray X-MP system organization, including flexible element-availability vector chaining, independent memory ports, and separate vector floating-point/scalar/address functional units (pp.47-49). The paper does not disclose the internal adder, multiplier, reciprocal-approximation, or rounding mechanisms, so no existing arithmetic family can be assigned. Reported system results include more than eight words per clock period from memory and more than 1.9-times speedup on a two-processor X-MP for short-vector inner loops (pp.49-50).

## families
none

## new_families
### flexible_vector_chaining  (domain: other, closest: none, why_not: Existing families describe arithmetic datapaths rather than element-level scheduling between vector registers, memory ports, and functional units.)
mechanism: The X-MP replaces the Cray-1 fixed chain-slot time with flexible chaining. Independent memory ports sacrifice synchronous, predictable memory access, while additional logic permits simultaneous reading from and writing to a vector register. A dependent functional unit starts for each vector element when that element becomes available, so chaining can begin at any point in the vector stream. Each processor has two vector-load ports, one vector-store port, and one I/O port. Software handles general memory hazards, with two limited hardware protections (pp.47-48).
choices:
  chain_trigger: {fixed_chain_slot, individual_element_availability}; document value: individual_element_availability  # p.47
  memory_port_organization: {single_shared_high_bandwidth, independent_per_processor}; document value: independent_per_processor  # p.47
  memory_hazard_handling: {conservative_hardware_checks, software_with_limited_hardware_protection}; document value: software_with_limited_hardware_protection  # p.48
results:
| metric | value | unit | technology / device | baseline | condition | page |
| memory delivery | more than 8 | words per clock period | four-processor Cray X-MP, 16-gate emitter-coupled logic gate arrays; year UNKNOWN | UNKNOWN | 64 banks, memory stress test, without delay | p.49 |
| memory-bandwidth fluctuation | less than 5 | percent | Cray X-MP, 16-gate emitter-coupled logic gate arrays; year UNKNOWN | UNKNOWN | real user environments | p.49 |
| multiprocessing speedup | more than 1.9 | times | two-processor Cray X-MP, 16-gate emitter-coupled logic gate arrays; year UNKNOWN | one-processor machine | inner loop contains short vectors | p.50 |
| clock period | 8.5 | nanoseconds | Cray X-MP, faster circuits; year 1986 | 9.5-nanosecond original-design period | faster circuits became available | p.50 |
evidence: The chaining and port mechanism is described under “Memory issues” on pp.47-48; Figure 1 inventories the arithmetic functional units on p.47; measured bandwidth and multiprocessing results appear on pp.49-50.

## space_gaps
* No component slot connects vector arithmetic functional units to element-availability chaining through vector registers and independent memory ports (p.47).
* No existing arithmetic-family choice records bitwise compatibility with a predecessor as a constraint on reciprocal and rounding redesigns (p.49).
* No existing integration choice records separate result paths from each functional unit to scalar/address registers (p.49).

## open_questions
* The circuit styles and topologies of the 64-bit vector/scalar add-subtract units and the 24-bit address add-subtract unit are not stated (p.47).
* The multiplier reduction/final-adder structures are not stated for the vector floating-point or address multipliers (p.47).
* The shipped reciprocal-approximation algorithm and the simulated replacement algorithm are not stated; the replacement would have occupied “a little over half” the old unit’s space and been “slightly faster,” but it was withdrawn for bitwise compatibility (p.49).
* The floating-point rounding mechanism is not stated; several investigated alternatives were abandoned for compatibility (p.49).
* The measurement years for the memory-bandwidth and multiprocessing-speedup results are not stated (pp.49-50).
