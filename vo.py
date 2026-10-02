import json, os, sys, numpy as np, soundfile as sf
# Each scene: (words spoken while the title card is up, the rest). On-screen title = first part, said naturally.
SCENES = [
  ("These days, people just ask AI, and it gives them one name.", "Right now, that name probably isn't yours."),
  ("Here's the thing. AI only has pieces of you.", "It's piecing your business together from scraps all over the internet. And when some are missing, or just wrong, it can't see the full picture. So it plays it safe, and recommends someone else."),
  ("Sure, you could fix it yourself.", "But that's hundreds of sites. They change every week, and it never ends."),
  ("Or, you put yourself on the record.", "Local AI Registry pulls every piece into one page. You claim it, make sure the facts are right, and it's yours."),
  ("And the more AI knows you, the more it says your name.", "We keep teaching it from your record, and every plan turns that up."),
  ("So next time someone asks, be the name AI says.", "Your record's already live. Claim it. It's free."),
]
END = "Local A.I. Registry, dot com."
MIN_ANIM = [6.0, 6.5, 7.5, 9.5, 9.5, 5.5]
VOICE = os.environ.get("VOICE", "af_heart")
os.makedirs("vo", exist_ok=True)
from kokoro import KPipeline
pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
def synth(text, path):
    audio = np.concatenate([np.asarray(a) for _, _, a in pipe(text, voice=VOICE, speed=1.0)])
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
