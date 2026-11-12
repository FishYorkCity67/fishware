#!/usr/bin/env python3
"""FishWare-Grafikgenerator.

Zeichnet alle FishWare-Grafiken (1-Bit, Flipper-Display 128x64) per Code:
  - Fisch-Portraets fuer den Pass (6 Arten x 3 Stimmungen)
  - Aquarium-App-Sprites
  - Asset-Pack "FishWare": Ozean-Animationen, Level-up, Fisch statt Delfin
  - Pass-Hintergrund, Hauptmenue-Icon, Update-/Startbild

Aufruf:  python scripts/fishware/gen_gfx.py
Schwarz (0) = Pixel an, Weiss (1) = aus.
"""

import math
import os
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
ON = 0
OFF = 1
TAU = math.pi * 2

SPECIES = ["guppy", "clown", "puffer", "ray", "sword", "shark"]
MOODS = ["happy", "okay", "angry"]


def new(w, h):
    return Image.new("1", (w, h), OFF)


def save(img, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


# ---------------------------------------------------------------- Zeichenstift
class Pen:
    """Zeichnet in Fisch-Einheiten; flip spiegelt horizontal (Blickrichtung)."""

    def __init__(self, img, cx, cy, s=1.0, flip=False):
        self.img = img
        self.d = ImageDraw.Draw(img)
        self.cx, self.cy, self.s, self.flip = cx, cy, s, flip

    def clone(self, img):
        return Pen(img, self.cx, self.cy, self.s, self.flip)

    def p(self, x, y):
        if self.flip:
            x = -x
        return (round(self.cx + x * self.s), round(self.cy + y * self.s))

    def poly(self, pts, fill=None, outline=None):
        self.d.polygon([self.p(*q) for q in pts], fill=fill, outline=outline)

    def line(self, pts, fill=ON, width=1):
        self.d.line([self.p(*q) for q in pts], fill=fill, width=width)

    def ell(self, x0, y0, x1, y1, fill=None, outline=None):
        a, b = self.p(x0, y0), self.p(x1, y1)
        box = [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]
        self.d.ellipse(box, fill=fill, outline=outline)

    def dot(self, x, y, c=ON):
        put(self.img, *self.p(x, y), c)


def put(img, x, y, c=ON):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c)


def get(img, x, y):
    if 0 <= x < img.width and 0 <= y < img.height:
        return img.getpixel((x, y))
    return OFF


def checker(x, y):
    return (x + y) % 2 == 0


def sparse(x, y):
    return x % 2 == 0 and y % 2 == 0


def very_sparse(x, y):
    return x % 4 == 0 and (y % 4 == 0)


def shape_mask(pen, draw_fn):
    """Maske (L-Bild) einer Form, mit demselben Stift-Transform gezeichnet."""
    mask = Image.new("L", pen.img.size, 0)
    draw_fn(pen.clone(mask), 255)
    return mask


def fill_mask(img, mask, pattern=None, extra=None):
    """Fuellt die Maske: pattern(x,y)->bool setzt Pixel an, sonst aus."""
    px = mask.load()
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y] and (extra is None or extra(x, y)):
                img.putpixel((x, y), ON if (pattern and pattern(x, y)) else OFF)


def solid(pen, draw_fn, pattern=None):
    """Form weiss (oder gemustert) fuellen und schwarz umranden."""
    mask = shape_mask(pen, draw_fn)
    fill_mask(pen.img, mask, pattern)
    draw_fn(pen, None, outline=True)
    return mask


# ---------------------------------------------------------------- Gesicht
def face(pen, ex, ey, mx, my, mood, big=True):
    """Auge + Mund in Bildschirm-Pixeln (Richtung beruecksichtigt)."""
    img = pen.img
    sx = -1 if pen.flip else 1
    ex, ey = pen.p(ex, ey)
    mx, my = pen.p(mx, my)
    # Augenhoehle freiraeumen (sonst verschwindet das Auge im Muster)
    rad = 2 if big else 1
    for dx in range(-rad, rad + 1):
        for dy in range(-rad, rad + 1):
            if abs(dx) + abs(dy) <= rad + 1:
                put(img, ex + dx, ey + dy, OFF)
    if mood == "sleep":
        for i in (-1, 0, 1):
            put(img, ex + i, ey)
    elif mood == "happy":
        # geschlossenes, laechelndes Auge  ^
        put(img, ex - 1, ey + 1)
        put(img, ex, ey)
        put(img, ex + 1, ey + 1)
        if big:
            put(img, ex - 2, ey + 2)
            put(img, ex + 2, ey + 2)
    else:
        if big:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    put(img, ex + dx, ey + dy)
            put(img, ex + sx, ey - 1, OFF)  # Glanzpunkt
        else:
            put(img, ex, ey)
            put(img, ex + sx, ey)
        if mood == "angry":
            # Augenbraue, zur Schnauze hin abfallend
            for i in range(-2, 3):
                put(img, ex + sx * i, ey - (3 if big else 2) + (1 if i > 0 else 0) + (1 if i > 1 else 0))
    # Mund (an der Schnauze, nach hinten gerichtet)
    if mood == "happy":
        put(img, mx, my)
        put(img, mx - sx, my + 1)
        put(img, mx - 2 * sx, my + 1)
        put(img, mx - 3 * sx, my)
    elif mood == "angry":
        put(img, mx, my + 1)
        put(img, mx - sx, my)
        put(img, mx - 2 * sx, my)
        put(img, mx - 3 * sx, my + 1)
    elif mood == "sleep":
        put(img, mx, my)
        put(img, mx - sx, my)
    else:
        for i in range(0, 3):
            put(img, mx - i * sx, my)


# ---------------------------------------------------------------- Fischarten
# Alle Arten schauen nach rechts (+x). t = Animationsphase 0..1.
# Einheiten ~ Pixel bei s=1, Fisch ca. 40 Einheiten lang.


def wag(t, amp=2.0):
    return math.sin(t * TAU) * amp


