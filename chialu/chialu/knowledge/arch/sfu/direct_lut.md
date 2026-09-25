# direct_lut

A full-value table: the n-bit argument addresses one memory whose
entry holds the function value rounded to the target precision, so
evaluation is a single read with no multiplier and no arithmetic,
and an initiation interval of one comes for free. Storage is n x 2^n
bits for n-bit words, which is 60 kbytes at n = 15 and 144 kbytes
for 18-bit values at 16-bit addresses where a bipartite table needs
11, so the table grows exponentially with the address width and the
family serves low precision only.

The family has no design choices beyond the address and output
widths; its whole trade is memory against everything else. The
accuracy contract is one rounding per tabulated value: each entry
contributes up to 1/2 ulp, so a table read to the target precision
cannot deliver a final error bounded by 1/2 ulp or slightly more,
and a datapath that multiplies two tabulated values, as the FPGA
exponential does with e^A and e^Z - Z - 1, carries 1/2 ulp from each.

It wins where the argument is short: the single-precision FPGA
exponential reduces its argument to 9 bits and stores both tables in
one 2^9 x 36 dual-port memory, one BlockRAM or two M9K, before the
final multiplication, while the same table-based method does not
scale to double precision; fixed-point root extraction reads an
integer exponent's reciprocal from a 2^ny table for ny up to 12 and
falls back to a digit recurrence above that. Its loss to the
bipartite and multipartite families is the memory ratio above, and
it remains the storage baseline those families are measured against.
The family is feed-forward and carries no checker.

The seed instantiates the library's generated value table for this family (`chialu/targets/rtl/families/sfu.py`: one entry per pattern of the format, the pattern in and the result pattern out, for formats of at most 16 bits). `python3 -m chialu.targets.rtl.families.sfu --function <fn> --format <format> --family direct_lut --pins k=v,...` emits the module with its modeled error for a rewrite.

## references

muller_2016 -> J.-M. Muller, "Elementary Functions: Algorithms and Implementation", 3rd ed., Birkhauser, 2016
muller_1999 -> J.-M. Muller, "A Few Results on Table-Based Methods", Reliable Computing, vol. 5, no. 3, pp. 279-288, 1999
pasca_2011 -> B. Pasca, "High-Performance Floating-Point Computing on Reconfigurable Circuits", PhD thesis, ENS Lyon, 2011
vazquez_2013 -> A. Vazquez, J. D. Bruguera, "Iterative Algorithm and Architecture for Exponential, Logarithm, Powering, and Root Extraction", IEEE Transactions on Computers, vol. 62, no. 9, pp. 1721-1731, 2013
