"""
LetX promo — voiceover render (Kokoro-82M, local).

Each line is generated on its own so Kokoro produces natural sentence-final
prosody, then auto-fitted: if a take overruns its slot we nudge `speed` and
re-render rather than time-stretching (stretching is what makes TTS sound
robotic).

Timings are locked to the video's scene boundaries: 3.0 / 8.0 / 19.0 / 25.0.
"""
import sys
import numpy as np
import soundfile as sf
from scipy import signal

SR_TTS = 24000
SR = 48000
VOICE = sys.argv[1] if len(sys.argv) > 1 else 'af_heart'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'vo.wav'
DUR = 30.0

# (start, text, max_len, base_speed)
# `text` is spelled for the phonemizer, not for humans:
#   "dot tek"  -> .tex the way LaTeX users actually say it
#   "Let X"    -> LetX
LINES = [
    # --- Scene 1: the hook -------------------------------------------------
    (0.45,  "We've all been here.",                          1.60, 0.96),
    (2.28,  "Stop emailing dot tek files.",                  1.90, 1.00),
    # --- Scene 2: the problem ----------------------------------------------
    (4.30,  "Version chaos.",                                1.05, 1.02),
    (5.70,  "Add a collaborator? Pay up.",                   1.85, 1.02),
    # --- Scene 3: the product ----------------------------------------------
    (8.30,  "Let X is different.",                           1.35, 0.98),
    (9.60,  "Two cursors. One document. Live.",              2.45, 0.99),
    (12.20, "Compiles in seconds.",                          1.45, 0.98),
    (13.55, "Drag your whole project in. It just opens.",    2.65, 1.01),
    (16.45, "Over a thousand publisher ready templates.",    2.60, 1.01),
    # --- Scene 4: proof ----------------------------------------------------
    (19.90, "Used in universities across forty plus countries.", 2.70, 1.00),
    (23.15, "Unlimited collaborators. Free.",                2.20, 0.94),
    # --- Scene 5: CTA ------------------------------------------------------
    (26.10, "Let X dot app.",                                1.35, 0.95),
    (27.55, "No installation. Drag your project in.",        2.35, 0.99),
]


def trim(x, thresh=0.012, pad_head=0.012, pad_tail=0.06):
    """Strip the dead air Kokoro leaves at both ends."""
    a = np.abs(x)
    win = int(0.005 * SR_TTS)
    e = np.convolve(a, np.ones(win) / win, mode='same')
    nz = np.where(e > thresh)[0]
    if len(nz) == 0:
        return x
    i0 = max(0, nz[0] - int(pad_head * SR_TTS))
    i1 = min(len(x), nz[-1] + int(pad_tail * SR_TTS))
    return x[i0:i1]


def render(pipe, text, speed):
    chunks = [a.output.audio.numpy() for a in pipe(text, voice=VOICE, speed=speed)]
    return trim(np.concatenate(chunks))


def main():
    from kokoro import KPipeline
    pipe = KPipeline(lang_code='a')

    track = np.zeros(int(SR_TTS * (DUR + 3)))
    report = []

    for start, text, maxlen, base in LINES:
        speed = base
        for attempt in range(6):
            au = render(pipe, text, speed)
            dur = len(au) / SR_TTS
            if dur <= maxlen or attempt == 5:
                break
            # overran the slot — speak a little quicker, re-render clean
            speed = min(1.35, speed * (dur / maxlen) ** 0.65)
        i = int(start * SR_TTS)
        # short fades so nothing clicks at the seams
        f = int(0.008 * SR_TTS)
        au[:f] *= np.linspace(0, 1, f)
        au[-f:] *= np.linspace(1, 0, f)
        track[i:i + len(au)] += au
        report.append((start, round(dur, 2), round(start + dur, 2),
                       round(speed, 3), text))

    track = track[:int(SR_TTS * DUR)]

    # 24k -> 48k to match the music/SFX beds
    track = signal.resample_poly(track, SR // 1000, SR_TTS // 1000)

    sf.write(OUT, track, SR, subtype='PCM_24')

    print(f'voice={VOICE}  ->  {OUT}')
    print(f"{'start':>6} {'len':>5} {'end':>6} {'spd':>5}  line")
    for s, d, e, sp, t in report:
        print(f'{s:6.2f} {d:5.2f} {e:6.2f} {sp:5.2f}  {t}')


if __name__ == '__main__':
    main()
