"""Generate assets/gyro-codeart.png: code-art portrait + terminal profile card.

Usage:
    uv run --with pillow python assets/make_codeart.py <source.png> assets/gyro-codeart.png

The source image is not versioned. Fonts: DejaVu Sans Mono (fonts-dejavu-core on Debian/Ubuntu).
"""
import colorsys
import random
import sys

from PIL import Image, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
random.seed(7)

# palette
BG = (11, 15, 20)
BORDER = (31, 42, 55)
EMERALD = (52, 211, 153)
GOLD = (245, 185, 66)
CYAN = (103, 232, 249)
PURPLE = (159, 143, 224)
WHITE = (230, 237, 243)
DIM = (110, 122, 135)
RAIN = (26, 74, 58)

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
f_art = ImageFont.truetype(MONO, 10)
f_art_b = ImageFont.truetype(MONO_B, 10)
f_ui = ImageFont.truetype(MONO, 22)
f_ui_b = ImageFont.truetype(MONO_B, 22)
f_small = ImageFont.truetype(MONO, 18)

W, H = 1600, 790
card = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(card)
d.rounded_rectangle([8, 8, W - 9, H - 9], radius=18, outline=BORDER, width=2)

# ---- top bar -------------------------------------------------------------
x = 56
for txt, col, font in [("santiago@spin", EMERALD, f_ui_b), (":", DIM, f_ui), ("~", CYAN, f_ui_b),
                       ("$ ", DIM, f_ui), ("cat profile.ansi", WHITE, f_ui)]:
    d.text((x, 40), txt, font=font, fill=col)
    x += d.textlength(txt, font=font)
right = "palette: emerald / gold / cyan"
d.text((W - 56 - d.textlength(right, font=f_small), 44), right, font=f_small, fill=DIM)
d.line([56, 90, W - 56, 90], fill=BORDER, width=2)

# ---- code-art portrait ---------------------------------------------------
CODE = (
    "def spin(x): return x @ W.T + b  agents = [Planner(), Retriever(), Critic()]  "
    "for chunk in stream: yield asr(chunk)  q = embed(chunk)  hits = index.search(q, k=8)  "
    "assert quote in transcript  ctx = rerank(hits)  out = llm(prompt_v1, ctx)  "
    "if not valid(out): retry(backoff=2**n)  loss.backward()  opt.step()  "
    "async with session.begin(): await commit(run)  softmax(z) = exp(z) / sum(exp(z))  "
    "λ ∇ Σ ⊕ → ∞  while golden_ratio: rotate(ball, φ=1.618)  "
)
ART_X, ART_Y, CW, CH = 56, 112, 6, 11
COLS, ROWS = 106, 54
src = Image.open(SRC).convert("RGB")
crop = src.crop((205, 0, 205 + 600, 562))            # face + hat + steel ball
from PIL import ImageOps, ImageEnhance
small = ImageEnhance.Contrast(ImageOps.autocontrast(crop, cutoff=1)).enhance(1.25).resize((COLS, ROWS), Image.LANCZOS)
px = small.load()

LIPS = (0.42, 0.73, 0.10, 0.06)                        # (cx, cy, rx, ry) in crop fractions


def mix(c, f):
    return tuple(int(BG[i] + (c[i] - BG[i]) * max(0.0, min(1.0, f))) for i in range(3))


k = 0
tints, glyphs = [], []
for r in range(ROWS):
    for c in range(COLS):
        ch = CODE[k % len(CODE)]
        k += 1
        R, G, B = (v / 255 for v in px[c, r])
        h, s, v = colorsys.rgb_to_hsv(R, G, B)
        hd = h * 360
        xf, yf = c / COLS, r / ROWS
        in_lips = ((xf - LIPS[0]) / LIPS[2]) ** 2 + ((yf - LIPS[1]) / LIPS[3]) ** 2 < 1
        green = 65 < hd < 170 and s > 0.18

        if green and not in_lips:                     # background: sparse rain
            if random.random() < 0.10:
                col, bold = RAIN, False
            else:
                continue
        elif v < 0.24:                                # ink lines stay black
            continue
        else:
            if in_lips and green:
                base = EMERALD
            elif 230 < hd < 320 and s > 0.2:
                base = PURPLE
            elif 150 <= hd <= 200 and s > 0.25:
                base = EMERALD
            elif (hd < 45 or hd > 340) and s > 0.22:
                base = GOLD
            elif v > 0.82:
                base = WHITE
            else:
                base = CYAN
            if base is CYAN:
                f = 0.15 + 0.6 * v ** 1.4
            else:
                f = 0.55 + 0.6 * v
            col = mix(base, f)
            bold = base is not CYAN or v > 0.75
            tint = mix(base, {CYAN: 0.16, WHITE: 0.30}.get(base, 0.46) * v)

        if ch == " ":
            ch, col = "·", mix(col, 0.6)
        dx = 0
        if xf > 0.80:                                 # dispersion toward the right edge
            p = ((xf - 0.80) / 0.20) ** 1.4
            if random.random() < p * 0.85:
                if random.random() < 0.35:
                    dx = int(random.expovariate(1 / 26))
                    col = mix(col, 0.55)
                else:
                    continue
        x0, y0 = ART_X + c * CW, ART_Y + r * CH
        if not (green and not in_lips) and dx == 0:
            tints.append(([x0, y0, x0 + CW - 1, y0 + CH - 1], tint))
        glyphs.append(((x0 + dx, y0), ch, f_art_b if bold else f_art, col))

