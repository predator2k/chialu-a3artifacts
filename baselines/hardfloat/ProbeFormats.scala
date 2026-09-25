// Which HardFloat modules elaborate at each comparison format: (5, 11) fp16,
// (8, 8) bf16, (5, 3) fp8e5m2. HardFloat's adder needs a significand wide
// enough for its internal bit ranges; the probe records what fails, so the
// wrapper can state which lanes the reference design covers.
package hardfloat.eval

import chisel3._
import hardfloat._

object ProbeFormats extends App {
  val fmts = Seq(("fp16", 5, 11), ("bf16", 8, 8), ("fp8e5m2", 5, 3))
  val units: Seq[(String, (Int, Int) => RawModule)] = Seq(
    ("AddRecFN", (e, s) => new AddRecFN(e, s)),
    ("MulRecFN", (e, s) => new MulRecFN(e, s)),
    ("MulAddRecFN", (e, s) => new MulAddRecFN(e, s)),
    ("CompareRecFN", (e, s) => new CompareRecFN(e, s)))
  for ((name, e, s) <- fmts; (uname, mk) <- units) {
    val verdict = try {
      (new chisel3.stage.ChiselStage).emitVerilog(mk(e, s), Array("--target-dir", args.headOption.getOrElse("probe")))
      "ok"
    } catch { case t: Throwable => "FAILED: " + t.getMessage.split("\n").head.take(160) }
    println(s"PROBE $uname($e,$s) $name: $verdict")
  }
}
