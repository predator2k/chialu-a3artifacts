// The Berkeley HardFloat reference design behind chiALU's `alu_core` interface of
// targets/eval/fp_alu_cmp.yaml (see baselines/fpnew/fpnew_alu_core.sv for the
// interface and the contract notes). Design point "one module per (format, op)":
// fp16 = (5, 11), bf16 = (8, 8), fp8e5m2 = (5, 3); recFNFromFN / fNFromRecFN at the
// boundary; MulRecFN and CompareRecFN per format; the fp8 mode has two lanes, so two
// sets of fp8 units. HardFloat has no min/max: the wrapper builds them from
// CompareRecFN and a mux under the minimumNumber rule (a NaN operand yields the other
// operand, two NaNs the canonical NaN), which the report lists as wrapper cost.
//
// What HardFloat's adder elaborates (baselines/hardfloat/ProbeFormats.scala): AddRecFN
// only for fp16 (its raw adder assumes a significand wider than the exponent);
// MulAddRecFN elaborates for fp16 and bf16 but not for (5, 3). So the add of bf16 is
// MulAddRecFN computing a * 1.0 + b (one rounding, the same function), and the fp8
// lanes have no adder in this reference design: fadd and fsub in the fp8 mode return
// zero and the conformance verdict lists that class as not covered.
//
// Rounding modes: HardFloat's round_near_even, round_minMag, round_min, round_max are
// 0, 1, 2, 3, the order of chiALU's rounding_sel. Tininess is detected after rounding.
// Exception flags: HardFloat's {invalid, infinite, overflow, underflow, inexact} map to
// chiALU's [invalid, overflow, underflow, inexact] per lane slot; fcmp, fmin and fmax
// take the quiet comparison's flags (invalid on a signalling NaN alone).
package hardfloat.eval

import chisel3._
import chisel3.util._
import hardfloat._

class FormatUnits(expWidth: Int, sigWidth: Int, addKind: String) extends RawModule {
  // addKind: "add" (AddRecFN), "mac" (MulAddRecFN as a * 1 + b) or "none"
  val w = expWidth + sigWidth
  val io = IO(new Bundle {
    val a = Input(UInt(w.W))
    val b = Input(UInt(w.W))
    val op = Input(UInt(3.W))            // 0 fadd, 1 fsub, 2 fmul, 3 fmin, 4 fmax, 5 fcmp
    val roundingMode = Input(UInt(3.W))
    val y = Output(UInt(w.W))
    val flags = Output(UInt(4.W))        // invalid, overflow, underflow, inexact
  })
  val recA = recFNFromFN(expWidth, sigWidth, io.a)
  val recB = recFNFromFN(expWidth, sigWidth, io.b)

  // the adder: AddRecFN where it elaborates, else MulAddRecFN as a * 1.0 + (-)b
  val addOut = Wire(UInt((w + 1).W))
  val addExc = Wire(UInt(5.W))
  addKind match {
    case "add" =>
      val add = Module(new AddRecFN(expWidth, sigWidth))
      add.io.subOp := io.op === 1.U
      add.io.a := recA
      add.io.b := recB
      add.io.roundingMode := io.roundingMode
      add.io.detectTininess := consts.tininess_afterRounding
      addOut := add.io.out
      addExc := add.io.exceptionFlags
    case "mac" =>
      val mac = Module(new MulAddRecFN(expWidth, sigWidth))
      val one = recFNFromFN(expWidth, sigWidth, Cat(0.U(1.W), ((BigInt(1) << (expWidth - 1)) - 1).U(expWidth.W), 0.U((sigWidth - 1).W)))
      mac.io.op := Cat(0.U(1.W), io.op === 1.U)   // op(0) negates the addend: a * 1 - b
      mac.io.a := recA
      mac.io.b := one
      mac.io.c := recB
      mac.io.roundingMode := io.roundingMode
      mac.io.detectTininess := consts.tininess_afterRounding
      addOut := mac.io.out
      addExc := mac.io.exceptionFlags
    case _ =>
      addOut := 0.U
      addExc := 0.U
  }

  val mul = Module(new MulRecFN(expWidth, sigWidth))
  mul.io.a := recA
  mul.io.b := recB
  mul.io.roundingMode := io.roundingMode
  mul.io.detectTininess := consts.tininess_afterRounding

  val cmp = Module(new CompareRecFN(expWidth, sigWidth))
  cmp.io.a := recA
  cmp.io.b := recB
  cmp.io.signaling := false.B

