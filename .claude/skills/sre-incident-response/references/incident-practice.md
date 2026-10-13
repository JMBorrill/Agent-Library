# Incident practice notes

Original wording for this library, based on widely used industry practice. The registered source
(`google-sre`) was inaccessible in this environment and its claimed licence forbids adaptations,
so nothing here paraphrases the books.

## Roles
| Role | Does | Does not |
|---|---|---|
| Incident commander (IC) | Owns the incident; sets priorities; assigns roles; decides on mitigations; declares resolution | Debug systems hands-on |
| Operations lead | Investigates and changes production under IC direction | Make external announcements |
| Communications lead | Status page, customer success, internal stakeholders on a fixed cadence | Speculate on cause |
| Scribe | Keeps the timestamped log of observations, decisions and actions | Filter what is "important" |

Hand over IC explicitly ("you are now IC") and record it.

## Status update skeleton
`[time UTC] Impact: <who/what>. Status: <investigating | mitigating | monitoring | resolved>.
Actions: <what we are doing>. Next update: <time>.`

## Blameless writing
- Describe what people knew and saw at the time, and why their actions made sense then.
- Name roles, not people, in causes. Replace "X forgot to run the job" with "the deploy procedure
  relied on a manual reindex step with no check that it ran".
- Look for: missing guardrails, misleading signals, unclear ownership, time pressure, defaults.
- Phrases the checker flags (heuristic): "human/operator error", "should have known", "careless",
  "negligent", "at fault", "<Name> forgot/neglected/ignored/failed to".

## Good action items
- Change the system: automated checks, safer defaults, alerts on the leading signal, runbooks.
- Small and specific, one owner, a priority, a date, a ticket.
- Mix of: prevent (stop recurrence), detect (find it sooner), mitigate (reduce impact), process.

## Timeline tips
- Use UTC with the date on at least the first entry; keep entries in order.
- Include: trigger (change/event), first impact, detection, declaration, key decisions, mitigation,
  recovery, resolution. Time to detect and time to mitigate fall out of these.
