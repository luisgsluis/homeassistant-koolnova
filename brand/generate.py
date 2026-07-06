#!/usr/bin/env python3
"""Generate Koolnova brand assets (snowflake/nova mark, cool->warm gradient)."""
import math, os
from PIL import Image, ImageDraw, ImageFont

OUT = "/tmp/claude-1000/-home-admin/90b90299-024f-4810-b6e3-3d99538d15fc/scratchpad/brand"
os.makedirs(OUT, exist_ok=True)

COOL = (34, 199, 217)   # cyan  (top-left)
COOL2 = (47, 128, 237)  # blue
WARM = (255, 122, 69)   # orange
WARM2 = (255, 61, 78)   # red-ish (bottom-right)
SS = 4                  # supersample for the mask

def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))

def grad_color(t):
    # 3-stop diagonal: cyan -> blue -> orange -> red
    if t < 0.33:
        return lerp(COOL, COOL2, t / 0.33)
    if t < 0.66:
        return lerp(COOL2, WARM, (t - 0.33) / 0.33)
    return lerp(WARM, WARM2, (t - 0.66) / 0.34)

def diagonal_gradient(S):
    img = Image.new("RGB", (S, S))
    px = img.load()
    maxd = 2 * (S - 1)
    lut = [grad_color(i / maxd) for i in range(maxd + 1)]
    for y in range(S):
        for x in range(S):
            px[x, y] = lut[x + y]
    return img

def round_line(d, p0, p1, w, fill):
    d.line([p0, p1], fill=fill, width=w)
    r = w / 2
    for (x, y) in (p0, p1):
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

def snowflake_mask(S):
    """White snowflake on black, rendered supersampled then downscaled."""
    s = S * SS
    m = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(m)
    cx = cy = s / 2
    R = 0.455 * s
    wmain = int(0.072 * s)
    wbr = int(0.052 * s)
    for k in range(6):
        a = math.radians(-90 + k * 60)
        tip = (cx + R * math.cos(a), cy + R * math.sin(a))
        round_line(d, (cx, cy), tip, wmain, 255)
        # side branches at two positions along the arm
        for frac, blen, bw in ((0.52, 0.26, wbr), (0.78, 0.18, wbr)):
            base = (cx + R * frac * math.cos(a), cy + R * frac * math.sin(a))
            for sign in (+1, -1):
                ba = a + sign * math.radians(60)
                bt = (base[0] + R * blen * math.cos(ba),
                      base[1] + R * blen * math.sin(ba))
                round_line(d, base, bt, bw, 255)
    # solid hex core
    core = 0.13 * s
    pts = [(cx + core * math.cos(math.radians(-90 + i * 60)),
            cy + core * math.sin(math.radians(-90 + i * 60))) for i in range(6)]
    d.polygon(pts, fill=255)
    return m.resize((S, S), Image.LANCZOS)

def make_icon(S):
    grad = diagonal_gradient(S).convert("RGBA")
    grad.putalpha(snowflake_mask(S))
    return grad

def load_font(size):
    for p in ("/tmp/claude-1000/-home-admin/0dce8832-ee3a-4505-9f33-575c9c4f0842/scratchpad/xbmc-master/addons/webinterface.default/themes/base/fonts/opensans/opensans-semibold-webfont.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def make_logo(H, wordmark_rgb):
    """Landscape logo: mark + 'koolnova' wordmark. Trimmed, transparent bg."""
    mark = make_icon(H)
    fsize = int(H * 0.52)
    font = load_font(fsize)
    text = "koolnova"
    tmp = Image.new("RGBA", (H * 8, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    bbox = td.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    gap = int(H * 0.10)
    W = H + gap + tw
    logo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    logo.alpha_composite(mark, (0, 0))
    ld = ImageDraw.Draw(logo)
    ty = (H - th) / 2 - bbox[1]
    ld.text((H + gap, ty), text, font=font, fill=wordmark_rgb + (255,))
    return logo

def save(img, name):
    p = os.path.join(OUT, name)
    img.save(p, "PNG", optimize=True)
    print(f"{name:22} {img.size}")

save(make_icon(256), "icon.png")
save(make_icon(512), "icon@2x.png")
save(make_logo(256, (27, 39, 51)), "logo.png")          # dark slate wordmark (light bg)
save(make_logo(512, (27, 39, 51)), "logo@2x.png")
save(make_logo(256, (255, 255, 255)), "dark_logo.png")  # white wordmark (dark bg)
save(make_logo(512, (255, 255, 255)), "dark_logo@2x.png")
print("done ->", OUT)
