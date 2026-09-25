# The hint, the table and the buffer

Eight bits per load PC:

```
  [7:4] selection   index into the ensemble; 0 means do not prefetch
  [3:2] degree      0 unused, 1/2/3 = Q1 / median / Q3 of the selected
                    member's native range
  [1:0] filter      0 none, 1..3 an index into the table's three-entry
                    filter-candidate list
```

Two bits cannot name one of seven (or, in the paper, twelve) members, so
the packer counts which members the generator filters most often, emits
the top three as a side table with the hints, and rewrites each PC's
filter into a slot index. A generator that filters more than three
distinct members across one binary will have the rest dropped -- so
concentrate the filter on the members it actually helps.

`hint.fields` says how much of this the hardware applies:

* `S` -- selection only; every selected member runs at its median degree
  and nothing is filtered.
* `SD` -- selection and degree.
* `SDF` -- all three.

A table packed for `S` carries no degree or filter bits, so a generator
cannot rely on them under that declaration.

## The table and the buffer

The table (PHT) lives in main memory, indexed by the 48-bit virtual PC.
A 256-entry buffer (PHB) caches it on chip. A lookup that misses the
buffer is served from memory, and while it is in flight that access runs
the reserved entry's policy -- `hint.default`. With a few hundred
distinct load PCs in the region of interest, a 256-entry buffer takes a
cold miss per PC and hits afterwards, so `hint.default` matters far less
than the hints themselves. It matters more as the buffer shrinks.

`phb.entries`, `hint.fields`, `hint.default` and `ensemble` are all
declared in the candidate's block, and every one of them changes what
the generator should emit. Under `ensemble: reduced` only `none`,
`next_line`, `ip_stride` and `streamer` exist, and a hint naming any
other member is ignored by the hardware -- the `ensemble` argument
passed to `emit_hints` is the authoritative list.
