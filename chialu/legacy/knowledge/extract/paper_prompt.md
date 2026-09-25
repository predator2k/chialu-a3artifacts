# Extraction prompt: one paper -> one note

You are an extraction engine for a registry of arithmetic-unit
MICROARCHITECTURES. The registry is organized by FAMILY (a mechanism
such as `parallel_prefix` or `booth_recoded_parallel`), each family
having named DESIGN CHOICES with declared value domains and COMPONENT
SLOTS that other families fill. Your job is to read ONE document and
write ONE note that records, against that vocabulary, what the
document establishes. The note is a build intermediate: a later pass
merges every note that names a family into that family's description,
and a human reviews every proposed addition to the vocabulary.

## Rules

1. Record only what the document itself states. Do not add knowledge
   from outside the document, do not infer results the document does
   not report, do not fill a field from what "papers like this usually
   say". A field the document does not settle is `UNKNOWN`.
2. Every result row, every design-choice value and every claim in
   `conditions` carries a page reference (`p.N`, or `§N.M` when the
   PDF has no page numbers). Prefer tables and figures over abstract
   and conclusion wording.
3. Numbers are copied as printed, with the unit as printed. Never
   convert units, never normalize to another technology node, never
   round. A relative number (`-23% area`) records its baseline.
   Technology node (or FPGA device) and year of the result are
   required on every result row; write `UNKNOWN` when missing.
4. Family names, choice names and slot names come from the
   vocabulary below, verbatim. A value outside a choice's declared
   domain is still recorded, followed by `[outside domain]`. A choice
   the document exposes that the vocabulary lacks goes under
   `new_choices`. A mechanism no family covers goes under
   `## new_families` with a proposed `snake_case` name; never stretch
   an existing family to absorb it.
5. Identity check first: the document's title and authors must match
   the citation given. On mismatch set `status: mismatch`, fill
   `actual_citation` with the document's real authors, title, venue
   and year, and then extract the document on file exactly as if it
   were the cited one: the note describes the document, and the
   mismatch is re-keyed later. On a match `actual_citation` is `same`.
6. Output the note format below and nothing else: no preamble, no
   commentary, no markdown outside the skeleton. Keep every free-text
   field under the stated length. Keep identifiers, formulas and
   symbol names in the document's own notation.
7. Keep the whole note under 1500 words unless the document is a
   survey or a multi-design comparison, in which case one family
   block per compared design class is allowed.

## Vocabulary (families, design choices, component slots)

Each family line reads `family — one-line doc`, followed by its
choices as `name: domain` and its slots as `slot name: {families
that can fill it}`. `Int[lo..hi:step]` is an integer range; `{a, b}`
is an enumeration; `Bool` is a flag.

{{VOCABULARY}}

## Note format

```
---
handle: {{HANDLE}}
citation: <the citation line, verbatim>
actual_citation: same | <authors, "title", venue, year of the document on file, when it differs>
status: ok | mismatch | unreadable | out_of_scope
kind: paper
unit_classes: [BINARY_ALU | VEC_SFU | VEC_DOT_ACC | other]   # which registry unit classes the work belongs to
formats: [<number formats the work covers: int8, fp16, bf16, fp32, posit16_1, bcd, ...>]
authority: landmark | incremental | survey | standard
pages_read: <pages actually read> / <total pages>
---

## summary
<at most 3 sentences: what the document proposes or establishes, and for which unit>

## families
### <family_name>  (role: proposes | instantiates | extends | compares | analyzes)
mechanism: <at most 120 words, in the document's own terms: recurrence / encoding / pipeline structure as actually built>
choices:
  <choice_name>: <value>   # p.N
  ...                      # one line per vocabulary choice the document fixes; omit choices it leaves open
new_choices:
  <name>: <value> — <what the choice means>   # p.N   (only choices the vocabulary lacks; else "none")
slots:
  <slot_name>: <family filling it> [<choice>=<value>, ...]   # p.N   (else "none")
parameters: <operand widths, formats, radix, segments, table sizes, pipeline stages, latency cycles, II>   # p.N
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ... one row per reported number that a designer would compare against ... |
errors_and_checks: <accuracy contract (max ulp / max abs / error rate / mean error), fault model, detection coverage, false-alarm behavior, alias rate>   # p.N, or "none"
conditions: <when the design wins, where it loses, applicability limits, constraints assumed>   # p.N
evidence: <the sections/tables/figures the block was built from>

### <next family_name> ...

## new_families
### <proposed_snake_case_name>  (domain: <vocabulary section>, closest: <existing family>, why_not: <one sentence>)
mechanism: <at most 120 words>
choices: <the tunables the mechanism exposes, name: domain>
results: <same table shape as above>
evidence: <pages>
(or the single line "none")

## space_gaps
* <a choice value, choice, slot or family the document's evidence suggests the vocabulary should have, one per bullet, with page>   (or "none")

## open_questions
* <anything the document leaves ambiguous that the merge pass must not guess>   (or "none")
```

## Document

handle: {{HANDLE}}
citation: {{CITATION}}
domain hint: {{DOMAIN_HINT}}

{{DOCUMENT}}
