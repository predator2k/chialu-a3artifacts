# direct_compare

The plain comparator of a concurrent error-detection scheme: the
predicted check symbol and the symbol computed from the result are
compared bit for bit by one equality comparator, and the checker's
alarm is their inequality. Under a residue or count code the compared
words are the two residues or counts; under duplication they are the
result and its copy, so the comparator is the whole checker beyond the
replica.

The comparator is not self-checking. A fault inside the equality
comparator, a stuck-at on its output or a fault common to both
compared words is masked, so the scheme's fault coverage is bounded by
the comparator's own reliability the way a majority voter's is by the
voter. A two-rail tree or a constant-weight checker replaces it where
the checker itself must be totally self-checking; the direct compare
is the cheapest form and the default, since one XOR row and a
reduction tree over k bits is the floor every self-checking comparator
adds to.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes
this family in the comparator slot (`checker.comparator.family`) as the
SystemVerilog inequality of the two words, for every coded word and
for the duplicated outputs and their copies; it is the default of the
slot, and every run file that names another comparator pays its
self-checking property on top of this compare.

## references

lala_2001 -> P. K. Lala, "Self-Checking and Fault-Tolerant Digital Design", Morgan Kaufmann, 2001
