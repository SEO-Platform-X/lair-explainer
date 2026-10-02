import json, subprocess, wave, os, glob, sys
LINES = [
  "Here's something that's changed. When people need a business now, they don't scroll through search results anymore. They just ask AI, and it gives them one name. And right now, that name probably isn't yours.",
  "See, AI doesn't actually know your business. It's piecing you together from scraps all over the internet. And when half of those scraps are missing or just wrong, it can't make out the full picture. So it plays it safe and recommends someone else.",
  "Now, you could try to fix all of that yourself. But we're talking hundreds of sites, and they change every week. It's a job that never ends.",
  "Or, you put yourself on the record. Local AI Registry pulls every piece into one page. You claim it, check that the facts are right, and that's it. It's yours.",
  "From there, we keep teaching AI about your business, straight from that record. And the more it knows you, the more it recommends you. Each plan just turns that up.",
  "So the next time someone asks, the answer is you. Your record's already live. Go claim it. It's free.",
]
END = "Local A.I. Registry, dot com."
os.makedirs("vo", exist_ok=True); os.makedirs("voices", exist_ok=True)

def fetch(name):
    for flags in (["--data-dir", "voices"], ["--download-dir", "voices"]):
        r = subprocess.run([sys.executable, "-m", "piper.download_voices", name] + flags, capture_output=True, text=True)
        print("download", name, flags, "rc", r.returncode, (r.stdout + r.stderr)[-300:])
        hits = glob.glob(f"voices/**/{name}.onnx", recursive=True)
        if hits: return hits[0]
    return None

import numpy as np, soundfile as sf
VOICE = os.environ.get("VOICE", "am_michael")
try:
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    def synth(text, path):
        chunks = [a for _, _, a in pipe(text, voice=VOICE, speed=1.0)]
        audio = np.concatenate([np.asarray(c) for c in chunks])
        audio = np.concatenate([np.zeros(int(0.15 * 24000)), audio, np.zeros(int(0.25 * 24000))])
        sf.write(path, audio, 24000)
        return len(audio) / 24000
    print("using kokoro", VOICE)
except Exception as e:
    print("kokoro failed, falling back to piper:", repr(e))
    model = fetch("en_US-ryan-high") or fetch("en_US-lessac-medium")
    from piper import PiperVoice
    voice = PiperVoice.load(model)
    def synth(text, path):
        with wave.open(path, "wb") as w: voice.synthesize_wav(text, w)
        with wave.open(path) as w: return w.getnframes() / w.getframerate()

sched = {"cards": [], "anims": []}
base_anim = [6.5, 8, 8.5, 10.5, 11, 7.5]
for i, line in enumerate(LINES):
    d = synth(line, f"vo/s{i}.wav")
    print(i, round(d, 2))
    sched["cards"].append(3.2)
    sched["anims"].append(round(max(base_anim[i], d + 0.6 - 3.2 + 1.4), 2))
sched["end"] = synth(END, "vo/end.wav")
json.dump(sched, open("schedule.json", "w"), indent=1)
print(sched)
