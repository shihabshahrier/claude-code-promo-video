"""
LetX explainer — voiceover via OpenRouter `openai/gpt-audio`.

Why not Kokoro (which the 30s promo uses): gpt-audio's decoder is markedly more
natural, and at roughly $0.004 per line a full 95 s render costs about $0.06 —
cheap enough to re-render freely while tuning timing.

Two API quirks worth knowing:
  * Audio output **requires** `stream: true`. A non-streaming request 400s with
    "Audio output requires stream: true".
  * Audio arrives as base64 PCM chunks on `delta.audio.data`, 24 kHz mono.

Fitting lines to their slots: gpt-audio has no `speed` parameter, so instead of
time-stretching (which is exactly what makes TTS sound synthetic) we escalate a
pacing instruction and re-render. Same principle as the promo's Kokoro path.

Usage:  python vo_gpt.py [voice] [out.wav]
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

import numpy as np
import soundfile as sf
from scipy import signal

SR_TTS = 24000
SR = 48000
DUR = 95.0
URL = 'https://openrouter.ai/api/v1/chat/completions'
MODEL = 'openai/gpt-audio'

VOICE = sys.argv[1] if len(sys.argv) > 1 else 'marin'
OUT = sys.argv[2] if len(sys.argv) > 2 else f'vo_{VOICE}.wav'

# The persona is sent with every line. Keeping it identical across lines is what
# holds the voice consistent — gpt-audio drifts if the framing changes.
PERSONA = (
    "You are the voiceover artist for a polished software product explainer. "
    "Warm, confident, unhurried, genuinely enthusiastic without being salesy. "
    "You sound like a real person who uses and believes in this product — not "
    "an announcer, not an advert. Speak the line as a complete thought with "
    "natural sentence-final intonation."
)

# `text` is spelled for the speech model, not for humans:
#   "Lay-tek"  -> LaTeX, said the way its users say it (never "latex")
#   "Let X"    -> LetX
#   "Let X dot app" -> letx.app
# (start, text, max_len)
LINES = [
    (0.60,  "Tired of clunky Lay-tek setups?",                                  3.4),
    (5.35,  "Meet Let X — collaborative Lay-tek, right in your browser.",        4.4),
    (10.30, "No installs. Just start writing, for free.",                        3.5),
    (14.45, "Sign in in seconds. Zero config.",                                  3.4),
    (19.45, "Keep every project organized — or import straight from GitHub, or a zip.", 5.9),
    (26.40, "Choose from over a thousand templates, ready to go.",               4.8),
    (32.45, "Write together in real time. No conflicts, no version clashes.",    6.2),
    (40.45, "Compile in seconds. No paywalls, no waiting.",                      5.6),
    (48.45, "Meet your A I assistant — like Cursor, for papers. "
            "Ask it to write a section, and watch it generate right in your editor.", 11.0),
    (61.45, "Editor, templates, A I, and P D F — all in one platform.",          5.4),
    (68.70, "Loved by students and faculty who've made the switch.",             7.2),
    (78.45, "Built by researchers, for researchers.",                            5.2),
    (85.70, "Start writing, free — at Let X dot app.",                           7.4),
]

# Escalating pace nudges, used only when a take overruns its slot.
PACE = [
    "",
    " Speak at a slightly brisker pace than usual, still relaxed.",
    " Speak briskly and efficiently, but keep it natural.",
    " Speak quickly and tightly, without sounding rushed or clipped.",
]


def say(text, voice, extra=''):
    """One take. Returns float32 mono at SR_TTS, plus the reported cost."""
    body = {
        'model': MODEL,
        'modalities': ['text', 'audio'],
        'audio': {'voice': voice, 'format': 'pcm16'},
        'stream': True,
        'messages': [{'role': 'user',
                      'content': f'{PERSONA}{extra}\n\nSay only these words:\n{text}'}],
    }
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {os.environ["OPENROUTER_API_KEY"]}',
                 'Content-Type': 'application/json'})

    chunks, cost = [], 0.0
    with urllib.request.urlopen(req, timeout=300) as r:
        for raw in r:
            line = raw.decode().strip()
            if not line.startswith('data: '):
                continue
            payload = line[6:]
            if payload == '[DONE]':
                break
            try:
                ev = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if ev.get('usage'):
                cost = ev['usage'].get('cost', 0.0)
            for ch in ev.get('choices') or []:
                a = (ch.get('delta') or {}).get('audio')
                if isinstance(a, dict) and a.get('data'):
                    chunks.append(base64.b64decode(a['data']))

    pcm = np.frombuffer(b''.join(chunks), dtype='<i2').astype(np.float32) / 32768.0
    return pcm, cost


def trim(x, thresh=0.010, pad_head=0.010, pad_tail=0.05):
    """Strip the dead air the model leaves at both ends."""
    win = max(1, int(0.005 * SR_TTS))
    e = np.convolve(np.abs(x), np.ones(win) / win, mode='same')
    nz = np.where(e > thresh)[0]
    if len(nz) == 0:
        return x
    i0 = max(0, nz[0] - int(pad_head * SR_TTS))
    i1 = min(len(x), nz[-1] + int(pad_tail * SR_TTS))
    return x[i0:i1]


def main():
    if not os.environ.get('OPENROUTER_API_KEY'):
        sys.exit('OPENROUTER_API_KEY not set — source the repo .env first')

    track = np.zeros(int(SR_TTS * (DUR + 6)), dtype=np.float32)
    report, total = [], 0.0

    for start, text, maxlen in LINES:
        best = None
        for attempt in range(len(PACE)):
            au, cost = say(text, VOICE, PACE[attempt])
            total += cost
            au = trim(au)
            dur = len(au) / SR_TTS
            if best is None or dur < best[1]:
                best = (au, dur, attempt)
            if dur <= maxlen:
                break
        au, dur, attempt = best
        if dur > maxlen:
            print(f'  ! {start:6.2f} still {dur:.2f}s > {maxlen:.2f}s slot', file=sys.stderr)

        f = int(0.008 * SR_TTS)
        au = au.copy()
        au[:f] *= np.linspace(0, 1, f)
        au[-f:] *= np.linspace(1, 0, f)

        i = int(start * SR_TTS)
        track[i:i + len(au)] += au
        report.append((start, dur, start + dur, attempt, text))

    track = track[:int(SR_TTS * DUR)]
    track = signal.resample_poly(track, SR // 1000, SR_TTS // 1000)
    sf.write(OUT, track, SR, subtype='PCM_24')

    print(f'voice={VOICE}  ->  {OUT}   cost=${total:.3f}')
    print(f"{'start':>6} {'len':>5} {'end':>6} {'try':>4}  line")
    for s, d, e, a, t in report:
        print(f'{s:6.2f} {d:5.2f} {e:6.2f} {a:4d}  {t[:64]}')
    speech = sum(d for _, d, _, _, _ in report)
    print(f'\nspeech {speech:.1f}s of {DUR:.0f}s ({speech / DUR * 100:.0f}%)')


if __name__ == '__main__':
    main()
