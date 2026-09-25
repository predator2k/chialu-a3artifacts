---
family: ling_prefix
pin: {topology: sklansky}
---
# sklansky

The original Ling adder's tree: four-bit groups form pseudo-carry
lookahead signals, the group results combine in a minimum-depth
doubling-fanout network, and the final sum is produced in parallel by
the Sklansky conditional-sum method, which selects a conditional
value once H is available. Under a fan-in and fan-out of four with
eight-emitter dotting a 32-bit addition takes three logic levels.

Sklansky is the pick when the technology offers wide fan-in and
dotting and the design is bounded by logic levels rather than by
wire, which is the setting of the 1981 design and its four-level
address-generation variant behind a carry-save adder. It gives up
the unit fanout of Kogge-Stone, so in a CMOS process where fanout
must be buffered the Kogge-Stone Ling adders are the reported pick.

## references

ling1981 -> H. Ling, "High-Speed Binary Adder", IBM Journal of Research and Development, vol. 25, no. 2-3, pp. 156-166, 1981.
