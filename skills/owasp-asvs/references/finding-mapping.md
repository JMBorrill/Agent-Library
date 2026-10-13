# Mapping findings to ASVS requirements

ASVS 5.0 removed direct CWE and NIST mappings from the standard (PDF pp. 22-23); OWASP intends to map
via the Common Requirement Enumeration project instead (PDF p. 22). This library therefore provides a
transparent, deterministic *suggestion* tool, not an authoritative mapping.

## Tool

```sh
python -m agentlib asvs map-findings findings.json [--top 5] [--level 2] [--min-score 1.0] [--format md|json]
```

Input: list (JSON/YAML) or CSV of findings with `title` and/or `description`; optional `id`, `cwe`
(`"CWE-79"`, `79` or a list), `category`, `tags`.

## How candidates are ranked (`agentlib/frameworks/asvs.py`)

1. **Keyword index** built from every requirement's text, its section title and its chapter title
   (catalog `owasp-asvs-5`). Tokens are lower-cased, split on non-alphanumerics, stopwords removed and
   lightly stemmed.
2. **Query** = finding title + description (+ category/tags), expanded with a short, documented synonym
   list (`SYNONYMS`, e.g. `xss`, `idor`, `ssrf`, `jwt`).
3. **Score** = sum over matched terms of IDF x field weight (text 1.0 with BM25 length normalisation,
   section title 1.5, chapter title 0.5) + a bonus for query bigrams found verbatim in the text
   (ignoring common-word bigrams) + a fixed bonus (`CWE_BONUS`) when the finding's CWE appears in the
   library-authored `CWE_SECTION_HINTS` table for the requirement's section.
4. Sorted by score (descending) then requirement id - fully deterministic.

## Using the output

- Treat every candidate as a hypothesis. Run `asvs show <id>` and confirm the requirement is actually
  violated by the observed behaviour. A finding can map to several requirements (e.g. a missing
  documentation decision *and* its implementation).
- If no candidate fits, record the finding as "no direct ASVS requirement" rather than forcing a map.
- Prefer the most specific requirement (e.g. 1.2.4 for SQL injection over generic 1.3.3 sanitisation).
- Do not change the finding's severity because of the requirement's level.
