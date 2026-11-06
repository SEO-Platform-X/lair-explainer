"""Dispensary explainer audio via ElevenLabs.

mode.txt picks the job:
  audition  list the account's voices and read the opening line in each candidate voice
  takes     one take per scene from script2.json, with character timestamps (voice from voice.txt)
  music     instrumental bed from music.json
"""
import json, os, base64, subprocess, urllib.request, urllib.error

KEY = os.environ["ELEVENLABS_API_KEY"].strip()
os.makedirs("out", exist_ok=True)
MODE = open("mode.txt").read().strip()
SETTINGS = json.load(open("voice_settings.json")) if os.path.exists("voice_settings.json") else \
    {"stability": 0.40, "similarity_boost": 0.8, "style": 0.40, "use_speaker_boost": True}


def get(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"xi-api-key": KEY}), timeout=60).read())


def tts(voice_id, text, path, prev=None, nxt=None):
    body = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": SETTINGS}
    if prev: body["previous_text"] = prev
    if nxt: body["next_text"] = nxt
    r = urllib.request.Request(
        "https://api.elevenlabs.io/v1/text-to-speech/" + voice_id + "/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    try:
        res = json.loads(urllib.request.urlopen(r, timeout=300).read())
    except urllib.error.HTTPError as e:
        print("ERROR", e.code, e.read().decode(errors="replace")[:500]); return None
    open(path + ".mp3", "wb").write(base64.b64decode(res["audio_base64"]))
    return res.get("alignment")


voices = get("https://api.elevenlabs.io/v1/voices")["voices"]
json.dump([{"id": v["voice_id"], "name": v["name"], "category": v.get("category"), "labels": v.get("labels"),
            "description": v.get("description")} for v in voices], open("out/voices.json", "w"), indent=1)
by_name = {v["name"].split(" ")[0].lower(): v for v in voices}

if MODE == "audition":
    line = json.load(open("script2.json"))[0][1]
    for name in json.load(open("audition.json")):
        v = by_name.get(name.lower())
        if not v: print("no voice", name); continue
        tts(v["voice_id"], line, "out/aud-" + name.lower())
        print("audition", name)
elif MODE == "takes":
    name = open("voice.txt").read().strip().lower()
    v = by_name[name]; print("voice", v["name"])
    P = json.load(open("script2.json"))
    ONLY = json.load(open("only.json")) if os.path.exists("only.json") else None
    for i, (sid, text) in enumerate(P):
        if ONLY and sid not in ONLY: continue
        prev = " ".join(t for _, t in P[max(0, i - 2):i]) or None
        nxt = " ".join(t for _, t in P[i + 1:i + 2]) or None
        al = tts(v["voice_id"], text, f"out/t{i:02d}-{sid}", prev, nxt)
        if al is not None:
            json.dump({"scene": sid, "text": text, "alignment": al}, open(f"out/t{i:02d}-{sid}.json", "w"))
            print(sid, "ok")
elif MODE == "music":
    cfg = json.load(open("music.json"))
    for k, prompt in enumerate(cfg["prompts"]):
        r = urllib.request.Request("https://api.elevenlabs.io/v1/music",
            data=json.dumps({"prompt": prompt, "music_length_ms": cfg["ms"], "model_id": "music_v1", "force_instrumental": True}).encode(),
            headers={"xi-api-key": KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"})
        try:
            open(f"out/music{k}.mp3", "wb").write(urllib.request.urlopen(r, timeout=600).read()); print("music", k)
        except urllib.error.HTTPError as e:
            print("ERROR music", e.code, e.read().decode(errors="replace")[:500])
