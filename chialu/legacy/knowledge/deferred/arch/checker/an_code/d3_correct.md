---
family: an_code
pin: {code_distance: d3_correct}
---
# d3_correct

The correcting AN code: A is chosen so that every possible single-bit
error, every +-2^k pattern, and the no-error case map to distinct
residues modulo A, which gives minimum distance at least three. The
residue of a received word identifies the erroneous position through
table lookup or a repeated arithmetic residue sequence, and any
multi-bit pattern whose total numeric corruption is +-2^k is corrected
as well.

The price is a larger A and a longer word: base-10 single-digit codes
such as 19n+42 or 27n+6 need 8 bits, and the B=0 code 71n needs 35
binary symbols for numbers up to 483,939,977 at 6.15 bits of
redundancy against 6 bits for a 35-digit Hamming code. Codes with B=0
eliminate post-add correction only when the whole operand is one
digit and the base exceeds every result value; general multidigit
An+B addition still needs correction for B and for digit carries.
Detection can use an A divisible by 3 for the fast modulo-3 test and
defer the division by A until an error occurs. Against d2_detect it
adds location logic and redundancy; it is the pick when the
arithmetic must continue through a single fault without a retry.

The generated checker realizes this variant (`checker.code_distance: d3_correct`): the decode, the coded result over A, is the correction, named in a comment because the interface carries no corrected result.

## references

brown_1960 -> D. T. Brown, "Error Detecting and Correcting Binary Codes for Arithmetic Operations", IRE Transactions on Electronic Computers, vol. EC-9, pp. 333-337, 1960
garner_1966 -> H. L. Garner, "Error Codes for Arithmetic Operations", IEEE Transactions on Electronic Computers, vol. EC-15, pp. 763-770, 1966
