import json, subprocess, wave, os, glob, sys
LINES = [
  ("People ask AI. And it gives one name.", "Right now, that name is not yours."),
  ("AI only has pieces of you.", "It gathers your story from all over the internet. When pieces are missing or wrong, it can't see you. So it skips you."),
  ("You could fix it yourself.", "Hundreds of sites. They change every week. It never ends."),
  ("Or put yourself on the record.", "Local AI Registry pulls every piece onto one page. You claim it, confirm the facts, and it's yours."),
  ("The more AI knows you, the more it says your name.", "We keep teaching AI from your record. Each plan teaches it faster."),
  ("Be the name AI says.", "The next customer who asks gets you. Your record is live. Claim it free."),
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
        chunks = [a for _, _, a in pipe(text, voice=VOICE, speed=0.93)]
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
for i, (c, a) in enumerate(LINES):
    dc = synth(c, f"vo/c{i}.wav"); da = synth(a, f"vo/a{i}.wav")
    print(i, round(dc, 2), round(da, 2))
    sched["cards"].append(round(max(3.2, dc + 1.0), 2))
    sched["anims"].append(round(max(base_anim[i], da + 1.8), 2))
sched["end"] = synth(END, "vo/end.wav")
json.dump(sched, open("schedule.json", "w"), indent=1)
print(sched)
