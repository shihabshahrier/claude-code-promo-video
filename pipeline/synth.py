"""
LetX promo — procedural score + SFX.

Everything here is synthesized from scratch (numpy), so the output is
100% licence-clean and every hit lands on an exact frame of the video.

Video: 1080x1920, 30fps, 30.000s.
Tempo: 120 BPM -> beat 0.5s, bar 2.0s. Scene cuts at 3.0 / 8.0 / 19.0 / 25.0
all land on beat or half-bar boundaries.
"""
import numpy as np
from scipy import signal
import soundfile as sf

SR = 48000
DUR = 30.0
N = int(SR * DUR)
T = np.arange(N) / SR

BPM = 120.0
BEAT = 60.0 / BPM          # 0.5s
BAR = BEAT * 4             # 2.0s

rng = np.random.default_rng(7)   # fixed seed -> reproducible render


# ---------------------------------------------------------------- utilities
def buf():
    return np.zeros(N, dtype=np.float64)


def idx(t):
    return int(round(t * SR))


def add(dst, src, at):
    """Mix `src` into `dst` starting at time `at` (seconds), clipped to length."""
    i = idx(at)
    if i >= N:
        return
    if i < 0:
        src = src[-i:]
        i = 0
    n = min(len(src), N - i)
    dst[i:i + n] += src[:n]


def adsr(n, a=0.005, d=0.1, s=0.0, r=0.1):
    """Simple ADSR over n samples."""
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    s_n = max(0, n - a_n - d_n - r_n)
    env = np.concatenate([
        np.linspace(0, 1, a_n, endpoint=False),
        np.linspace(1, s, d_n, endpoint=False),
        np.full(s_n, s),
        np.linspace(s, 0, r_n),
    ])
    return env[:n] if len(env) >= n else np.pad(env, (0, n - len(env)))