# hi-res tint layer (3x grid) so the silhouette reads at small sizes
TS = 3
big = ImageEnhance.Contrast(ImageOps.autocontrast(crop, cutoff=1)).enhance(1.25).resize((COLS * TS, ROWS * TS), Image.LANCZOS)
tl = Image.new("RGB", big.size, BG)
bp, tp = big.load(), tl.load()
for yy in range(big.size[1]):
    for xx in range(big.size[0]):
        R, G, B = (v / 255 for v in bp[xx, yy])
        h, s, v = colorsys.rgb_to_hsv(R, G, B)
        hd = h * 360
        xf, yf = xx / big.size[0], yy / big.size[1]
        in_lips = ((xf - LIPS[0]) / LIPS[2]) ** 2 + ((yf - LIPS[1]) / LIPS[3]) ** 2 < 1
        green = 65 < hd < 170 and s > 0.18
        if (green and not in_lips) or v < 0.24:
            continue
        if in_lips and green:
            base = EMERALD
        elif 230 < hd < 320 and s > 0.2:
            base = PURPLE
        elif 150 <= hd <= 200 and s > 0.25:
            base = EMERALD
        elif (hd < 45 or hd > 340) and s > 0.22:
            base = GOLD
        elif v > 0.82:
            base = WHITE
        else:
            base = CYAN
        a = {CYAN: 0.16, WHITE: 0.30}.get(base, 0.46) * v
        if xf > 0.8 and random.random() < ((xf - 0.8) / 0.2) ** 1.4 * 0.9:
            continue
        tp[xx, yy] = mix(base, a)
tl = tl.resize((COLS * CW, ROWS * CH), Image.BOX)
card.paste(tl, (ART_X, ART_Y))
for pos, ch, font, col in glyphs:
    d.text(pos, ch, font=font, fill=col)

# ---- neofetch-style panel ------------------------------------------------
PX, PY, LH = 820, 150, 44
d.text((PX, PY), "santiago", font=f_ui_b, fill=EMERALD)
d.text((PX + d.textlength("santiago", font=f_ui_b), PY), "@", font=f_ui, fill=DIM)
d.text((PX + d.textlength("santiago@", font=f_ui_b), PY), "spin", font=f_ui_b, fill=GOLD)
d.text((PX, PY + 32), "─" * 13, font=f_ui, fill=BORDER)
rows = [
    ("role", "systems engineering student"),
    ("focus", "applied ai · agentic systems"),
    ("pipeline", "ingest → ground → validate → eval"),
    ("now", "maulwurf · asr + llm analysis"),
    ("langs", "python · typescript · sql"),
    ("infra", "docker · postgres · redis · grpc"),
    ("explore", "local inference · networking"),
    ("", "self-hosting · open source"),
]
y = PY + 76
for key, val in rows:
    d.text((PX, y), key, font=f_ui_b, fill=CYAN)
    d.text((PX + 150, y), val, font=f_ui, fill=WHITE)
    y += LH
y += 18
for i, col in enumerate([BORDER, RAIN, EMERALD, CYAN, PURPLE, GOLD, WHITE]):
    d.rectangle([PX + i * 44, y, PX + i * 44 + 34, y + 22], fill=col)

# ---- footer ---------------------------------------------------------------
d.line([56, H - 66, W - 56, H - 66], fill=BORDER, width=2)
d.text((56, H - 50), "# lesson 5: the spin is in the details.", font=f_small, fill=DIM)
tag = "return { grounded, validated, evaluated }"
d.text((W - 56 - d.textlength(tag, font=f_small), H - 50), tag, font=f_small, fill=GOLD)

card.save(OUT, optimize=True)
print("ok", OUT)
