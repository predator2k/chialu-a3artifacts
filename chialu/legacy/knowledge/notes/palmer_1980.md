---
handle: palmer_1980
citation: J. F. Palmer, "The Intel 8087 Numeric Data Processor", Proc. 7th Annual Symposium on Computer Architecture, pp. 174-181, 1980.
actual_citation: same
status: ok
kind: paper
unit_classes: [BINARY_ALU, other]
formats: [fp32, fp64, fp80, int16, int32, int64, packed_bcd80]
authority: landmark
pages_read: 8 / 8
---

## summary
The document describes the Intel 8087 stack-based numeric coprocessor, which converts seven external formats into an 80-bit Temporary Real internal format and implements arithmetic/square-root/transcendental instructions (pp.174-179). The document reports architectural/timing/accuracy properties but defers detailed arithmetic algorithms and hardware structures to another publication (p.179).

## families
### shift_round_convert  (role: instantiates)
mechanism: All memory operands are converted without rounding error to Temporary Real before arithmetic, and results are converted to the requested memory type when stored (p.177). The control word selects result precision independently of operand precision and selects unbiased round-to-nearest or one of three directed rounding modes (pp.175-176). Hardware shifts left/right by 0 to 63 places and detects the most significant one for formatting/normalization/denormalization (p.179).
choices:
  rounding_modes: four_modes_unbiased_nearest_plus_three_directed [outside domain]   # pp.175-176
new_choices:
  destination_precision: {24_bit, 53_bit, 64_bit} — selects the precision to which a Temporary Real result is rounded   # pp.175-176
  inbound_conversion: {exact} — requires conversion of supported memory operands to Temporary Real without rounding error   # p.177
slots:
  none
parameters: fp32/fp64/fp80, int16/int32/int64, 80-bit packed BCD with 18 digits and sign; Temporary Real has a 15-bit exponent and 64-bit significand; shift range 0 to 63 places in one clock cycle   # pp.175-177, p.179
results:
| metric | value | unit | technology / device | baseline | condition | page |
| inbound conversion error | no rounding error | — | technology node UNKNOWN; Intel 8087; 1980 | none | conversion of all seven supported data types to Temporary Real | p.177 |
| shift latency | one | clock cycle | technology node UNKNOWN; Intel 8087; 1980 | none | left/right shift by 0 to 63 places | p.179 |
errors_and_checks: The P exception indicates that the delivered result differs from the completely precise result because it was rounded; masked P returns the correctly rounded result, while unmasked P generates an interrupt (pp.176-177, p.179).
conditions: All arithmetic uses Temporary Real internally, so destination precision is independent of operand precision (pp.176-177). Output conversion occurs when a result is stored in another format (p.177).
evidence: §3.1 pp.175-176; §3.2 p.177; §3.3 p.179

### range_reduction  (role: extends)
mechanism: DECOMPOSE separates an operand into an integral exponent and a significand scaled between 1 and 2, with corresponding negative bounds (p.177). REMAINDER computes an exact full or partial remainder after a fixed number of steps; software repeats the instruction until the magnitude of TOP is less than the magnitude of next-of-TOP (pp.177-178).
choices:
  method: decompose_and_partial_remainder_instructions [outside domain]   # p.177
new_choices:
  completion_control: {software_loop_over_fixed_step_primitive} — exposes a fixed-step partial remainder instruction completed by a software termination test   # p.177
slots:
  none
parameters: fixed steps per REMAINDER instruction, count UNKNOWN; termination when |TOP| < |TOP+1|   # p.177
results:
| metric | value | unit | technology / device | baseline | condition | page |
| remainder error | no roundoff error | — | technology node UNKNOWN; Intel 8087; 1980 | none | REMAINDER result or partial remainder | p.177 |
errors_and_checks: The reduced trigonometric functions are exactly periodic with period 2π*, where π* is the machine approximation to π, rather than with period 2π (pp.177-178).
conditions: REMAINDER may return only a partial remainder, so completion requires a software loop (p.177). Exact periodicity applies to the machine approximation π* because π cannot be represented exactly (pp.177-178).
evidence: §3.2 pp.177-178

