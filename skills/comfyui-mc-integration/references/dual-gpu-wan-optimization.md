# Dual-GPU Wan 2.2 / Flux optimization (GPU-NODE = dual-3060)

## Context
GPU-NODE (gpu-node) is the ComfyUI host. It has TWO GPUs; Wan currently uses only
GPU0 (12 GB) and treats GPU1 as "decorative" (WanVideoWrapper rejects it). The
"dual 3060 12 GB" rig Fable analyzed IS this GPU-NODE box. The goal: stop wasting GPU1
and raise output quality + speed for the TikTok + Etsy POD pipelines.

Source: Fable (claude-fable-5) advice, verified against the live Wan 2.2 T2V graph
at `/path/to/pipeline\wan_api.json` (ported to MC as `comfy_workflows/wan22_t2v.json`).

## Hard constraint (Anthropic billing)
Pro / Max / Sage / "free" web-plan credits are claude.ai-WEB only. The API is a
separate meter. None of this optimization consumes those credits — it is free
VRAM rearrangement + model-choice work.

## Core principle
ComfyUI CANNOT split one diffusion model across two cards. The win is OFFLOAD:
put the text encoder (umt5-xxl) + VAE on GPU1, give GPU0's full 12 GB to the
Wan/Flux model. This removes the constant model-swapping that forces resolution/
step cuts → better quality AND speed. Second pattern: two ComfyUI instances (one
per card) for parallel batch throughput (good for TikTok bulk gen).

## Text-to-Video — Wan 2.2 14B
- Use the 14B model, NOT 5B (5B is the usual quality killer).
- Quant: Q4_K_M is the floor for a single 12 GB card. WITH encoder/VAE offloaded
  to GPU1 you can run Q8_K (near-fp16) on GPU0, or keep Q6_K and drop
  `blocks_to_swap`. Current proven graph = Q6_K + blocks_to_swap=30 on GPU0-only.
- Lightning: LightX2V Wan2.2-Lightning LoRA (HIGH-noise + LOW-noise variants —
  do NOT cross them) → 4 steps total (2+2), cfg 1.0, shift 5.0, euler/simple.
  Without Lightning: 20 steps (10+10), cfg 3.5.
- Resolutions: native Wan VERTICAL for TikTok = 720×1280 or 816×1440 (FINALS);
  iteration 480×832. 81 frames @16 fps ≈ 5 s, or 161 @24 fps ≈ 6.7 s.
  (Fable's 1280×720 is 16:9 YouTube-shaped — WRONG for TikTok; use vertical.)
- VAE: Wan 2.2 14B uses the 2.1 VAE (`wan_2.1_vae.safetensors`). Only the 5B has
  its own VAE.
- Encoder: umt5-xxl in fp8 (fp8_e4m3fn_scaled) on GPU1.

## Text-to-Image — Flux.1-dev
- Flux.1-dev Q8_0 GGUF (~12 GB) on GPU0, T5-xxl fp8 encoder on GPU1.
- Settings: 20–28 steps, euler + simple, guidance 3.5, 1024×1024 or 896×1152
  (square for Etsy product shots).
- Stylized/anime: Illustrious-XL or NoobAI checkpoint beats Flux on 12 GB and
  runs trivially.
- Quality lift via SD Ultimate Upscale + 4x model rather than higher native res.
- NOTE: Flux largely IGNORES the negative prompt — don't rely on it there
  (unlike SD/Wan, where negative is essential).

## Two implementation paths

### PATH A — native Wan + ComfyUI-MultiGPU (true dual-GPU split; Fable's pick)
1. Install `ComfyUI-MultiGPU` (maintained fork) + `ComfyUI-GGUF` via ComfyUI Manager
   (or git clone into `custom_nodes`). VERIFY the exact repo before installing —
   forks churn.
2. In ComfyUI, open the built-in **Wan 2.2 T2V** template, then swap the 3 loader
   nodes for the MultiGPU versions:
   - `UnetLoaderGGUFDisTorchMultiGPU` → `wan2.2_t2v_high_noise_14B_Q8_K.gguf`,
     device `cuda:0` (load the low-noise 14B the same way; chain high→low sampler).
   - `CLIPLoaderMultiGPU` → `umt5_xxl_fp8_e4m3fn_scaled.safetensors`, type `wan`,
     device `cuda:1`.
   - `VAELoaderMultiGPU` → `wan_2.1_vae.safetensors`, device `cuda:1`.
3. Apply LightX2V Lightning LoRA (high + low variants) to both models.
4. Settings: 4 steps (2+2), cfg 1.0, shift 5.0, euler/simple; vertical res.
5. OOM fallback: Q4_K_S → then reduce frames BEFORE resolution.
- BUILD THE GRAPH FROM COMFYUI'S BUILT-IN "Wan 2.2 T2V" TEMPLATE ON GPU-NODE (steps
  above). Do NOT ship a hand-written JSON — the template guarantees a correct
  graph for your installed ComfyUI version. Just swap the 3 loader nodes for the
  MultiGPU versions per step 2.

