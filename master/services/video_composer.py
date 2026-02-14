"""
Video Composer Service — FFmpeg-based video composition.

Inspired by huobao-drama's ffmpeg.go, adapted for our Python/FastAPI pipeline.
Supports: concatenation, xfade transitions, resolution normalization, audio handling.
"""

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from loguru import logger


# ── Transition Types ────────────────────────────────────────────────────────

class TransitionType(str, Enum):
    NONE = "none"
    FADE = "fade"
    FADEBLACK = "fadeblack"
    FADEWHITE = "fadewhite"
    DISSOLVE = "dissolve"
    WIPELEFT = "wipeleft"
    WIPERIGHT = "wiperight"
    WIPEUP = "wipeup"
    WIPEDOWN = "wipedown"
    SLIDELEFT = "slideleft"
    SLIDERIGHT = "slideright"
    SLIDEUP = "slideup"
    SLIDEDOWN = "slidedown"
    CIRCLEOPEN = "circleopen"
    CIRCLECLOSE = "circleclose"
    PIXELIZE = "pixelize"


# ── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class VideoClip:
    """Represents a single clip in the composition timeline."""
    path: str                                  # Local file path to video
    duration: float = 0.0                      # Duration in seconds
    start_time: float = 0.0                    # Trim start
    end_time: float = 0.0                      # Trim end (0 = full clip)
    transition_type: str = "none"              # Transition to NEXT clip
    transition_duration: float = 1.0           # Transition duration (seconds)


@dataclass
class ComposeOptions:
    """Options for final video composition."""
    output_path: str
    clips: List[VideoClip] = field(default_factory=list)
    resolution: Optional[Tuple[int, int]] = None    # Force resolution (w, h)
    fps: int = 24
    codec: str = "libx264"
    preset: str = "medium"
    crf: int = 23


# ── Video Composer Service ──────────────────────────────────────────────────

