# Factbase source change blocks the extension collection (2026-11-25)

Found 2026-11-25 ~05:48 UTC (00:48 local) while collecting the one pre-registered extension (pooling rule, `decisions.md` 2026-11-09).
**The extension has not been scored. No locked or extension outcome was read.**

## What changed at rollcall.com (Factbase)
- **Calendar:** the monthly pages the frozen parser reads (`/factbase/trump/calendar/<month>-<year>/`) now return
  **HTTP 404**. Checked November 2026 and October 2026. The base `/factbase/trump/calendar/` page (HTTP 200, ~96 KB)
  is now drawn client-side from a JSON feed (`media-cdn.rollcall.com/rss/json/trump/calendar-full.json`, 7,364
  entries, 2025-01-18 → 2026-11-26) and a CSV feed.
- **Transcripts:** pages still return HTTP 200, but the text is no longer in the HTML. Example: the Nov 9, 2026
  impromptu press conference page is 108 KB, where earlier pages were ~5 MB. The frozen `parse_transcript` finds
  **0 segments**.
- The cached calendar pages (fetched 2026-11-09 13:28 UTC) and the cached transcripts (through 2026-11-08) are intact.

## How close the new feed is to the old calendar (checked, not used)
For 2026-06-01 → 2026-11-08, (date, time, description) entries:
- 2,113 of the 2,116 entries the old parser stored are identical in the feed.
- 3 are old-only.
- 325 are feed-only, mostly untimed "TBD" travel entries that the old parser never stored.

Transcript links: all 361 old links are in the feed (363 links in the feed). For Nov 9–20, the feed has 151 entries,
24 of them with transcript links.

## What this blocks (counts only)
- KXTRUMPMENTION locked events with first close ≤ 2026-11-20: **19 events / 712 markets** (all strikes).
  - 17 of them first closed by Nov 8. **11** of those have a Factbase start time from the Nov 9 calendar cache, and
    after the spec-v2 filters they come to **11 events / 403 markets** (already priced on Nov 9).
  - **2 events** first closed Nov 9–20. The frozen code can't get start times for them, or transcripts after Nov 8
    (their base rates would miss up to ~11 days of history).
- Pooled floor (≥ 300 markets / ≥ 30 events) is met either way: test 60 / 1,640 + extension 11 / 403 = 71 / 2,043.

## Why this isn't worked around
The task rule is: if the data is missing, stop and tell Ian. Handling it means either:
- new collection code (an adapter, outside `src/` so the freeze still holds), or
- a narrower extension set than the pooling rule defines.

Both are changes to how the pre-registered extension is built, so per the change rule they need Ian's dated
decision first. Requests this session: Kalshi 12 (`collect-markets`, paced 1.05 s, no 429). rollcall/media-cdn 6
(≥ 2 s apart). The JSON feed and the test page are kept only in the session scratchpad and aren't committed (Q4).
