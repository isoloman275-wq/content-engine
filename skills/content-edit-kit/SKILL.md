---
name: content-edit-kit
description: "Edit/caption screen-rec and creative content video."
---

# Content Edit Kit (the lab)

The creative/video-editing stack set up 2026-08-14 for screen-rec + edited
content with Hermes as the technical/automation arm. **You drive the feel; I
handle cuts, captions, b-roll, export.**

## What's installed (verified)
- **OBS Studio** — `C:\Program Files\obs-studio\bin\64bit\obs64.exe`. Has a
  dedicated **"Screen Rec"** scene (Display Capture + Desktop Audio + Mic/Aux)
  added to `C:\Users\<you>\AppData\Roaming\obs-studio\basic\scenes\Untitled.json`
  (backup at `.bak`). Original scene ("Scene") had VSeeFace Game Capture — don't
  break it.
- **Shotcut 26.8.1** — `C:\Users\<you>\AppData\Local\Programs\Shotcut\shotcut.exe`
  (installed per-user, NOT Program Files). Free professional NLE.
- **ffmpeg v8** on Linux + Windows (WinGet at `C:\Users\<you>\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe`).
- **faster-whisper** venv at `/path/to/projects` for word-level captioning.
- **ComfyUI + Wan 2.2** on GPU-NODE `gpu-node:8188` (live) for AI b-roll.

## Key files
- `/path/to/projects` — auto-caption tool
- `/path/to/projects` — launch + batch caption
- `/path/to/projects` — user doc

## Launcher (media-kit.sh)
```bash
cd /path/to/projects
./media-kit.sh shotcut          # open editor
./media-kit.sh obs              # open recorder
./media-kit.sh both
./media-kit.sh caption <f|dir> [--burn] [--model small]   # auto-caption
```
Launch uses `powershell.exe Start-Process` from `/mnt/c` — `cmd start` fails
silently from UNC/WSL working dirs (got "Access is denied"). This matters.

## Caption Copilot
- Word-timed SRT + words.json + optional burned MP4.
- Enforces the HARD rule: first caption ≤0.5s from speech, captions never
  overflow screen width, tail gap flagged. Run on any raw clip.
- **Pitfall (fixed):** burn-in font size must scale to WIDTH for portrait, and
  text must wrap — a long line on 720px-wide 9:16 overflowed off-screen
  ("rdware you already"). Now `fontsize=int(w*0.055)` portrait / `h*0.05`
  landscape + `re.findall` wrapping + `\n` escapes.

## Screen-rec workflow
1. OBS "Screen Rec" scene → record.
2. Shotcut → drop raw clip on timeline.
3. `./media-kit.sh caption raw.mp4 --burn` → .srt (subtitle track) + .json
   (cut signals) + .burned.mp4 (ready to post).
4. Dead-air gaps are auto-flagged as cut candidates — feed them back for
   auto-cuts.

## "Emulate my style"
ffmpeg edits are deterministic — reverse-engineer any cut the user likes into
a repeatable script. When user says "make the next one like that," pin the
pattern (captions, pacing, transitions, b-roll).

## DaVinci Resolve
NOT installable via winget and its download is gated behind a free registration
form on blackmagicdesign.com (API 404s from script). Shotcut covers the need.
Do NOT claim Resolve is script-installable. Offer the form URL only if asked.
