"""Segments -> one 1080x1920 MP4 with ffmpeg. No editor app involved."""
import os
import subprocess
import urllib.request

from .render import face_background

FPS = 30
UA = "otejiji-pipeline/0.1"
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-ar", "44100", "-ac", "2"]


def _run(cmd):
    subprocess.run(cmd, check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def fetch(url, dest):
    """Download once into the cache. Returns the path, or None if unavailable (pipeline keeps going)."""
    if not url:
        return None
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            f.write(r.read())
        return dest
    except Exception as e:  # noqa: BLE001
        print(f"[warn] could not download {url}: {e}")
        return None


def _audio_inputs(voice, dur):
    if voice:
        return ["-i", voice]
    return ["-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anullsrc=r=44100:cl=stereo"]


def _afilter(idx, dur, voice):
    delay = "adelay=150|150," if voice else ""
    return (f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,{delay}"
            f"apad,atrim=0:{dur:.2f}[a]")


def image_segment(png, dur, voice, out):
    _run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.2f}", "-i", png,
          *_audio_inputs(voice, dur), "-filter_complex", _afilter(1, dur, voice),
          "-map", "0:v", "-map", "[a]", *ENC, "-t", f"{dur:.2f}", out])


def face_segment(bg_png, clip, overlay, dur, voice, out):
    frames = int(dur * FPS) + 1
    if clip:
        src = ["-stream_loop", "-1", "-i", clip]
        vf = (f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps={FPS},"
              f"format=yuv420p[bg]")
    else:
        src = ["-i", bg_png]
        vf = (f"[0:v]zoompan=z='min(zoom+0.0007,1.15)':d={frames}:x='iw/2-(iw/zoom/2)':"
              f"y='ih/2-(ih/zoom/2)':s=1080x1920:fps={FPS},format=yuv420p[bg]")
    fc = f"{vf};[bg][1:v]overlay=0:0[v];{_afilter(2, dur, voice)}"
    _run(["ffmpeg", "-v", "error", "-y", *src, "-loop", "1", "-i", overlay, *_audio_inputs(voice, dur),
          "-filter_complex", fc, "-map", "[v]", "-map", "[a]", *ENC, "-t", f"{dur:.2f}", out])


def build(segments, assets, workdir, out_path, theme=None):
    """segments from render.story_segments; assets = parsed assets/otejiji.json."""
    cache = os.path.join(workdir, "cache")
    os.makedirs(cache, exist_ok=True)
    face = fetch(assets.get("face"), os.path.join(cache, "face.png"))
    bg = os.path.join(workdir, "face_bg.png")
    face_background(face).save(bg)
    clips = {k: fetch(u, os.path.join(cache, f"clip_{k}.mp4")) for k, u in (assets.get("clips") or {}).items()}
    voice_lines = ((assets.get("voice") or {}).get("lines")) or {}

    parts, timeline, t = [], [], 0.0
    for i, s in enumerate(segments):
        voice = None
        if s.get("voice") and voice_lines.get(s["voice"]):
            safe = s["voice"].replace(" ", "_").replace(".", "_")
            voice = fetch(voice_lines[s["voice"]], os.path.join(cache, f"v_{safe}.mp3"))
        dur = max(s["base"], duration(voice) + 0.45) if voice else s["base"]
        part = os.path.join(workdir, f"part{i:02d}.mp4")
        if s["type"] == "face":
            face_segment(bg, clips.get(s.get("role")), s["overlay"], dur, voice, part)
        else:
            image_segment(s["path"], dur, voice, part)
        parts.append(part)
        timeline.append({"start": round(t, 2), "dur": round(dur, 2), "voice": s.get("voice"), "has_voice": bool(voice)})
        t += dur

    lst = os.path.join(workdir, "parts.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    joined = os.path.join(workdir, "joined.mp4")
    _run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])

    if theme and os.path.exists(theme):
        _run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-stream_loop", "-1", "-i", theme, "-filter_complex",
              "[1:a]volume=0.16[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]",
              "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-ar", "44100", "-movflags", "+faststart",
              out_path])
    else:
        _run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-c", "copy", "-movflags", "+faststart", out_path])
    return timeline, round(t, 2)