def draw_guppy(pen, mood, t=0.0, big=True):
    w = wag(t, 2)

    def tail(p, fill, outline=False):
        pts = [(-7, 0), (-19, -9 + w), (-22, -3 + w), (-22, 3 + w), (-19, 9 + w)]
        p.poly(pts, fill=fill if not outline else None, outline=ON if outline else None)

    solid(pen, tail)
    for ty in (-6, 0, 6):
        pen.line([(-9, 0), (-20, ty + w)])

    def fin(p, fill, outline=False):
        p.poly([(-3, -5), (2, -10), (6, -5)], fill=fill if not outline else None,
               outline=ON if outline else None)

    solid(pen, fin)

    def body(p, fill, outline=False):
        p.ell(-10, -6, 11, 6, fill=fill if not outline else None, outline=ON if outline else None)

    solid(pen, body)
    if big:
        for x, y in ((-4, 1), (-1, 3), (1, 0), (-6, -2)):
            pen.dot(x, y)
    face(pen, 6, -1, 10, 2, mood, big)


def draw_clown(pen, mood, t=0.0, big=True):
    w = wag(t, 2)

    def tail(p, fill, outline=False):
        p.poly([(-12, 0), (-21, -8 + w), (-18, 0 + w), (-21, 8 + w)],
               fill=fill if not outline else None, outline=ON if outline else None)

    solid(pen, tail, sparse)

    def fin(p, fill, outline=False):
        p.poly([(-7, -8), (-1, -13), (6, -8)], fill=fill if not outline else None,
               outline=ON if outline else None)

    solid(pen, fin, sparse)

    def body(p, fill, outline=False):
        p.ell(-14, -9, 14, 9, fill=fill if not outline else None, outline=ON if outline else None)

    mask = solid(pen, body, sparse)
    # weisse Streifen mit dunklem Rand
    px = mask.load()
    for bx0, bx1 in ((-8, -4), (2, 6)):
        a = pen.p(bx0, 0)[0]
        b = pen.p(bx1, 0)[0]
        lo, hi = min(a, b), max(a, b)
        for y in range(pen.img.height):
            for x in range(lo, hi + 1):
                if 0 <= x < pen.img.width and px[x, y]:
                    edge = x in (lo, hi)
                    pen.img.putpixel((x, y), ON if edge else OFF)
    body(pen, None, outline=True)
    face(pen, 9, -2, 13, 2, mood, big)


def draw_puffer(pen, mood, t=0.0, big=True, puff=0.0):
    r = 11 + puff * 4
    w = wag(t, 1.5)

    def tail(p, fill, outline=False):
        p.poly([(-r + 1, 0), (-r - 6, -5 + w), (-r - 6, 5 + w)],
               fill=fill if not outline else None, outline=ON if outline else None)

    solid(pen, tail)
    # Stacheln
    n = 14
    for i in range(n):
        a = i / n * TAU + 0.2
        pen.line([(math.cos(a) * r, math.sin(a) * r),
                  (math.cos(a) * (r + 3 + puff), math.sin(a) * (r + 3 + puff))])

    def body(p, fill, outline=False):
        p.ell(-r, -r, r, r, fill=fill if not outline else None, outline=ON if outline else None)

    solid(pen, body)
    # Flecken auf dem Ruecken
    if big:
        for x, y in ((-6, -6), (-2, -8), (2, -6), (-7, -1), (-3, -3), (-9, -4)):
            pen.dot(x, y)
    # Bauch-Linie
    pen.line([(-r * 0.6, r * 0.45), (r * 0.5, r * 0.5)])

    def pect(p, fill, outline=False):
        p.ell(-2, 1, 4, 5, fill=fill if not outline else None, outline=ON if outline else None)

    solid(pen, pect)
    face(pen, r * 0.45, -3, r - 1, 2, mood, big)


def draw_ray(pen, mood, t=0.0, big=True):
    # Draufsicht: Fluegel schlagen, Schwanz schlaengelt
    f = math.sin(t * TAU) * 2.5
    pts_tail = [(-11 - i * 2, math.sin(t * TAU + i * 0.7) * (i * 0.25)) for i in range(9)]
    pen.line(pts_tail)

    def body(p, fill, outline=False):
        p.poly([(17, 0), (6, -9), (-2, -15 - f), (-6, -12 - f), (-12, 0),
                (-6, 12 + f), (-2, 15 + f), (6, 9)],
               fill=fill if not outline else None, outline=ON if outline else None)

    mask = solid(pen, body, sparse)
    # Mittelstreifen hell lassen
    px = mask.load()
    for y in range(pen.img.height):
        for x in range(pen.img.width):
            if px[x, y]:
                lx, ly = x - pen.cx, y - pen.cy
                if abs(ly) <= 3 * pen.s and abs(lx) <= 14 * pen.s:
                    pen.img.putpixel((x, y), OFF)
    body(pen, None, outline=True)
    # zwei Augen oben, Mund-Ausdruck vorne
    sx = -1 if pen.flip else 1
    for ey in (-3, 3):
        cx, cy = pen.p(9, ey)
        if mood == "happy":
            put(pen.img, cx - sx, cy)
            put(pen.img, cx, cy - (1 if ey < 0 else -1))
            put(pen.img, cx + sx, cy)
        else:
            put(pen.img, cx, cy)
            put(pen.img, cx + sx, cy)
            if mood == "angry":
                put(pen.img, cx - sx, cy - (2 if ey < 0 else -2))
                put(pen.img, cx, cy - (2 if ey < 0 else -2))
    mx, my = pen.p(14, 0)
    if mood == "happy":
        put(pen.img, mx, my - 1)
        put(pen.img, mx + sx, my)
        put(pen.img, mx, my + 1)
    elif mood == "angry":
        put(pen.img, mx + sx, my - 1)
        put(pen.img, mx, my)
        put(pen.img, mx + sx, my + 1)
    else:
        put(pen.img, mx, my - 1)
        put(pen.img, mx, my)
        put(pen.img, mx, my + 1)


