# ADIR-DECL v1
# ADIR-END
"""The hint generator: for every load PC of a binary, decide which member
of the L1D prefetcher ensemble may prefetch for it, how aggressively, and
which member must not see its demand request.

You are handed the binary's disassembly. Nothing else -- no trace, no IPC,
no profile. Whatever you decide has to be readable off the code.

    emit_hints(disasm, loads, ensemble, fields) -> {pc: hint}

      disasm   every instruction, in address order:
               {pc, mnemonic, operands, text, func, is_load}
      loads    the subset that reads memory; each also carries `context`,
               the 128 instructions either side of it as text
      ensemble the member names this build may select between
      fields   'SDF' | 'SD' | 'S' -- which fields the hardware applies

      hint     {'select': <member or 'none'>,   who may prefetch for this PC
                'degree': 1 | 2 | 3,            Q1 / median / Q3 of that
                                                member's native range
                'filter': <member> or None}     who must not see this load

A PC with no entry, or 'select': 'none', gets no prefetch.

This seed is deliberately the simplest thing that works end to end: it
asks next_line to prefetch for every load at the median degree. It is a
starting point, not a design -- next_line is wrong for a pointer chase
and too timid for a long stride.
"""


def registers(operands):
    """The registers named inside a memory operand, e.g.
    'rax,QWORD PTR [rbx+rcx*8]' -> ['rbx', 'rcx']. Plumbing, not policy."""
    out = []
    if "[" not in operands:
        return out
    inside = operands[operands.index("[") + 1:operands.rindex("]")]
    for tok in inside.replace("+", " ").replace("-", " ").replace("*", " ").split():
        if tok[:1] in "re" and tok.isalnum():
            out.append(tok)
    return out


def destination(operands):
    """The register an instruction writes, when it writes one."""
    first = operands.split(",")[0].strip()
    return first if first and "[" not in first else ""


def emit_hints(disasm, loads, ensemble, fields):
    hints = {}
    for rec in loads:
        hints[rec["pc"]] = {"select": "next_line", "degree": 2, "filter": None}
    return hints

