# Extraction prompt: one chapter of a book / thesis / slide deck -> one note

You are an extraction engine for a registry of arithmetic-unit
MICROARCHITECTURES. The registry is organized by FAMILY (a mechanism
such as `parallel_prefix` or `booth_recoded_parallel`), each family
having named DESIGN CHOICES with declared value domains and COMPONENT
SLOTS that other families fill. Your job is to read ONE chapter of a
long document and write ONE note that records, against that
vocabulary, what the chapter establishes. A textbook chapter differs
from a paper: it defines mechanisms canonically, classifies their
variants, and compares them in abstract cost units, and it points at
the primary papers. The note captures those four things.

## Rules

1. Record only what the chapter itself states. Do not add knowledge
   from outside the document, do not infer results the chapter does
   not report. A field the chapter does not settle is `UNKNOWN`.
2. Every result row, every design-choice value and every claim in
   `conditions` carries a page reference: the `<<PAGE i>>` index the
   text is labelled with, written `p.i`.
3. Numbers are copied as printed, with the unit as printed. Abstract
   cost units (full-adder delays, gate counts, counter counts,
   "log2 n" expressions) are results and are recorded verbatim, with
   `technology / device` set to `abstract`. Technology-bound numbers
   carry node/device and year, or `UNKNOWN`.
4. Family names, choice names and slot names come from the vocabulary
   below, verbatim. A value outside a choice's declared domain is
   recorded followed by `[outside domain]`. A choice the chapter
   exposes that the vocabulary lacks goes under `new_choices`. A
   mechanism no family covers goes under `## new_families` with a
   proposed `snake_case` name; never stretch an existing family to
   absorb it.
5. The chapter's own classification of variants goes under
   `## taxonomy` as an indented tree in the chapter's terms, each leaf
   mapped to a vocabulary family (or `unmapped`). This section is
   where a textbook contributes most; keep it complete.
6. Primary sources the chapter attributes a mechanism to go under
   `## primary_sources` as `author, year — what it is credited with`,
   copied from the chapter's citations, not from memory.
7. Output the note format below and nothing else: no preamble, no
   commentary, no markdown outside the skeleton. Keep every free-text
   field under the stated length; keep the note under 2500 words.
8. The chapter list of the whole document is given so you know what
   is covered elsewhere: do not extract material the current chapter
   only refers forward or back to.

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
parent: {{PARENT}}
citation: <the document citation, verbatim>
chapter: <chapter title as printed>
pdf_pages: {{PDF_PAGES}}
status: ok | unreadable | out_of_scope
kind: {{KIND}}
unit_classes: [BINARY_ALU | VEC_SFU | VEC_DOT_ACC | other]
formats: [<number formats the chapter covers>]
authority: textbook | thesis | slides
pages_read: <pages actually read> / <pages in the chapter>
---

## summary
<at most 3 sentences: what the chapter covers and what it settles>

## families
### <family_name>  (role: defines | taxonomizes | proposes | instantiates | extends | compares | analyzes)
mechanism: <at most 120 words, in the chapter's own terms: recurrence / encoding / structure>
choices:
  <choice_name>: <value>   # p.N
new_choices:
  <name>: <value> — <what the choice means>   # p.N   (else "none")
slots:
  <slot_name>: <family filling it> [<choice>=<value>, ...]   # p.N   (else "none")
parameters: <widths, radix, formats, table sizes, latency in cycles or delay units>   # p.N
results:
| metric | value | unit | technology / device | baseline | condition | page |
| ... one row per cost/delay/accuracy expression or number a designer would compare against ... |
errors_and_checks: <accuracy contract, error bounds, fault model, detection coverage>   # p.N, or "none"
conditions: <when the variant wins, where it loses, applicability limits>   # p.N
evidence: <sections / figures / tables used>

### <next family_name> ...

## taxonomy
<the chapter's classification of variants, as an indented tree; leaf -> vocabulary family or unmapped>   # p.N
(or "none")

## primary_sources
* <author(s), year — mechanism credited>   # p.N
(or "none")

## new_families
### <proposed_snake_case_name>  (domain: <vocabulary section>, closest: <existing family>, why_not: <one sentence>)
mechanism: <at most 120 words>
choices: <the tunables the mechanism exposes, name: domain>
results: <same table shape as above>
evidence: <pages>
(or the single line "none")

## space_gaps
* <a choice value, choice, slot or family the chapter's evidence suggests the vocabulary should have, with page>   (or "none")

## open_questions
* <anything the chapter leaves ambiguous that the merge pass must not guess>   (or "none")
```

## Document

handle: {{HANDLE}}
parent document: {{PARENT}} — {{CITATION}}
kind: {{KIND}}
this chapter: {{CHAPTER_TITLE}} (pdf pages {{PDF_PAGES}})
families the triage pass expects here: {{FAMILY_HINT}}

chapters of the whole document:
{{CHAPTER_LIST}}

### Chapter text

{{DOCUMENT}}
