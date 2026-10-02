import json, numpy as np, soundfile as sf, subprocess
SR = 44100
sched = json.load(open("schedule.json")); off = json.load(open("offset.json"))["offset"]
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", "video.mp4"], capture_output=True, text=True).stdout)
vo = np.zeros(int(SR * dur))
def place(path, at):
    a, sr = sf.read(path)
    if a.ndim > 1: a = a.mean(1)
    if sr != SR:
        import math; idx = (np.arange(int(len(a) * SR / sr)) * sr / SR).astype(int); a = a[np.minimum(idx, len(a) - 1)]
    i = int(at * SR); e = min(len(vo), i + len(a)); vo[i:e] += a[: e - i]
# read the per-frame marker colour from the strip below the frame (one rgb pixel per frame at 30 fps)
raw = np.frombuffer(open("strip.rgb", "rb").read(), dtype=np.uint8).reshape(-1, 3)
starts = {}
for f, (r, g, b) in enumerate(raw):
    if r > 150 and g < 80 and b < 80: key = "end"
    elif g > 10 and r < 80: key = int(round((g - 20) / 40))
    else: continue
    if key not in starts: starts[key] = f / 30.0
print("scene starts", starts)
for i in range(6):
    place(f"vo/s{i}.wav", starts[i] + 0.25)
place("vo/end.wav", starts["end"] + 0.8)
vo = vo / (np.abs(vo).max() + 1e-9) * 0.85
sf.write("vo.wav", vo, SR)
# real track first (internal use), generated bed as fallback
import urllib.request
TRACKS = [
  "https://assets.mixkit.co/music/preview/mixkit-driving-ambition-32.mp3",
  "https://assets.mixkit.co/music/preview/mixkit-dreaming-big-31.mp3",
  "https://assets.mixkit.co/music/preview/mixkit-tech-house-vibes-130.mp3",
]
got = False
for u in TRACKS:
    try:
        urllib.request.urlretrieve(u, "track.mp3")
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "3", "-i", "track.mp3", "-t", str(dur), "-af", f"afade=t=in:d=1,afade=t=out:st={max(0, dur - 3)}:d=3", "-ac", "2", "-ar", "44100", "music.wav"])
        if r.returncode == 0: print("music:", u); got = True; break
    except Exception as e: print("track failed", u, e)
if not got: subprocess.run(["python3", "music.py", str(dur)], check=True)
subprocess.run(["ffmpeg", "-y", "-i", "video.mp4", "-i", "vo.wav", "-i", "music.wav",
  "-filter_complex", "[2:a]volume=0.30[m];[1:a]volume=1.0[v];[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
  "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", "lair-explainer-1080p-audio.mp4"], check=True)
