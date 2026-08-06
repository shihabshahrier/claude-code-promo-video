"""
LetX promo — final mix.

  VO   : HPF, de-ess, presence EQ, compression, gentle saturation, small room
  Music: ducked under the VO (sidechain), high-shelf carved where speech lives
  SFX  : lightly ducked, kept punchy

Output is a 48 kHz stereo master; loudness is normalised to -14 LUFS by the
ffmpeg step in build.sh (the social-platform target).
"""
import sys
import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
VO_PATH = sys.argv[1] if len(sys.argv) > 1 else 'vo_af_heart.wav'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'mix.wav'


def read(path):
    x, sr = sf.read(path, always_2d=True)
    assert sr == SR, f'{path}: {sr}'
    return x.T  # -> (channels, n)


def to_stereo(x):
    return np.vstack([x, x]) if x.shape[0] == 1 else x


def biquad(x, b, a):
    return signal.lfilter(b, a, x, axis=-1)


def hpf(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'high')
    return biquad(x, b, a)


def lpf(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'low')
    return biquad(x, b, a)


def peaking(x, fc, gain_db, q=1.0):
    """RBJ peaking EQ."""
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * fc / SR
    alpha = np.sin(w0) / (2 * q)
    b = [1 + alpha * A, -2 * np.cos(w0), 1 - alpha * A]
    a = [1 + alpha / A, -2 * np.cos(w0), 1 - alpha / A]
    return biquad(x, np.array(b) / a[0], np.array(a) / a[0])


def highshelf(x, fc, gain_db, q=0.707):
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * fc / SR
    alpha = np.sin(w0) / (2 * q)
    c, s = np.cos(w0), np.sqrt(A)
    b = [A * ((A + 1) + (A - 1) * c + 2 * s * alpha),
         -2 * A * ((A - 1) + (A + 1) * c),
         A * ((A + 1) + (A - 1) * c - 2 * s * alpha)]
    a = [(A + 1) - (A - 1) * c + 2 * s * alpha,
         2 * ((A - 1) - (A + 1) * c),
         (A + 1) - (A - 1) * c - 2 * s * alpha]
    return biquad(x, np.array(b) / a[0], np.array(a) / a[0])


def envelope(x, attack=0.005, release=0.12):
    """Mono peak follower with separate attack/release."""
    m = np.abs(x).max(axis=0) if x.ndim > 1 else np.abs(x)
    ka = np.exp(-1 / (attack * SR))
    kr = np.exp(-1 / (release * SR))
    out = np.empty_like(m)
    e = 0.0
    for i in range(len(m)):
        v = m[i]
        k = ka if v > e else kr
        e = k * e + (1 - k) * v
        out[i] = e
    return out


def compress(x, thresh_db=-20, ratio=3.5, attack=0.006, release=0.12, makeup_db=0):
    env = envelope(x, attack, release)
    env_db = 20 * np.log10(np.maximum(env, 1e-9))
    over = np.maximum(0.0, env_db - thresh_db)
    gain_db = -over * (1 - 1 / ratio) + makeup_db
    g = 10 ** (gain_db / 20)
    return x * g


def deess(x, fc=6800, thresh=0.12, amount=0.65):
    """Split the sibilant band and compress only that."""
    b, a = signal.butter(2, [5200 / (SR / 2), 11000 / (SR / 2)], 'band')
    sib = biquad(x, b, a)
    env = envelope(sib, 0.001, 0.045)
    red = np.clip(thresh / np.maximum(env, 1e-9), 0, 1)
    red = 1 - (1 - red) * amount
    return x - sib * (1 - red)


def reverb(x, mix=0.10, decay=0.22, predelay=0.018):
    """Small, dry room — just enough that the VO isn't stuck to the speaker."""
    n = x.shape[-1]
    wet = np.zeros_like(x)
    taps = [(0.0113, 0.7), (0.0197, 0.55), (0.0291, 0.45),
            (0.0431, 0.35), (0.0619, 0.26), (0.0893, 0.18)]
    for dt, g in taps:
        d = int((dt + predelay) * SR)
        if d >= n:
            continue
        wet[..., d:] += x[..., :n - d] * g * decay
    wet = lpf(hpf(wet, 400), 5200)
    return x + wet * mix


