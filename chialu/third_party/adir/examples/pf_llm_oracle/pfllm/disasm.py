"""The disassembly a hint generator reads.

PF-LLM could not use the public ChampSim traces because a trace record
carries the PC but no opcode, so the PCs belong to whoever compiled the
binary. We compile the benchmarks ourselves with `-no-pie`, which keeps
the link-time addresses, so an objdump address is the PC that appears in
the trace. This module turns `objdump -d` into the records the generator
is handed.
"""
from __future__ import annotations

import re
import subprocess

# objdump -d --no-show-raw-insn line:  "  401136:\tmov    rax,QWORD PTR [rbx+rax*8]"
_LINE = re.compile(r"^\s*([0-9a-f]+):\t(\S+)\s*(.*)$")
_FUNC = re.compile(r"^([0-9a-f]+)\s+<([^>]+)>:")
_MEM = re.compile(r"(?:[A-Z]+ PTR\s*)?(?:[a-z]{2}:)?\[([^\]]+)\]")

# mnemonics that write, rather than read, their memory operand
_STORE_ONLY = {"mov", "movq", "movl", "movb", "movw", "movd", "movups", "movaps",
               "movsd", "movss", "movdqa", "movdqu", "vmovups", "vmovaps", "vmovdqa",
               "vmovdqu", "vmovsd", "vmovss"}
_NO_MEM_READ = {"lea", "nop", "prefetcht0", "prefetcht1", "prefetcht2", "prefetchnta"}


def _is_load(mnemonic: str, operands: str) -> bool:
    """True when the instruction reads memory. A `mov` whose memory
    operand is the destination is a store; `lea` computes an address and
    touches no memory; a read-modify-write (`add [rbx],rax`) does read."""
    if mnemonic in _NO_MEM_READ:
        return False
    m = _MEM.search(operands)
    if not m:
        return False
    parts = [p.strip() for p in operands.split(",")]
    mem_is_first = bool(parts) and "[" in parts[0]
    if mem_is_first and mnemonic in _STORE_ONLY:
        return False
    return True


def parse_objdump(text: str) -> list:
    """[{pc, mnemonic, operands, text, func, is_load}], in address order."""
    out, func = [], "?"
    for line in text.splitlines():
        f = _FUNC.match(line.strip())
        if f:
            func = f.group(2)
            continue
        m = _LINE.match(line)
        if not m:
            continue
        pc = int(m.group(1), 16)
        mnem, ops = m.group(2), m.group(3).split("#")[0].strip()
        out.append({"pc": pc, "mnemonic": mnem, "operands": ops,
                    "text": f"{mnem} {ops}".strip(), "func": func,
                    "is_load": _is_load(mnem, ops)})
    out.sort(key=lambda r: r["pc"])
    return out


def disassemble(binary: str, objdump: str = "objdump") -> list:
    r = subprocess.run([objdump, "-d", "--no-show-raw-insn", "-M", "intel", binary],
                       capture_output=True, text=True, check=True)
    return parse_objdump(r.stdout)


def window(disasm: list, pc: int, lines: int = 128) -> str:
    """The `lines` instructions on either side of `pc`, the context the
    paper's model was given (it used 128 either side, 257 in all)."""
    idx = next((i for i, r in enumerate(disasm) if r["pc"] == pc), None)
    if idx is None:
        return ""
    lo, hi = max(0, idx - lines), min(len(disasm), idx + lines + 1)
    out = []
    for i in range(lo, hi):
        r = disasm[i]
        mark = "  <== the load" if r["pc"] == pc else ""
        out.append(f"  {r['pc']:x}:\t{r['text']}{mark}")
    return "\n".join(out)
