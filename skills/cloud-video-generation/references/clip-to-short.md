# Clip to Finished Vertical Short

Post-generation assembly: turning verified downloaded clips into a posted
short with voiceover and burned captions. Generation itself is in SKILL.md.

## Order of operations

1. **ffprobe every clip** (dimensions, duration, audio streams) before any
   edit. A clip with no audio stream is fine — the mix handles it.
2. **VO first, video edits second.** Generate the TTS file, measure its real
   duration with ffprobe, then build the caption timeline mapped onto the
   VIDEO length (proportional by word count, scaled by video_dur / vo_dur).
   Segments stay aligned even when VO and video lengths differ.
3. **SRT hard gates:** first caption starts at 00:00:00,000 (the ≤0.5s rule);
   the LAST caption's end is pinned exactly to video end regardless of
   proportion; captions are on-screen text beats (numbers, labels, CTA), not
   the spoken words verbatim — viewers read before they hear.
4. **Mix:** duck generated ambient to ~15% under the VO (`volume=0.15`), pad
   VO with `apad`, `amix=inputs=2:duration=first` so video length wins. Copy
   the video stream (`-c:v copy`) — do not re-encode here.
5. **Burn captions last** with the subtitles filter + `force_style`
   (monospace FontName, Bold=1, Outline=1, MarginV=30, Alignment=2) and the
   single final re-encode (libx264 crf 19, yuv420p). One encode total: mix
   with copy, re-encode only at the burn.
6. **Verify like a skeptic:** ffprobe the final (dims, duration, audio
   present), then extract frames at start / middle / end and VISION-check
   them: caption text exact, no garbled glyphs, emoji render as real glyphs
   (🔗 renders as a chain, not a tofu box), text sits in a calm low-detail
   region. Text QA beats spec QA — a wrong number in a burned caption ships
   to the feed and cannot be edited after posting.

## Cost discipline

A retry with changed parameters (e.g. `generate_audio:false` after a failed
job) is a new charge under the same budget gate. If the retry stays inside
the approved envelope, proceed and report both costs together; if it exceeds
the envelope, re-ask first.