  // NaN tests on the IEEE encodings, for min/max and the unordered case of fcmp
  def isNaN(x: UInt): Bool = x(w - 2, sigWidth - 1).andR && x(sigWidth - 2, 0).orR
  val nanA = isNaN(io.a)
  val nanB = isNaN(io.b)
  val canonicalNaN = Cat(0.U(1.W), Fill(expWidth, 1.U(1.W)), 1.U(1.W), 0.U((sigWidth - 2).W))

  // fmin / fmax under minimumNumber / maximumNumber; CompareRecFN calls -0 and +0 equal, so the
  // signed-zero order (-0 below +0, as chiALU's reference and FPnew have it) is decided here
  val aNeg = io.a(w - 1)
  val aSmaller = cmp.io.lt || (cmp.io.eq && aNeg && !io.b(w - 1))
  val minSel = Mux(nanA && nanB, canonicalNaN, Mux(nanA, io.b, Mux(nanB, io.a, Mux(aSmaller, io.a, io.b))))
  val maxSel = Mux(nanA && nanB, canonicalNaN, Mux(nanA, io.b, Mux(nanB, io.a, Mux(aSmaller, io.b, io.a))))

  val unordered = nanA || nanB
  val cmpBits = Cat(cmp.io.gt && !unordered, cmp.io.eq && !unordered, cmp.io.lt && !unordered)

  def toFlags(exc: UInt): UInt = Cat(exc(0), exc(1), exc(2), exc(4)) // inexact, underflow, overflow, invalid -> bits 3..0

  io.y := 0.U
  io.flags := 0.U
  switch(io.op) {
    is(0.U, 1.U) { io.y := Mux((addKind != "none").B, fNFromRecFN(expWidth, sigWidth, addOut), 0.U); io.flags := toFlags(addExc) }
    is(2.U)      { io.y := fNFromRecFN(expWidth, sigWidth, mul.io.out); io.flags := toFlags(mul.io.exceptionFlags) }
    // the quiet CompareRecFN raises invalid for a signalling NaN alone: the IEEE rule for min, max and a quiet compare
    is(3.U)      { io.y := minSel; io.flags := toFlags(cmp.io.exceptionFlags) }
    is(4.U)      { io.y := maxSel; io.flags := toFlags(cmp.io.exceptionFlags) }
    is(5.U)      { io.y := cmpBits.pad(w); io.flags := toFlags(cmp.io.exceptionFlags) }
  }
}

class HardFloatAluCore extends RawModule {
  override def desiredName = "alu_core"
  // the ports as chiALU's testbench names them (no `io_` prefix: each is its own IO)
  val a = IO(Input(UInt(16.W)))
  val b = IO(Input(UInt(16.W)))
  val op = IO(Input(UInt(3.W)))
  val mode = IO(Input(UInt(2.W)))              // 0 fp16, 1 bf16, 2 two fp8e5m2 lanes
  val rounding_sel = IO(Input(UInt(2.W)))      // 0 RNE, 1 RTZ, 2 RDN, 3 RUP
  val y = IO(Output(UInt(16.W)))
  val flags = IO(Output(UInt(4.W)))   // flag_scope: per_operation, one word for the whole operation
  val rm = Cat(0.U(1.W), rounding_sel)
  val fp16 = Module(new FormatUnits(5, 11, "add"))
  val bf16 = Module(new FormatUnits(8, 8, "mac"))
  val fp8l0 = Module(new FormatUnits(5, 3, "none"))
  val fp8l1 = Module(new FormatUnits(5, 3, "none"))
  for (u <- Seq(fp16, bf16, fp8l0, fp8l1)) { u.io.op := op; u.io.roundingMode := rm }
  fp16.io.a := a;         fp16.io.b := b
  bf16.io.a := a;         bf16.io.b := b
  fp8l0.io.a := a(7, 0);  fp8l0.io.b := b(7, 0)
  fp8l1.io.a := a(15, 8); fp8l1.io.b := b(15, 8)
  y := 0.U
  flags := 0.U
  switch(mode) {
    is(0.U) { y := fp16.io.y; flags := fp16.io.flags }
    is(1.U) { y := bf16.io.y; flags := bf16.io.flags }
    is(2.U) { y := Cat(fp8l1.io.y, fp8l0.io.y); flags := fp8l1.io.flags | fp8l0.io.flags }
  }
}

object GenAluCore extends App {
  (new chisel3.stage.ChiselStage).emitVerilog(new HardFloatAluCore, args)
}
