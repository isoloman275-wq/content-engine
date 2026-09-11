---
name: comfyui-mc-integration
description: Integrate a remote ComfyUI instance (optionally on a VRAM-sharing GPU host) into the Mission Control dashboard — config-driven workflow registry, preview/gallery, and M2 VRAM coordination. Use when adding image/video generation (SD, Wan T2V/i2v, etc.) to MC or wiring any external ComfyUI service behind the dashboard. Companion to the `comfyui` skill.
---

# ComfyUI → Mission Control Integration

## When to use
- Adding image/video generation to the MC dashboard (GEN panel dropdown + PREVIEW gallery).
- Pointing the wrapper at a remote ComfyUI (here M2 = gpu-node-2:8188) that shares VRAM with agent brains.
- Adding a new workflow (e.g. Wan T2V/i2v) without restarting MC.

## Architecture
```
MC server.py (localhost:8777)
  ├─ comfy_wrapper.py   (config-driven ComfyUI client)
  │     COMFYUI_BASE_URL  (env > comfy_env.json > http://127.0.0.1:8188)
  │     COMFY_CLIENT_ID = "mission-control"
  │     _load_comfy_env() reads comfy_env.json
  │     list_workflows()  -> manifest.json
  │     submit()          -> inject params into graph nodes, POST /prompt, poll /history
  │     comfy_output_bytes (PUBLIC attr) -> output file bytes
  │     gallery()         -> scan output dir (images + videos)
  ├─ /api/comfy/workflows | /status | /submit | /output | /gallery
  ├─ /api/comfy/m2_vram   (read-only: probe M2 Ollama /api/ps)
  └─ /api/comfy/free_m2   (unload M2 models via Ollama keep_alive:0)
       win_proxy_post()   -> POST to firewalled LAN host via cmd.exe /c curl (JSON in C:\tmp)
Frontend: index.html (#gen-panel,#preview-panel,#m2-vram,#free-m2) + css + app.js
  initGen() populates dropdown from /api/comfy/workflows (runs ONCE on load)
  submitGen(), refreshPreview(), refreshM2Vram(), freeBtn click -> confirm -> /api/comfy/free_m2
```

## Adding a workflow (no restart needed)
1. Drop the workflow JSON (ComfyUI API format) into `comfy_workflows/`.
2. Add a manifest entry to `comfy_workflows/manifest.json`:
   ```json
   {
     "id": "wan22_t2v",
     "label": "Wan 2.2 · Text to Video",
     "type": "video",
     "file": "wan22_t2v.json",
     "params": [
       {"name":"prompt","label":"Prompt","type":"text","default":"","from":"16.positive_prompt"},
       {"name":"negative_prompt","label":"Negative","type":"text","default":"","from":"16.negative_prompt"},
       {"name":"seed","label":"Seed","type":"int","default":42,"from":"27.seed"},
       {"name":"steps","label":"Steps","type":"int","default":6,"from":"27.steps"},
       {"name":"cfg","label":"CFG","type":"float","default":1.0,"from":"27.cfg"},
       {"name":"width","label":"Width","type":"int","default":480,"from":"37.width"},
       {"name":"height","label":"Height","type":"int","default":832,"from":"37.height"},
       {"name":"frames","label":"Frames","type":"int","default":161,"from":"37.num_frames"},
       {"name":"filename_prefix","label":"File prefix","type":"text","default":"WanVideo2_1_T2V","from":"30.filename_prefix"}
     ]
   }
   ```
   IMPORTANT: `params` is an **array** of objects, NOT a key→value object. Each entry needs
   `name` (form field id), `label` (UI label), `type` (`text`|`int`|`float`), `default`, and
   `from` = `"<nodeId>.<widget>"` into the workflow JSON. At submit the server sets
   `prompt[nodeId]["inputs"][widget] = value`. Copy node IDs/widgets from the workflow JSON's
   top-level `"<id>": {...}` keys and their `"inputs"` dict. `file` is the API-format workflow
   JSON in `comfy_workflows/`.
3. Server reads manifest PER REQUEST → new workflow is live immediately.
4. Frontend dropdown only repopulates on PAGE RELOAD (initGen runs once) → tell user to refresh.

## Wan 2.2 Text-to-Video (proven, 12 GB VRAM)
- Source proven graph: `/path/to/pipeline/wan_api.json` (WanVideoWrapper, A14B Q6_K, blocks_to_swap=30, force_offload). Copy → `comfy_workflows/wan22_t2v.json`.
- Settings that work on 12 GB: Q6_K GGUF, blocks_to_swap≈30, sampler dpm++_sde, steps 6, cfg 1, shift 5, 480×832, 161 frames.
- Models referenced (must exist on ComfyUI host): `Wan2.2-T2V-A14B-HighNoise-Q6_K.gguf`, `wan_2.1_vae.safetensors`, `umt5_xxl_fp16.safetensors`.
- Param map (node.widget): prompt→16.positive_prompt, neg→16.negative_prompt, seed→27.seed, steps→27.steps, cfg→27.cfg, width/height→37, frames→37.num_frames, prefix→30.filename_prefix.
- Output: VHS_VideoCombine → MP4; gallery treats `videos[]` separately (play, not <img>).

