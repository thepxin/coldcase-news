"""Turns an article's Reel script (front matter social.reel: 2-3 short, fact-checked lines) into a 15-second vertical
video for Instagram Reels and YouTube Shorts: static/reels/<article>.mp4 (served at coldcasetech.com/reels/...).

Voice: Kokoro (open-source voice model, Apache 2.0 licence, runs here, no account). Music: chords made here from
scratch, so nobody else owns any of the sound. Pictures: drawn here in the site's own fonts and colours.
A Reel is a bonus: if anything fails, the article is unaffected and Instagram gets the picture post instead.

Usage: python scripts/reel.py [--recent] content/posts/<article>.md [more.md ...]
  --recent also makes the videos missing for articles of the last 2 days (a run where the Reel step failed).
Needs ffmpeg and: pip install kokoro-onnx soundfile fonttools brotli pillow numpy pyyaml
"""
import glob
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta, timezone

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.environ.get("REEL_OUT_DIR") or os.path.join(ROOT, "static", "reels")
KEEP_DAYS = int(os.environ.get("REEL_KEEP_DAYS", "21"))   # older videos are removed (Instagram keeps its own copy)
MODEL_DIR = os.path.expanduser(os.environ.get("REEL_MODEL_DIR", "~/.cache/coldcase-reel"))
MODEL_FILES = {   # the voice model's files, as published by the kokoro-onnx project on GitHub
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
VOICE, SPEED = os.environ.get("REEL_VOICE", "af_heart"), float(os.environ.get("REEL_SPEED", "1.05"))

W, H, FPS = 1080, 1920, 30
PAPER, INK, INK2, MUTED = "#0f1115", "#ece8df", "#c9c5bc", "#9a9fab"
BRASS, OK, WARN, BAD = "#c9a862", "#6fcf9f", "#e3bd6b", "#ee8f88"
X0, X1 = 96, 984          # safe area: Instagram's buttons sit on the right and at the bottom
MONTHS = {"Jan.": "January", "Feb.": "February", "Mar.": "March", "Apr.": "April", "Aug.": "August",
          "Sept.": "September", "Sep.": "September", "Oct.": "October", "Nov.": "November", "Dec.": "December"}


# ------------------------------------------------------------------------------------------------ inputs
def read_article(path):
    text = open(path, encoding="utf-8").read()
    fm = yaml.safe_load(text.split("\n---", 2)[0].lstrip("-\n")) or {}
    return fm


def kind_of(fm):
    """report / open / ok / warn / bad, as on the site's seal (layouts/_partials/seal_kind.html)."""
    if fm.get("status") == "open":
        return "open"
    if fm.get("status") == "report" or not fm.get("verdict"):
        return "report"
    v = str(fm.get("verdict", "")).lower()
    return "ok" if v in ("delivered", "verified") else "bad" if v in ("not delivered", "escalated") else "warn"


def spoken(text):
    """What the voice reads: the same words, with abbreviations it might stumble on written out."""
    t = text.replace("ColdCaseTech", "Cold Case Tech")
    for a, b in MONTHS.items():
        t = re.sub(rf"\b{re.escape(a)}", b, t)
    return t


def plan(fm, today=None):
    """The scenes: what is said, what is shown. Returns dict or None when the article has no Reel script."""
    lines = [str(x).strip() for x in ((fm.get("social") or {}).get("reel") or []) if str(x).strip()][:3]
    if len(lines) < 2:
        return None
    k = kind_of(fm)
    today = today or datetime.now(timezone.utc).date()
    labels = {"report": ("THE NEWS", "THE DETAIL"), "open": ("PROMISED", "WHERE IT STANDS")}.get(k, ("PROMISED", "WHAT HAPPENED"))
    stamp, stamp_color, stamp_say, stamp_sub = None, BRASS, "", ""
    if k in ("ok", "warn", "bad"):
        v = str(fm["verdict"])
        stamp = v.upper().replace("PARTIALLY ", "PARTLY ")
        stamp_color = {"ok": OK, "warn": WARN, "bad": BAD}[k]
        stamp_say = f"Verdict: {v.lower().replace('partially', 'partly')}."
    elif k == "open":
        stamp = "OPEN CASE"
        due = str(fm.get("due") or "").strip()
        stamp_say = f"Due: {due}. We check on the day." if due else "We check on the day."
        try:
            days = (datetime.strptime(str(fm.get("due_by")), "%Y-%m-%d").date() - today).days
            stamp_sub = f"Due {due} · {days} day{'s' if days != 1 else ''} left" if days >= 0 else f"Was due {due}"
        except (TypeError, ValueError):
            stamp_sub = f"Due {due}" if due else ""
    tags = [t for t in (fm.get("tags") or []) if str(t).lower() != "tech"]
    field = str(tags[0]).upper() if tags else "TECH"
    kicker = f"{field} · " + {"report": "NEWS REPORT", "open": "OPEN CASE"}.get(k, "CASE FILE")
    return {"lines": lines, "labels": labels, "kind": k, "stamp": stamp, "stamp_color": stamp_color,
            "stamp_say": stamp_say, "stamp_sub": stamp_sub, "kicker": kicker, "title": str(fm.get("title", ""))}


# ------------------------------------------------------------------------------------------------ sound
def ensure_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for name, url in MODEL_FILES.items():
        p = os.path.join(MODEL_DIR, name)
        if not os.path.exists(p) or os.path.getsize(p) < 1_000_000:
            print(f"  reel: downloading the voice model ({name})")
            urllib.request.urlretrieve(url, p + ".part")
            os.replace(p + ".part", p)
    from kokoro_onnx import Kokoro
    return Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin"))


def narrate(kokoro, sentences):
    """One sentence after another with short pauses; returns (audio, sample rate, [(start, end)] per sentence)."""
    out, times, t, sr = [], [], 0.0, 24000
    for i, s in enumerate(sentences):
        a, sr = kokoro.create(spoken(s), voice=VOICE, speed=SPEED, lang="en-us")
        gap = np.zeros(int(sr * (0.35 if i == 0 else 0.25)), dtype=np.float32)
        seg = np.concatenate([gap, np.asarray(a, dtype=np.float32)])
        times.append((t + len(gap) / sr, t + len(seg) / sr))
        t += len(seg) / sr
        out.append(seg)
    audio = np.concatenate(out + [np.zeros(int(sr * 0.6), dtype=np.float32)])
    return audio, sr, times


def music(total, thud_at=None, sr=48000):
    """Slow minor chords on soft pads (made here, nobody else's recording), and a low thud for the stamp."""
    def note(f, dur):
        t = np.arange(int(sr * dur)) / sr
        w = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t + 0.3) + 0.12 * np.sin(2 * np.pi * 3 * f * t + 0.7)
        w *= 1 + 0.004 * np.sin(2 * np.pi * 0.25 * t)
        return w * np.clip(np.minimum(t / 1.2, (dur - t) / 1.5), 0, 1)
    chords = [[110, 164.81, 220, 261.63], [87.31, 130.81, 174.61, 220], [130.81, 196, 261.63, 329.63], [98, 146.83, 196, 246.94]]
    out = np.zeros(int(sr * (total + 1)))
    for i in range(int(total // 4) + 2):
        s = int(i * 4.0 * sr)
        if s >= len(out):
            break
        c = sum(note(f, 5.5) for f in chords[i % 4]) / 4
        e = min(len(out), s + len(c))
        out[s:e] += c[:e - s]
    # gentle low-pass (one-pole filter), done in blocks for speed
    a, y, acc = 0.05, np.empty_like(out), 0.0
    for i in range(len(out)):
        acc += a * (out[i] - acc)
        y[i] = acc
    out = y
    if thud_at is not None:
        t = np.arange(int(sr * 0.9)) / sr
        thud = np.sin(2 * np.pi * (55 + 40 * np.exp(-t * 12)) * t) * np.exp(-t * 5.5)
        s = int(thud_at * sr)
        out[s:s + len(thud)] += 1.6 * thud[:max(0, len(out) - s)]
    out = out[:int(sr * total)]
    fade = int(sr * 1.2)
    out[-fade:] *= np.linspace(1, 0, fade)
    return (0.9 * out / max(1e-9, np.max(np.abs(out)))).astype(np.float32), sr


# ------------------------------------------------------------------------------------------------ pictures
class Fonts:
    def __init__(self, tmp):
        from fontTools.ttLib import TTFont
        self.files = {}
        for f in glob.glob(os.path.join(ROOT, "static", "fonts", "*.woff2")):
            t = TTFont(f)
            t.flavor = None
            out = os.path.join(tmp, os.path.basename(f).replace(".woff2", ".ttf"))
            t.save(out)
            self.files[os.path.basename(out)] = out
        self.cache = {}

    def get(self, name, size):
        key = (name, size)
        if key not in self.cache:
            self.cache[key] = ImageFont.truetype(self.files[name], size)
        return self.cache[key]

    cas = lambda self, s: self.get("libre-caslon-display-latin-400-normal.ttf", s)
    ser = lambda self, s: self.get("source-serif-4-latin-400-normal.ttf", s)
    mono = lambda self, s: self.get("jetbrains-mono-latin-400-normal.ttf", s)
    monob = lambda self, s: self.get("jetbrains-mono-latin-700-normal.ttf", s)


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def back(x):
    x = clamp(x)
    return 1 + 2.9 * (x - 1) ** 3 + 1.9 * (x - 1) ** 2
def vis(t, a, b, d=0.35): return clamp((t - a) / d) * clamp((b - t) / d)


def wrap(text, font, width):
    lines, cur = [], ""
    for w in text.split():
        test = (cur + " " + w).strip()
        if font.getlength(test) <= width or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def fit(fonts, text, maker, sizes, max_lines):
    for s in sizes:
        f = maker(s)
        if len(wrap(text, f, X1 - X0)) <= max_lines:
            return f
    return maker(sizes[-1])


def draw_text(img, xy, s, font, fill, alpha=1.0, dy=0.0, anchor="la"):
    if alpha <= 0.01:
        return
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((xy[0], xy[1] + dy), s, font=font, fill=fill, anchor=anchor)
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(layer)


def draw_block(img, y, s, font, fill, t, start, end, gap=1.18):
    lh = int(font.size * gap)
    rows = wrap(s, font, X1 - X0)
    for i, row in enumerate(rows):
        k = ease((t - start - i * 0.12) / 0.45)
        draw_text(img, (X0, y + i * lh), row, font, fill, alpha=k * vis(t, start, end), dy=(1 - k) * 36)
    return y + len(rows) * lh


def make_stamp(fonts, label, color, size=440):
    s = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    d.ellipse((8, 8, size - 8, size - 8), outline=color, width=7)
    d.ellipse((34, 34, size - 34, size - 34), outline=color, width=3)
    f = fonts.monob(50)
    while f.getlength(label) > size - 110 and f.size > 26:
        f = fonts.monob(f.size - 2)
    d.text((size / 2, size / 2), label, font=f, fill=color, anchor="mm")
    return s.rotate(-8, resample=Image.BICUBIC, expand=True)


def renderer(fonts, p, times, total):
    """Returns frame(t) for this Reel. times: (start, end) of each spoken sentence, in order:
    the 2-3 lines, then the stamp sentence (if any), then the closing sentence."""
    n = len(p["lines"])
    starts = [a for a, _ in times]
    s_stamp = starts[n] if p["stamp_say"] else None
    s_end = starts[-1]
    f1 = fit(fonts, p["lines"][0], fonts.cas, (92, 84, 76, 68, 60), 4)
    f2 = fit(fonts, p["lines"][1], fonts.cas, (96, 88, 80, 72, 64), 4)
    f3 = fit(fonts, p["lines"][2], fonts.ser, (64, 58, 52, 46), 5) if n > 2 else None
    stamp = make_stamp(fonts, p["stamp"], p["stamp_color"]) if p["stamp"] else None
    label2_color = p["stamp_color"] if p["kind"] in ("ok", "warn", "bad") else BRASS
    after2 = starts[2] if n > 2 else (s_stamp or s_end)

    def frame(t):
        img = Image.new("RGBA", (W, H), PAPER)
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, int(W * clamp(t / total)), 9), fill=BRASS)   # progress bar
        cas52 = fonts.cas(52)
        draw_text(img, (X0, 214), "ColdCase", cas52, INK)
        draw_text(img, (X0 + cas52.getlength("ColdCase"), 214), "Tech", cas52, BRASS)
        draw_text(img, (X1, 236), "THE RECORD OF TECH PROMISES", fonts.mono(19), MUTED, anchor="ra")
        d.line((X0, 300, X1, 300), fill=BRASS, width=2)
        d.line((X0, 308, X1, 308), fill=BRASS, width=1)
        draw_text(img, (X0, 352), p["kicker"], fonts.mono(26), BRASS)
        # 1. the promise / the news
        e1 = starts[1] - 0.05
        draw_text(img, (X0, 640), p["labels"][0], fonts.monob(30), BRASS, alpha=vis(t, 0.15, e1))
        draw_block(img, 700, p["lines"][0], f1, INK, t, 0.3, e1)
        # 2. what happened / where it stands / the detail
        e2 = after2 - 0.05
        draw_text(img, (X0, 640), p["labels"][1], fonts.monob(30), label2_color, alpha=vis(t, starts[1], e2))
        draw_block(img, 700, p["lines"][1], f2, INK, t, starts[1] + 0.05, e2)
        # 3. the striking fact
        if n > 2:
            e3 = (s_stamp or s_end) - 0.05
            draw_text(img, (X0, 640), "ON THE RECORD", fonts.monob(30), MUTED, alpha=vis(t, starts[2], e3))
            draw_block(img, 700, p["lines"][2], f3, INK2, t, starts[2] + 0.05, e3, gap=1.32)
        # 4. the stamp
        if stamp is not None:
            a = s_stamp if s_stamp is not None else s_end - 1.6
            k = vis(t, a - 0.05, s_end - 0.05, d=0.2)
            if k > 0:
                draw_text(img, (W / 2, 640), "VERDICT" if p["kind"] in ("ok", "warn", "bad") else "STATUS",
                          fonts.monob(34), MUTED, alpha=k, anchor="ma")
                sc = 1.9 - 0.9 * back((t - a) / 0.42)
                st = stamp.resize((int(stamp.width * sc), int(stamp.height * sc)), Image.BICUBIC)
                st.putalpha(st.getchannel("A").point(lambda v: int(v * k)))
                img.alpha_composite(st, (int(W / 2 - st.width / 2), int(1020 - st.height / 2)))
                if p["stamp_sub"]:
                    draw_text(img, (W / 2, 1320), p["stamp_sub"], fonts.mono(30), INK2,
                              alpha=k * ease((t - a - 0.4) / 0.4), anchor="ma")
        # 5. where the receipts are
        y = draw_block(img, 760, "Every source, linked.", fonts.cas(100), INK, t, s_end, total + 1)
        draw_text(img, (X0, y + 60), "coldcasetech.com", fonts.monob(52), BRASS, alpha=ease((t - s_end - 0.4) / 0.4))
        draw_text(img, (X0, y + 140), "Link in bio", fonts.ser(44), INK2, alpha=ease((t - s_end - 0.6) / 0.4))
        draw_text(img, (X0, 1440), "Narration: AI voice", fonts.mono(24), MUTED, alpha=ease((t - s_end - 0.6) / 0.4))
        return img.convert("RGB")
    return frame


