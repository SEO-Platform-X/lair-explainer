import json, os, sys, subprocess, asyncio, urllib.request, urllib.error, numpy as np, soundfile as sf
SCENES = [
  ("Today, people just ask AI.", "And it gives them one name. Right now? Probably not yours."),
  ("AI only has pieces of you.", "Scraps from all over the internet. Some are missing, some are wrong. So it skips you."),
  ("You could fix it yourself.", "Hundreds of sites. Every week. Forever."),
  ("Or, put yourself on the record.", "One page with every piece. Claim it, confirm it, done."),
  ("And the more AI knows you, the more it says your name.", "Turn it up, and AI recommends you more and more."),
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

EL_KEY = os.environ.get("ELEVENLABS_API_KEY", "").strip()
EL_VOICE = os.environ.get("ELEVENLABS_VOICE_ID", "").strip()
if EL_KEY and not EL_VOICE:
    # free plans can only use voices already in the account: list them and pick the most fun-sounding female
    try:
        req = urllib.request.Request("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": EL_KEY})
        voices = json.loads(urllib.request.urlopen(req, timeout=60).read())["voices"]
        def score(vv):
            lab = {k: str(x).lower() for k, x in (vv.get("labels") or {}).items()}
            d = (vv.get("description") or "").lower() + " " + " ".join(lab.values()) + " " + vv.get("name", "").lower()
            s = 0
            if "female" in lab.get("gender", "") or "female" in d: s += 10
            for w, pts in (("playful", 6), ("fun", 6), ("bright", 4), ("upbeat", 5), ("energetic", 5), ("young", 3), ("cheerful", 5), ("lively", 4), ("warm", 2), ("casual", 2), ("conversational", 2), ("american", 2)):
                if w in d: s += pts
            if "british" in d: s -= 1
            if vv.get("category") == "premade": s += 1
            return s
        voices.sort(key=score, reverse=True)
        for vv in voices[:12]: print("voice option", vv["voice_id"], vv["name"], vv.get("category"), vv.get("labels"), (vv.get("description") or "")[:80])
        EL_VOICE = voices[0]["voice_id"]; print("picked", voices[0]["name"])
    except Exception as e:
        print("voice list failed", repr(e)[:200]); EL_VOICE = "jBpfuIE2acCO8z3wKNLl"
CB = None
def chatterbox():
    global CB
    if CB is None:
        import torch; from chatterbox.tts import ChatterboxTTS
        torch.set_num_threads(os.cpu_count() or 4)
        CB = ChatterboxTTS.from_pretrained(device="cpu")
    return CB
def synth(text, path):
    mp3 = path + ".mp3"
    try:
        return synth_inner(text, path, mp3)
    except Exception as e:
        print("voice engine failed, using Edge Ava:", repr(e)[:200])
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, "en-US-AvaMultilingualNeural", rate="+4%").save(mp3))
        return finish(mp3, path)
def finish(mp3, path):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-ac", "1", "-ar", "24000", path], check=True)
    a, sr = sf.read(path); a = trim(a)
    a = np.concatenate([np.zeros(int(0.05 * 24000)), a, np.zeros(int(0.1 * 24000))])
    sf.write(path, a, 24000); return len(a) / 24000
def synth_inner(text, path, mp3):
    if not EL_KEY and os.environ.get("TTS", "chatterbox") == "chatterbox":
        import torch, torchaudio
        m = chatterbox(); torch.manual_seed(7)
        wav = m.generate(text, exaggeration=float(os.environ.get("EXAG", "0.55")), cfg_weight=0.45, temperature=0.7)
        torchaudio.save(path, wav, m.sr)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-ac", "1", "-ar", "24000", path + ".tmp.wav"], check=True)
        os.replace(path + ".tmp.wav", path)
        a, sr = sf.read(path); a = trim(a)
        a = np.concatenate([np.zeros(int(0.05 * 24000)), a, np.zeros(int(0.1 * 24000))])
        sf.write(path, a, 24000); return len(a) / 24000
    if EL_KEY:
        import urllib.request, json as _j
        req = urllib.request.Request(
            "https://api.elevenlabs.io/v1/text-to-speech/" + EL_VOICE + "?output_format=mp3_44100_128",
            data=_j.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                           "voice_settings": {"stability": 0.38, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True}}).encode(),
            headers={"xi-api-key": EL_KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"})
        try:
            open(mp3, "wb").write(urllib.request.urlopen(req, timeout=120).read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:400]
            print("ELEVENLABS ERROR", e.code, body)
            # retry once with the previous voice, then give up to Edge
            if False:
                req2 = urllib.request.Request(
                    "https://api.elevenlabs.io/v1/text-to-speech/nPczCjzI2devNBz1zQrb?output_format=mp3_44100_128",
                    data=req.data, headers=dict(req.headers))
                try:
                    open(mp3, "wb").write(urllib.request.urlopen(req2, timeout=120).read()); print("fell back to Brian")
                except urllib.error.HTTPError as e2:
                    print("ELEVENLABS ERROR (Brian)", e2.code, e2.read().decode(errors="replace")[:400]); raise
            else: raise
    else:
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, VOICE, rate=RATE).save(mp3))
    return finish(mp3, path)

from faster_whisper import WhisperModel
wm = WhisperModel("base.en", device="cpu", compute_type="int8")
def card_end(path, nwords):
    segs, _ = wm.transcribe(path, word_timestamps=True)
    words = [w for s in segs for w in s.words]
    return words[nwords - 1].end if len(words) >= nwords else None

print("voice", "elevenlabs:" + EL_VOICE if EL_KEY else ("chatterbox" if os.environ.get("TTS", "chatterbox") == "chatterbox" else VOICE + " " + RATE))
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
