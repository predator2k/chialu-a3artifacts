# Reading an access pattern off x86-64 disassembly

The generator sees `objdump -d -M intel` output. The addressing mode and
the surrounding few instructions usually settle what a load does. These
are the shapes that matter here.

**Sequential walk.** The base register is advanced by a constant in the
same basic block:

```
  401248:  movsxd rsi,DWORD PTR [rax]
  40124c:  add    rax,0x4
```

Predictable, and the step is in the code. A small step means dense
sequential access; `next_line` or `streamer` serve it. A step larger
than a cache line means most lines are touched once -- `next_line` then
fetches lines nobody reads, and `ip_stride`, which replays the actual
delta, is the right member.

**Induction-variable index.** The index register is incremented by the
loop, and the scale is in the operand:

```
  401220:  movsxd rax,DWORD PTR [r13+r10*4+0x0]
  ...
  401266:  add    r10,0x1
```

Effective step is `scale * increment`. Same reasoning as above.

**Pointer chase.** The register the load writes is the register it read
through -- the next address is not known until this load returns:

```
  4012c0:  mov    rbx,QWORD PTR [rbx]
```

Nothing can predict this. Prefetching for it is wasted bandwidth and
wasted cache lines, and it trains every member with meaningless deltas.
`select: none`, and filter the member it would otherwise pollute.

**Dependent gather.** The index comes from another load, so the address
is a function of data, not of the loop counter:

```
  401248:  movsxd rsi,DWORD PTR [rax]      <- loads an index
  401252:  cmp    DWORD PTR [rsi],0x0      <- uses it as an address
```

The *index* load is regular and prefetchable; the *gather* is not. They
are different PCs and should get different hints -- this is exactly the
case a single global prefetcher choice cannot serve.

**Reuse.** A small footprint indexed by a wrapped or masked counter:

```
  4012f0:  and    eax,0xff
  4012f3:  mov    edx,DWORD PTR [rbx+rax*4]
```

It already hits in L1. Prefetching for it displaces lines that other
loads need.

## Method

Work from the operand first (does it name a base that the block
advances? is the index register written by a nearby load?), then widen
to the loop body. `loads[i]['context']` is the 128 instructions either
side as text; `disasm` is the whole listing if a def-use walk needs it.
The decision that matters most is which loads get `none`: a wrong
`select` on an unpredictable load costs more than a missing hint on a
predictable one.
