#!/usr/bin/env python3
"""Extract a frame for the video-to-article workflow.

Two source modes:

1. Screen Studio project (--project PATH.screenstudio): extract from the
   display-only (no webcam) track at a given *edited-timeline* timestamp.
   Screen Studio records the raw screen into a display track such as
   recording/channel-1-display-<n>.mp4 or channel-2-display-<n>.mp4 (source
   time), while subtitles and the exported video live on the edited timeline.
   project.json scenes[].slices[] describes how source ranges are concatenated
   into the edited timeline; this script maps an edited timestamp back to
   source time and extracts the exact frame with ffmpeg.

2. Plain video (--video PATH.mp4): extract directly at the given timestamp.
   Subtitle time and video time are the same timeline, so no mapping is
   needed. Frames keep whatever the video shows (webcam overlay, branding).

Usage:
  extract_frame.py --project PATH.screenstudio --time 74.5 --output frame.png
  extract_frame.py --project PATH.screenstudio --list
  extract_frame.py --video PATH.mp4 --time 74.5 --output frame.png
  extract_frame.py --video PATH.mp4 --list
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def load_segments(project_path: Path):
    """Return [(edited_start_ms, session_index, source_start_ms, source_end_ms, time_scale)]."""
    doc = json.loads((project_path / "project.json").read_text())
    scenes = doc["json"]["scenes"]
    segments = []
    cursor = 0.0
    for scene in scenes:
        session = scene.get("sessionIndex", 0)
        for sl in scene.get("slices", []):
            scale = sl.get("timeScale", 1) or 1
            src_start = float(sl["sourceStartMs"])
            src_end = float(sl["sourceEndMs"])
            edited_dur = (src_end - src_start) / scale
            segments.append((cursor, session, src_start, src_end, scale))
            cursor += edited_dur
    return segments, cursor


def map_time(segments, edited_ms):
    """Map edited-timeline ms to (session_index, source_ms)."""
    for edited_start, session, src_start, src_end, scale in segments:
        edited_dur = (src_end - src_start) / scale
        if edited_start <= edited_ms < edited_start + edited_dur:
            return session, src_start + (edited_ms - edited_start) * scale
    if segments:
        edited_start, session, src_start, src_end, scale = segments[-1]
        return session, src_end
    raise ValueError("project has no slices")


def display_track(project_path: Path, session: int) -> Path:
    rec = project_path / "recording"
    # Screen Studio has used different channel numbers for the display track
    # across project versions. Match the semantic track name instead of
    # assuming that display is always channel 2.
    matches = sorted(rec.glob(f"channel-*-display-{session}.mp4"))
    matches = [m for m in matches if not m.name.endswith("-0000.mp4")]
    if matches:
        return matches[0]
    raise FileNotFoundError(f"no display track for session {session} in {rec}")


def video_duration_s(video: Path) -> float:
    out = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0", str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return float(out)


def extract(track: Path, time_s: float, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-ss", f"{time_s:.3f}",
            "-i", str(track),
            "-frames:v", "1",
            "-y", str(out),
        ],
        check=True,
    )


def main():
    ap = argparse.ArgumentParser()
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--project", help="PATH.screenstudio project directory")
    source.add_argument("--video", help="plain video file (mp4/mov)")
    ap.add_argument("--time", type=float, help="time in seconds (edited timeline for --project, video time for --video)")
    ap.add_argument("--output", help="output image path (png/jpg)")
    ap.add_argument("--list", action="store_true", help="print timeline info and exit")
    args = ap.parse_args()

    if args.video is not None:
        video = Path(args.video)
        if not video.is_file():
            ap.error(f"video not found: {video}")
        if args.list:
            print(f"video duration: {video_duration_s(video):.2f}s")
            return
        if args.time is None or not args.output:
            ap.error("--time and --output are required unless --list")
        duration = video_duration_s(video)
        if not 0 <= args.time <= duration:
            ap.error(f"--time {args.time} outside video duration 0-{duration:.2f}s")
        out = Path(args.output)
        extract(video, args.time, out)
        print(f"video {args.time:.2f}s -> {out}")
        return

    project = Path(args.project)
    segments, total_ms = load_segments(project)

    if args.list:
        print(f"edited duration: {total_ms / 1000:.2f}s, slices: {len(segments)}")
        for edited_start, session, src_start, src_end, scale in segments:
            print(
                f"  edited {edited_start / 1000:8.2f}s -> session {session} "
                f"source {src_start / 1000:.2f}s-{(src_end) / 1000:.2f}s (x{scale})"
            )
        return

    if args.time is None or not args.output:
        ap.error("--time and --output are required unless --list")

    session, source_ms = map_time(segments, args.time * 1000.0)
    track = display_track(project, session)
    out = Path(args.output)
    extract(track, source_ms / 1000.0, out)
    print(f"edited {args.time:.2f}s -> session {session} source {source_ms / 1000.0:.3f}s -> {out}")


if __name__ == "__main__":
    sys.exit(main())
