---
family: an_code
pin: {code_distance: d2_detect}
---
# d2_detect

The detecting AN code: each message n is encoded as An+B with an odd A
other than 1, which gives minimum distance at least two, so every
single-bit error is detected; A=3 is the minimum-redundancy detecting
construction at 1 to 3 redundant bits. A received word is checked by
subtracting B and testing divisibility by A, or by testing the residue
B modulo A; for A=3 the residue is the difference between the
one-counts in even and odd bit positions modulo 3, which has a
combinational form.

Detection is where the AN code is cheapest: g=3 is the smallest check
base for binary single-error detection, and the modulo-3 test is
combinational while division-based checking is expensive in time.
Adding two codewords in a conventional adder gives A(i+j)+2B, so
multidigit addition needs a corrective addition set by each digit's
carry-in and carry-out with interdigit carries blocked during that
cycle. The STAR processor pairs d2_detect with A=15, the 2^a-1 form at
a=4, and a modulo-15 checksum accumulator that expects all ones,
reaching 100 per cent coverage of single determinate repeated-use
faults over its isolated 4-bit channels. Against d3_correct it locates
nothing, so a bad residue issues a fault warning rather than a
repair; it is the pick when detection with recovery elsewhere
suffices and the redundancy budget is small.

The generated checker realizes this variant (`checker.code_distance: d2_detect`).

## references

brown_1960 -> D. T. Brown, "Error Detecting and Correcting Binary Codes for Arithmetic Operations", IRE Transactions on Electronic Computers, vol. EC-9, pp. 333-337, 1960
garner_1966 -> H. L. Garner, "Error Codes for Arithmetic Operations", IEEE Transactions on Electronic Computers, vol. EC-15, pp. 763-770, 1966
avizienis_1973 -> A. Avizienis, "Arithmetic Algorithms for Error-Coded Operands", IEEE Transactions on Computers, vol. C-22, pp. 567-572, 1973
