# carry_increment

Carry-select with the duplicate adder removed: each block's adder
computes only the carry-in-0 sum and its carry-out, a constant-time
incrementer adds one to that stored sum when the block's actual
incoming carry arrives, and the block carry-out is formed from the
block adder's carry-out, the group propagate and the incoming carry.
One carry, rather than two, propagates along the word. In prefix
terms the structure is hierarchical levels of serial evaluation
chains rather than an evaluation tree: the one-level form reduces to
two prefix levels, and the two-level form, which replaces the ripple
blocks with merged second-level increment blocks, reduces to three.

The incrementer is much cheaper than the second carry-propagate adder
and the selection circuitry of carry_select, and part of the block
adder and incrementer logic can be merged, so the family reaches the
same constant carry-in processing delay at medium rather than double
hardware and Pareto-dominates carry-select in cell-based flows.
block_sizing ramps the block widths along the word, and every thesis
block pins the ramp. increment_levels trades depth for wiring: the
two-level form (CIA-2L) implements the optimized variable-group
2-level group-prefix algorithm, adds negligible area over the
one-level form and gives the lowest area-time and power-time products
at large width; at 24 unit-gate delays the one-level form reaches 67
bits and the two-level form 177. More than two levels help only above
64 bits and add complexity. In the prefix-graph view the level count
places the structure between the serial-prefix chain and the Sklansky
tree, and bounding the black nodes per bit column recovers
size-optimal graphs for difficult arrival profiles.

intergroup_carry decides how block carries move: the thesis
structures ripple them through one carry operator per block, whereas
the FPGA CAI form drives them through a fast carry chain and replaces
the duplicated one-carry sum with a comparison of the block operands,
which nearly halves the stored speculative-sum registers and removes
the wide carry-control fanout; pipelined CAI is the first fallback
when the combinational adders miss frequency. The block_adder slot is
a ripple chain in every block that pins it. On a fine-grained FPGA
the one-level structure is the high-speed pick over ripple and
carry-skip, at 6 logic cells per bit against 4 for ripple carry on
the Xilinx XC6216 and less than half the ripple delay at 32 bits; the
two-level form wires less regularly and routes only for some
placements. The family is feed-forward and combinational.

## design choices

### block_sizing

| member | what it selects |
| --- | --- |
| `uniform` | every block has the same width. |
| `variable_ramp` | the blocks widen by one from the bottom, so a later block's carry arrives no later than its inputs. |

### intergroup_carry

| member | what it selects |
| --- | --- |
| `rippled` | the block carries ripple from block to block. |
| `lookahead_tree` | the block carries come from a lookahead tree over the blocks' generate and propagate. |

## references

zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
