# The L1D prefetcher ensemble

Seven members. `select` names at most one of them per load PC; the
`degree` field then picks a quartile of that member's own native range,
so degree 3 means something different for each.

| member | mechanism | native degrees (Q1/med/Q3) | serves | wasted on |
| --- | --- | --- | --- | --- |
| `none` | issues nothing | -- | a load whose address is unpredictable | -- |
| `next_line` | fetches the following `d` lines | 1 / 2 / 4 | dense sequential reads | anything sparse: every line it fetches is a line it evicted |
| `ip_stride` | per-PC table of the last address and the last delta; replays the delta when it repeats | 1 / 3 / 6 | a load walking an array with a constant step, including a large one | a PC whose delta changes every iteration |
| `streamer` | per 4 KB page, detects a direction after two accesses and runs ahead; never crosses a page | 2 / 4 / 8 | long unbroken runs through big arrays | short visits to many pages |
| `ampm` | per-page access bitmap; a delta is credible when the two previous positions at that delta were touched | 1 / 2 / 4 | strided and interleaved patterns inside one page | pointer chasing |
| `sandbox` | scores candidate offsets against recent accesses and adopts the winner each epoch | 1 / 2 / 4 | a pattern with one dominant offset that shifts over phases | a mixture of several offsets at once |
| `sms` | records which offsets of a page a trigger PC touched, and replays that footprint on the next page | 2 / 4 / 8 | a PC that touches the same shape in page after page | irregular footprints |

Two things worth keeping in mind.

**Degree is not free.** An L1D line fetched wrongly evicts a line that
was going to be used, and costs DRAM bandwidth the demand misses need.
A high degree on a load that misses 99% of the time does not help: the
addresses are not predictable, so the extra prefetches are noise.

**Members train on every access unless filtered.** Each member updates
its tables on every demand request that reaches it, whatever the hint
selected. A load with a random address stream trains `ip_stride` with
garbage deltas and fills `streamer`'s page table with one-shot entries.
That is what the `filter` field is for: it withholds this load from one
named member, so the member's tables stay clean for the loads it does
serve. Filtering costs nothing and is the only way to stop one bad PC
from degrading a member for every other PC.