## new_families
### stack_based_numeric_coprocessor  (domain: fp, closest: single_path, why_not: single_path describes an FP-adder datapath, while this mechanism organizes a complete add/multiply/divide/square-root/SFU coprocessor around a tagged stack and host instruction-stream interface (pp.174-175, p.179))
mechanism: The 8087 monitors the 8086/8088 instruction stream, captures ESCAPE instructions/data, releases the bus after fetching operands, and computes concurrently with the host (pp.174, 178). Eight tagged 80-bit stack registers hold operands/results, and all calculations use Temporary Real (pp.174-175, p.178). A greater-than-64-bit ALU, a one-cycle 0-to-63-place shifter, leading-one detection, and special multiply/divide/remainder/square-root hardware support the instruction set (p.179).
choices:
  stack_depth: Int[8..8:1]   # pp.174-175
  register_width_bits: Int[80..80:1]   # pp.174-175
  internal_significand_bits: Int[64..64:1]   # pp.174, 176
  internal_exponent_bits: Int[15..15:1]   # pp.174-176
  host_interface: {escape_instruction_stream_monitoring}   # pp.174, 178
  host_execution_overlap: Bool   # pp.174, 178
  masked_exception_handling: {on_chip_default_response}   # pp.175-176, p.179
results:
| metric | value | unit | technology / device | baseline | condition | page |
| system speedup | more than 100 | factor | technology node UNKNOWN; Intel 8087; 1980 | software | 8086/8088 system numeric capability | p.174 |
| COMPARE latency | 5 | Microseconds | technology node UNKNOWN; Intel 8087; 1980 | none | 5MHz, stack operands | p.179 |
| ADD (MAGNITUDE) latency | 10 | Microseconds | technology node UNKNOWN; Intel 8087; 1980 | none | 5MHz, stack operands | p.179 |
| SUBTRACT (MAGNITUDE) latency | 16 | Microseconds | technology node UNKNOWN; Intel 8087; 1980 | none | 5MHz, stack operands | p.179 |
| MULTIPLY latency | 16, 24* | Microseconds | technology node UNKNOWN; Intel 8087; 1980 | none | 5MHz, stack operands; shorter if either operand was originally Real (32 bit) | p.179 |
| DIVIDE latency | 38 | Microseconds | technology node UNKNOWN; Intel 8087; 1980 | none | 5MHz, stack operands | p.179 |
| SQUARE ROOT latency | 38 | Microseconds | technology node UNKNOWN; Intel 8087; 1980 | none | 5MHz, stack operands | p.179 |
| transcendental error bound | about 2 | units in the last place | technology node UNKNOWN; Intel 8087; 1980 | none | TANGENT/ARCTANGENT/EXPONENTIAL/LOGARITHM | p.178 |
evidence: §1.0 p.174; §2.0 pp.174-175; §3.2 pp.176-178; §3.3 pp.178-179

## space_gaps
* `shift_round_convert.rounding_modes` lacks the implemented four-mode set of unbiased round-to-nearest plus three directed modes (pp.175-176).
* `shift_round_convert` lacks choices for exact inbound conversion and independently selectable 24/53/64-bit destination precision (pp.176-177).
* `range_reduction.method` lacks a DECOMPOSE plus fixed-step partial-REMAINDER instruction mechanism (p.177).
* The vocabulary lacks a family for a tagged-stack numeric coprocessor with one internal extended format and overlapped host execution (pp.174-175, pp.178-179).

## open_questions
* The adder/multiplier/divider/square-root/SFU circuit topologies are UNKNOWN because the document defers internal hardware and algorithms (p.179).
* The fixed number of steps performed by each REMAINDER instruction is UNKNOWN (p.177).
* The precise mapping of the printed MULTIPLY times `16, 24*` to operand cases is ambiguous beyond the note that the shorter time applies if either operand was originally Real (p.179).
* The fabrication technology node is UNKNOWN (pp.174-181).
