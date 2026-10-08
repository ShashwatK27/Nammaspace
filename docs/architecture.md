# Architecture

NammaSpace is built as four **decoupled stages** joined by one contract — the
**scene bundle**. The viewer never knows *how* a scene was reconstructed, which lets
us swap reconstruction engines freely.

```
          ┌─────────────── RECONSTRUCTION (pluggable) ───────────────┐
 CAPTURE ─┤                                                          ├─► SCENE BUNDLE ─► WEB VIEWER
 (phone   │  A. Feed-forward     VGGT  → posed point cloud (seconds) │   scene.json      (zero-install,
  video)  │  B. Classic   COLMAP + 3DGS → Gaussian splat (minutes)   │   + assets         WASD free-roam)
          └──────────────────────────────────────────────────────────┘
```

## Why two reconstruction backends (the differentiator)
Most teams run only **COLMAP + 3DGS** — slow (20–40 min), fragile, and demanding a
strict capture SOP. We keep that for peak fidelity **and** add a 2025 **feed-forward
geometry foundation model** so *any casual video* works:

| Backend | Tool | Strength | Trade-off |
|---|---|---|---|
| **A. Feed-forward** | **VGGT** (CVPR 2025, self-hosted) | **No SfM, no COLMAP, any trajectory, seconds**; robust to casual/unposed video | point cloud (less photorealistic) |
| **B. Classic** | **COLMAP + 3D Gaussian Splatting** (Brush) | photorealistic splats, high fidelity | slow; needs the capture SOP |

Both emit the **same scene bundle**, so the viewer renders either a **GLB point
cloud** (VGGT) or a **Gaussian splat** (3DGS) through one code path — demonstrably
proving the decoupling. The team picks the backend per need; VGGT's
**seconds-not-minutes turnaround** is decisive for Round 3's on-site, time-boxed
reconstruction.

## The scene bundle (`scene.json` — the universal contract)
```jsonc
{
  "id": "string", "name": "string",
  "coordinateSystem": "y-up", "units": "arbitrary | meters",
  "transform": { "quaternion": [x,y,z,w] },     // up-alignment applied to the asset
  "bounds": { "min": [x,y,z], "max": [x,y,z] },  // auto-derived if omitted
  "spawn":  { "position": [x,y,z], "yaw": 0.0 }, // auto-derived if omitted
  "player": { "eyeHeight": 1.6, "walkSpeed": 3.2, "sprintMultiplier": 2.2, "flyVertical": true },
  "assets": { "mesh": "model.glb", "splat": "scene.ksplat" }  // either; both null → placeholder
}
```
- `assets.splat` → Gaussian-splat render (mkkellogg; `.ksplat`/`.spz`/`.ply`).
- `assets.mesh` → GLB mesh **or point cloud** (VGGT output) via GLTFLoader.
- If `bounds`/`spawn` are missing, the viewer **auto-frames** from the geometry, so a
  raw feed-forward reconstruction drops in with a 3-line `scene.json`.

## Reconstruction pipeline (`reconstruction/`)
- `preprocessing/extract_frames.py` — ffmpeg sampling, downscale, blur drop.
- **Backend A:** `pipeline/run_vggt.py` — VGGT forward pass → posed point cloud → GLB.
- **Backend B:** `pipeline/run_colmap.py` → `pipeline/train_splat.py` (Brush) → `.ply`.
- `pipeline/build_scene.py` — turns a COLMAP model + asset into the scene bundle
  (camera-based up estimation, bounds, spawn). Pure stdlib; self-tested.
- `scripts/reconstruct.py` — one-command orchestrator (`frames→colmap→train→scene`).
- Web compression: `viewer/convert-ksplat.mjs` (`.ply` → `.ksplat`, ~10×).

## Web viewer (`viewer/src/`)
- `main.js` — renderer, loop, HUD, pointer-lock; `?scene=<id>` switches scenes.
- `sceneLoader.js` — splat / GLB-mesh / point-cloud loaders + auto-framing.
- `firstPersonControls.js` — velocity-smoothed WASD + Q/E fly, spawn/reset, bounds.
- Deployed on Vercel with COOP/COEP headers (cross-origin isolation for the splat sort).

## Preserved for Round 2/3 (navigation)
Camera poses, scene bounds, coordinate system, and (via ArUco markers) metric scale
are retained so the digital-twin layer can later add POIs, a spatial index, and an
obstacle-aware nav graph **without touching the viewer**.
