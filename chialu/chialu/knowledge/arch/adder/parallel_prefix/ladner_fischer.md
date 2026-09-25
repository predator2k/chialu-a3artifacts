---
family: parallel_prefix
pin: {topology: ladner_fischer}
---
# ladner_fischer

The recursive prefix construction with a size/depth knob: the graph is
built from two recursion patterns, one of minimum depth ceil(log2 n)
whose highest-fanout node drives more than n/2 successors, and one that
spends k extra levels, k from 0 to ceil(log2 n), to reduce the size to
O(n) operators. A bounded-fanout form inserts buffers and duplicates
selected prefix operators so fanout stays at any f >= 3 without adding
depth, at a size increase of 1 + O(1/f).

Ladner-Fischer is the pick when the design wants a minimum-depth graph
but must cap fanout below Sklansky's without paying Kogge-Stone's
wiring, since the buffered form holds the depth of the unbounded graph
and adds at most 3n/2 buffers. The k parameter moves the graph along the
same depth-size line that the Brent-Kung end of the family occupies, so
a designer selects k by the delay slack rather than switching topology.
In the (l,f,t) taxonomy it is one of the six established networks on the
plane l + f + t = L - 1, so it trades logic levels, fanout and wiring
tracks against its neighbours along that plane rather than at an
interior point. The evidence on file describes the construction and its
bounds rather than a laid-out adder, so no technology numbers back the
choice.

## references

harris2003 -> D. Harris, "A Taxonomy of Parallel Prefix Networks", 37th Asilomar Conference on Signals, Systems and Computers, 2003.
