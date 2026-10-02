import json, os, sys, subprocess, asyncio, numpy as np, soundfile as sf
SCENES = [
  ("People just ask AI now.", "And it gives them one name. Right now? Probably not yours."),
  ("AI only has pieces of you.", "Scraps from all over the internet. Some missing, some wrong. So it skips you."),
  ("You could fix it yourself.", "Hundreds of sites. Every week. Forever."),
  ("Or, put yourself on the record.", "One page with every piece. Claim it, confirm it, done."),
  ("And the more AI knows you, the more it says your name.", "We keep teaching it. Every plan turns it up."),
  ("So next time someone asks, it's you.", "Your record's live. It's free. Go claim it."),
]
END = "Be the name AI says."
MIN_ANIM = [4.3, 4.6, 5.3, 6.7, 6.7, 3.9]
VOICE = os.environ.get("VOICE", "en-US-AvaMultilingualNeural")
RATE = os.environ.get("RATE", "+4%")
os.makedirs("vo", exist_ok=True)

def trim(a, thr=0.01, keep=int(0.08 * 24000)):
    idx = np.where(np.abs(a) > thr)[0]
    return a if len(idx) == 0 else a[max(0, idx[0] - keep): min(len(a), idx[-1] + keep)]

def synth(text, path):
    import edge_tts
    mp3 = path + ".mp3"
    asyncio.run(edge_tts.Communicate(text, VOICE, rate=RATE).save(mp3))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-ac", "1", "-ar", "24000", path], check=True)
    a, sr = sf.read(path); a = trim(a)
    a = np.concatenate([np.zeros(int(0.05 * 24000)), a, np.zeros(int(0.1 * 24000))])
    sf.write(path, a, 24000); return len(a) / 24000

from faster_whisper import WhisperModel
wm = WhisperModel("base.en", device="cpu", compute_type="int8")
def card_end(path, nwords):
    segs, _ = wm.transcribe(path, word_timestamps=True)
    words = [w for s in segs for w in s.words]
    return words[nwords - 1].end if len(words) >= nwords else None

print("voice", VOICE, RATE)
sched = {"cards": [], "anims": [], "vo": []}
for i, (card, rest) in enumerate(SCENES):
    d = synth(card + " " + rest, f"vo/s{i}.wav")
    n = len(card.split()); ce = card_end(f"vo/s{i}.wav", n)
    if ce is None: ce = d * n / (n + len(rest.split()))
    cdur = round(max(1.8, ce + 0.35), 2); adur = round(max(MIN_ANIM[i], d - cdur + 0.6), 2)
    print(i, "vo", round(d, 2), "card", cdur, "anim", adur)
    sched["cards"].append(cdur); sched["anims"].append(adur); sched["vo"].append(round(d, 2))
sched["end"] = synth(END, "vo/end.wav")
json.dump(sched, open("schedule.json", "w"), indent=1)
print(sched)
