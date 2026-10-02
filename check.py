import glob, os
from faster_whisper import WhisperModel
m = WhisperModel("base.en", device="cpu", compute_type="int8")
for f in sorted(glob.glob("vo/*.wav")):
    segs, _ = m.transcribe(f)
    print(f, os.path.getsize(f), "|", " ".join(s.text.strip() for s in segs))
