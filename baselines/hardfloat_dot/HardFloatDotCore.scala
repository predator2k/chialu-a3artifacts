// The Berkeley HardFloat FMA cascade behind chiALU's `dot_core` interface of
// targets/eval/vec_dot_acc_cmp_fp16.yaml (two terms) and vec_dot_acc_cmp_fp8.yaml
// (four terms): d = fma(a_{n-1}, b_{n-1}, ... fma(a0, b0, c)), every stage a
// MulAddRecFN on fp32 = (8, 24). The fp16 = (5, 11) or fp8e5m2 = (5, 3) elements
// are recoded (recFNFromFN) and widened exactly to fp32 (RecFNToRecFN, which
// rounds nothing when both widths grow), the addend c enters recoded, and the
// last stage's result leaves through fNFromRecFN.
//
// The contract: each stage rounds its exact product plus addend once to fp32
// (round to nearest even, tininess after rounding), so the cascade rounds after
// every term. Since an fp16 or fp8 product is exact in fp32, this is chiALU's
// `sequential` contract (docs/formats-and-options.md, section 6). Element k of
// `a` and `b` sits at bits [w*k +: w] and is the k-th term added.
//
// HardFloat produces the canonical quiet NaN (0x7fc00000 after fNFromRecFN)
// for every NaN result, which is chiALU's `nan_payload: canonical`. The zero
// sign of an exact cancellation follows IEEE 754 (+0 under RNE), where chiALU's
// sequential reference keeps the chain's first term's sign; that class is
// recorded on the row rather than counted as a value mismatch.
package hardfloat.eval

import chisel3._
import chisel3.util._
import hardfloat._

class HardFloatDotCore(expWidth: Int, sigWidth: Int, terms: Int) extends RawModule {
  override def desiredName = "dot_core"
  val w = expWidth + sigWidth
  val a = IO(Input(UInt((terms * w).W)))
  val b = IO(Input(UInt((terms * w).W)))
  val c = IO(Input(UInt(32.W)))
  val d = IO(Output(UInt(32.W)))

  // an element recoded in its own format, then widened exactly to fp32's recoded form
  def widen(x: UInt): UInt = {
    val conv = Module(new RecFNToRecFN(expWidth, sigWidth, 8, 24))
    conv.io.in := recFNFromFN(expWidth, sigWidth, x)
    conv.io.roundingMode := consts.round_near_even
    conv.io.detectTininess := consts.tininess_afterRounding
    conv.io.out
  }

  var acc: UInt = recFNFromFN(8, 24, c)
  for (k <- 0 until terms) {
    val mac = Module(new MulAddRecFN(8, 24))
    mac.io.op := 0.U                       // a * b + c
    mac.io.a := widen(a((k + 1) * w - 1, k * w))
    mac.io.b := widen(b((k + 1) * w - 1, k * w))
    mac.io.c := acc
    mac.io.roundingMode := consts.round_near_even
    mac.io.detectTininess := consts.tininess_afterRounding
    acc = mac.io.out
  }
  d := fNFromRecFN(8, 24, acc)
}

object GenDotCoreFp16 extends App {
  (new chisel3.stage.ChiselStage).emitVerilog(new HardFloatDotCore(5, 11, 2), args)
}

object GenDotCoreFp8 extends App {
  (new chisel3.stage.ChiselStage).emitVerilog(new HardFloatDotCore(5, 3, 4), args)
}
