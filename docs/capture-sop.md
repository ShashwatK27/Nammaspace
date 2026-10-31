# Smartphone Capture SOP — NammaSpace

A reproducible **Standard Operating Procedure** for capturing an indoor space with
an ordinary smartphone (no LiDAR required) so that it reconstructs reliably into a
photorealistic 3D Gaussian-splat twin. Written so a non-technical teammate can
follow it and get a usable capture on the first try.

> **Why an SOP matters:** reconstruction quality is set at capture time. Garbage in →
> no amount of training fixes it. This SOP is **data-driven** — every rule below
> traces to a failure we actually hit and fixed (see *Empirical validation*).

---

## 0. Principles (the "why")
Two things matter more than everything else combined: **sharp frames** and **parallax**.
A blurry frame doesn't just blur one spot — the blur spreads through the whole
reconstruction as haze and floaters, and it can't be recovered later. Parallax (the way
near and far objects shift as you *move*) is what gives depth; panning on the spot gives
none and the scene collapses into mush.

So, for every surface you want in the twin:
1. **Sharp frames above all** — fast shutter, no motion blur. Fewer sharp frames beat
   many blurry ones.
2. **Parallax — WALK, never pan.** Move your feet; don't rotate on the spot.
3. **Multiple viewpoints** of each surface (≥3 angles) at **60–80% overlap**.
4. **Texture** — featureless walls, mirrors and glass are the enemies.

Everything below serves those four.

---

## 1. Pre-capture checklist (2 minutes, do every time)
- [ ] **Resolution 1080p or 4K.** Phone's native camera app. *(Our first try was a
      WhatsApp-shared clip silently recompressed to 848×478 → it reconstructed poorly.
      See §6 for transfer.)*
- [ ] **Lock exposure & focus (AE/AF lock)** — tap-and-hold on a mid-brightness
      surface until it locks. Prevents frame-to-frame brightness flicker and refocus blur.
- [ ] **Turn on all lights; open or fully close curtains** — bright, even, diffuse
      light. Avoid blown-out windows and harsh moving shadows.
- [ ] **Tidy the scene** — remove or accept moving elements (people, pets). Moving
      objects create ghost artifacts.
- [ ] **(For Round 2 metric scale)** place 1–3 **printed ArUco markers** of known
      size flat in the scene (floor/table), visible in several frames.
- [ ] **30 GB free + battery > 50%.** A 3-min 4K clip is ~1.5 GB.

## 2. Camera settings
| Setting | Value | Why |
|---|---|---|
| Mode | **Video** | steadier overlap than burst photos |
| Resolution | **4K** (1080p only if you must) | detail = fidelity; 4K is a clear step up |
| Frame rate | **30 fps** | we sample 2–4 fps later; 60 just wastes storage |
| **Shutter speed** | **≥ 1/500 s, locked** | **the #1 rule — stops motion blur.** Sacrifice ISO (sensor noise is fine; blur is fatal) |
| Bitrate / codec | **Max bitrate, H.265** | keep detail; ProRes is overkill (~10 GB/min) |
| Exposure/Focus | **Locked** | no flicker / refocus blur |
| Stabilization | On (standard) | avoid heavy "action/warp" modes |
| Orientation | **Landscape**, kept consistent | don't rotate phone mid-capture |

