import json, os, sys, numpy as np, soundfile as sf
# Each scene: (words spoken while the title card is up, the rest). On-screen title = first part, said naturally.
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
VOICE = os.environ.get("VOICE", "af_sarah")
os.makedirs("vo", exist_ok=True)
from kokoro import KPipeline
pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
import re as _re
def synth(text, path):
    parts = [p.strip() for p in _re.split(r'(?<=[.!?])\s+', text) if p.strip()]
    gap = np.zeros(int(0.14 * 24000)); pieces = []
    def trim(a, thr=0.012, keep=int(0.06 * 24000)):
        idx = np.where(np.abs(a) > thr)[0]
        if len(idx) == 0: return a
        return a[max(0, idx[0] - keep): min(len(a), idx[-1] + keep)]
    for p in parts:
        pieces.append(trim(np.concatenate([np.asarray(a) for _, _, a in pipe(p, voice=VOICE, speed=1.08)]))); pieces.append(gap)
    audio = np.concatenate(pieces[:-1])
    audio = np.concatenate([np.zeros(int(0.05 * 24000)), audio, np.zeros(int(0.1 * 24000))])
    sf.write(path, audio, 24000); return len(audio) / 24000
from faster_whisper import WhisperModel
wm = WhisperModel("base.en", device="cpu", compute_type="int8")
def card_end(path, nwords):
    segs, _ = wm.transcribe(path, word_timestamps=True)
    words = [w for s in segs for w in s.words]
    if len(words) >= nwords: return words[nwords - 1].end
    return None
sched = {"cards": [], "anims": [], "vo": []}
for i, (card, rest) in enumerate(SCENES):
    d = synth(card + " " + rest, f"vo/s{i}.wav")
    n = len(card.split())
    ce = card_end(f"vo/s{i}.wav", n)
    if ce is None: ce = d * n / (n + len(rest.split()))
    cdur = round(max(1.8, ce + 0.35), 2)
    adur = round(max(MIN_ANIM[i], d - cdur + 0.6), 2)
    print(i, "vo", round(d, 2), "card", cdur, "anim", adur)
    sched["cards"].append(cdur); sched["anims"].append(adur); sched["vo"].append(round(d, 2))
sched["end"] = synth(END, "vo/end.wav")
json.dump(sched, open("schedule.json", "w"), indent=1)
print(sched)
