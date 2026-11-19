# NammaSpace — Shared Scene Contract (Round 2)

**Owner:** Team Lord Shashwat. This is the single source of truth every workstream builds
on. Changes are agreed with the Team Lord and reflected immediately in the sample bundle.

> One coordinate system · one metric scale · stable frame & object IDs.

---

## 1. Coordinate system & units
- **Right-handed, Y-up.** +X right, +Y up, −Z forward (matches the viewer / three.js).
- **Units: metres.** Every distance, extent, bound, grid cell and route is in metres.
- The reconstruction comes out of COLMAP **up-to-scale**; we multiply by a single
  `metricScale` (section 4) so the stored scene is already in metres. Downstream code
  never re-scales.

## 2. The bundle (what the Team Lord ships)
```
scenes/<id>/
├── scene.json            # this contract, per scene (schema below)
├── splat/scene.ksplat    # visual asset (3DGS), already in metric coords
├── cameras.json          # per-frame camera poses + intrinsics + preprocessing transform
├── depth/<frameId>.png   # per-frame metric depth (16-bit, millimetres) — model TBD (§6)
└── frames/<frameId>.jpg  # the registered frames (source for masks/objects)
```

## 3. `scene.json` (v2 — extends the Round 1 schema)
```jsonc
{
  "id": "apartment",
  "schema": "nammaspace/scene@2",
  "coordinateSystem": "y-up-right-handed",
  "units": "m",
  "metricScale": 1.0,              // already applied to splat+poses; 1.0 = coords are metres
  "transform": { "quaternion": [x,y,z,w] },   // display up-axis correction
  "bounds": { "min": [x,y,z], "max": [x,y,z] },// metres
  "spawn":  { "position": [x,y,z], "yaw": 0.0 },
  "player": { "eyeHeight": 1.6, "radius": 0.25, "walkSpeed": 1.4 }, // metres / m·s⁻¹
  "assets": {
    "splat":   "splat/scene.ksplat",
    "cameras": "cameras.json",
    "depthDir":"depth/",
    "framesDir":"frames/",
    "objects": "objects.json",     // produced by Vaidehi (§7)
    "navmap":  "navmap.json"       // produced by Amartya (§8)
  }
}
```

## 4. Metric scale (how we get real metres)
At capture we place / measure **one known reference distance** (e.g. a 1.000 m tape, a
printed A-series marker, or a measured door width). After COLMAP:
`metricScale = known_metres / measured_distance_in_model`, applied to all point/camera
coordinates before export. **Record the reference and the resulting scale in `scene.json`
and the capture log** so it is auditable (R2 wants claims backed by evidence).

## 5. `cameras.json` — poses + preprocessing (critical for projecting masks to 3D)
```jsonc
{
  "cameras": [{
    "frameId": "f00017",                 // STABLE id, shared by frames/ and depth/
    "model": "OPENCV",
    "intrinsics": { "fx":…, "fy":…, "cx":…, "cy":…, "dist":[…] },
    "imageSize": [W, H],                  // size of the frame actually used
    "qvec": [qw,qx,qy,qz], "tvec": [tx,ty,tz],  // world->camera (metres)
    "preprocess": { "srcSize":[W0,H0], "scale":s, "cropXY":[x,y] } // map a detection in
  }]                                      // the processed frame back to the original pixels
}
```
**Rule:** frame IDs never change, and the `preprocess` transform is preserved so Vaidehi's
masks (in processed-frame pixels) can be mapped to original pixels and projected to 3D.

## 6. Depth (model decision — DA3 vs VGGT)
Per-frame **metric** depth, 16-bit PNG in millimetres, aligned to `cameras.json`.
Candidates benchmarked on real frames (frozen by 20 Nov):
- **VGGT** — multi-view, gives geometry + poses + depth in one pass; already self-hosted.
- **DA3 (Depth Anything 3)** — monocular, sharp relative depth; needs scale alignment to our poses.
Decision criteria: metric consistency with COLMAP poses, edge quality, 4 GB-VRAM/Colab fit,
runtime. Result recorded here once frozen.

## 7. `objects.json` (Vaidehi's output — contract defined here)
```jsonc
{ "objects": [{
  "id": "obj_003", "label": "sofa", "aliases": ["couch"],
  "confidence": 0.86,
  "aabb": { "min":[x,y,z], "max":[x,y,z] },   // metres
  "marker": [x,y,z],                           // where the object IS
  "approachPoint": [x,y,z],                     // a REACHABLE spot to stand (separate!)
  "sourceFrames": ["f00017","f00042"],
  "relations": ["near:entrance"]
}] }
```
**Rule:** the object marker and its reachable approach point are stored separately; manual
corrections are preserved when AI suggestions are regenerated.

## 8. `navmap.json` (Amartya's output — contract defined here)
```jsonc
{
  "origin": [x,z], "cellSize": 0.1,            // metres per grid cell
  "size": [cols, rows],
  "grid": "<base64 occupancy>",                // free / obstacle / UNKNOWN(blocked)
  "playerRadius": 0.25
}
```
Routing + movement collision checks respect `playerRadius`; **unknown space stays blocked
until reviewed**; a disconnected destination returns **"No route available."**

## 9. Change control
Any coordinate, unit, ID or schema change goes through the Team Lord and is pushed to the
sample bundle the same day, so the four workstreams never drift apart.