# ------------------------------------------------------------------------------------------------ one Reel
def make(path, kokoro, fonts, tmp, today=None):
    slug = os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(OUT_DIR, slug + ".mp4")
    if os.path.exists(out):
        print(f"  reel: {slug} already has a video")
        return out
    p = plan(read_article(path), today)
    if not p:
        print(f"  reel: {slug} has no Reel script; Instagram gets the picture instead")
        return ""
    sentences = p["lines"] + ([p["stamp_say"]] if p["stamp_say"] else []) + ["Every source is linked at ColdCaseTech."]
    t0 = time.time()
    voice, vsr, times = narrate(kokoro, sentences)
    total = len(voice) / vsr
    if total > 59:
        print(f"  reel: {slug} would run {total:.0f} s (over 59 s); skipped")
        return ""
    import soundfile as sf
    vpath, mpath, video = (os.path.join(tmp, f"{slug}.{x}") for x in ("voice.wav", "music.wav", "video.mp4"))
    sf.write(vpath, voice, vsr)
    m, msr = music(total, thud_at=times[len(p["lines"])][0] if p["stamp"] else None)
    sf.write(mpath, m, msr)
    frame = renderer(fonts, p, times, total)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                           "-pix_fmt", "yuv420p", video], stdin=subprocess.PIPE)
    for i in range(int(total * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg could not encode the frames")
    os.makedirs(OUT_DIR, exist_ok=True)
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", vpath, "-i", mpath, "-filter_complex",
                        "[1:a]aresample=48000[v];[2:a]volume=0.14[m];[v][m]amix=inputs=2:duration=longest:normalize=0,"
                        "loudnorm=I=-14:TP=-1.5:LRA=11[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "160k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg could not add the sound: " + r.stderr[-300:])
    print(f"  reel: made {os.path.relpath(out, ROOT)} ({total:.1f} s, {os.path.getsize(out) // 1024} KB, {time.time() - t0:.0f} s)")
    return out


def prune(today=None):
    """Remove videos older than KEEP_DAYS (by the date at the start of the file name). Instagram keeps its copy."""
    today = today or datetime.now(timezone.utc).date()
    for f in glob.glob(os.path.join(OUT_DIR, "*.mp4")):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-", os.path.basename(f))
        if m and datetime.strptime(m.group(1), "%Y-%m-%d").date() < today - timedelta(days=KEEP_DAYS):
            os.remove(f)
            print(f"  reel: removed {os.path.basename(f)} (older than {KEEP_DAYS} days)")


def missing_recent(days=2, today=None):
    """Articles from the last `days` days that have a Reel script but no video yet."""
    today = today or datetime.now(timezone.utc).date()
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "content", "posts", "*.md"))):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-", os.path.basename(f))
        if not m or datetime.strptime(m.group(1), "%Y-%m-%d").date() < today - timedelta(days=days):
            continue
        slug = os.path.splitext(os.path.basename(f))[0]
        if os.path.exists(os.path.join(OUT_DIR, slug + ".mp4")):
            continue
        try:
            if plan(read_article(f), today):
                out.append(os.path.relpath(f, ROOT))
        except Exception:
            continue
    return out


def main(args):
    recent = "--recent" in args
    paths = [p for p in args if p.endswith(".md") and os.path.exists(p)]
    if recent:
        for p in missing_recent():
            if p not in paths and os.path.join(ROOT, p) not in paths:
                paths.append(p)
    prune()
    if not paths:
        print("reel: no new articles")
        return 0
    kokoro = ensure_model()
    with tempfile.TemporaryDirectory() as tmp:
        fonts = Fonts(tmp)
        for p in paths:
            try:
                make(p, kokoro, fonts, tmp)
            except Exception as e:   # one Reel failing never stops the others, or the article
                print(f"  reel: {os.path.basename(p)} failed ({str(e)[:200]}); Instagram gets the picture instead")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
