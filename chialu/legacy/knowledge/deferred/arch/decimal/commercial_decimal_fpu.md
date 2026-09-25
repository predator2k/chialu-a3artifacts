# commercial_decimal_fpu

The shipped IBM decimal units: a BCD significand dataflow of 144 bits
(36 digits) with DPD/BCD codecs, a two-cycle rotator, a two-stage
decimal/binary adder built from 4-digit conditional adders that runs
as one 36-digit or two 18-digit pipelines, a 2X/5X multiples
generator, a prescale table and quotient correction; multiplication
iterates multiples through that adder one digit per cycle, and
division is a prescaled digit recurrence over the same hardware.
Before the dedicated unit, the z900 ran packed-decimal arithmetic on
the fixed-point unit's 64-bit combined binary/decimal adder, and the
z9 ran decimal floating-point as millicode over that hardware.

implementation trades latency against flexibility. Millicode with
hardware assists reuses packed-decimal hardware through milli-ops for
register transfer, DPD decode/encode and BCD add/subtract/multiply/
divide; on the z9 a 16-digit add takes about 100 to 150 cycles and a
divide 350 to 400, ten times faster than pure software, and the
authors projected another factor of ten from full hardware. The
hardware DFU delivers it: the z196 accelerator adds decimal64 in 6
cycles and decimal128 in 8 against 154 and 233 in software, at 1.43
mm2 in 45 nm and 5.2 GHz, with multiply and divide operand-dependent
across 13 to 140 cycles. The z15 redesign of multiply/divide keeps
that variable latency and gains about 3x on existing code.

datapath_width_digits follows the format: 16 digits for the z900's
packed-decimal adder, 36 digits from POWER6 on so that one 34-digit
quadword operation or two simultaneous 16-digit operations fit.
shared_with_binary_fpu decides where the unit lives: the z900 adder
is the fixed-point unit's own, POWER6 reuses the binary floating-point
register file, and the z10 places the decimal macros in a
separate unit at the cost of communication delay to the core. The
z196 pipeline is four stages, which favours fixed-point decimal
latency over DFP throughput; the POWER8 DFU is fully pipelined with a
13-cycle dependent latency, and the z13 carries one DFU in each of
two vector/floating-point units.

The significand_adder slot is direct BCD addition with the +6
presum correction in the z900 and the conditional-adder dataflow of
POWER6/z10, and speculative addition of the rounding increment in
the z196. The multiplier slot is iterative with double and quintuple
multiples only. The divider slot is a nonredundant digit recurrence
with divisor prescaling, whose extra cost over restoring on POWER6 is
a 0.25 KB table and four registers because the shared adder rules out
the redundant-adder alternative. Fault contract: the z900 replicates
the whole fixed-point unit, the z10 protects the significand dataflow
with residue-3 checking and its interfaces with parity, and the z196
recovery unit flushes and restarts on a detected error. Execution is
variable-iteration, with multiply and divide latency set by the
significant digits.

No unit template opens `decimal_misc_space`: the family belongs to a decimal floating-point unit (or a conversion between number systems) that the ALU, dot and SFU templates do not provision, so no seed declares it and the library has no module for it; the BCD ALU's decimal adders, multipliers and dividers come from `chialu/targets/rtl/families/decimal.py`.

## references

busaba_2001 -> Busaba, Krygowski, Li, Schwarz, Carlough, "The IBM z900 Decimal Arithmetic Unit", 35th Asilomar Conference on Signals, Systems and Computers, 2001
schwarz_2002 -> E. M. Schwarz, M. A. Check, C.-L. K. Shum, et al., "The Microarchitecture of the IBM eServer z900 Processor", IBM Journal of Research and Development, vol. 46, no. 4/5, pp. 381-395, 2002
duale_2007 -> Duale, Decker, Zipperer, Aharoni, Bohizic, "Decimal Floating-Point in z9: An Implementation and Testing Perspective", IBM Journal of Research and Development, 2007
schwarz_2007 -> Schwarz, Carlough, "Power6 Decimal Divide", IEEE ASAP, 2007
wang_2009 -> Wang, Schulte, Thompson, Jairam, "Hardware Designs for Decimal Floating-Point Addition and Related Operations", IEEE Transactions on Computers, 2009
schwarz_2009 -> Schwarz, Kapernick, Cowlishaw, "Decimal Floating-Point Support on the IBM System z10 Processor", IBM Journal of Research and Development, 2009
carlough_2011 -> Carlough, Collura, Mueller, Kroener, "The IBM zEnterprise-196 Decimal Floating-Point Accelerator", 20th IEEE Symposium on Computer Arithmetic (ARITH-20), 2011
sinharoy_2015 -> B. Sinharoy, et al., "IBM POWER8 Processor Core Microarchitecture", IBM Journal of Research and Development, vol. 59, no. 1, pp. 2:1-2:21, 2015.
