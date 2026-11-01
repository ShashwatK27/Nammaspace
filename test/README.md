# NammaSpace — Sample Data & Reconstruction Test

This directory contains **sample capture data** and the exact commands to reconstruct
a scene end-to-end, so the pipeline can be verified on a real input.

> **Live result (no setup needed):** https://nammaspace.vercel.app
> — `?scene=room2` and `?scene=livingroom` are the scenes reconstructed from the
> samples below.

## Contents
```
test/
├── README.md
└── sample/
    ├── room2_capture.mp4        # single-room capture (feed the whole clip)
    └── livingroom_capture.mp4   # one room cut from a longer apartment walkthrough
```
Both clips are **downscaled, compressed copies** of the original 4K captures (kept small
so the repo stays light and the test runs quickly). The full-resolution originals are
provided separately in the submission's Google Drive folder.

## Prerequisites
Install and put on PATH (or set `FFMPEG_BIN` / `COLMAP_BIN` / `BRUSH_BIN`):
- **ffmpeg** — frame extraction
- **COLMAP 3.12+** — Structure-from-Motion
- **Brush** — WebGPU Gaussian-splat trainer (no CUDA required) — https://github.com/ArthurBrussee/brush
- **Python 3.10+** and **Node 18+** (for the `.ksplat` web compression)

## Reconstruct — one command per scene
From the repository root:

**Room (single-room capture — fully automatic):**
```bash
python scripts/reconstruct.py --video test/sample/room2_capture.mp4 --scene-id room2_test --run
```
The whole clip goes in; Stage 1 samples frames (2 fps), drops near-duplicates
(`mpdecimate`) and the blurriest ~3% automatically — no manual frame selection.

**Living room (same clip is already the trimmed room):**
```bash
python scripts/reconstruct.py --video test/sample/livingroom_capture.mp4 --scene-id livingroom_test --run
```

> The living-room clip was isolated from the full apartment walkthrough using the
> pipeline's built-in trim, which is reproducible on the original:
> ```bash
> python scripts/reconstruct.py --video <apartment_walkthrough.mp4> \
>     --scene-id livingroom_test --start 141 --duration 74 --run
> ```

Each run writes a COLMAP workspace under `data/processed/<scene-id>/` and a scene
bundle under `output/scenes/<scene-id>/` (`scene.json` + the trained splat).

## Compress for the web & view
```bash
# .ply -> .ksplat (about 10x smaller)
node viewer/convert-ksplat.mjs output/scenes/room2_test/train/scene.ply \
     viewer/public/scenes/room2_test/splat/scene.ksplat

# serve the viewer and open ?scene=room2_test
cd viewer && npm install && npm run dev
```

## What to expect
- **COLMAP** registers the frames into a single model (the capture follows the SOP in
  `docs/capture-sop.md` — sharp frames + parallax).
- **Brush** trains for 30k steps and exports a `.ply`; compressing it yields a few-MB
  `.ksplat` that free-roams at ~60 FPS in the browser.
- Reference hardware: a single laptop, **NVIDIA RTX 2050 (4 GB VRAM) / 16 GB RAM** — no
  cloud step required. COLMAP takes a few minutes; training is the longest stage.

> Note: these samples are downscaled to 1280 px to stay small, so a local run is
> slightly lower-resolution than the hosted result, which used the full-res capture.
