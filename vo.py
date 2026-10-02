import json, subprocess, wave, os
LINES = [
  ("People ask AI. And it gives one name.", "Right now, that name is not yours."),
  ("AI only has pieces of you.", "It gathers your story from all over the internet. When pieces are missing or wrong, it can't see you. So it skips you."),
  ("You could fix it yourself.", "Hundreds of sites. They change every week. It never ends."),
  ("Or put yourself on the record.", "Local AI Registry pulls every piece onto one page. You claim it, confirm the facts, and it's yours."),
  ("The more AI knows you, the more it says your name.", "We keep teaching AI from your record. Each plan teaches it faster."),
  ("Be the name AI says.", "The next customer who asks gets you. Your record is live. Claim it free."),
]
END = "Local A I Registry dot com."
VOICE = os.environ.get("VOICE", "en_US-ryan-high")
os.makedirs("vo", exist_ok=True)
def synth(text, path):
    subprocess.run(["piper", "-m", VOICE, "--data-dir", "voices", "--download-dir", "voices", "--length-scale", "1.08", "--sentence-silence", "0.35", "-f", path], input=text.encode(), check=True)
    with wave.open(path) as w: return w.getnframes() / w.getframerate()
sched = {"cards": [], "anims": [], "clips": []}
base_anim = [6.5, 8, 8.5, 10.5, 11, 7.5]
for i, (c, a) in enumerate(LINES):
    dc = synth(c, f"vo/c{i}.wav"); da = synth(a, f"vo/a{i}.wav")
    sched["cards"].append(round(max(3.2, dc + 1.0), 2))
    sched["anims"].append(round(max(base_anim[i], da + 1.8), 2))
de = synth(END, "vo/end.wav")
sched["end"] = de
json.dump(sched, open("schedule.json", "w"), indent=1)
print(sched)
