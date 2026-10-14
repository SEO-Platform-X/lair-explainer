import json, os, re, subprocess, base64, urllib.request

VIDEO_URL = open("ads/invisible/video_url.txt").read().strip()
KEY = os.environ["ELEVENLABS_API_KEY"].strip()
VOICE = "cgSgspJ2msm6clMCkdW9"  # Jessica, same voice as the explainer
LINES = [
    "Your customers stopped Googling. They ask AI.",
    "And if AI can't verify your business... it doesn't recommend you. It doesn't even know you exist.",
    "Local AI Registry gives your business a verified profile that ChatGPT, Gemini and Perplexity actually cite.",
    "Don't be invisible.",
]

def sh(c): return subprocess.run(c, shell=True, check=True, capture_output=True, text=True)

urllib.request.urlretrieve(VIDEO_URL, "stitched.mp4")
urllib.request.urlretrieve(open("ads/invisible/couch_url.txt").read().strip(), "couch.mp4")
# final cut: couch shot (4s) + stitched video from 8s (fade, lights out, restore, client walks in)
sh('ffmpeg -y -i couch.mp4 -ss 8 -i stitched.mp4 -filter_complex "[0:v]fps=24,setsar=1[a];[1:v]fps=24,setsar=1[b];[a][b]concat=n=2:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p src.mp4')
dur = float(sh("ffprobe -v error -show_entries format=duration -of csv=p=0 src.mp4").stdout)
cuts = [4, 10, 16, 24]
print("duration", dur, "cuts", cuts)
anchors = [0.4, cuts[0] + 0.6, cuts[2] + 0.8, cuts[3] + 1.0]

clips, t_end = [], 0
for i, text in enumerate(LINES):
    body = {"text": text, "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True}}
    if i: body["previous_text"] = " ".join(LINES[:i])
    if i < len(LINES) - 1: body["next_text"] = " ".join(LINES[i+1:])
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128",
                                 data=json.dumps(body).encode(), headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    open(f"l{i}.mp3", "wb").write(base64.b64decode(r["audio_base64"]))
    al = r["alignment"]
    words, cur, ws = [], "", None
    for ch, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            if cur: words.append((cur, ws, we)); cur = ""
        else:
            if not cur: ws = s
            cur += ch; we = e
    if cur: words.append((cur, ws, we))
    ldur = float(sh(f"ffprobe -v error -show_entries format=duration -of csv=p=0 l{i}.mp3").stdout)
    start = max(anchors[i], t_end + 0.35)
    t_end = start + ldur
    clips.append({"start": start, "dur": ldur, "words": [(w, start + a, start + b) for w, a, b in words]})
    print(f"line {i}: start {start:.2f} end {t_end:.2f}")
if t_end > dur - 0.3: print("WARNING voiceover runs past video end")

# captions: up to 3 words per card, Bricolage Grotesque, lower third
def ts(t): h=int(t//3600); m=int(t%3600//60); s=t%60; return f"{h}:{m:02d}:{s:05.2f}"
ass = ["[Script Info]","ScriptType: v4.00+","PlayResX: 720","PlayResY: 1280","",
       "[V4+ Styles]","Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,Bricolage Grotesque,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,300,1","",
       "[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for c in clips:
    w = c["words"]
    for k in range(0, len(w), 3):
        grp = w[k:k+3]
        end = w[k+3][1] if k + 3 < len(w) else grp[-1][2] + 0.25
        ass.append(f"Dialogue: 0,{ts(grp[0][1])},{ts(end)},Cap,,0,0,0,,{' '.join(x[0] for x in grp)}")
open("caps.ass", "w").write("\n".join(ass))

inputs = " ".join(f"-i l{i}.mp3" for i in range(len(clips)))
delays = ";".join(f"[{i+1}:a]adelay={int(c['start']*1000)}|{int(c['start']*1000)}[a{i}]" for i, c in enumerate(clips))
mixin = "".join(f"[a{i}]" for i in range(len(clips)))
af = f"{delays};{mixin}amix=inputs={len(clips)}:normalize=0,apad,loudnorm=I=-14:TP=-1.5[aout]"
sh(f"ffmpeg -y -i src.mp4 {inputs} -filter_complex \"{af}\" -map 0:v -map \"[aout]\" -c:v copy -c:a aac -b:a 192k -t {dur} lair-invisible-voiceover.mp4")
sh(f"ffmpeg -y -i lair-invisible-voiceover.mp4 -vf \"subtitles=caps.ass:fontsdir=fonts\" -c:v libx264 -crf 18 -preset slow -c:a copy -movflags +faststart lair-invisible-captions.mp4")
# contact sheet at each caption start for review
times = [c["start"] + 0.6 for c in clips] + [dur - 1]
for j, t in enumerate(times): sh(f"ffmpeg -y -ss {t:.2f} -i lair-invisible-captions.mp4 -frames:v 1 -vf scale=360:-1 f{j}.png")
sh("ffmpeg -y " + " ".join(f"-i f{j}.png" for j in range(len(times))) + f" -filter_complex hstack=inputs={len(times)} contact-sheet.png")
json.dump({"duration": dur, "cuts": cuts, "lines": [{"text": LINES[i], "start": c["start"], "end": c["start"] + c["dur"]} for i, c in enumerate(clips)]}, open("timing.json", "w"), indent=1)
