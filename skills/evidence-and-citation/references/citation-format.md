# Citation format

```
[<source-id> <locator>, p. <pdf-page>]
[<source-id> <locator>, pp. <first>-<last>]
```

| Part | Rule | Example |
|---|---|---|
| source-id | An `id` from `sources/pdf-manifest.json` (`sources` or `linked_sources`) or a `framework_aliases` key | `nist-ssdf` |
| locator | Optional. Requirement/control id, section, paragraph, table or figure. Prefer the most specific stable id. | `PW.7.1`, `para 5.32`, `Table 4.2-1`, `Appendix C` |
| page | PDF page index (1-based) in the pinned file. Printed page labels differ from PDF indices in the NASA SE Handbook, Green Book, SSDF, ASVS and AI RMF (they match in NPR 7150.2D and NASA-STD-8739.8B); give the printed page inside the locator if a reader needs it. | `p. 23`, `pp. 52-54` |

## Examples

- `[nist-ai GOVERN 1.1, p. 27]`
- `[nasa-se 6.7 Technical Assessment, p. 196]`
- `[nasa-software-requirements SWE-033, p. 20]`
- `[owasp-asvs V6.2.1, p. 46]`
- `[treasury-green para 5.32, p. 35]`

## Link-only sources

Sources such as `nasa-software` (SWEHB wiki), `gov-service` and `dora` are not bundled. Cite them by id and
section and include the URL and access date in the bibliography; the checker accepts them but cannot
range-check a page, so write `p. 1` only if the page concept is meaningful — otherwise use a footnote-style
reference with the URL instead of the bracket form.

## Why PDF pages

Printed page labels restart in front matter and appendices; PDF indices are unambiguous and checkable
against the pinned file's SHA-256 in the manifest. Record both when the reader will use a printed copy.
