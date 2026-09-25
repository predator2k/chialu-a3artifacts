# subtractor_comparator

The comparator is the subtraction A - B with the difference bits
stripped: the carry-out of A + not(B) + 1 is the greater-or-equal flag,
the whole-word propagate signal of the prefix adder is the equality
flag, and simple logic on those two derives the remaining ordering
relations. Richards' borrow-only magnitude circuit reproduces the
borrow portion of a subtracter without producing difference bits;
Zimmermann obtains both flags for free from a parallel-prefix adder.

This structure is the pick when an adder or its prefix tree already
exists, because both flags cost no additional logic on top of the
existing carry-out and whole-word propagate. Its delay is the adder's
carry path, and plain sign sensing after subtraction does not
distinguish equality on its own: Richards notes that separating equal
from greater then needs either a zero detector or a second subtraction.
Against prefix_comparator's msb_first_prefix it trades the wide-operand speed and activity
savings of a dedicated scan for reuse of the datapath; against
tree_reduction it adds magnitude, which an equality tree does not give.
The `subtractor` slot names the adder family the carry-out is
taken from (any carry-propagate adder of the library), and
`zero_detect` takes equality from the difference's zero test or from
the operands' XNOR tree, which needs no adder output.

## design choices

### zero_detect

| member | what it selects |
| --- | --- |
| `sum_or_tree` | equality from the difference: the subtractor's sum bits are tested against zero, which waits for the carry chain. |
| `operand_xnor` | equality from the operands: an XNOR tree over the two words, which runs beside the subtractor rather than behind it. |

## references

richards_1955 -> Richards, "Arithmetic Operations in Digital Computers", Van Nostrand, 1955
zimmermann1997 -> R. Zimmermann, "Binary Adder Architectures for Cell-Based VLSI and their Synthesis", PhD thesis, Diss. ETH No. 12480, ETH Zurich, 1997.
