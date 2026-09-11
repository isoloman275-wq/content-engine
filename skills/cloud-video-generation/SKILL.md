---
name: cloud-video-generation
description: "Use for cloud AI video generation — pricing, chains, QA."
version: 1.0.0
license: MIT
---

# Cloud Video Generation

Generate AI video clips via cloud APIs (OpenRouter video endpoint as the reference
implementation — other aggregators follow the same submit/poll/download shape).
Covers: live pricing discipline, budget gate, model selection, multi-shot
continuity chaining, and delivery verification.

## Always-on rules

- **Budget gate.** Every paid render needs explicit per-purchase approval from the
  user — research and price first, present the cost, wait for the go. Verify the
  account balance before AND after; the before/after delta is the audit trail, and
  the job's `usage.cost` is the per-render authority.
- **Price from the live API, never from memory or blog posts.** Model tables,
  durations, resolutions, and rates rotate monthly. Pull `/videos/models` and
  `/credits` fresh every session; a stale price or a discontinued model slug
  produces a wrong budget or a 404.
- **Verify credential liveness before diagnosing the endpoint as broken.** Pull
  API keys from a LIVE process environment or the canonical secret store —
  backup/old config copies carry stale keys whose 401s masquerade as "the API
  is down", sending debugging down the wrong path. One cheap authenticated call
  (credits or models) before any paid submit separates key failure from API
  failure.
- **Quality-check before spend scales.** Models differ enormously in prompt
  adherence and motion at similar price points. Before committing a long or
  multi-shot deliverable, render one SHORT clip per candidate model with the real
  prompt style and let the user judge — price never predicts picture quality.
- **ffprobe-verify every download before claiming success.** A completed job whose
  content URL was fetched without auth, or that saved a provider error body,
  produces a tiny file that looks like success. Check dimensions, frame count, and
  audio-stream presence match what was ordered.
- **Prefer audio ON where it is free.** Several models bundle audio at zero extra
  cost (check the `pricing_skus` table for a `*_without_audio` split — no split
  means bundled). Native audio saves an entire TTS/music pass and the sync edit.
  Generated audio can still fail the WHOLE job on a provider-side copyright
  filter triggered by ambient/background music — when a job fails on audio,
  resubmit with `generate_audio:false` before touching the prompt (VO is dubbed
  on later anyway for short-form work).

## Core procedure

```bash
KEY="$OPENROUTER_API_KEY"
# 1. Discover + budget
curl -s https://openrouter.ai/api/v1/videos/models -H "Authorization: Bearer $KEY" -o /tmp/vidmodels.json
curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $KEY"
# 2. Submit
curl -s -X POST https://openrouter.ai/api/v1/videos \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"<slug>","prompt":"...","duration":5,"resolution":"480p","aspect_ratio":"9:16","generate_audio":true,"seed":777}'
# 3. Poll polling_url every ~20s until status becomes completed|failed (5s clip ≈ 2-5 min)
# 4. Download — the content URL in unsigned_urls[0] STILL REQUIRES the auth header
#    (bare GET returns a tiny error body that masquerades as a download)
curl -sL "$CONTENT_URL" -H "Authorization: Bearer $KEY" -o shot.mp4
# 5. Verify
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,nb_frames -of csv=p=0 shot.mp4
ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 shot.mp4
```

Save each completed poll JSON next to the clip — `usage.cost` in it is the charge
record and reconciles against the credits endpoint.

For cutting generated clips into a finished vertical short (voiceover, captions,
audio ducking, frame-level QA), follow `references/clip-to-short.md`.

## Duration planning

Per-model duration caps differ widely (5s / 15s / 30s). Longer content is either
ONE long generation on a model that supports it, or N shots chained (see
`references/frame-chaining.md`) — chain seams are pixel-locked and read as
deliberate cuts, so N-shot is usually the better social edit, not a compromise.
Price both routes from the live table before choosing; token-formula models cost
height × width × duration × 24 ÷ 1024 tokens, so resolution tier dominates.

## Known model behavior (re-verify against live tables — this section ages)

- Watch for discount windows: budget-tier models at 60% off can undercut premium
  models 3:1 at equal spec — always compare at the EXACT duration × resolution
  ordered, not per-second headline rates.
- `frame_images` = exact-frame image-to-video (first/last); `input_references` =
  style/subject guidance only. If both are sent, `frame_images` wins. Data URIs
  are accepted as image URLs — no public hosting needed for handoff frames.
- `seed` is accepted and makes chain demos reproducible, but providers do not
  guarantee cross-run determinism — never promise pixel-identical reruns.
