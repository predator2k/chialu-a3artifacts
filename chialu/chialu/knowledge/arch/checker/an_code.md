# an_code

Nonseparate arithmetic code: every operand X is carried as AX (or
An+B), so a codeword is a multiple of A and each unit that computes on
codewords returns a codeword when fault-free. An odd A above 1 gives
minimum distance two and detects every single-bit error; an A large
enough that every ±2^k error pattern has its own residue class gives
distance three and locates the faulty bit from the residue. The check
is a divisibility test, which for A=3 reduces to the difference of the
one-counts in even and odd positions modulo 3 and for A = 2^a - 1 to a
modulo-A checksum of a-bit bytes. Complementation is bitwise when A
divides 2^n - 1, so the low-cost codes use one's-complement arithmetic.

The A choice sets redundancy against reach. A=3 is the
minimum-redundancy detecting code (1 to 3 extra bits) and has a
combinational legality test, while A = 2^a - 1 keeps operands
complementable and lets a byte-serial machine check partial and final
results with one modulo-A accumulator: the STAR processor ran 32-bit
15X operands in 4-bit bytes with full coverage of single determinate
repeated-use faults in its isolated channels. Raising A to a correcting
distance costs word length rather than checker logic; the 71n code
spends 6.15 bits of redundancy on 35 symbols against 6 for a Hamming
code, and locates the error by table lookup or by an arithmetic residue
sequence. The offset B is what makes complementation and single-digit
sums work, and it is also what forces a corrective addition after every
multidigit add unless B=0 fits in one digit.

The decode_point choice trades checker traffic for arithmetic
complexity. Staying coded to the domain exit means multiplication forms
A^2 XY, divides by A and applies coded roundoff, division premultiplies
the dividend, and multiple-precision and floating-point operations
become cumbersome; the STAR's fixed-point range also shrank to |X| <
1/30 under its simple sign and overflow rules. Decoding per operation
removes those costs and hands the job to a separate residue checker,
which is the replacement mutation. The systematic nonseparate form
exists exactly when GCD(g, M) = 1 and M < g^t, and for two's-complement
binary a g=3 systematic code exists at every length, while no efficient
simple code exists for Mg = 2^n - 1.

The fault contract is the single-error model: distance two detects
every single error and the distance-three codes correct any pattern
whose numeric corruption is ±2^k; behaviour outside that model is not
reported. Execution is feed-forward, with the check as a separate
divisibility or residue test on the coded result.

The generated checker (`chialu/targets/rtl/alu_checker.py`) realizes this family as the checker's own coded replica: the operands times A, the add class and mul_wide computed on the codewords with the wrap recovered from the patterns, A times the result compared with the coded result, and the coded result checked for divisibility by A (the replica's self-check); d3_correct names the decode (the coded result over A) as the correction and decode_point where it would sit.

## references

brown_1960 -> D. T. Brown, "Error Detecting and Correcting Binary Codes for Arithmetic Operations", IRE Transactions on Electronic Computers, vol. EC-9, pp. 333-337, 1960
garner_1966 -> H. L. Garner, "Error Codes for Arithmetic Operations", IEEE Transactions on Electronic Computers, vol. EC-15, pp. 763-770, 1966
avizienis_1973 -> A. Avizienis, "Arithmetic Algorithms for Error-Coded Operands", IEEE Transactions on Computers, vol. C-22, pp. 567-572, 1973
