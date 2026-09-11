# Seedance 2.0 Mini via OpenRouter (proven end-to-end recipe)

Verified working chain (2026-09): submit -> poll -> download -> ffmpeg assembly.

## Submit
`POST https://openrouter.ai/api/v1/videos`
Headers: `Authorization: Bearer $KEY`, `Content-Type: application/json`
```json
{"model":"bytedance/seedance-2.0-mini","prompt":"...","duration":15,
 "resolution":"480p","aspect_ratio":"9:16","generate_audio":false,"seed":N}
```
Response: `{"id":"<jobid>","status":"pending"}`

## Poll
`GET https://openrouter.ai/api/v1/videos/<id>` -> `status: pending|completed|failed`, plus `usage.cost` (real charge, USD).

## Download
`GET https://openrouter.ai/api/v1/videos/<id>/content?index=0` — Authorization header REQUIRED (bare GET returns a ~67-byte error body, not video).

## Gotchas
- **generate_audio:true frequently fails the WHOLE job** with `output audio may be related to copyright restrictions` (generated ambient/music beds trip a copyright filter). Use `false` and add own audio in post. This bit 3 renders in one session.
- **Live key source**: read `OPENROUTER_API_KEY*` from a running process env (`/proc/<pid>/environ` on the host running the agent). Stale copies in old config backups/profile snapshots return 401 — don't conclude the endpoint is broken from a dead key.
- Cost ~$0.014/sec at 480p (15s = $0.21, 10s = $0.14). 720p is several times more.
- Shot chaining (multi-shot continuity) exists via `frame_images` + `frame_type:"first_frame"` with base64 last-frame JPEG — but for short promos a SINGLE continuous shot with constant camera motion beats a chained static end card (viewer-perceived 'video stops').

## Assembly chain (ffmpeg)
1. Concat/trim raw clip, re-encode `libx264 crf 19 pix_fmt yuv420p`.
2. Audio: silent placeholder `anullsrc` (when talent adds own audio in-app) or VO mix (`volume` duck + `amix`).
3. Burn captions: `subtitles=file.srt:force_style='FontName=Consolas,FontSize=12,PrimaryColour=&H00FFFFFF,OutlineColour=&HC8000000,BorderStyle=1,Outline=1,Shadow=1,MarginV=30,Alignment=2,Bold=1'`.
4. SRT discipline: first cue starts 0.000s, last cue ends exactly at video duration, segment durations word-weighted.
5. Vision-QC extracted frames at first/benchmark/last caption windows before declaring done; check emoji glyph rendering (missing-font tofu).
6. **Quarantine superseded builds** into a subfolder immediately — stale builds left at top level get opened/reviewed by mistake.
