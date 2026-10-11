import json, os, urllib.request, urllib.error, subprocess
KEY = os.environ["ELEVENLABS_API_KEY"].strip()
os.makedirs("out", exist_ok=True)
def post(url, body, path):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"xi-api-key": KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        open(path, "wb").write(urllib.request.urlopen(r, timeout=600).read()); return True
    except urllib.error.HTTPError as e:
        print("ERROR", url, e.code, e.read().decode(errors="replace")[:600]); return False
dur = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
mode = open("mode.txt").read().strip() if os.path.exists("mode.txt") else "vo"
if mode == "vo":
    P = json.load(open("phrases.json"))
    voices = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": KEY}), timeout=60).read())["voices"]
    v = next((x for x in voices if x["name"].lower().startswith("jessica")), voices[0]); print("voice", v["name"])
    info = []
    for i, (sid, beat, text) in enumerate(P):
        p = f"out/p{i:02d}.mp3"
        ok = post("https://api.elevenlabs.io/v1/text-to-speech/" + v["voice_id"] + "?output_format=mp3_44100_128",
                  {"text": text, "model_id": "eleven_multilingual_v2",
                   "previous_text": " ".join(t for _, _, t in P[max(0, i - 3):i]) or None,
                   "next_text": " ".join(t for _, _, t in P[i + 1:i + 3]) or None,
                   "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.5, "use_speaker_boost": True}}, p)
        info.append({"i": i, "scene": sid, "beat": beat, "text": text, "file": os.path.basename(p), "dur": round(dur(p), 3) if ok else 0})
        print(i, text, info[-1]["dur"])
    json.dump(info, open("out/phrases.json", "w"), indent=1)
else:
    cfg = json.load(open("music.json"))
    for k, prompt in enumerate(cfg["prompts"]):
        p = f"out/music{k}.mp3"
        if post("https://api.elevenlabs.io/v1/music", {"prompt": prompt, "music_length_ms": cfg["ms"], "model_id": "music_v1", "force_instrumental": True}, p):
            print("music", k, dur(p))