def saturate(x, drive=1.4, blend=0.35):
    return x * (1 - blend) + np.tanh(x * drive) / np.tanh(drive) * blend


def duck(target, control, depth_db=-11.0, attack=0.012, release=0.28,
         thresh=0.02, lookahead=0.05):
    """
    Sidechain: pull `target` down wherever `control` (the VO) is speaking.
    Lookahead means the duck opens *before* the word, not on top of it.
    """
    env = envelope(control, attack, release)
    la = int(lookahead * SR)
    env = np.concatenate([env[la:], np.zeros(la)])
    act = np.clip((env - thresh) / 0.10, 0, 1) ** 0.6
    w = int(0.03 * SR)
    k = np.hanning(w)
    k /= k.sum()
    act = np.convolve(act, k, mode='same')
    gain = 10 ** ((depth_db * act) / 20)
    return target * gain


def limit(x, ceiling=0.97, lookahead=0.003):
    la = int(lookahead * SR)
    m = np.abs(x).max(axis=0)
    m = np.concatenate([m[la:], np.zeros(la)]) if la else m
    env = envelope(np.vstack([m, m]), 0.0005, 0.06)
    g = np.minimum(1.0, ceiling / np.maximum(env, 1e-9))
    w = int(0.004 * SR)
    k = np.hanning(w)
    k /= k.sum()
    g = np.convolve(g, k, mode='same')
    return np.tanh(x * g / ceiling) * ceiling


def main():
    vo = to_stereo(read(VO_PATH))
    music = to_stereo(read('music.wav'))
    sfx = to_stereo(read('sfx.wav'))

    n = min(vo.shape[-1], music.shape[-1], sfx.shape[-1])
    vo, music, sfx = vo[:, :n], music[:, :n], sfx[:, :n]

    # ---------------------------------------------------------------- VOICE
    v = hpf(vo, 95, order=3)          # kill rumble/DC
    v = peaking(v, 260, -2.2, q=1.1)  # de-mud
    v = peaking(v, 1900, 1.6, q=0.9)  # intelligibility
    v = peaking(v, 4200, 2.8, q=0.8)  # presence / "in the room"
    v = highshelf(v, 9000, 1.8)       # air
    v = deess(v, thresh=0.10, amount=0.7)
    v = compress(v, thresh_db=-21, ratio=3.2, attack=0.005, release=0.11,
                 makeup_db=5.5)
    v = compress(v, thresh_db=-12, ratio=2.4, attack=0.001, release=0.05,
                 makeup_db=2.0)       # second, faster stage = broadcast glue
    v = saturate(v, drive=1.6, blend=0.30)
    v = reverb(v, mix=0.09)
    v = v / max(1e-9, np.abs(v).max()) * 0.80

    # ---------------------------------------------------------------- MUSIC
    m = music
    m = peaking(m, 2400, -3.4, q=0.7)   # carve a pocket where speech lives
    m = peaking(m, 55, 2.0, q=0.9)      # keep the sub weight on phone speakers
    m = highshelf(m, 11000, 1.2)
    m = duck(m, v, depth_db=-11.5, release=0.30)
    m = m * 0.30

    # ------------------------------------------------------------------ SFX
    s = sfx
    s = peaking(s, 3000, -1.8, q=0.8)
    s = duck(s, v, depth_db=-4.5, release=0.22)
    s = s * 0.46

    bus = v + m + s
    # Light glue only — loudnorm does the loudness lift downstream, and
    # crushing here collapses LRA and pushes inter-sample peaks over 0 dBTP.
    bus = compress(bus, thresh_db=-11, ratio=1.6, attack=0.015, release=0.22,
                   makeup_db=1.0)
    bus = limit(bus, ceiling=0.89)

    sf.write(OUT, bus.T, SR, subtype='PCM_24')

    peak = 20 * np.log10(np.abs(bus).max())
    rms = 20 * np.log10(np.sqrt((bus ** 2).mean()))
    print(f'{OUT}: {n / SR:.2f}s  peak {peak:.2f} dBFS  rms {rms:.2f} dBFS')


if __name__ == '__main__':
    main()
