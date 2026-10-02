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
t = off
for i in range(6):
    place(f"vo/c{i}.wav", t + 0.35)
    place(f"vo/a{i}.wav", t + sched["cards"][i] + 0.7)
    t += sched["cards"][i] + sched["anims"][i]
place("vo/end.wav", t - sched["anims"][5] + 7.5 + 0.4 + 0.8)
vo = vo / (np.abs(vo).max() + 1e-9) * 0.85
sf.write("vo.wav", vo, SR)
subprocess.run(["python3", "music.py", str(dur)], check=True)
subprocess.run(["ffmpeg", "-y", "-i", "video.mp4", "-i", "vo.wav", "-i", "music.wav",
  "-filter_complex", "[2:a]volume=0.28[m];[1:a]volume=1.0[v];[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
  "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", "lair-explainer-1080p-audio.mp4"], check=True)
