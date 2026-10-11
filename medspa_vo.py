import json, os, urllib.request, subprocess
KEY = os.environ["ELEVENLABS_API_KEY"].strip()
LINES = [
 ("ask", "So. Your next patient wants Botox. Does she ask a friend? Nope. She asks AI."),
 ("answer", "AI gives her a few names. Great names! Just... not yours."),
 ("shift", "And she's not alone. A year ago, six percent of people did this. Now? Forty-five."),
 ("few", "Here's the tricky part. Google shows plenty of businesses. AI? It picks about one."),
 ("before", "It used to be easy. Search, click, your website. Done."),
 ("scattered", "But now AI reads about you everywhere. Google, Yelp, reviews, directories. And when they don't agree? AI gets nervous, and sends her somewhere else."),
 ("record", "That's where we come in. You tell us your facts once. We make every one of those places say the same thing. Every month."),
 ("approve", "You don't lift a finger. Okay, one finger. Tap approve."),
 ("named", "So next time she asks, guess who AI picks?"),
 ("end", "You. Local AI Registry. Be the name AI gives."),
]
req = urllib.request.Request("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": KEY})
voices = json.loads(urllib.request.urlopen(req, timeout=60).read())["voices"]
want = os.environ.get("VOICE_NAME", "Jessica").lower()
v = next((x for x in voices if x["name"].lower().startswith(want)), voices[0])
print("voice", v["voice_id"], v["name"])
os.makedirs("out", exist_ok=True)
info = []
for i, (sid, text) in enumerate(LINES):
    body = {"text": text, "model_id": "eleven_multilingual_v2",
            "previous_text": " ".join(t for _, t in LINES[:i])[-600:] or None,
            "next_text": " ".join(t for _, t in LINES[i + 1:])[:600] or None,
            "voice_settings": {"stability": 0.36, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True}}
    body = {k: x for k, x in body.items() if x is not None}
    r = urllib.request.Request("https://api.elevenlabs.io/v1/text-to-speech/" + v["voice_id"] + "?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), headers={"xi-api-key": KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    p = f"out/{i:02d}-{sid}.mp3"
    open(p, "wb").write(urllib.request.urlopen(r, timeout=120).read())
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
    info.append({"id": sid, "file": os.path.basename(p), "dur": round(d, 2), "text": text})
    print(sid, round(d, 2))
json.dump({"voice": v["name"], "lines": info}, open("out/lines.json", "w"), indent=1)