def draw_sword(pen, mood, t=0.0, big=True):
    w = wag(t, 2)

    def tail(p, fill, outline=False):
        p.poly([(-13, 0), (-21, -9 + w), (-17, 0 + w), (-21, 9 + w)],
               fill=fill if not outline else None, outline=ON if outline else None)

    solid(pen, tail, checker)

    def sail(p, fill, outline=False):
        p.poly([(-9, -5), (-6, -15), (2, -14), (8, -5)], fill=fill if not outline else None,
               outline=ON if outline else None)

    solid(pen, sail, sparse)
    pen.line([(14, -1), (28, -2)])

    def body(p, fill, outline=False):
        p.ell(-15, -6, 15, 6, fill=fill if not outline else None, outline=ON if outline else None)

    mask = shape_mask(pen, body)
    top = pen.cy
    fill_mask(pen.img, mask, lambda x, y: checker(x, y) and y < top - 1)
    body(pen, None, outline=True)
    pen.line([(-12, 2), (10, 2)])
    face(pen, 9, -2, 14, 2, mood, big)


def draw_shark(pen, mood, t=0.0, big=True):
    w = wag(t, 2)

    def tail(p, fill, outline=False):
        p.poly([(-15, 0), (-24, -11 + w), (-20, 0 + w), (-23, 8 + w)],
               fill=fill if not outline else None, outline=ON if outline else None)

    solid(pen, tail, checker)

    def dorsal(p, fill, outline=False):
        p.poly([(-3, -7), (1, -17), (6, -7)], fill=fill if not outline else None,
               outline=ON if outline else None)

    solid(pen, dorsal, checker)

    def body(p, fill, outline=False):
        p.poly([(21, 1), (15, -5), (1, -8), (-12, -5), (-17, -2), (-17, 2), (-10, 5),
                (4, 7), (15, 5)], fill=fill if not outline else None,
               outline=ON if outline else None)

    mask = shape_mask(pen, body)
    top = pen.cy
    fill_mask(pen.img, mask, lambda x, y: checker(x, y) and y < top - 1)
    body(pen, None, outline=True)

    def pect(p, fill, outline=False):
        p.poly([(3, 5), (-2, 12), (8, 6)], fill=fill if not outline else None,
               outline=ON if outline else None)

    solid(pen, pect)
    for gx in (8, 10, 12):
        pen.line([(gx, -2), (gx - 1, 2)])
    face(pen, 14, -2, 19, 3, mood if mood != "happy" else "okay", big)
    # Grinsen mit Zaehnchen bei gut gelaunt
    if mood == "happy" and big:
        sx = -1 if pen.flip else 1
        mx, my = pen.p(19, 3)
        for i in range(0, 6):
            put(pen.img, mx - i * sx, my + (1 if i in (1, 4) else 0))


DRAW = {
    "guppy": draw_guppy,
    "clown": draw_clown,
    "puffer": draw_puffer,
    "ray": draw_ray,
    "sword": draw_sword,
    "shark": draw_shark,
}

PORTRAIT_SCALE = {"guppy": 1.0, "clown": 1.1, "puffer": 1.05, "ray": 1.0, "sword": 0.8, "shark": 0.85}
PORTRAIT_X = {"guppy": 24, "clown": 24, "puffer": 22, "ray": 25, "sword": 19, "shark": 22}