class VideoComposer:
    """
    FFmpeg subprocess wrapper for video composition.
    
    Workflow:
    1. Normalize all clips (re-encode to uniform resolution/codec)
    2. Apply xfade transitions between adjacent clips
    3. Handle audio (silence generation, crossfade)
    4. Output final composed video
    """

    def __init__(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), "aipipe-compose")
        os.makedirs(self.temp_dir, exist_ok=True)
        self._verify_ffmpeg()

    def _verify_ffmpeg(self):
        """Check that FFmpeg and FFprobe are available."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, check=True, timeout=10
            )
            subprocess.run(
                ["ffprobe", "-version"],
                capture_output=True, check=True, timeout=10
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            logger.error(f"FFmpeg/FFprobe not found: {e}")
            raise RuntimeError(
                "FFmpeg is required for video composition. "
                "Install from https://ffmpeg.org/download.html"
            ) from e

    # ── Public API ──────────────────────────────────────────────────────────

    def compose(self, opts: ComposeOptions) -> str:
        """
        Compose multiple video clips into a single output file.
        Returns the output file path.
        """
        if not opts.clips:
            raise ValueError("No video clips to compose")

        logger.info(f"Starting composition: {len(opts.clips)} clips → {opts.output_path}")

        # 1. Validate all input files exist
        for i, clip in enumerate(opts.clips):
            if not os.path.exists(clip.path):
                raise FileNotFoundError(f"Clip {i} not found: {clip.path}")

        # 2. Get actual durations from files
        for clip in opts.clips:
            if clip.duration <= 0:
                clip.duration = self.get_video_duration(clip.path)

        # 3. Detect target resolution
        if opts.resolution:
            target_w, target_h = opts.resolution
        else:
            target_w, target_h = self._detect_max_resolution(opts.clips)
        logger.info(f"Target resolution: {target_w}x{target_h}")

        # 4. Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(opts.output_path)), exist_ok=True)

        # 5. Single clip → just re-encode
        if len(opts.clips) == 1:
            self._reencode_clip(opts.clips[0].path, opts.output_path, target_w, target_h, opts)
            logger.info(f"Single clip composed → {opts.output_path}")
            return opts.output_path

        # 6. Check if any transitions are needed
        has_transitions = any(
            clip.transition_type.lower() not in ("none", "")
            for clip in opts.clips[:-1]  # last clip's transition is ignored
        )

        if not has_transitions:
            # Simple concatenation (fast, no re-encode needed for concat)
            self._concat_simple(opts.clips, opts.output_path, target_w, target_h, opts)
        else:
            # Complex xfade composition
            self._compose_with_xfade(opts.clips, opts.output_path, target_w, target_h, opts)

        logger.info(f"Composition complete → {opts.output_path}")
        return opts.output_path

    def compose_from_shots(self, shots: list, output_path: str,
                           transition: str = "fade",
                           transition_duration: float = 0.5) -> str:
        """
        Convenience method: compose directly from Shot model objects.
        Only includes shots that have a generated_video_path.
        """
        clips = []
        for shot in shots:
            video_path = getattr(shot, "generated_video_path", None)
            if not video_path or not os.path.exists(video_path):
                logger.warning(f"Shot {shot.id} has no video, skipping")
                continue

            clips.append(VideoClip(
                path=video_path,
                duration=getattr(shot, "duration_seconds", 0.0),
                transition_type=transition,
                transition_duration=transition_duration,
            ))

        if not clips:
            raise ValueError("No shots have generated videos to compose")

        opts = ComposeOptions(output_path=output_path, clips=clips)
        return self.compose(opts)

    # ── FFprobe Utilities ───────────────────────────────────────────────────

    def get_video_duration(self, path: str) -> float:
        """Get video duration in seconds using ffprobe."""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1",
                 path],
                capture_output=True, text=True, timeout=30
            )
            duration = float(result.stdout.strip())
            return duration if duration > 0 else 1.0
        except Exception as e:
            logger.warning(f"Could not get duration for {path}: {e}")
            return 1.0

    def get_video_resolution(self, path: str) -> Tuple[int, int]:
        """Get video resolution (width, height) using ffprobe."""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-select_streams", "v:0",
                 "-show_entries", "stream=width,height",
                 "-of", "csv=p=0",
                 path],
                capture_output=True, text=True, timeout=30
            )
            parts = result.stdout.strip().split(",")
            if len(parts) == 2:
                w, h = int(parts[0]), int(parts[1])
                if w > 0 and h > 0:
                    return (w, h)
        except Exception as e:
            logger.warning(f"Could not get resolution for {path}: {e}")
        return (1920, 1080)  # Default

    def has_audio_stream(self, path: str) -> bool:
        """Check if video file contains an audio stream."""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-select_streams", "a:0",
                 "-show_entries", "stream=codec_type",
                 "-of", "default=noprint_wrappers=1:nokey=1",
                 path],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout.strip() == "audio"
        except Exception:
            return False

    # ── Private: Resolution Detection ───────────────────────────────────────

    def _detect_max_resolution(self, clips: List[VideoClip]) -> Tuple[int, int]:
        """Find the maximum resolution across all clips."""
        max_w, max_h = 0, 0
        for clip in clips:
            w, h = self.get_video_resolution(clip.path)
            max_w = max(max_w, w)
            max_h = max(max_h, h)
        return (max_w or 1920, max_h or 1080)

    # ── Private: Simple Concatenation ───────────────────────────────────────

    def _reencode_clip(self, input_path: str, output_path: str,
                       target_w: int, target_h: int, opts: ComposeOptions):
        """Re-encode a single clip with target resolution."""
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                   f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", opts.codec, "-preset", opts.preset, "-crf", str(opts.crf),
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            "-y", output_path
        ]
        self._run_ffmpeg(cmd, "re-encode")

    def _concat_simple(self, clips: List[VideoClip], output_path: str,
                       target_w: int, target_h: int, opts: ComposeOptions):
        """Concatenate clips without transitions using concat demuxer."""
        # First normalize all clips to same resolution
        normalized = []
        try:
            for i, clip in enumerate(clips):
                norm_path = os.path.join(self.temp_dir, f"norm_{int(time.time())}_{i}.mp4")
                self._reencode_clip(clip.path, norm_path, target_w, target_h, opts)
                normalized.append(norm_path)

            # Create concat file list
            list_file = os.path.join(self.temp_dir, f"concat_{int(time.time())}.txt")
            with open(list_file, "w") as f:
                for p in normalized:
                    # Escape single quotes in path for FFmpeg concat
                    escaped = p.replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

            cmd = [
                "ffmpeg",
                "-f", "concat", "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                "-y", output_path
            ]
            self._run_ffmpeg(cmd, "concat")

            # Clean up
            os.remove(list_file)
        finally:
            for p in normalized:
                if os.path.exists(p):
                    os.remove(p)

    # ── Private: XFade Composition ──────────────────────────────────────────

    def _map_transition(self, t: str) -> str:
        """Map user-facing transition name to FFmpeg xfade type."""
        mapping = {
            "fade": "fade", "fadeblack": "fadeblack", "fadewhite": "fadewhite",
            "dissolve": "dissolve", "pixelize": "pixelize",
            "wipeleft": "wipeleft", "wiperight": "wiperight",
            "wipeup": "wipeup", "wipedown": "wipedown",
            "slideleft": "slideleft", "slideright": "slideright",
            "slideup": "slideup", "slidedown": "slidedown",
            "circleopen": "circleopen", "circleclose": "circleclose",
            "horzopen": "horzopen", "horzclose": "horzclose",
            "vertopen": "vertopen", "vertclose": "vertclose",
            "distance": "distance",
        }
        return mapping.get(t.lower(), "fade")

    def _compose_with_xfade(self, clips: List[VideoClip], output_path: str,
                            target_w: int, target_h: int, opts: ComposeOptions):
        """
        Compose clips with xfade transitions.
        
        Following the huobao-drama approach:
        1. Scale all clips to target resolution with padding
        2. Apply tpad (freeze last frame) for transition overlap
        3. Chain xfade filters between adjacent clips
        4. Handle audio with acrossfade
        """
        n = len(clips)

        # Detect audio streams
        audio_present = [self.has_audio_stream(c.path) for c in clips]
        has_any_audio = any(audio_present)

        # Build FFmpeg args: inputs
        args = []
        for clip in clips:
            args.extend(["-i", clip.path])

        # ── Video filter chain ──

        # Step 1: Scale + pad each input to uniform resolution
        # Apply tpad (freeze last frame) if clip needs a transition to next
        scale_filters = []
        for i in range(n):
            base = (f"[{i}:v]scale={target_w}:{target_h}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2")

            # Add tpad if this clip transitions to the next
            if i < n - 1:
                t_type = clips[i].transition_type.lower()
                if t_type not in ("none", ""):
                    t_dur = clips[i].transition_duration
                    base += f",tpad=stop_mode=clone:stop_duration={t_dur:.2f}"

            scale_filters.append(f"{base}[v{i}]")

        # Step 2: Chain xfade filters
        xfade_filters = []
        offset = 0.0

        for i in range(n - 1):
            clip_dur = clips[i].duration
            if clips[i].end_time > 0 and clips[i].start_time >= 0:
                clip_dur = clips[i].end_time - clips[i].start_time

            t_type = clips[i].transition_type.lower()
            t_dur = clips[i].transition_duration if t_type not in ("none", "") else 0.0
            mapped_type = self._map_transition(t_type) if t_dur > 0 else "fade"

            offset += clip_dur
            if offset < 0:
                offset = 0

            # Input labels
            if i == 0:
                in_label = "[v0][v1]"
            else:
                in_label = f"[vx{i-1:02d}][v{i+1}]"

            # Output label
            if i == n - 2:
                out_label = "[outv]"
            else:
                out_label = f"[vx{i:02d}]"

            xfade_filters.append(
                f"{in_label}xfade=transition={mapped_type}:"
                f"duration={t_dur:.1f}:offset={offset:.1f}{out_label}"
            )

        # ── Audio filter chain ──
        audio_filters = []
        audio_crossfades = []

        if has_any_audio:
            for i in range(n):
                clip_dur = clips[i].duration
                if clips[i].end_time > 0:
                    clip_dur = clips[i].end_time - clips[i].start_time

                # Calculate pad duration for transition
                pad_dur = 0.0
                if i < n - 1:
                    t_type = clips[i].transition_type.lower()
                    if t_type not in ("none", ""):
                        pad_dur = clips[i].transition_duration

                if not audio_present[i]:
                    # Generate silence
                    total_dur = clip_dur + pad_dur
                    audio_filters.append(
                        f"anullsrc=channel_layout=stereo:sample_rate=44100:"
                        f"duration={total_dur:.2f}[a{i}]"
                    )
                elif pad_dur > 0:
                    # Pad existing audio with silence
                    audio_filters.append(f"[{i}:a]apad=pad_dur={pad_dur:.2f}[a{i}]")
                else:
                    audio_filters.append(f"[{i}:a]acopy[a{i}]")

            # Audio crossfades
            for i in range(n - 1):
                t_type = clips[i].transition_type.lower()
                t_dur = clips[i].transition_duration if t_type not in ("none", "") else 0.0

                if i == 0:
                    in_label = "[a0][a1]"
                else:
                    in_label = f"[ax{i-1:02d}][a{i+1}]"

                if i == n - 2:
                    out_label = "[outa]"
                else:
                    out_label = f"[ax{i:02d}]"

                audio_crossfades.append(
                    f"{in_label}acrossfade=d={t_dur:.2f}:c1=tri:c2=tri{out_label}"
                )

        # ── Combine all filters ──
        all_filters = scale_filters + xfade_filters
        if has_any_audio:
            all_filters += audio_filters + audio_crossfades
        filter_complex = ";".join(all_filters)

        # ── Build final command ──
        args.extend(["-filter_complex", filter_complex])
        args.extend(["-map", "[outv]"])
        if has_any_audio:
            args.extend(["-map", "[outa]"])

        args.extend([
            "-c:v", opts.codec, "-preset", opts.preset, "-crf", str(opts.crf),
        ])
        if has_any_audio:
            args.extend(["-c:a", "aac", "-b:a", "128k"])

        args.extend(["-y", output_path])

        logger.debug(f"Filter complex: {filter_complex}")
        self._run_ffmpeg(["ffmpeg"] + args, "xfade compose")

    # ── Private: Run FFmpeg ─────────────────────────────────────────────────

    def _run_ffmpeg(self, cmd: List[str], operation: str):
        """Execute an FFmpeg command and handle errors."""
        logger.debug(f"[{operation}] Running: {' '.join(cmd[:6])}...")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600
            )
            if result.returncode != 0:
                logger.error(f"[{operation}] FFmpeg failed:\n{result.stderr[-2000:]}")
                raise RuntimeError(f"FFmpeg {operation} failed: {result.stderr[-500:]}")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"FFmpeg {operation} timed out (10 min limit)")

    # ── Cleanup ─────────────────────────────────────────────────────────────

    def cleanup_temp(self):
        """Remove all temporary files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            os.makedirs(self.temp_dir, exist_ok=True)
