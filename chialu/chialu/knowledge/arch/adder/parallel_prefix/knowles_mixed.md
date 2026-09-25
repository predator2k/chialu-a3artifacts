---
family: parallel_prefix
pin: {topology: knowles_mixed}
---
# knowles_mixed

The intermediate prefix graphs between Sklansky and Kogge-Stone: the
network keeps the minimum logical depth of 1 + log2(n) unate stages and
is identified by a per-level lateral fanout vector, where the level-j
wire spans 2^j bits and its fanout is a power of two from 1 to 2^j,
non-decreasing toward the inputs. Reducing the fanout of a level adds
overlapping prefix subterms and lateral wiring, so [16,8,4,2,1] is the
maximal-fanout end and [1,1,1,1,1] is Kogge-Stone.

The mixed point is the pick when neither end of the continuum fits: in a
0.25 um six-metal process the 32-bit [4,4,2,2,1] graph with three
buffered levels runs at 12.7 reference-inverter delays against 13.7 for
the maximal-fanout graph and 11.8 for Kogge-Stone, while both
Kogge-Stone layouts take 80% more area and its transverse wire flux of
42 is nearly three times the 16 of the mixed graph. The choice is made
per level, since fanout and buffering are recorded independently at each
level, and the same lattice is what the (l,f,t) taxonomy places on the
plane of logic levels, fanout and wiring tracks. Irregular
path-dependent hybrids inside a level preserve the critical path but
bring no area advantage in a structured layout, because density follows
the maximum per-level wire flux.

## references

knowles2001 -> S. Knowles, "A Family of Adders", 15th IEEE Symposium on Computer Arithmetic (ARITH-15), 2001 (first presented ARITH-14, 1999).
harris2003 -> D. Harris, "A Taxonomy of Parallel Prefix Networks", 37th Asilomar Conference on Signals, Systems and Computers, 2003.
