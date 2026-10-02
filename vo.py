import json, os, sys, numpy as np, soundfile as sf
# Each scene: (words spoken while the title card is up, the rest). On-screen title = first part, said naturally.
SCENES = [
  ("These days, people just ask AI, and it gives them one name.", "Right now, that name probably isn't yours. Someone else gets the call."),
  ("Here's the thing. AI only has pieces of you.", "It's piecing your business together from scraps all over the internet. And when some are missing, or just wrong, it can't see the full picture. So it plays it safe, and recommends someone else."),
  ("Sure, you could fix it yourself.", "But that's hundreds of sites. Google, Yelp, the directories, a dozen more you've never heard of. They change every week, and it never ends."),
  ("Or, you put yourself on the record.", "Local AI Registry pulls every piece into one page. You claim it, check the facts, your hours, your services, what you're known for, and it's yours."),
  ("And the more AI knows you, the more it says your name.", "We keep teaching it from your record. Start free, and when you want AI recommending you more, each plan turns it up."),
  ("So next time someone asks, the answer is you.", "Your record's already live, it's free, and it's waiting for you. Go claim it."),
]
END = "Be the name AI says."
MIN_ANIM = [6.0, 6.5, 7.5, 9.5, 9.5, 5.5]
VOICE = os.environ.get("VOICE", "af_bella")
os.makedirs("vo", exist_ok=True)
from kokoro import KPipeline
pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
import re as _re
def synth(text, path):
    parts = [p.strip() for p in _re.split(r'(?<=[.!?])\s+', text) if p.strip()]
    gap = np.zeros(int(0.22 * 24000)); pieces = []
    for p in parts:
        pieces.append(np.concatenate([np.asarray(a) for _, _, a in pipe(p, voice=VOICE, speed=0.95)])); pieces.append(gap)
    audio = np.concatenate(pieces[:-1])
    audio = np.concatenate([np.zeros(int(0.1 * 24000)), audio, np.zeros(int(0.2 * 24000))])
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
    cdur = round(max(2.4, ce + 0.45), 2)
    adur = round(max(MIN_ANIM[i], d - cdur + 1.0), 2)
    print(i, "vo", round(d, 2), "card", cdur, "anim", adur)
    sched["cards"].append(cdur); sched["anims"].append(adur); sched["vo"].append(round(d, 2))
sched["end"] = synth(END, "vo/end.wav")
json.dump(sched, open("schedule.json", "w"), indent=1)
print(sched)
