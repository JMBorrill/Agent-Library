---
type: regex
pattern: '\b(fully compliant|guarantee[sd]?|100% (secure|compliant))\b'
flags: i
match: not_contains
target: last_message
---