def expdecay(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def lp(x, fc, order=2):
    fc = np.clip(fc, 20, SR / 2 - 100)
    b, a = signal.butter(order, fc / (SR / 2), 'low')
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    fc = np.clip(fc, 20, SR / 2 - 100)
    b, a = signal.butter(order, fc / (SR / 2), 'high')
    return signal.lfilter(b, a, x)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band')
    return signal.lfilter(b, a, x)


def sweep_lp(x, fc_curve, order=2):
    """Time-varying lowpass, done in 512-sample blocks (cheap and smooth enough)."""
    out = np.zeros_like(x)
    blk = 512
    zi = None
    for i in range(0, len(x), blk):
        fc = float(np.clip(fc_curve[min(i, len(fc_curve) - 1)], 40, SR / 2 - 200))
        b, a = signal.butter(order, fc / (SR / 2), 'low')
        if zi is None:
            zi = np.zeros(max(len(a), len(b)) - 1)
        seg, zi = signal.lfilter(b, a, x[i:i + blk], zi=zi)
        out[i:i + blk] = seg
    return out


def saw(freq, n, phase=0.0, harm=14):
    """Additive band-limited saw."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, harm + 1):
        if freq * k > SR / 2.2:
            break
        out += np.sin(2 * np.pi * freq * k * t + phase) / k
    return out * (2 / np.pi)


def sine(freq, n, phase=0.0):
    return np.sin(2 * np.pi * freq * np.arange(n) / SR + phase)


def noise(n):
    return rng.standard_normal(n)


def reverb(x, decay=0.35, mix=0.25, predelay=0.02):
    """Cheap Schroeder-ish tail: a few delayed, filtered copies."""
    out = np.zeros(len(x) + int(SR * 1.2))
    out[:len(x)] = x
    taps = [(0.031, 0.75), (0.047, 0.66), (0.071, 0.58), (0.101, 0.5),
            (0.153, 0.4), (0.211, 0.3), (0.307, 0.2)]
    wet = np.zeros_like(out)
    for dt, g in taps:
        d = int((dt + predelay) * SR)
        seg = x * g * decay
        seg = lp(seg, 4200)
        n = min(len(seg), len(wet) - d)
        wet[d:d + n] += seg[:n]
        # second-order bounce
        d2 = d * 2
        n2 = min(len(seg), len(wet) - d2)
        if n2 > 0:
            wet[d2:d2 + n2] += seg[:n2] * decay * 0.5
    res = out + wet * mix
    return res[:len(x)]


def ramp(t0, t1, v0, v1, curve=1.0):
    """Piecewise gain curve helper -> full-length array segment writer."""
    g = np.zeros(N)
    i0, i1 = idx(t0), idx(t1)
    x = np.linspace(0, 1, max(1, i1 - i0)) ** curve
    g[i0:i1] = v0 + (v1 - v0) * x
    return g, i0, i1


def env_from_points(points, smooth=0.05):
    """points = [(time, value), ...] -> smoothed step/linear automation curve."""
    ts = np.array([p[0] for p in points])
    vs = np.array([p[1] for p in points])
    e = np.interp(T, ts, vs)
    w = max(3, int(smooth * SR))
    k = np.hanning(w)
    k /= k.sum()
    return np.convolve(e, k, mode='same')


# ---------------------------------------------------------------- note tables
def nt(name):
    """Note name -> Hz (A4 = 440)."""
    names = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6,
             'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
    p, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[p] + (o - 4) * 12 - 9) / 12)


# Am - F - C - G, one chord per bar, 4-bar loop = 8.0s (aligns with scene cuts)
PROG = [
    ('A', ['A2', 'C4', 'E4', 'A4']),
    ('F', ['F2', 'A3', 'C4', 'F4']),
    ('C', ['C3', 'E4', 'G4', 'C5']),
    ('G', ['G2', 'B3', 'D4', 'G4']),
]
ARP_SETS = [
    ['A4', 'C5', 'E5', 'C5', 'A4', 'E5', 'C5', 'G4'],
    ['F4', 'A4', 'C5', 'A4', 'F4', 'C5', 'A4', 'E5'],
    ['C5', 'E5', 'G5', 'E5', 'C5', 'G4', 'E5', 'C5'],
    ['G4', 'B4', 'D5', 'B4', 'G4', 'D5', 'B4', 'A4'],
]


# ================================================================== DRUMS
def kick():
    n = int(0.42 * SR)
    f = 130 * np.exp(-np.arange(n) / (0.022 * SR)) + 44
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * expdecay(n, 0.14)
    click = hp(noise(int(0.006 * SR)), 1800) * 0.35
    out = body
    out[:len(click)] += click
    return np.tanh(out * 1.6) * 0.9


def snap():
    n = int(0.22 * SR)
    x = noise(n)
    x = bp(x, 1400, 6500) * expdecay(n, 0.045)
    tone = sine(320, n) * expdecay(n, 0.03) * 0.25
    return (x * 0.7 + tone) * 0.55


def hat(open_=False):
    n = int((0.16 if open_ else 0.045) * SR)
    x = hp(noise(n), 7200) * expdecay(n, 0.05 if open_ else 0.014)
    return x * (0.24 if open_ else 0.2)


def rim():
    n = int(0.09 * SR)
    x = bp(noise(n), 900, 3000) * expdecay(n, 0.018)
    return x * 0.35


# ================================================================== SFX
def ui_tick(pitch=1900, level=0.34):
    """Crisp UI click — used for the filename stack."""
    n = int(0.09 * SR)
    tone = (sine(pitch, n) + 0.5 * sine(pitch * 2.01, n)) * expdecay(n, 0.012)
    click = hp(noise(int(0.004 * SR)), 4000) * 0.5
    out = tone * 0.8
    out[:len(click)] += click
    return lp(out, 12000) * level


def impact(level=1.0, bright=1.0):
    """Cinematic slam — sub drop + noise burst + short tail."""
    n = int(1.6 * SR)
    f = 120 * np.exp(-np.arange(n) / (0.05 * SR)) + 34
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * expdecay(n, 0.32)
    crack = lp(noise(n), 5000 * bright) * expdecay(n, 0.09) * 0.5
    body = bp(noise(n), 120, 900) * expdecay(n, 0.2) * 0.35
    x = np.tanh((sub * 1.1 + crack + body) * 1.3)
    return reverb(x, decay=0.3, mix=0.3) * 0.85 * level


def whoosh(dur=0.55, level=0.5, rise=True, lo=250, hi=6000):
    """Filtered noise sweep — transitions, wipes, swipes."""
    n = int(dur * SR)
    x = noise(n)
    curve = np.linspace(0, 1, n) ** 0.7
    fc = lo + (hi - lo) * (curve if rise else curve[::-1])
    x = sweep_lp(x, fc, order=2)
    x = hp(x, 180)
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.4
    return x * env * level


def swish(dur=0.26, level=0.3):
    """Small object moving — the attachment chips."""
    n = int(dur * SR)
    x = bp(noise(n), 700, 5200)
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return x * env * level


def key_click(level=0.16, pitch=2600):
    """Mechanical-ish keystroke, deliberately soft so it sits under the VO."""
    n = int(0.05 * SR)
    tone = sine(pitch * (0.9 + 0.2 * rng.random()), n) * expdecay(n, 0.006)
    body = bp(noise(n), 1200, 7000) * expdecay(n, 0.009)
    return (tone * 0.35 + body * 0.65) * level


def ping(freq=1320, level=0.4, dur=1.1, decay=0.28):
    """Bell-ish confirmation tone — compile chip, stat hits."""
    n = int(dur * SR)
    parts = [(1.0, 1.0, decay), (2.0, 0.4, decay * 0.6),
             (3.01, 0.18, decay * 0.4), (4.98, 0.09, decay * 0.3)]
    x = np.zeros(n)
    for mult, amp, tau in parts:
        x += sine(freq * mult, n) * expdecay(n, tau) * amp
    x *= adsr(n, a=0.002, d=0.02, s=0.85, r=dur * 0.7)
    return reverb(x, decay=0.35, mix=0.22) * level


def thud(level=0.55):
    """Something lands."""
    n = int(0.6 * SR)
    f = 90 * np.exp(-np.arange(n) / (0.03 * SR)) + 52
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * expdecay(n, 0.12)
    body = lp(noise(n), 1400) * expdecay(n, 0.05) * 0.4
    return np.tanh((sub + body) * 1.2) * level


def riser(dur=2.2, level=0.35, f0=180, f1=2400):
    """Tension riser — noise + rising detuned tone."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    curve = (t / dur) ** 1.8
    f = f0 + (f1 - f0) * curve
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
    tone += 0.6 * np.sin(2 * np.pi * np.cumsum(f * 1.005) / SR)
    nz = sweep_lp(noise(n), 400 + 9000 * curve)
    x = tone * 0.35 + nz * 0.5
    return x * (curve ** 1.2) * level


def reverse_swell(dur=1.0, level=0.4):
    """Reverse-cymbal style pull-in before a hit."""
    n = int(dur * SR)
    x = hp(noise(n), 900)
    env = np.linspace(0, 1, n) ** 2.5
    return x * env * level


def freeze_stop(level=0.6):
    """Record-stop / everything-freezes gesture."""
    n = int(0.9 * SR)
    f = np.linspace(700, 60, n)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * expdecay(n, 0.22)
    nz = sweep_lp(noise(n), np.linspace(9000, 250, n)) * expdecay(n, 0.18) * 0.5
    return np.tanh((tone + nz) * 1.1) * level


# ================================================================== MUSIC BED
def build_music():
    sub_b, arp_b, pad_b, drum_b, tex_b = buf(), buf(), buf(), buf(), buf()

    # ---- pad: sustained chord stack, one per bar, long overlapping tails
    for bar_i in range(int(DUR / BAR) + 1):
        t0 = bar_i * BAR
        if t0 >= DUR:
            break
        _, notes = PROG[bar_i % 4]
        n = int((BAR * 1.9) * SR)
        chord = np.zeros(n)
        for j, name in enumerate(notes[1:]):
            f = nt(name)
            for det in (-0.14, 0.0, 0.15):
                chord += saw(f * (1 + det / 100), n, phase=rng.random() * 6.28,
                             harm=8) * (0.5 / (j + 1.6))
        chord = lp(chord, 1500)
        chord *= adsr(n, a=0.55, d=0.4, s=0.55, r=BAR * 1.0)
        add(pad_b, chord * 0.20, t0)

    # ---- sub bass: root note, eighth-note pulse with a long first hit
    for bar_i in range(int(DUR / BAR) + 1):
        t0 = bar_i * BAR
        if t0 >= DUR:
            break
        root = nt(PROG[bar_i % 4][1][0])
        pattern = [0.0, 1.0, 1.5, 2.5, 3.0, 3.5]  # in beats
        for b in pattern:
            n = int(0.42 * SR)
            x = (sine(root, n) * 0.8 + sine(root * 2, n) * 0.18
                 + saw(root, n, harm=5) * 0.12)
            x *= adsr(n, a=0.004, d=0.16, s=0.35, r=0.2)
            add(sub_b, lp(x, 420) * 0.5, t0 + b * BEAT)

    # ---- arp: 16th plucks, the "premium dev tool" signature
    step = BEAT / 2
    total_steps = int(DUR / step)
    for s in range(total_steps):
        t0 = s * step
        bar_i = int(t0 // BAR) % 4
        note = ARP_SETS[bar_i][s % 8]
        f = nt(note)
        n = int(0.36 * SR)
        x = saw(f, n, harm=10) * 0.5 + sine(f * 2, n) * 0.18
        x = lp(x, 2600 + 900 * np.sin(t0 * 0.7))
        x *= expdecay(n, 0.055) * (1.0 if s % 2 == 0 else 0.62)
        add(arp_b, x * 0.17, t0)

    # ---- drums
    for bar_i in range(int(DUR / BAR) + 2):
        t0 = bar_i * BAR
        if t0 >= DUR:
            break
        for b in (0, 1, 2, 3):                      # four on the floor
            add(drum_b, kick(), t0 + b * BEAT)
        for b in (1, 3):                            # backbeat snap
            add(drum_b, snap(), t0 + b * BEAT)
        for h in range(8):                          # eighth hats
            add(drum_b, hat(open_=(h == 7)), t0 + h * (BEAT / 2))
        if bar_i % 4 == 3:                          # bar-end rim fill
            for r in (3.5, 3.75):
                add(drum_b, rim(), t0 + r * BEAT)

    # ---- texture: slow filtered-noise "air" so no frame is dead silent
    air = sweep_lp(noise(N), 600 + 500 * np.sin(2 * np.pi * 0.07 * T))
    air = hp(air, 300)
    tex_b += air * 0.012

    # ------------------------------------------------------------ arrangement
    # Gains keyed to the exact scene boundaries of the video.
    g_pad = env_from_points([
        (0.0, 0.55), (2.1, 0.55), (2.2, 0.9), (3.0, 0.7), (5.35, 0.7),
        (5.45, 1.05), (7.95, 0.6), (8.05, 0.95), (18.9, 0.95), (19.1, 0.8),
        (22.9, 0.8), (23.1, 1.0), (25.0, 1.0), (27.5, 1.0), (30.0, 0.55),
    ], smooth=0.10)

    g_sub = env_from_points([
        (0.0, 0.35), (2.15, 0.35), (2.25, 0.75), (2.95, 0.6), (3.05, 0.7),
        (5.35, 0.7), (5.45, 0.45), (7.9, 0.3), (8.0, 1.0), (18.9, 1.0),
        (19.1, 0.7), (22.9, 0.7), (23.1, 1.0), (25.0, 0.95), (28.5, 0.8),
        (30.0, 0.3),
    ], smooth=0.05)

    g_arp = env_from_points([
        (0.0, 0.0), (2.9, 0.0), (3.1, 0.55), (5.3, 0.75), (5.45, 0.18),
        (7.9, 0.18), (8.05, 1.0), (15.5, 1.0), (15.7, 0.85), (18.9, 0.85),
        (19.1, 0.45), (22.9, 0.5), (23.1, 0.9), (25.0, 0.8), (28.0, 0.6),
        (30.0, 0.2),
    ], smooth=0.05)

    g_drum = env_from_points([
        (0.0, 0.0), (2.95, 0.0), (3.05, 0.30), (5.3, 0.42), (5.45, 0.0),
        (7.95, 0.0), (8.05, 1.0), (18.9, 1.0), (19.1, 0.55), (22.9, 0.55),
        (23.1, 0.85), (25.0, 0.9), (27.6, 0.75), (28.6, 0.35), (29.4, 0.0),
    ], smooth=0.04)

    # Global filter automation: dark during the "freeze/paywall" beat,
    # wide open on the product drop.
    fc = env_from_points([
        (0.0, 2600), (2.2, 6000), (3.0, 5000), (5.35, 5200), (5.5, 620),
        (7.6, 480), (7.95, 900), (8.1, 16000), (19.0, 14000), (23.0, 16000),
        (28.0, 15000), (30.0, 7000),
    ], smooth=0.08)

    music = (pad_b * g_pad + sub_b * g_sub + arp_b * g_arp
             + drum_b * g_drum + tex_b)
    music = sweep_lp(music, fc, order=2)
    return music


# ================================================================== SFX TRACK
def build_sfx():
    s = buf()

    # --- SCENE 1 (0.0-3.0) filename stack + slam ---------------------------
    stack_times = [0.55, 0.83, 1.11, 1.39, 1.67, 1.95]
    for i, t in enumerate(stack_times):
        # each new filename a touch higher and louder — mounting absurdity
        add(s, ui_tick(pitch=1500 + i * 210, level=0.26 + i * 0.035), t)
    add(s, riser(dur=2.0, level=0.30, f0=200, f1=2600), 0.25)
    add(s, reverse_swell(dur=0.7, level=0.30), 1.5)
    add(s, impact(level=1.0), 2.2)              # "Stop emailing .tex files."

    # --- SCENE 2 (3.0-8.0) attachment chaos -> paywall ---------------------
    add(s, whoosh(0.4, 0.42, rise=False, lo=400, hi=7000), 2.98)   # hard cut
    chip_times = [3.35, 3.72, 4.05, 4.34, 4.60, 4.83, 5.03, 5.20]
    for i, t in enumerate(chip_times):
        # pans/pitches alternate to sell left-right flight
        add(s, swish(0.24 - i * 0.012, 0.24 + i * 0.02), t)
        add(s, ui_tick(pitch=1100 + (i % 2) * 700, level=0.12), t + 0.16)
    add(s, freeze_stop(0.62), 5.36)             # everything freezes
    add(s, thud(0.42), 5.62)                    # modal slides up
    add(s, ping(freq=660, level=0.22, dur=1.4, decay=0.4), 5.72)   # amber lock
    add(s, whoosh(0.5, 0.5, rise=True, lo=300, hi=5500), 7.38)     # swipe off

    # --- SCENE 3 (8.0-19.0) the product ------------------------------------
    add(s, whoosh(0.85, 0.62, rise=True, lo=200, hi=9000), 7.85)   # violet wipe
    add(s, impact(level=0.55, bright=1.4), 8.02)

    # two cursors typing at once: two interleaved, distinct key rhythms
    t = 8.62
    while t < 11.95:                            # "You" — steady, confident
        add(s, key_click(level=0.13, pitch=2500), t)
        t += 0.105 + rng.random() * 0.045
    t = 8.78
    while t < 11.95:                            # "Co-author" — different cadence
        add(s, key_click(level=0.10, pitch=3200), t)
        t += 0.135 + rng.random() * 0.06

    add(s, whoosh(0.35, 0.22, rise=True, lo=500, hi=4000), 11.9)   # PDF shimmer
    add(s, ping(freq=1568, level=0.34, dur=1.3, decay=0.3), 12.05)  # "Compiled in 3.8s"

    add(s, whoosh(0.3, 0.3, rise=False, lo=600, hi=6000), 12.55)   # zip falls
    add(s, thud(0.5), 12.86)                                        # it lands
    for i, t in enumerate([13.55, 13.72, 13.89]):                   # file tree slides in
        add(s, swish(0.28, 0.2), t)
        add(s, ui_tick(pitch=1700 + i * 260, level=0.16), t + 0.14)
    add(s, ping(freq=880, level=0.16, dur=1.0), 14.1)

    add(s, whoosh(0.7, 0.45, rise=True, lo=300, hi=8000), 15.5)    # cards streak up
    # counter ticking 0 -> 1,000+: accelerating soft ticks
    ct, tt = 15.95, 0.115
    while ct < 18.55:
        add(s, ui_tick(pitch=2100, level=0.055), ct)
        ct += tt
        tt = max(0.045, tt * 0.955)
    add(s, ping(freq=1174, level=0.3, dur=1.2), 18.6)              # counter lands

    # --- SCENE 4 (19.0-25.0) proof ----------------------------------------
    add(s, whoosh(0.35, 0.3, rise=False, lo=500, hi=6500), 18.92)
    for i, (t, f) in enumerate([(19.15, 1046.5), (19.65, 1318.5), (20.15, 1568.0)]):
        add(s, ping(freq=f, level=0.34, dur=1.5, decay=0.34), t)   # 1,000+ / 150+ / 40+
        add(s, thud(0.22), t)
    add(s, riser(dur=1.5, level=0.3, f0=300, f1=3000), 21.5)
    add(s, whoosh(0.4, 0.4, rise=True, lo=400, hi=7000), 22.85)    # collapse upward
    add(s, impact(level=0.8), 23.02)                               # "Unlimited... Free."

    # --- SCENE 5 (25.0-30.0) CTA ------------------------------------------
    add(s, reverse_swell(dur=0.9, level=0.40), 24.15)
    add(s, impact(level=0.92, bright=0.8), 25.02)                  # wordmark lands
    add(s, thud(0.40), 25.04)                                      # extra low weight
    add(s, hat(open_=True) * 2.2, 25.02)                           # top-end sparkle
    add(s, ping(freq=1046.5, level=0.32, dur=2.6, decay=0.6), 25.06)
    add(s, ui_tick(pitch=1900, level=0.24), 26.02)                 # letx.app
    add(s, ui_tick(pitch=2200, level=0.20), 26.82)                 # Free. No installation.
    add(s, thud(0.3), 27.62)                                       # pill button
    add(s, ping(freq=1318.5, level=0.30, dur=2.6, decay=0.6), 27.66)
    return s


# ================================================================== STEREO
def widen(x, amount=0.35, delay_ms=9.0):
    """Haas widening — keeps the low end mono, spreads the top."""
    d = int(SR * delay_ms / 1000)
    low = lp(x, 180)
    high = x - low
    l = high.copy()
    r = np.concatenate([np.zeros(d), high[:-d]]) if d else high.copy()
    l = low + l * (1 + amount)
    r = low + r * (1 + amount)
    return np.stack([l, r], axis=1)


if __name__ == '__main__':
    print('rendering music...')
    music = build_music()
    print('rendering sfx...')
    sfx = build_sfx()

    music /= max(1e-9, np.abs(music).max())
    sfx /= max(1e-9, np.abs(sfx).max())

    sf.write('music.wav', widen(music * 0.9, 0.4, 11.0), SR, subtype='PCM_24')
    sf.write('sfx.wav', widen(sfx * 0.9, 0.25, 7.0), SR, subtype='PCM_24')
    print('wrote music.wav + sfx.wav')
