# Move library: word- and bit-level rewrites for the micro-optimizer

One file per move. A move is a rewrite the level-2 micro-optimizer may propose on a conformant design point; the micro-optimizer tags each proposal `// MOVE: <id>` so the ledger and the surrogate can learn which moves pay on which families. Synthesis (ABC) already does gate-level Boolean optimization; the moves here are word-level restructurings and identities synthesis cannot find on its own, plus the bit tricks from the Stanford bithacks catalogue that map to datapath logic.

```
---
id: <snake_case>
tier: bit | word | structural
applies_to: [<domains or families>]
preserves: bit_exact | error_bounded | latency_neutral
check: tb | cec | error_budget
effect: <qualitative area/delay direction>
sources: [<bibliography handles>]
---
# <title>

pattern: <what the RTL looks like before>
rewrite: <what to write instead>
when: <where it applies and when it does not pay>
```

`python3 -m chialu.moves` lints the files (handles must exist in the bibliography, applies_to names must be domains or families) and renders the menu the micro-optimizer prompt receives for a family.