### PATH B — keep proven WanVideoWrapper graph (safe, known-good on this rig)
The ported graph `comfy_workflows/wan22_t2v.json` uses WanVideoWrapper nodes
(`LoadWanVideoT5TextEncoder` / `WanVideoModelLoader` / `WanVideoVAELoader`) with
`blocks_to_swap=30`, Q6_K, T5+VAE offloaded to CPU. In-graph optimizations you can
do WITHOUT restructuring:
- Add Lightning LoRA via `WanVideoLoraSelectMulti` (node 60): set `lora_0` to the
  LightX2V Wan2.2-Lightning (high-noise) file, strength 1; steps 6→4, cfg 1.0,
  shift 5.0. → deployed as `wan22_t2v_lightning.json`.
- Bump Q6_K → Q8_K IF the Q8 GGUF is downloaded to GPU-NODE (better quality).
- Change default resolution to TikTok vertical (see manifest entry).
- The full GPU1 encoder/VAE split requires WanVideoWrapper to support per-node
  device pinning. ATTEMPT: set `load_device` to `cuda:1` on node 11 (T5) and node 38
  (VAE). If WanVideoWrapper rejects it, use Path A.

## Deploy + verify (WSL CANNOT reach GPU-NODE — run from Windows host)
1. On GPU-NODE (or via Windows: `cmd.exe /c "ssh llm-user@gpu-node ..."`):
   - Install node packs via ComfyUI Manager (or git clone into `custom_nodes`).
   - Download models: Wan2.2-T2V-A14B-HighNoise/LowNoise Q8_K (or Q6_K),
     `umt5_xxl_fp8`, `wan_2.1_vae`, LightX2V Lightning LoRAs → ComfyUI models dir.
2. Drop the workflow JSON into `comfy_workflows/` and add a manifest entry.
3. Free GPU-NODE VRAM (unload Ollama brains) — MC "Free GPU-NODE VRAM" button or Ollama
   `keep_alive:0`. NEVER auto-trigger.
4. Start ComfyUI on GPU-NODE: `systemctl start comfyui` (or
   `/home/llm-user/start_comfyui.sh` with `--disable-smart-memory`).
5. Verify the dual-GPU split ACTUALLY happened:
   - `nvidia-smi` on GPU-NODE → both GPUs show memory used (GPU1 = encoder/VAE,
     GPU0 = model). If GPU1 stays at 0, the split didn't take — fall back to Path B
     or fix device strings.
   - MC GEN panel → reload page → pick the new workflow → generate a test clip →
     check output + `nvidia-smi`.
6. Benchmark: count usable-clip rate over ~2 weeks. If >40% rerolls for quality,
   the quantization is costing more than a used RTX 3090 (~NZ$1,200–1,500, 24 GB,
   runs Wan Q8 + Flux fp16 natively, ~2–2.5× throughput, one quality tier up). The
   dual-3060 rig then becomes a dedicated image-gen / encoder box.

## IP RULE (non-negotiable)
All prompts/motifs = YOUR Indigenous-led Aotearoa studio IP. Never name a real
artist as a "style" reference; no copyrighted characters/logos/lyrics in either
prompt. Keep negatives technical-only.

## Files
- Proven graph: `/path/to/pipeline\wan_api.json` → MC: `comfy_workflows/wan22_t2v.json`
- Lightning variant: `comfy_workflows/wan22_t2v_lightning.json` (deployable now)
- Path A graph: built from ComfyUI's built-in Wan 2.2 T2V template on GPU-NODE (no
  hand-written JSON shipped — too version-fragile to verify from WSL)
- Registry: `comfy_workflows/manifest.json`
- MC server: `/path/to/projects` (`comfy_wrapper.py`)


## Privileges and elevation

Some system commands (service management, package installs, writes to system-owned paths) may need elevated rights. Run them as the user that owns the service, or apply your environment's elevation mechanism where required.
