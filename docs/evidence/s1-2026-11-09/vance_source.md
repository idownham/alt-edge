# Vance source search (s1-plan #3b), 2026-11-09

Counts and timing only; no outcomes read.

**Start times — candidate found: Kalshi `/milestones` (category Mentions).** 8 paced requests (`bloodhound
collect-milestones`), 3,974 mention milestones, 311 for KXTRUMPMENTION / KXVANCEMENTION events.

| series, period | events | with a milestone |
|---|---|---|
| Vance dev | 39 | 37 |
| Vance test | 32 | 32 |
| Vance locked | 12 | 12 |
| Trump dev | 157 | 125 |
| Trump test | 84 | 82 |

Check against Factbase on the 93 Trump **dev** events that have both: milestone start − Factbase scheduled start =
median 0 min, p10 −15 min, p90 +0.5 min (min −330, max +840). Of 311 milestones, 289 have :00 seconds and 301 fall
on a quarter hour, so they look like scheduled times, not measured ones. **Caveat:** 230 of 311 were last
updated in one bulk edit on 2026-08-17, after most of these events, so we can't prove the times weren't
revised afterwards. `occurrence_datetime` on Vance markets is not usable: it sits minutes from close, so it looks like
an after-the-fact time.

**Transcripts — not found.** Factbase has search pages for Trump, Biden and Harris only; `/factbase/vance/`
redirects; the general transcript listing is filled in by the browser (no links in the HTML). A few Vance press
briefings sit under Trump's calendar, but there is no list of Vance events. Without a Vance transcript corpus there is
no base rate, so even with milestone start times Vance can't be modelled in S1.

Recommendation (for Ian): drop Vance for S1 per Q3a and note it; keep milestones as the start-time source if Vance
(or another series) is taken up later.