# ---------------------------------------------------------------- Umgebung
def bubble(img, x, y, r):
    d = ImageDraw.Draw(img)
    x, y = round(x), round(y)
    if r <= 0:
        put(img, x, y)
    elif r == 1:
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            put(img, x + dx, y + dy)
    else:
        d.ellipse([x - r, y - r, x + r, y + r], fill=OFF, outline=ON)
        put(img, x - r // 2, y - r // 2)


def bubbles(img, t, seeds, x_range=(0, 128), y_top=0, y_bottom=60):
    """Aufsteigende Blasen, nahtlos geloopt."""
    h = y_bottom - y_top
    for i, (x0, off, r, speed) in enumerate(seeds):
        prog = (t * speed + off) % 1.0
        y = y_bottom - prog * h
        x = x0 + math.sin(prog * TAU * 2 + i) * 1.5
        if x_range[0] <= x <= x_range[1]:
            bubble(img, x, y, r)


def sand(img, y0=58, phase=0.0):
    w = img.width
    for x in range(w):
        y = y0 + round(math.sin(x * 0.11 + phase) * 1.2 + math.sin(x * 0.037) * 1.0)
        put(img, x, y)
        for yy in range(y + 1, img.height):
            if (x * 7 + yy * 13) % 9 == 0:
                put(img, x, yy)


def seaweed(img, x, base, height, t, phase=0.0, amp=2.0):
    prev = None
    for i in range(height + 1):
        k = i / max(height, 1)
        sx = x + math.sin(t * TAU + phase + i * 0.35) * amp * k
        pt = (round(sx), base - i)
        if prev:
            ImageDraw.Draw(img).line([prev, pt], fill=ON)
        prev = pt
        if i % 4 == 2 and i < height:
            side = 1 if (i // 4) % 2 == 0 else -1
            put(img, pt[0] + side, pt[1] - 1)
            put(img, pt[0] + side * 2, pt[1] - 2)


def rock(img, x0, y0, x1, y1):
    d = ImageDraw.Draw(img)
    d.pieslice([x0, y0, x1, y1 + (y1 - y0)], 180, 360, fill=OFF, outline=ON)
    for y in range(y0 + 2, y1):
        for x in range(x0 + 2, x1 - 1):
            if sparse(x, y) and get(img, x, y) == OFF:
                # nur innerhalb des Bogens
                cx, rx = (x0 + x1) / 2, (x1 - x0) / 2
                ry = (y1 - y0)
                if ((x - cx) / rx) ** 2 + ((y - y1) / ry) ** 2 < 0.8:
                    put(img, x, y)


def surface(img, y, t, amp=1.0):
    for x in range(img.width):
        yy = y + round(math.sin(x * 0.2 + t * TAU) * amp)
        put(img, x, yy)
        if (x + int(t * 20)) % 11 == 0:
            put(img, x, yy + 2)


def tiny_fish(img, x, y, right=True):
    x, y = round(x), round(y)
    s = 1 if right else -1
    #  .##.      Koerper 4 breit, Gabelschwanz hinten
    # #####
    #  .##.
    for dx in (-1, 0, 1, 2):
        put(img, x + dx * s, y)
    for dx in (0, 1):
        put(img, x + dx * s, y - 1)
        put(img, x + dx * s, y + 1)
    put(img, x - 2 * s, y - 1)
    put(img, x - 2 * s, y + 1)


# ---------------------------------------------------------------- Schrift
FONT5 = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00000", "00100"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    " ": ["00000"] * 7,
}

FONT3 = {
    "F": ["111", "100", "110", "100", "100"],
    "I": ["111", "010", "010", "010", "111"],
    "S": ["011", "100", "010", "001", "110"],
    "H": ["101", "101", "111", "101", "101"],
    "W": ["101", "101", "101", "111", "101"],
    "A": ["010", "101", "111", "101", "101"],
    "R": ["110", "101", "110", "101", "101"],
    "E": ["111", "100", "110", "100", "111"],
    "<": ["001", "010", "100", "010", "001"],
    " ": ["000"] * 5,
}


def text(img, x, y, s, font=FONT5, scale=1, bold=False):
    for ch in s:
        g = font.get(ch.upper(), font[" "])
        for gy, row in enumerate(g):
            for gx, c in enumerate(row):
                if c == "1":
                    for sy in range(scale):
                        for sxx in range(scale + (1 if bold else 0)):
                            put(img, x + gx * scale + sxx, y + gy * scale + sy)
        x += (len(g[0]) + 1) * scale + (1 if bold else 0)
    return x


def text_width(s, font=FONT5, scale=1, bold=False):
    return sum((len(font.get(c.upper(), font[" "])[0]) + 1) * scale + (1 if bold else 0) for c in s) - scale


# ---------------------------------------------------------------- Ausgaben
def gen_portraits():
    out = ROOT / "assets/icons/FishWare"
    for sp in SPECIES:
        for mood in MOODS:
            img = new(46, 49)
            # kleine Blasen im Hintergrund
            for bx, by, r in ((5, 10, 2), (9, 4, 1), (40, 40, 1), (38, 8, 2)):
                bubble(img, bx, by, r)
            pen = Pen(img, PORTRAIT_X[sp], 26, PORTRAIT_SCALE[sp])
            if sp == "puffer":
                DRAW[sp](pen, mood, 0.0, True, puff=0.6 if mood == "angry" else 0.0)
            else:
                DRAW[sp](pen, mood, 0.0, True)
            save(img, out / f"fish_{sp}_{mood}_46x49.png")


def gen_aquarium_sprites():
    """Sprites fuer die Aquarium-App (in deren images-Ordner)."""
    out = ROOT / "applications/external/fish_aquarium/images"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    # Fische in Aquarium-Groesse, 2 Schwanzstellungen, beide Richtungen
    size = {"guppy": (30, 22), "clown": (34, 24), "puffer": (34, 32),
            "ray": (40, 34), "sword": (44, 26), "shark": (46, 30)}
    scale = {"guppy": 0.6, "clown": 0.65, "puffer": 0.7, "ray": 0.6, "sword": 0.6, "shark": 0.6}
    for sp in SPECIES:
        w, h = size[sp]
        for mood in ("happy", "okay", "angry", "sleep"):
            for fr in range(2):
                for flip in (False, True):
                    img = new(w, h)
                    pen = Pen(img, w // 2, h // 2 + (1 if sp in ("sword", "shark") else 0),
                              scale[sp], flip)
                    m = mood
                    if sp == "puffer":
                        DRAW[sp](pen, m, fr * 0.25, False, puff=0.5 if mood == "angry" else 0.0)
                    else:
                        DRAW[sp](pen, m, fr * 0.25, False)
                    d = "l" if flip else "r"
                    save(img, out / f"{sp}_{mood}_{d}{fr}_{w}x{h}.png")
    # Futter-Flocke, Pflanze
    img = new(3, 3)
    put(img, 1, 0)
    put(img, 0, 1)
    put(img, 2, 1)
    put(img, 1, 2)
    save(img, out / "food_3x3.png")


def write_meta(folder, n_passive, n_active, fps, bubbles_list, cycles=2, cooldown=5):
    order = " ".join(str(i) for i in range(n_passive + n_active))
    lines = [
        "Filetype: Flipper Animation",
        "Version: 1",
        "",
        "Width: 128",
        "Height: 64",
        f"Passive frames: {n_passive}",
        f"Active frames: {n_active}",
        f"Frames order: {order}",
        f"Active cycles: {cycles}",
        f"Frame rate: {fps}",
        "Duration: 3600",
        f"Active cooldown: {cooldown}",
        "",
        f"Bubble slots: {len(bubbles_list)}",
    ]
    end = n_passive + n_active * cycles - 1
    for i, (x, y, txt, ah, av) in enumerate(bubbles_list):
        lines += [
            "",
            f"Slot: {i}",
            f"X: {x}",
            f"Y: {y}",
            f"Text: {txt}",
            f"AlignH: {ah}",
            f"AlignV: {av}",
            f"StartFrame: {n_passive + 1}",
            f"EndFrame: {end}",
        ]
    (folder / "meta.txt").write_text("\n".join(lines) + "\n", newline="\n")


BUBBLE_SEEDS = [(10, 0.0, 1, 1), (18, 0.5, 2, 1), (100, 0.25, 1, 1), (112, 0.7, 2, 1),
                (60, 0.4, 0, 2), (76, 0.85, 1, 1)]


def reef_bg(img, t, weeds=((8, 22), (16, 15), (114, 24), (121, 14))):
    sand(img, 58)
    for i, (x, h) in enumerate(weeds):
        seaweed(img, x, 58, h, t, phase=i * 1.3)
    bubbles(img, t, BUBBLE_SEEDS, y_bottom=56)


def pet_anim(name, sp, n_passive=16, n_active=6, fps=4, texts=(), scale=0.75):
    folder = ROOT / f"assets/packs/FishWare/Anims/{name}"
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    frames = []
    for f in range(n_passive):
        t = f / n_passive
        img = new(128, 64)
        reef_bg(img, t)
        x = 64 + math.sin(t * TAU) * 34
        y = 34 + math.sin(t * TAU * 2) * 3
        right = math.cos(t * TAU) > 0
        pen = Pen(img, x, y, scale, not right)
        if sp == "puffer":
            DRAW[sp](pen, "happy", t * 4, scale > 0.6)
        else:
            DRAW[sp](pen, "happy", t * 4, scale > 0.6)
        frames.append(img)
    for f in range(n_active):
        t = f / n_active
        img = new(128, 64)
        reef_bg(img, t)
        pen = Pen(img, 40, 38, scale, False)
        DRAW[sp](pen, "happy", t, scale > 0.6)
        # Blasen aus dem Maul
        for k in range(3):
            prog = (t + k / 3) % 1.0
            bubble(img, 58 + k * 2 + prog * 4, 34 - prog * 20, 1 if k != 1 else 2)
        frames.append(img)
    for i, im in enumerate(frames):
        save(im, folder / f"frame_{i}.png")
    write_meta(folder, n_passive, n_active, fps,
               [(66, 26, txt, "Left", "Bottom") for txt in texts])


def scene_anim(name, n, fps, draw_fn, n_active=0, active_fn=None, texts=(), bubble_pos=(66, 26)):
    folder = ROOT / f"assets/packs/FishWare/Anims/{name}"
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    frames = []
    for f in range(n):
        img = new(128, 64)
        draw_fn(img, f / n)
        frames.append(img)
    for f in range(n_active):
        img = new(128, 64)
        (active_fn or draw_fn)(img, f / max(n_active, 1))
        frames.append(img)
    for i, im in enumerate(frames):
        save(im, folder / f"frame_{i}.png")
    write_meta(folder, n, n_active, fps,
               [(bubble_pos[0], bubble_pos[1], txt, "Left", "Bottom") for txt in texts])


def draw_treasure(img, t, open_lid=None):
    sand(img, 58)
    seaweed(img, 10, 58, 20, t, 0.3)
    seaweed(img, 120, 58, 16, t, 1.7)
    d = ImageDraw.Draw(img)
    # Truhe
    x0, y0 = 70, 44
    d.rectangle([x0, y0, x0 + 26, y0 + 13], fill=OFF, outline=ON)
    d.line([x0, y0 + 4, x0 + 26, y0 + 4], fill=ON)
    for xx in (x0 + 6, x0 + 20):
        d.line([xx, y0, xx, y0 + 13], fill=ON)
    d.rectangle([x0 + 11, y0 + 3, x0 + 15, y0 + 7], fill=OFF, outline=ON)
    lid = open_lid if open_lid is not None else max(0.0, math.sin(t * TAU))
    lift = round(lid * 6)
    d.chord([x0, y0 - 8 - lift, x0 + 26, y0 + 2 - lift], 180, 360, fill=OFF, outline=ON)
    d.line([x0, y0 - 3 - lift, x0 + 26, y0 - 3 - lift], fill=ON)
    if lift > 2:
        # Muenzen funkeln
        for i, (cx, cy) in enumerate(((x0 + 8, y0 - 1), (x0 + 15, y0 - 2), (x0 + 21, y0))):
            if (i + int(t * 8)) % 2 == 0:
                put(img, cx, cy - 2)
                put(img, cx, cy + 2)
                put(img, cx - 2, cy)
                put(img, cx + 2, cy)
            put(img, cx, cy)
        seeds = [(x0 + 10, 0.1, 1, 1), (x0 + 16, 0.6, 2, 1), (x0 + 13, 0.35, 0, 1)]
        bubbles(img, t, seeds, y_bottom=y0 - 4)
    # Fischschwarm im Hintergrund
    for i in range(5):
        fx = (20 + i * 9 + t * 128) % 140 - 6
        tiny_fish(img, fx, 14 + (i % 3) * 5 + math.sin(t * TAU + i) * 1.5, True)


def draw_school(img, t):
    reef_bg(img, t, weeds=((6, 18), (122, 20)))
    cx, cy = 64 + math.sin(t * TAU) * 20, 30
    for i in range(12):
        a = t * TAU + i / 12 * TAU
        r = 14 + (i % 3) * 3
        x = cx + math.cos(a) * r * 1.4
        y = cy + math.sin(a) * r * 0.6
        tiny_fish(img, x, y, right=math.sin(a) < 0)


def jelly(img, x, y, t):
    d = ImageDraw.Draw(img)
    squash = math.sin(t * TAU)
    w = 9 + squash * 1.5
    h = 7 - squash * 1.5
    d.chord([x - w, y - h, x + w, y + h], 180, 360, fill=OFF, outline=ON)
    d.line([x - w, y, x + w, y], fill=ON)
    for x2 in (x - 3, x + 3):
        put(img, round(x2), round(y - h / 2))
    for k in range(-2, 3):
        prev = None
        for i in range(10):
            px = x + k * 3 + math.sin(t * TAU + i * 0.6 + k) * 1.2
            py = y + 1 + i * 1.3
            pt = (round(px), round(py))
            if prev:
                d.line([prev, pt], fill=ON)
            prev = pt


def draw_jelly(img, t):
    sand(img, 58)
    seaweed(img, 10, 58, 18, t, 0.5)
    seaweed(img, 118, 58, 22, t, 2.0)
    jelly(img, 46, 22 + math.sin(t * TAU) * 6, t)
    jelly(img, 84, 30 + math.sin(t * TAU + 2) * 5, (t + 0.4) % 1)
    bubbles(img, t, BUBBLE_SEEDS[:3], y_bottom=56)


def crab(img, x, y, t, mood="happy"):
    d = ImageDraw.Draw(img)
    x, y = round(x), round(y)
    d.ellipse([x - 8, y - 5, x + 8, y + 3], fill=OFF, outline=ON)
    for i in range(-6, 7, 3):
        put(img, x + i, y - 2)
    # Augen auf Stielen
    for ex in (-3, 3):
        d.line([x + ex, y - 5, x + ex, y - 8], fill=ON)
        put(img, x + ex - 1, y - 9)
        put(img, x + ex, y - 9)
        put(img, x + ex - 1, y - 8)
    snap = int(t * 8) % 2
    for side in (-1, 1):
        cx = x + side * 11
        d.line([x + side * 7, y - 2, cx, y - 6], fill=ON)
        d.ellipse([cx - 2, y - 10, cx + 2, y - 6], fill=OFF, outline=ON)
        if snap:
            put(img, cx, y - 10, OFF)
            put(img, cx, y - 9)
        # Beine
        for k in range(3):
            lx = x + side * (3 + k * 2)
            ly = y + 2
            off = 1 if (k + int(t * 8)) % 2 else 0
            d.line([lx, ly, lx + side * 3, ly + 3 + off], fill=ON)
    # Mund
    if mood == "happy":
        put(img, x - 1, y)
        put(img, x, y + 1)
        put(img, x + 1, y)


def draw_crab(img, t):
    sand(img, 58)
    seaweed(img, 120, 58, 22, t, 1.0)
    seaweed(img, 113, 58, 14, t, 2.0)
    rock(img, 2, 46, 26, 58)
    crab(img, 64 + math.sin(t * TAU) * 30, 53, t)
    bubbles(img, t, BUBBLE_SEEDS[2:5], y_bottom=50)


def draw_surface(img, t):
    d = ImageDraw.Draw(img)
    # Sonne
    d.ellipse([104, 2, 116, 14], fill=OFF, outline=ON)
    for k in range(8):
        a = k / 8 * TAU + t * TAU / 8
        put(img, round(110 + math.cos(a) * 9), round(8 + math.sin(a) * 9))
    # Wolke
    for cx, cy, r in ((20, 8, 4), (26, 6, 5), (32, 8, 4)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=OFF, outline=ON)
    d.rectangle([17, 8, 35, 12], fill=OFF)
    d.line([16, 12, 36, 12], fill=ON)
    # Wasser
    surface(img, 22, t, 1.5)
    # Boot
    bx = 60 + math.sin(t * TAU) * 3
    by = 20 + math.sin(t * TAU * 2) * 1
    d.polygon([(bx - 12, by - 4), (bx + 12, by - 4), (bx + 8, by + 1), (bx - 8, by + 1)],
              fill=OFF, outline=ON)
    d.line([bx, by - 4, bx, by - 18], fill=ON)
    d.polygon([(bx + 1, by - 17), (bx + 10, by - 6), (bx + 1, by - 6)], fill=OFF, outline=ON)
    # unter Wasser: Fisch + Blasen
    for i in range(3):
        fx = (t * 128 + i * 45) % 140 - 6
        tiny_fish(img, fx, 40 + i * 6, True)
    sand(img, 59)
    bubbles(img, t, BUBBLE_SEEDS[:4], y_top=26, y_bottom=56)


def draw_storm(img, t):
    d = ImageDraw.Draw(img)
    # Regen
    for i in range(24):
        x = (i * 23 + int(t * 60)) % 140 - 6
        y = (i * 17 + int(t * 64 * 2)) % 24
        d.line([x, y, x - 2, y + 4], fill=ON)
    # Blitz im letzten Viertel
    if 0.75 <= t < 0.82:
        d.line([(30, 0), (26, 8), (31, 8), (25, 18)], fill=ON, width=1)
    # rauer Wellengang
    for x in range(128):
        y = 24 + round(math.sin(x * 0.3 + t * TAU) * 2 + math.sin(x * 0.11 - t * TAU) * 1.5)
        put(img, x, y)
        put(img, x, y + 1)
        for yy in range(y + 2, 64):
            if (x + yy) % 2 == 0 and yy < 58:
                put(img, x, yy)
    sand(img, 58)


def draw_puff_angry(img, t, fish_sp="puffer"):
    reef_bg(img, t)
    puff = (math.sin(t * TAU) + 1) / 2
    pen = Pen(img, 44, 34, 0.9, False)
    draw_puffer(pen, "angry", t * 2, True, puff=puff * 0.8)


def gen_pack():
    root = ROOT / "assets/packs/FishWare"
    if (root / "Anims").exists():
        shutil.rmtree(root / "Anims")
    (root / "Anims").mkdir(parents=True)

    pet_anim("FW_Guppy_128x64", "guppy", scale=0.8,
             texts=("Blub!", "I'm small,\nbut fast!"))
    pet_anim("FW_Clown_128x64", "clown", scale=0.75,
             texts=("Blub blub!", "Stripes are\nin fashion"))
    pet_anim("FW_Puffer_128x64", "puffer", scale=0.7,
             texts=("Don't poke\nme, okay?", "Blub!"))
    pet_anim("FW_Ray_128x64", "ray", scale=0.8,
             texts=("I glide,\nI don't swim", "Blub..."))
    pet_anim("FW_Sword_128x64", "sword", scale=0.7,
             texts=("En garde!", "Fastest fish\nin the sea"))
    pet_anim("FW_Shark_128x64", "shark", scale=0.7,
             texts=("Sharp teeth,\nsoft heart", "Blub. Hi!"))

    scene_anim("FW_Treasure_128x64", 16, 4, draw_treasure,
               n_active=4, active_fn=lambda im, t: draw_treasure(im, t, 1.0),
               texts=("Treasure!",), bubble_pos=(40, 30))
    scene_anim("FW_School_128x64", 16, 4, draw_school)
    scene_anim("FW_Jelly_128x64", 12, 3, draw_jelly)
    scene_anim("FW_Crab_128x64", 16, 4, draw_crab, n_active=4,
               active_fn=lambda im, t: draw_crab(im, 0.25 + t * 0.05),
               texts=("Snip snap!",), bubble_pos=(30, 30))
    scene_anim("FW_Surface_128x64", 16, 3, draw_surface)
    scene_anim("FW_Storm_128x64", 12, 4, draw_storm)
    scene_anim("FW_Grumpy_128x64", 12, 3, draw_puff_angry, n_active=4,
               active_fn=lambda im, t: draw_puff_angry(im, 0.25),
               texts=("Grr!\nFeed me!", "Hmpf."), bubble_pos=(66, 22))

    # (Name, min_bh, max_bh, min_lvl, max_lvl, weight)
    manifest = [
        ("FW_Guppy_128x64", 0, 9, 1, 4, 6),
        ("FW_Clown_128x64", 0, 9, 5, 9, 6),
        ("FW_Puffer_128x64", 0, 9, 10, 14, 6),
        ("FW_Ray_128x64", 0, 9, 15, 19, 6),
        ("FW_Sword_128x64", 0, 9, 20, 24, 6),
        ("FW_Shark_128x64", 0, 9, 25, 30, 6),
        ("FW_Treasure_128x64", 0, 9, 1, 30, 3),
        ("FW_School_128x64", 0, 12, 1, 30, 3),
        ("FW_Jelly_128x64", 0, 14, 1, 30, 3),
        ("FW_Crab_128x64", 0, 9, 1, 30, 3),
        ("FW_Surface_128x64", 0, 9, 1, 30, 3),
        ("FW_Storm_128x64", 10, 14, 1, 30, 4),
        ("FW_Grumpy_128x64", 8, 14, 1, 30, 5),
    ]
    lines = ["Filetype: Flipper Animation Manifest", "Version: 1"]
    for name, b0, b1, l0, l1, w in manifest:
        lines += ["", f"Name: {name}", f"Min butthurt: {b0}", f"Max butthurt: {b1}",
                  f"Min level: {l0}", f"Max level: {l1}", f"Weight: {w}"]
    (root / "Anims/manifest.txt").write_text("\n".join(lines) + "\n", newline="\n")

    gen_pack_icons(root / "Icons")


def mascot(img, x, y, s=1.0, mood="happy", flip=False, t=0.0):
    draw_clown(Pen(img, x, y, s, flip), mood, t, True)


def check_mark(img, x, y):
    d = ImageDraw.Draw(img)
    d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=OFF, outline=ON)
    d.line([x - 4, y, x - 1, y + 3, x + 4, y - 3], fill=ON, width=2)


