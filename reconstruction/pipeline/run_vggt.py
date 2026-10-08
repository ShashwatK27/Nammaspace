"""Self-hosted VGGT reconstruction — feed-forward backend.

Turns a set of frames (or a video) into a posed, colored point cloud in one
forward pass of VGGT (CVPR 2025) — no COLMAP, no SfM, robust to casual/unposed
video. Exports a .glb the viewer loads directly (assets.mesh).

    python run_vggt.py --images data/processed/room2/images --out out.glb --num-frames 16
    python run_vggt.py --video data/raw/room.mp4 --out out.glb         (needs ffmpeg)

VRAM: VGGT-1B fits a few frames on 4 GB; use more frames on a bigger GPU (Colab).
Model: facebook/VGGT-1B (open-source; credit in the abstract).
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import tempfile

import numpy as np
import torch
import trimesh

from vggt.models.vggt import VGGT
from vggt.utils.load_fn import load_and_preprocess_images


def _sample(paths, n):
    if len(paths) <= n:
        return paths
    step = len(paths) / n
    return [paths[int(i * step)] for i in range(n)]


def _frames_from_video(video, n, max_width=1024):
    tmp = tempfile.mkdtemp(prefix="vggt_frames_")
    ff = os.environ.get("FFMPEG_BIN", "ffmpeg")
    vf = f"fps=2,scale='min(iw,{max_width})':-2"
    subprocess.run([ff, "-loglevel", "error", "-i", video, "-vf", vf,
                    "-fps_mode", "vfr", os.path.join(tmp, "f_%04d.jpg")], check=True)
    return _sample(sorted(glob.glob(os.path.join(tmp, "*.jpg"))), n)


def run(paths, out_glb, conf_percentile=50.0):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[vggt] {len(paths)} frames on {device}; loading VGGT-1B…", flush=True)
    model = VGGT.from_pretrained("facebook/VGGT-1B").to(device).eval()

    images = load_and_preprocess_images(paths).to(device)  # [S,3,518,518]
    with torch.no_grad():
        if device == "cuda":
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                preds = model(images)
        else:
            preds = model(images)

    wp = preds["world_points"][0]        # [S,H,W,3]
    conf = preds["world_points_conf"][0]  # [S,H,W]
    imgs = preds["images"][0]            # [S,3,H,W]

    pts = wp.reshape(-1, 3).float().cpu().numpy()
    cols = imgs.permute(0, 2, 3, 1).reshape(-1, 3).float().cpu().numpy()
    c = conf.reshape(-1).float().cpu().numpy()

    # Keep the more-confident points (drops floaters/sky/edges).
    thr = np.percentile(c, conf_percentile)
    keep = c >= thr
    pts, cols = pts[keep], np.clip(cols[keep], 0, 1)
    colors = (cols * 255).astype(np.uint8)

    print(f"[vggt] {len(pts)} points kept ({keep.mean()*100:.0f}% above conf p{conf_percentile:.0f})", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(out_glb)) or ".", exist_ok=True)
    trimesh.PointCloud(vertices=pts, colors=colors).export(out_glb)
    print(f"[vggt] wrote {out_glb} ({os.path.getsize(out_glb)/1e6:.1f} MB)", flush=True)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--images", help="directory of frames")
    src.add_argument("--video", help="video file (extracted with ffmpeg)")
    ap.add_argument("--out", required=True, help="output .glb")
    ap.add_argument("--num-frames", type=int, default=16)
    ap.add_argument("--conf-percentile", type=float, default=50.0,
                    help="drop points below this confidence percentile")
    args = ap.parse_args(argv)

    if args.images:
        paths = _sample(sorted(glob.glob(os.path.join(args.images, "*.jpg"))
                               + glob.glob(os.path.join(args.images, "*.png"))), args.num_frames)
    else:
        paths = _frames_from_video(args.video, args.num_frames)
    if not paths:
        print("no frames found", file=sys.stderr)
        return 1
    return run(paths, args.out, args.conf_percentile)


if __name__ == "__main__":
    raise SystemExit(main())
