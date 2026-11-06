import glob
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cpu", compute_type="int8")
with open("out/transcript.txt", "w") as f:
    for p in sorted(glob.glob("takes/*.mp3")):
        segs, _ = m.transcribe(p)
        line = p + " | " + " ".join(s.text.strip() for s in segs)
        print(line); f.write(line + "\n")
