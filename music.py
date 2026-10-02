import numpy as np, soundfile as sf, sys
SR = 44100; dur = float(sys.argv[1]); n = int(SR * dur); t = np.arange(n) / SR
def note(f): return 440 * 2 ** ((f - 69) / 12)
out = np.zeros(n)
bpm = 66; beat = 60 / bpm; bar = beat * 4
chords = [[60, 64, 67, 71], [57, 60, 64, 67], [65, 69, 72, 76], [67, 71, 74, 79]]  # Cmaj7 Am7 Fmaj7 G
nbars = int(dur / bar) + 1
rng = np.random.default_rng(7)
for b in range(nbars):
    ch = chords[b % 4]; s0 = b * bar; i0 = int(s0 * SR); seg = np.arange(0, int(bar * SR) + SR) / SR
    env = np.minimum(seg / 1.6, 1) * np.exp(-seg / 3.2)
    pad = np.zeros_like(seg)
    for m in ch:
        f = note(m - 12)
        pad += np.sin(2 * np.pi * f * seg) + 0.35 * np.sin(2 * np.pi * 2 * f * seg + 0.3) + 0.12 * np.sin(2 * np.pi * 3 * f * seg)
    pad *= env * 0.045
    end = min(n, i0 + len(seg)); out[i0:end] += pad[: end - i0]
    # sparse pluck arpeggio
    for k in range(8):
        if rng.random() < 0.55:
            m = ch[(k + b) % 4] + (12 if k % 3 == 0 else 0); st = s0 + k * beat / 2; i1 = int(st * SR)
            seg2 = np.arange(0, int(2.2 * SR)) / SR; f = note(m)
            pl = (np.sin(2 * np.pi * f * seg2) + 0.4 * np.sin(2 * np.pi * 2 * f * seg2)) * np.exp(-seg2 * 2.4) * 0.05
            e2 = min(n, i1 + len(seg2))
            if i1 < n: out[i1:e2] += pl[: e2 - i1]
# gentle fade in/out and soft limit
fade = int(2 * SR); out[:fade] *= np.linspace(0, 1, fade); out[-int(4 * SR):] *= np.linspace(1, 0, int(4 * SR))
out = np.tanh(out * 1.3) * 0.7
sf.write("music.wav", np.stack([out, out], 1), SR)
