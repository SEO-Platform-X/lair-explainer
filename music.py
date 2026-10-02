import numpy as np, soundfile as sf, sys
SR = 44100; dur = float(sys.argv[1]); n = int(SR * dur)
def note(m): return 440 * 2 ** ((m - 69) / 12)
rng = np.random.default_rng(3); out = np.zeros(n)
bpm = 118; beat = 60 / bpm; bar = beat * 4
chords = [[60, 64, 67], [67, 71, 74], [57, 60, 64], [65, 69, 72]]  # C G Am F
def add(i0, sig):
    e = min(n, i0 + len(sig)); 
    if i0 < n: out[i0:e] += sig[: e - i0]
nbars = int(dur / bar) + 1
for b in range(nbars):
    ch = chords[b % 4]; s0 = b * bar
    # warm pad
    seg = np.arange(0, int(bar * SR) + SR // 2) / SR; env = np.minimum(seg / 0.4, 1) * np.exp(-seg / 2.6)
    pad = sum(np.sin(2 * np.pi * note(m - 12) * seg) + 0.3 * np.sin(2 * np.pi * note(m) * seg) for m in ch) * env * 0.035
    add(int(s0 * SR), pad)
    for k in range(8):
        t = s0 + k * beat / 2; i0 = int(t * SR)
        # kick on beats, soft
        if k % 2 == 0:
            kg = np.arange(0, int(0.18 * SR)) / SR
            add(i0, np.sin(2 * np.pi * (55 + 80 * np.exp(-kg * 40)) * kg) * np.exp(-kg * 18) * 0.26)
        # hat on off-beats
        if k % 2 == 1:
            hg = np.arange(0, int(0.05 * SR)) / SR
            add(i0, rng.normal(0, 1, len(hg)) * np.exp(-hg * 90) * 0.05)
        # plucked arpeggio on every eighth
        m = ch[k % 3] + 12 * (1 if k % 4 in (1, 2) else 0)
        pg = np.arange(0, int(0.5 * SR)) / SR; f = note(m)
        add(i0, (np.sin(2 * np.pi * f * pg) + 0.5 * np.sin(2 * np.pi * 2 * f * pg) + 0.2 * np.sin(2 * np.pi * 3 * f * pg)) * np.exp(-pg * 7) * 0.07)
    # bass root on 1 and 3
    for k in (0, 2):
        i0 = int((s0 + k * beat) * SR); bg = np.arange(0, int(beat * SR)) / SR
        add(i0, np.sin(2 * np.pi * note(ch[0] - 24) * bg) * np.minimum(bg / 0.02, 1) * np.exp(-bg * 3) * 0.12)
fi = int(1.0 * SR); out[:fi] *= np.linspace(0, 1, fi); fo = int(3.0 * SR); out[-fo:] *= np.linspace(1, 0, fo)
out = np.tanh(out * 1.6) * 0.75
sf.write("music.wav", np.stack([out, out], 1), SR)
