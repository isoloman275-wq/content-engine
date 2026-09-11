# YouTube Title: Sidecar Metadata + Live Title Edits (Updated 2026-07-16)

## The Bug (default behaviour is broken)
`youtube_crosspost.py` and `yt_queue.py` historically built the YouTube title like this:
```python
title = v["name"].replace(".mp4","").replace("_"," ").title()
```
So `20260715_195953_evening_ch1.mp4` became the live title **"20260715 195953 Evening Ch1"** — garbage.
The pipeline DOES generate a real topic (e.g. "Why AI PCs are finally worth buying to stop runaway token bills with Bonsai 27B") but it was only written to `content_history.json` (which goes stale) and never carried to the video.

## The Fix — sidecar metadata next to each final video (VERIFIED)
1. In `orchestrator.py`, after `assemble_video`, write `{job_id}.meta.json` next to the final `.mp4` on M2 (`Z:\final\`):
   ```python
   meta_path = os.path.splitext(final_path)[0] + ".meta.json"
   meta = {
     "job_id": job_id, "slot": slot, "channel": ch_id,
     "topic": script_data.get("topic",""), "hook": script_data.get("hook",""),
     "caption": script_data.get("caption",""),
     "hashtags": script_data.get("hashtags",[]),
     "format": script_data.get("format",""),
     "created_at": datetime.now().isoformat(),
   }
   with open(meta_path,"w",encoding="utf-8") as mf:
       json.dump(meta, mf, indent=2, ensure_ascii=False)
   ```
2. In `youtube_crosspost.py` / `yt_queue.py`, read the sidecar over SSH and use `topic` as the title:
   ```python
   def get_meta(name):
       base = name[:-4] if name.endswith(".mp4") else name
       r = run(f'ssh m2 "cat /pipeline/final/{base}.meta.json 2>/dev/null"', timeout=30)
       if r.returncode == 0 and r.stdout.strip():
           try: return json.loads(r.stdout)
           except Exception: return None
       return None
   def make_title(name, meta):
       if meta and meta.get("topic"):
           return meta["topic"].strip()[:100]   # YouTube title hard cap = 100 chars
       return name.replace(".mp4","").replace("_"," ").title()  # fallback only
   ```
   The `description` and `tags` should also come from the sidecar (`caption`, `hashtags`), falling back to defaults.

## Back-filling past videos (no sidecar existed)
The real topics for already-rendered videos live in **`/path/to/pipeline\logs\pipeline.log`** on the Windows side (NOT M2). Parse it statefully:
```python
job_re = re.compile(r'Pipeline starting - job:\s*(\S+?)\s*\|\s*channel')
topic_re = re.compile(r'Topic:\s*(.+)')
job_for_topic = None
mapping = {}
for line in log.splitlines():
    mj = job_re.search(line)
    if mj: job_for_topic = mj.group(1).strip(); continue
    mt = topic_re.search(line)
    if mt and job_for_topic:
        mapping[job_for_topic] = mt.group(1).strip(); job_for_topic = None
```
Then `scp` a `{job_id}.meta.json` for every `.mp4` in `/pipeline/final/` to M2.
Two videos may be unrecoverable (topic not in log or history) — those keep the fallback filename title; flag them for manual edit or leave as-is.
NOTE: `content_history.json` (`/path/to/pipeline\data\channel-1\`) is **stale** (stops ~2026-07-14) — do NOT trust it as the topic source for recent videos; the pipeline.log is authoritative.

## Live title edits on already-uploaded videos (videos().update)
The uploader only had `videos().insert` (upload). To fix titles on live videos add `--update-titles` using `videos().update`:
```python
def update_video_title_api(video_id, title, description="", tags=None):
    youtube = get_authenticated_service()
    body = {"id": video_id, "snippet": {
        "title": title[:100], "description": description[:5000],
        "tags": (tags or [])[:500], "categoryId": "28"}}
    youtube.videos().update(part="snippet", body=body).execute()
```
The `posted/*.json` files store `video_id` + `video_path` (Windows path) + `title`.

## CRITICAL SCOPE GOTCHA — videos().update returns 403
`videos().update` requires the **`https://www.googleapis.com/auth/youtube.force-ssl`** scope.
The original `--setup` only requested `youtube.upload`, so live title edits fail with:
`HttpError 403 ... insufficient authentication scopes ... insufficientPermissions`.
FIX: add the scope to `setup_oauth()` SCOPES, then the USER must re-run `--setup` once to re-consent (broader scope). After that `--update-titles` works.
```python
SCOPES = [
  "https://www.googleapis.com/auth/youtube.upload",
  "https://www.googleapis.com/auth/youtube.force-ssl",
]
```

## CRITICAL WINDOWS-PATH TRAP (WSL/Linux Python)
`os.path.basename("C:\\pipeline\\youtube-queue\\videos\\20260715_x.mp4")` on **Linux Python** returns the
ENTIRE string (backslashes are NOT separators on Linux), so the sidecar lookup `ssh m2 "cat /pipeline/final//path/to/pipeline\..."` fails.
The fixer runs under **Windows Python** (via `powershell.exe`), where backslashes ARE separators — so the fixer worked but WSL-side verification scripts broke.
For WSL-side verification, derive the base with Windows-aware parsing:
```python
import re
base = re.sub(r".*[\\/]", "", video_path)   # strip both / and \ prefixes
base = os.path.splitext(base)[0]
# OR run the lookup via powershell.exe where [System.IO.Path]::GetFileNameWithoutExtension works:
#   $base = [System.IO.Path]::GetFileNameWithoutExtension($d.video_path)
```
