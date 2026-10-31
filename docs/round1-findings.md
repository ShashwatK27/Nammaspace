# NammaSpace — Round 1 Findings & Results

*Working notes to lift into the Technical Abstract. Everything below is measured on our
own captures through our own pipeline, on consumer hardware (RTX 2050, 4 GB VRAM / 16 GB
RAM). Numbers are exact and reproducible from the repo.*

---

## 1. One-line claim
A smartphone video of an indoor space → a photorealistic, free-roamable 3D digital twin
in a desktop web browser. **Phone only, no LiDAR.** End-to-end: frames → COLMAP SfM →
3D Gaussian Splatting (Brush, WebGPU) → `.ksplat` → browser free-roam viewer.

## 2. Pipeline architecture (what to describe in the abstract)
Four decoupled stages, each swappable, joined by one contract:

1. **Frame extraction** — sample 2–4 fps from video, auto-drop the blurriest ~3%.
2. **Structure-from-Motion** — COLMAP 4.2 (faiss), sequential matcher **with loop closure**.
3. **Gaussian-splat training** — Brush (wgpu/WebGPU, no CUDA needed), 30k steps.
4. **Web viewer** — three.js + mkkellogg DropInViewer, first-person free-roam.

**Key design decision — `scene.json` is the only contract.** The viewer never knows how
the geometry was produced (splat, mesh, or VGGT point cloud all load through the same
bundle). This is what lets us show a 3DGS scene and a VGGT feed-forward scene in the same
viewer, and is the clean extension point for Round 2.

## 3. Headline result — loop closure turns a multi-room walkthrough into ONE model
The single biggest quality fix this round. A continuous walk through several rooms was
fragmenting at every doorway because the sequential matcher only matched neighbouring
frames.

| Capture / setting | Registered | Models | Points |
|---|---|---|---|
| Multi-room walkthrough, **sequential-only** matching | 620 / 659 | **6 fragments** | — |
| Same walkthrough, **+ vocab-tree loop closure** | **579 / 667** | **1 connected model** | 100k |

Enabling `--SequentialMatching.loop_detection` (faiss vocab tree, auto-downloaded) let
COLMAP recognise when the walk re-entered a seen room and stitch the whole apartment into
a **single** scene. This is the capability that makes a *whole-space* twin possible from
one take, not just isolated rooms.

*Robustness work that made this reliable:* graceful fallback to sequential-only if loop
detection errors (legacy FLANN vocab trees are incompatible with COLMAP ≥ 3.12); and a
`_promote_largest_model` fix because COLMAP numbers sub-models by **creation order, not
size** — `sparse/0` is not always the good model.

## 4. Capture quality is set at capture time — the SOP (data-driven)
Two levers dominate everything else: **sharp frames** and **parallax**. Measured, same room:

| Capture | Registered | Models | Points | Outcome |
|---|---|---|---|---|
| WhatsApp-shared, 848×478, fast motion | 132 / 225 | 3 fragments | 4.4k | patchy, unrecognizable |
| **Our SOP:** 4K, 3 min, slow, looped walk | **351 / 351** | **1 clean model** | **111k** | complete, recognizable |

Actionable rules that came out of this (now in `docs/capture-sop.md`):
- **Shutter ≥ 1/500 s, locked** — the #1 rule. Motion blur spreads through the whole
  reconstruction as haze + floaters and is unrecoverable. Sacrifice ISO, not sharpness.
- **WALK, never pan** — panning gives no parallax; the scene collapses to mush.
- **Spiral + loop back** — feeds loop closure so rooms reconnect.
- **Shoot the ceiling** — a lesson learned the hard way: an eye-level-only capture
  rendered a black upper half because the ceiling was never filmed.
- **Transfer the original file** — never over chat-app "video" (it recompresses to ~480p).

## 5. Training depth — 12k → 30k steps
Brush's densification/growth stops at ~15k steps; the remaining steps are pure refinement
that prunes floaters via opacity resets. Training to the full **30k** (from our earlier
12k) visibly reduces streaky floaters at grazing angles. Floaters correlate strongly with
blurry input frames — which is why §4's shutter rule is upstream of this.

## 6. Scenes delivered (live at nammaspace.vercel.app, switchable in the viewer)
| Scene | Frames | Sparse pts | `.ksplat` | Role |
|---|---|---|---|---|
| **room2** *(default)* | 351 | 111k | 7.1 MB | **Fidelity showcase** — clean single room |
| **livingroom** | 219 | 53k | 8.9 MB | 4K sharp single-room capture |
| **fullhouse** | 579 | 100k | 3.4 MB | **Scale demo** — whole apartment, one connected model |
| apartment | 341 | 166k | 9.1 MB | large single room |
| vggt-room2 | — | — | — | VGGT feed-forward baseline (points) |

**Fidelity vs. coverage tradeoff (worth stating honestly in the abstract):** single rooms
carry 2–3× the splat density of the whole-apartment scene. `fullhouse` proves we can
reconstruct an *entire* space as one connected model from one walkthrough, but at lower
per-surface density on 4 GB VRAM. room2/livingroom are the fidelity proof; fullhouse is
the scale proof.

## 7. Viewer / web-delivery findings
- **`gpuAcceleratedSort: false`** is mandatory — the GPU splat sort silently fails on
  ANGLE/D3D11 (Windows Edge/Chrome); CPU-worker sort renders correctly everywhere.
- **`.ksplat` compression** keeps whole scenes at 3–9 MB → fast load over the web.
- **Per-scene spherical-harmonics** opt-in (`render.sphericalHarmonicsDegree`) — view-
  dependent gloss when wanted, without paying file-size/render cost on every scene.
- COOP/COEP headers enable `SharedArrayBuffer` for multi-threaded splat sorting.

## 8. Hardware reality (a real finding, not just a caveat)
Everything above runs on a **4 GB-VRAM / 16 GB-RAM laptop**. Consequences we hit and
engineered around: large 30k runs OOM / get memory-reaped, so we added VRAM-bounding knobs
(`max-splats`, `max-resolution`, `subsample-frames`) and checkpoint exports. The dense
whole-apartment version is the one run that needs more than this box — the clean path for
it is **Colab + gsplat** (CUDA), not local Brush.

## 9. Claims safe to make in the abstract
- Phone-only capture, no LiDAR, consumer laptop — **no specialised hardware**.
- **Reproducible capture SOP** with measured before/after, so quality isn't luck.
- **Loop closure → whole-space single model** from one continuous take.
- **Method-agnostic scene contract** — viewer decoupled from reconstruction (splat / mesh
  / feed-forward all load the same way); clean Round 2 extension point.
- **Web-native free-roam** at interactive frame rates from compressed multi-MB bundles.

## 10. Honest limitations / Round 2 hooks
- COLMAP is accurate only **up to scale** — metric scale needs ArUco markers (SOP §1);
  required for obstacle-aware pathfinding in Round 2.
- Density on large scenes is VRAM-bound locally → Colab/gsplat for the dense twin.
- Textureless walls, mirrors and glass remain SfM-hard (mitigations in SOP §4).