def gen_pack_icons(icons):
    if icons.exists():
        shutil.rmtree(icons)
    # Delfin-Bilder -> Fisch (gleiche Namen und Groessen)
    img = new(80, 58)
    mascot(img, 32, 32, 1.4)
    check_mark(img, 68, 12)
    save(img, icons / "Dolphin/DolphinDone_80x58.png")

    img = new(91, 55)
    mascot(img, 34, 30, 1.4)
    check_mark(img, 76, 12)
    for sx, sy in ((62, 4), (86, 26), (66, 24)):
        put(img, sx, sy)
        put(img, sx - 1, sy)
        put(img, sx + 1, sy)
        put(img, sx, sy - 1)
        put(img, sx, sy + 1)
    save(img, icons / "Dolphin/DolphinSuccess_91x55.png")

    img = new(92, 58)
    mascot(img, 34, 32, 1.4)
    d = ImageDraw.Draw(img)
    d.rectangle([66, 4, 86, 24], fill=OFF, outline=ON)
    d.rectangle([70, 4, 82, 11], fill=OFF, outline=ON)
    d.rectangle([69, 15, 83, 24], fill=OFF, outline=ON)
    d.line([79, 6, 79, 9], fill=ON)
    save(img, icons / "Dolphin/DolphinSaved_92x58.png")

    img = new(59, 63)
    mascot(img, 28, 40, 1.3, "happy")
    for bx, by, r in ((44, 18, 2), (48, 8, 3), (40, 4, 1)):
        bubble(img, bx, by, r)
    save(img, icons / "Dolphin/DolphinReadingSuccess_59x63.png")

    img = new(59, 54)
    mascot(img, 28, 34, 1.3, "okay")
    d = ImageDraw.Draw(img)
    # Sanduhr
    d.polygon([(44, 2), (56, 2), (50, 9)], fill=OFF, outline=ON)
    d.polygon([(44, 16), (56, 16), (50, 9)], fill=OFF, outline=ON)
    d.line([49, 14, 51, 14], fill=ON)
    save(img, icons / "Dolphin/DolphinWait_59x54.png")

    for name, flip in (("WarningDolphin_45x42", False), ("WarningDolphinFlip_45x42", True)):
        img = new(45, 42)
        mascot(img, 22 + (4 if flip else -4), 28, 0.9, "okay", flip)
        d = ImageDraw.Draw(img)
        ex = 6 if flip else 38
        d.rectangle([ex - 1, 2, ex + 1, 10], fill=ON)
        d.rectangle([ex - 1, 13, ex + 1, 15], fill=ON)
        save(img, icons / f"Dolphin/{name}.png")

    # Level-up: Fisch waechst, Funkeln
    lv = icons / "Animations/Levelup_128x64"
    lv.mkdir(parents=True, exist_ok=True)
    for f in range(11):
        img = new(128, 64)
        k = f / 10
        sand(img, 58)
        s = 0.6 + 0.8 * min(1.0, k * 1.4)
        mascot(img, 64, 32, s, "happy", False, f / 4)
        for i in range(8):
            a = i / 8 * TAU + k * 2
            r = 22 + k * 18
            x, y = 64 + math.cos(a) * r * 1.5, 32 + math.sin(a) * r * 0.8
            if (i + f) % 2 == 0 and not (f >= 6 and y < 12):
                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(img, round(x) + dx, round(y) + dy)
        if f >= 6:
            wtxt = "LEVEL UP!"
            text(img, 64 - text_width(wtxt) // 2, 2, wtxt)
        save(img, lv / f"frame_{f:02d}.png")
    (lv / "frame_rate").write_text("2", newline="\n")


def gen_passport_bg():
    path = ROOT / "assets/icons/Passport/passport_128x64.png"
    git_src = ROOT / "scripts/fishware/passport_orig.png"
    if not git_src.exists():
        shutil.copy(path, git_src)
    img = Image.open(git_src).convert("1")
    d = ImageDraw.Draw(img)
    d.rectangle([12, 53, 56, 59], fill=OFF)
    x = text(img, 14, 54, "FISHWARE", FONT3)
    # kleiner Fisch
    tiny_fish(img, x + 3, 56, True)
    save(img, path)


def gen_menu_icon():
    out = ROOT / "assets/icons/MainMenu/FishWare_14"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    n = 8
    for f in range(n):
        t = f / n
        img = new(14, 14)
        pen = Pen(img, 7 + math.sin(t * TAU) * 1, 8, 0.32, False)
        d = pen
        w = math.sin(t * TAU) * 1.2
        d.poly([(-6, 0), (-19, -8 + w * 3), (-19, 8 + w * 3)], fill=ON)
        d.ell(-11, -9, 14, 9, fill=OFF, outline=ON)
        put(img, *pen.p(7, -2))
        # Blase
        by = 5 - (f % 4)
        put(img, 12, by)
        save(img, out / f"frame_{f + 1:02d}.png")
    (out / "frame_rate").write_text("3", newline="\n")

    # Aquarium-App (FAP-Icon 10x10): kleines Becken mit Fisch
    old = ROOT / "assets/icons/MainMenu/Aquarium_14"
    if old.exists():
        shutil.rmtree(old)
    img = new(10, 10)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1, 9, 9], outline=ON)
    put(img, 0, 1, OFF)
    put(img, 9, 1, OFF)
    for x in range(1, 9):
        put(img, x, 3 + (1 if x % 4 < 2 else 0))
    tiny_fish(img, 4, 6, True)
    put(img, 8, 6)
    save(img, ROOT / "applications/external/fish_aquarium/aquarium_10px.png")


