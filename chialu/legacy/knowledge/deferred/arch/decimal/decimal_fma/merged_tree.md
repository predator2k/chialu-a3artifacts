---
family: decimal_fma
pin: {structure: merged_tree}
---
# merged_tree

The addend is aligned within a 4p-digit width and its middle 2p digits
enter the carry-save tree together with the signed-digit-recoded
partial products, so a single decimal carry-propagate adder yields the
2p-digit intermediate; two leading-zero-digit counters guide result
alignment. In the combined binary/decimal form the column-wise reduced
vectors meet the aligned addend in a 4:2 carry-save adder and a [-6,6]
redundant adder finishes the addition.

It is the pick when one carry-propagate adder must serve the whole
a*b+-c and when the same tree should also deliver multiplication and
addition/subtraction through an operation selector, with four pipeline
stages giving one result per cycle. The tree also admits binary/decimal
sharing of the multiplier and adder, which cuts area by about 23%
against separate units in TSMC 65 nm LP. The cost is the wide
alignment datapath, 4p or 3p+1 digits, against the cascade's separate
2p-digit adder and off-path pre-alignment.

The family's space is opened by no unit template; the variant is documented for the knowledge base alone.

## references

samy_2010 -> Samy, Fahmy, Raafat, Mohamed, ElDeeb, Farouk, "A Decimal Floating-Point Fused-Multiply-Add Unit", 53rd IEEE Midwest Symposium on Circuits and Systems (MWSCAS), 2010
wahba_2017 -> Wahba, Fahmy, "Area Efficient and Fast Combined Binary/Decimal Floating Point Fused Multiply Add Unit", IEEE Transactions on Computers, 2017
