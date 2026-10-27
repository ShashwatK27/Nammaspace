# NammaSpace

An end-to-end spatial engine that turns an ordinary **smartphone video of an indoor
space** into a **photorealistic, interactive 3D digital twin** you can free-roam from
any desktop browser — zero install, no manual 3D modelling.

**Live demo:** https://nammaspace.vercel.app
&nbsp;·&nbsp; `?scene=vggt-room2` for the feed-forward reconstruction.

---

## Overview

```
📱 smartphone video ──► reconstruction ──► scene bundle ──► 🌐 WebGL viewer ──► 🖥️ WASD free-roam
                         (two backends)     (scene.json       (Three.js,
                                             + assets)          60 FPS)
```

The system is split into four decoupled stages joined by a single contract — the
**scene bundle** (`scene.json` + a geometry asset). The viewer is agnostic to how a
scene was produced, so reconstruction backends are interchangeable.

## Reconstruction — dual backend

Depth/stitching for real indoor spaces is hard, so the pipeline supports two engines
that both emit the same scene bundle:

| Backend | Method | Input | Output | Typical runtime |
|---------|--------|-------|--------|-----------------|
| **Feed-forward** | **VGGT** (ViT, single forward pass) | casual / unposed video, any trajectory | posed colored point cloud (`.glb`) | **seconds**, no SfM |
| **Photorealistic** | **COLMAP** SfM + **3D Gaussian Splatting** | SOP-guided capture | Gaussian splat (`.ply` → `.ksplat`) | COLMAP ~16 min + training ~15 min |

- **Feed-forward (VGGT):** no COLMAP, no capture choreography — robust to handheld,
  low-overlap footage. Used when speed / arbitrary input matters.
- **Photorealistic (3DGS):** higher visual fidelity; needs the capture SOP
  (`docs/capture-sop.md`). Trained with Brush, VRAM-capped for commodity GPUs.

Both paths preserve camera poses, scene bounds and coordinate system for downstream
navigation.

## Web viewer

- **Three.js + WebGL2**, zero-install, deployed on Vercel (COOP/COEP headers for
  cross-origin isolation).
- Gaussian splats rendered via `@mkkellogg/gaussian-splats-3d` (CPU-sorted for
  ANGLE/D3D11 compatibility); GLB meshes/point clouds via `GLTFLoader`.
- First-person controls: velocity-smoothed **WASD** + mouse-look, **Q/E** vertical,
  **Shift** sprint, **R** reset; scene bounds clamping and auto-framing.
- Sustains **~60 FPS** on commodity laptops with ~300k splats.

## Performance (measured, RTX 2050 4 GB laptop)

| Stage | Result |
|-------|--------|
| Capture | 4K, ~3 min handheld video |
| Frame extraction | ffmpeg, 2 fps, 1080p downscale, blur/dup filter |
| COLMAP SfM | 351/351 frames registered, 1 model, 111k sparse points (~16 min) |
| 3DGS training | ~295k splats @ 1400px (Brush, VRAM-capped) |
| Web compression | 70 MB `.ply` → **7.1 MB `.ksplat`** (~10×) |
| VGGT feed-forward | 8 frames → ~1 M points `.glb`, single forward pass |
| Viewer | ~60 FPS, ~7 MB initial load |

## Repository layout

```
reconstruction/
  preprocessing/extract_frames.py   # ffmpeg sampling, downscale, blur drop
  pipeline/
    run_colmap.py                   # COLMAP SfM (sequential/exhaustive)
    train_splat.py                  # 3D Gaussian Splatting (Brush)
    run_vggt.py                     # VGGT feed-forward reconstruction -> GLB
    build_scene.py                  # COLMAP model -> scene.json (poses/bounds/up)
    colmap_io.py                    # dependency-free COLMAP model reader
  config/pipeline.json              # tunable parameters
scripts/reconstruct.py              # one-command orchestrator
viewer/
  src/{main,sceneLoader,firstPersonControls}.js
  convert-ksplat.mjs                # .ply -> .ksplat compression
  public/scenes/<id>/               # deployed scene bundles
data/        raw/ + processed/      # captures & intermediates (gitignored)
output/scenes/<id>/                 # generated scene bundles
docs/        architecture.md · capture-sop.md · reconstruction.md
```

## Usage

### Viewer
```bash
cd viewer
npm install
npm run dev          # open the printed URL
```

### Reconstruction (photorealistic, COLMAP + 3DGS)
```bash
# requires ffmpeg, COLMAP, and a splat trainer on PATH
python scripts/reconstruct.py --video data/raw/room.mp4 --scene-id room --run
# -> output/scenes/room/scene.json (+ splat). Compress for the web:
node viewer/convert-ksplat.mjs output/scenes/room/splat/scene.ply viewer/public/scenes/room/splat/scene.ksplat
```

### Reconstruction (feed-forward, VGGT)
```bash
pip install "git+https://github.com/facebookresearch/vggt.git" trimesh
python reconstruction/pipeline/run_vggt.py --video data/raw/room.mp4 --out model.glb --num-frames 16
```

A finished scene bundle (`scene.json` + asset) is placed under
`viewer/public/scenes/<id>/` and loaded with `?scene=<id>`.

## Tech stack & credits

Built on open-source tools, used under their respective licenses:

- [VGGT](https://github.com/facebookresearch/vggt) — feed-forward geometry
- [COLMAP](https://colmap.github.io/) — Structure-from-Motion
- [3D Gaussian Splatting](https://github.com/graphdeco-inria/gaussian-splatting) /
  [Brush](https://github.com/ArthurBrussee/brush) — splat training
- [Three.js](https://threejs.org/) ·
  [@mkkellogg/gaussian-splats-3d](https://github.com/mkkellogg/GaussianSplats3D) ·
  [Vite](https://vitejs.dev/) · [ffmpeg](https://ffmpeg.org/)