def gen_boot_logo():
    """Logo beim Hochfahren / Updaten (62x15)."""
    img = new(62, 15)
    w = text_width("FISHWARE", FONT5, 1, bold=True)
    text(img, (62 - w) // 2, 1, "FISHWARE", FONT5, 1, bold=True)
    for x in range(2, 60):
        put(img, x, 11 + round(math.sin(x * 0.6)))
    save(img, ROOT / "assets/icons/Update/Updating_Logo_62x15.png")


def logo(img, y=6):
    w = text_width("FISHWARE", FONT5, 2, bold=True)
    x = (128 - w) // 2
    text(img, x, y, "FISHWARE", FONT5, 2, bold=True)
    # Wellenlinie unter dem Logo
    for xx in range(x, x + w):
        put(img, xx, y + 17 + round(math.sin(xx * 0.5)))


def gen_slides():
    # Nach dem Update
    img = new(128, 64)
    logo(img, 4)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([18, 40, 36, 52], 2, fill=OFF, outline=ON)
    text(img, 21, 43, "OK", FONT5)
    text(img, 44, 43, "UPDATED", FONT5)
    pen = Pen(img, 112, 47, 0.45, False)
    draw_clown(pen, "happy", 0, False)
    save(img, ROOT / "assets/slideshow/update_default/frame_00.png")

    # Erster Start: Titelbild
    img = new(128, 64)
    logo(img, 4)
    sand(img, 58)
    seaweed(img, 8, 58, 16, 0.2)
    seaweed(img, 120, 58, 18, 0.6)
    mascot(img, 64, 42, 0.6, "happy")
    bubble(img, 80, 34, 2)
    bubble(img, 84, 28, 1)
    save(img, ROOT / "assets/slideshow/firstboot/frame_00.png")


def preview_sheet():
    """Uebersicht aller Portraets + je ein Animationsbild (nur zur Kontrolle)."""
    portraits = ROOT / "assets/icons/FishWare"
    sheet = Image.new("1", (46 * 6 + 7, 49 * 3 + 4), OFF)
    for i, sp in enumerate(SPECIES):
        for j, mood in enumerate(MOODS):
            im = Image.open(portraits / f"fish_{sp}_{mood}_46x49.png")
            sheet.paste(im, (1 + i * 47, 1 + j * 50))
    out = ROOT / "build/fishware_preview"
    out.mkdir(parents=True, exist_ok=True)
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(out / "portraits.png")
    anims = sorted((ROOT / "assets/packs/FishWare/Anims").glob("FW_*"))
    cols = 3
    rows = (len(anims) + cols - 1) // cols
    sheet = Image.new("1", (cols * 130, rows * 66), ON)
    for k, a in enumerate(anims):
        im = Image.open(a / "frame_3.png")
        sheet.paste(im, ((k % cols) * 130 + 1, (k // cols) * 66 + 1))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(out / "anims.png")
    extras = [ROOT / "assets/slideshow/update_default/frame_00.png",
              ROOT / "assets/slideshow/firstboot/frame_00.png",
              ROOT / "assets/icons/Passport/passport_128x64.png",
              ROOT / "assets/packs/FishWare/Icons/Animations/Levelup_128x64/frame_08.png"]
    sheet = Image.new("1", (2 * 130, 2 * 66), ON)
    for k, p in enumerate(extras):
        sheet.paste(Image.open(p).convert("1"), ((k % 2) * 130 + 1, (k // 2) * 66 + 1))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(out / "extras.png")
    sheet = Image.new("1", (100 * 4, 64 * 2), OFF)
    for k, p in enumerate(sorted((ROOT / "assets/packs/FishWare/Icons/Dolphin").glob("*.png"))):
        sheet.paste(Image.open(p).convert("1"), ((k % 4) * 100, (k // 4) * 64))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(out / "icons.png")


if __name__ == "__main__":
    gen_portraits()
    gen_aquarium_sprites()
    gen_pack()
    gen_passport_bg()
    gen_menu_icon()
    gen_boot_logo()
    gen_slides()
    preview_sheet()
    print("FishWare-Grafiken erzeugt.")