## Pitfalls (hit these before)
1. **`comfy_wrapper.py` must expose PUBLIC function/attribute names** for everything the routes call (`comfy_status`, `comfy_workflows`, `comfy_generate`, `comfy_output_bytes`, `gallery`, …). A route calling a `_private` name raises `AttributeError` **before** the response is sent → the client gets **HTTP 000 / empty response, NOT a 404** (the handler crashes during dispatch, so nothing is returned). This bit us with `_comfy_output_bytes`.
2. **Cache-bust on UI edits**: editing index.html / style.css / app.js requires a `?v=` bump in the HTML links. Server-read assets (manifest, workflow JSON) do NOT need a bump.
3. **M2 VRAM sharing**: ComfyUI cannot run while `qwen3.8:27b-132k` + `ornith:35b` are loaded on M2. Free them first (`/api/comfy/free_m2` → Ollama keep_alive:0). NEVER auto-trigger free_m2 — user confirms.
4. **WSL ↔ LAN**: WSL cannot reach 192.168.1.x and SSH is firewalled. Reach M2 Ollama via `cmd.exe /c curl` with JSON body written to `C:\tmp` temp files (the `win_proxy_post` helper). No remote-exec possible.
5. **Orphan nodes** in a workflow JSON are tolerated (ComfyUI warns, still runs). MUTED_NODES absent in the proven Wan file = clean.
6. **i2v not built** — needs an i2v workflow JSON + an `input_image` manifest param feeding a `LoadImage` → WanVideo image-encode → sampler `image_embeds`.

## To test end-to-end
1. Click "Free M2 VRAM" in GEN panel.
2. Start ComfyUI on M2 (port 8188).
3. Refresh MC page, pick "Wan 2.2 · Text to Video", enter prompt, Generate.
4. MP4 appears in PREVIEW gallery.

## Starting / Restarting ComfyUI on M2

M2 = gpu-node-2, port 8188 (GPU0) + 8189 (GPU1, decorative — Wan rejects it with empty status:error). SSH user is **llm-user** (NOT agent-user). There is a systemd service `comfyui` AND a launcher script `/home/llm-user/start_comfyui.sh`.

**VRAM FIRST:** ComfyUI shares M2's GPU with the Ollama brains (qwen3.8:27b-132k + ornith:35b). Free them first or ComfyUI OOM-kills mid-render:
  - MC GEN panel → "Free M2 VRAM" button, OR
  - POST `{"keep_alive":0}` to M2 Ollama `/api/generate` per loaded model.
  (Do NOT auto-trigger free_m2 — user must confirm.)

**Get shell on M2:** `ssh llm-user@gpu-node-2` (or `ssh m2` if ~/.ssh/config alias set). CRITICAL: from WSL you CANNOT SSH to M2 (firewalled / LAN-unreachable from WSL side) — run the start from the Windows host (`cmd.exe /c "ssh llm-user@gpu-node-2 \"sudo systemctl start comfyui\""`) or directly on M2.

**Start:**
  - Option A (service): `sudo systemctl start comfyui`  (launches both 8188+8189); use `restart` after a crash.
  - Option B (script): `bash /home/llm-user/start_comfyui.sh` — launches both instances with `--disable-smart-memory` (load-bearing; without it Wan OOM-kills on 12GB; do NOT use `--gpu-only`).

**Verify (first-run model load ~45s):**
  - On M2: `curl -s 127.0.0.1:8188/system_stats` → JSON
  - Ports: `for p in 8188 8189; do timeout 4 bash -c "echo > /dev/tcp/gpu-node-2/$p" 2>/dev/null && echo "$p OPEN" || echo "$p CLOSED"; done`
  - From Windows (pipeline side): `cmd.exe /c "curl -s -o nul -w %{http_code} --max-time 8 http://gpu-node-2:8188/"` → 200

## Pre-filling GEN panel defaults (e.g. a default Negative)

To make a field appear pre-filled on every Generate, add a `"default"` key to that param object in `comfy_workflows/manifest.json`. Verified: `static/js/app.js` line ~1133 does `if(p.default!=null) inp.value = p.default;` for every GEN param (textarea included), so the field populates on load.

Gotchas the next session must know:
  - **No server restart needed:** server.py reads `manifest.json` PER REQUEST, so edits are live immediately.
  - **User MUST refresh the MC page:** the GEN dropdown + fields are built ONCE on page load (`initGen` runs once). A manifest edit won't show until the page is reloaded.
  - **Cache-bust rule:** editing `manifest.json` does NOT need a `?v=` bump (server-read asset). Editing `index.html` / `app.js` / `style.css` DOES need a `?v=` bump.

Example — pre-fill a default Negative for SD1.5 + Wan (pure technical-quality junk, zero IP risk under the HARD IP RULE):
  `blurry, low quality, lowres, bad anatomy, extra fingers, mutated hands, deformed, watermark, text, signature, jpeg artifacts, oversaturated`
Add it as `"default":"..."` on each `negative_prompt` param object.

## Positive vs Negative prompt (GEN panel)

- **Positive** = what you WANT (model steers toward it). **Negative** = what you DON'T want (model repels it). Negative is optional but strongly recommended for quality.
- **Model-specific:** SD1.5 / SDXL → negative very effective, always use one. **Flux Dev largely IGNORES the negative prompt** — don't rely on it there. Wan T2V → negative applies, cleans warped frames.
- So: always pre-fill a default negative for SD/Wan workflows; for Flux, leave it empty (or it's simply inert).
- IP RULE: keep positives to YOUR Indigenous-led Aotearoa motifs; never name a real artist as a "style" reference or put copyrighted characters/logos in either prompt.
