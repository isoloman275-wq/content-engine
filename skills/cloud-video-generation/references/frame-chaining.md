# Frame-Chaining — Multi-Shot Continuity for Cloud Video

Two independent text-to-video runs of the 'same scene' produce different-looking
clips: hands change, props drift shape, lighting jumps. Naive stitching reads as
two videos, not one story. Fix: chain shots through literal frames.

## The method (verified end-to-end, seamless)

1. **Shot 1** — text-to-video with a fixed `seed`. Any duration the model supports.
2. **Extract its literal last frame:**
   ```bash
   ffmpeg -y -sseof -0.1 -i shot1.mp4 -frames:v 1 -q:v 2 last_frame.jpg
   ```
3. **Shot 2** — submit with that frame as an exact conditioning frame:
   ```json
   "frame_images": [{"type": "image_url",
                     "image_url": {"url": "data:image/jpeg;base64,<b64>"},
                     "frame_type": "first_frame"}],
   "seed": <same-as-shot1>,
   "prompt": "Continuation: <describe the NEXT action/beat>..."
   ```
   Same seed + same first frame keeps style locked; the prompt only directs the
   new beat (lift the object, turn to camera, reveal the result).
4. **Stitch with audio:**
   ```bash
   ffmpeg -i shot1.mp4 -i shot2.mp4 \
     -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" \
     -map "[v]" -map "[a]" -c:v libx264 -crf 19 -pix_fmt yuv420p -c:a aac out.mp4
   ```

## Why it works

Shot 2's frame 0 IS Shot 1's final frame — the seam is pixel-identical by
construction, not blended or hidden. What the viewer sees at the cut is a framing
change (tight → wide, action A → action B), which reads as deliberate editing.
Identity carry-through across the cut is then a single-generation problem, which
modern models handle well.

## Rules

- Cut ON the handoff, never mid-action — write each shot's prompt to end (and
  begin) on a restful pose or completed motion so the framing change lands on a
  natural beat.
- Keep seed, resolution, and aspect ratio identical across chained shots; change
  only the prompt's action clause.
- Cost scales linearly: an N-shot piece = N × per-shot price. Price the whole
  chain from the live table before asking for the budget go.
- Verify the seam: extract frames either side of the cut (`ffmpeg -ss`) and check
  subject/prop/lighting identity — don't trust 'it should be seamless'.
- For unbroken single-take concepts (continuous camera move, no cut), a model
  with native long-duration support beats chaining — chaining is for cut-based
  storytelling.
