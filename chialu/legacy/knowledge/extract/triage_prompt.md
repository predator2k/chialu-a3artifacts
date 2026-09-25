# Triage pass: which chapters to extract, against the family vocabulary

You receive the chapter list of one long document, with a 500-word
excerpt of each chapter, and the registry's vocabulary of
microarchitecture families. Decide, per chapter, whether an
extraction pass over the full chapter text would add to the registry,
and which families it would inform.

## Rules

1. `extract: true` when the chapter describes, defines, classifies,
   compares or evaluates an arithmetic-unit mechanism that a family in
   the vocabulary covers, or a mechanism the vocabulary lacks but that
   belongs to the same unit classes (integer/FP/decimal/posit adders,
   multipliers, dividers, square root, elementary-function units,
   dot-product/FMA units, format converters, shifters, error checkers).
2. `extract: false` for front and back matter, chapters about
   software libraries, compilers, languages, numerical analysis
   without a hardware mechanism, general VLSI/process/layout material,
   memory/control/IO, and history without design detail.
3. `families` lists vocabulary family names (verbatim) the chapter
   would inform; an empty list is allowed when `extract` is true
   because the chapter proposes something the vocabulary lacks.
4. `why` is one sentence.
5. Output JSON only, matching the schema you were given, with one
   entry per chapter id and no chapter omitted.

## Vocabulary

{{VOCABULARY}}

## Document

key: {{KEY}}
citation: {{CITATION}}
kind: {{KIND}}

{{SEGMENTS}}
