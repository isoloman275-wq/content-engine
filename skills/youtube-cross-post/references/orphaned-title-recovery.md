# Orphaned YouTube Title Recovery (no sidecar)

When `python youtube_api_uploader.py --update-titles` logs
`no sidecar topic (keeping current title)` for a video, the FIXER is working
correctly — it just has no real topic to apply. Root cause: the M2 sidecar
`/pipeline/final/<base>.meta.json` does not exist for that upload (predates the
sidecar feature, or orchestrator never wrote one).

## Step 1 — confirm the sidecar is missing on M2
```
ssh llm-user@m2 "for b in 20260710_183020_morn 20260710_190000_even 20260711_123000_midd 20260711_190000_even 20260713_083343_morn; do if [ -f /pipeline/final/$b.meta.json ]; then echo HAVE $b; else echo MISSING $b; fi; done"
```
All MISSING = orphan. All HAVE = fixer should have corrected them (re-run).

## Step 2 — why you can't recover the topic locally
- `/path/to/pipeline\content_history.json` ROTATES — after a few days it holds only
  ~1 entry (today's). Old topics are gone.
- `/path/to/pipeline\logs\pipeline.log` ALSO rotates (fresh each day). Old
  `[AGENT] Topic:` lines are gone.
- Do NOT waste time grepping these for past topics. They aren't there.

## Step 3 — pick a recovery option
1. USER SUPPLIES TOPIC (best, if video still gets views):
   ```
   ssh llm-user@m2 "cat > /pipeline/final/20260713_083343_morn.meta.json <<'EOF'
   {"topic":"Real Topic Here (max 100 chars)","caption":"...","hashtags":["AI","Shorts"]}
   EOF"
   ```
   Then re-run `python youtube_api_uploader.py --update-titles`.

2. STOPGAP CLEANED-FILENAME TITLE (removes garbage look, not real topic):
   Write sidecar with `topic` = humanized filename, e.g.
   `20260713_083343_morn` -> "Morning Update July 13". Same ssh write as above,
   then `--update-titles`.

3. LEAVE THEM (low impact): 1+ week old, and ALL new uploads (post-sidecar)
   already title correctly. The fixer's `already correct, skip` lines confirm the
   healthy ones.

## Do NOT
- Loop `--update-titles` expecting it to invent titles. It won't. The blocker is
  always missing sidecar metadata, never the fixer code.
- Trust `os.path.basename` on a Windows path from WSL — use
  `re.sub(r".*[/\\]", "", p)` or powershell `Split-Path -Leaf`.