> The stock camera hides shutter speed and keeps changing it. For control, use a
> **manual video app** that lets you **lock shutter ≥ 1/500 s** (Android: *mcpro24fps*,
> *MotionCam*, or the phone's **Pro video** mode; iOS: *Blackmagic Camera*, free).
> **Clean the lens first.** Use the **main** rear lens — avoid the ultra-wide (0.5×): its
> distortion is harder for SfM and the rasterised splat.

## 3. Capture procedure (the walk)
- **WALK, don't pan.** Move your feet through the space — never stand in one spot and
  rotate. Panning gives no parallax and the reconstruction collapses. *Zoom with your feet.*
- **Speed:** slow, steady walk. **Smooth turns only** — never whip the phone around
  (abrupt motion = blur). Hold the phone **landscape, angled slightly** (not dead-straight)
  — it generates parallax more efficiently.
- **Pattern:** a gradual **spiral** gives the smoothest coverage. Walk slowly **along each
  wall**, **cross through the centre**, orbit furniture, then **loop back the other way**
  (loop closure reconnects the model — our COLMAP now uses it, so one walkthrough can
  cover several rooms as a single scene).
- **Cover every surface from ≥3 angles**, with **60–80% overlap** between views.
- **Three heights — this is critical for a *complete* twin:**
  - **Low** (~0.8 m) — floor, furniture bases.
  - **Mid** (~1.4 m) — eye level, the main pass.
  - **High / tilt up** (~1.8 m, angled upward) — **upper walls and CEILING.**
  > ⚠️ *Lesson learned:* our best capture still rendered a **black upper half** because
  > we only shot eye-level and down — the ceiling was never filmed, so there were no
  > splats there. **Deliberately tilt up and sweep the ceiling and wall-tops.**
- **Orbit key objects** (desk, sofa, reception) — walk a small arc around them.
- **Corners & doorways:** capture each from **two+ directions**. Through a doorway,
  slow almost to a stop and sweep so **many frames see *both* rooms at once** — that
  overlap is what lets loop closure stitch the rooms into one model.
- **Shoot a bit *beyond* the area you'll show.** If you capture only exactly what you want
  viewers to see, the edges fall apart the moment they move past your path.

## 4. Hard surfaces (mitigate SfM failure)
- **Mirrors / glossy floors:** never fill the frame with a reflection; shoot at oblique
  angles.
- **Windows / glass:** blinds partly closed or grazing angles; don't rely on glass for features.
- **Blank / textureless walls:** move slowly and keep a **corner or edge in frame** as a
  feature anchor; sweep adjacent textured areas.

## 5. Duration
- **~1.5–3 minutes per room** → ~300 sharp frames after sampling. (Below ~150 frames
  tends to fragment; see validation.)

## 6. File handling (don't lose your resolution!)
- **Transfer the ORIGINAL file** — **never send the video over WhatsApp/chat as a
  "video"** (it recompresses to ~480p). Use **USB cable, Google Drive (original
  quality), or WhatsApp "Document" mode**.
- **Format:** `.mp4` (H.264). **Name:** `data/raw/<space>_<date>_<take>.mp4`.

## 7. Post-capture validation (how to know it's good *before* training)
Run the pipeline's frames + COLMAP stages, then check:
- [ ] **Registered images ÷ extracted frames ≥ ~90%** in **one** model
      (`sparse/0`). Many sub-models or a low % = capture problem → recapture.
- [ ] **Sparse point count** is in the tens of thousands, not hundreds.
- [ ] Spot-check a few frames for motion blur; the pipeline auto-drops the blurriest 3%.

## 8. Empirical validation (this SOP works — measured)
Same room, two captures through the identical pipeline:

| Capture | Result |
|---|---|
| WhatsApp-shared, 848×478, fast motion | **132 / 225** frames registered, **3 fragmented models**, 4.4k points — patchy, unrecognizable |
| **This SOP:** 4K, 3 min, slow, looped | **351 / 351** frames registered, **1 clean model**, **111k points** — complete, recognizable room |
| 4K multi-room walkthrough, **sequential-only** matching | 620 / 659 registered but **6 fragmented models** — doorways broke the chain |
| Same walkthrough, **+ vocab-tree loop closure** | **579 / 667 in ONE model** — the whole apartment reconnected as a single scene |

The only change was following the SOP (resolution + coverage + overlap), plus enabling
**loop closure** in COLMAP so multi-room walkthroughs stay one connected model.

---

## Metric scale (for Round 2)
COLMAP is accurate only *up to scale*. The ArUco markers from §1 fix **origin,
orientation, and metric scale** when detected in the frames — the reproducible way to
get real metres for obstacle-aware pathfinding. A ruler/A4 sheet in frame is a weaker
fallback.
