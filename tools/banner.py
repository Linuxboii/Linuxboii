"""Generate assets/banner-{light,dark}.svg: rotating point-cloud padlock + name + ASCII Charminar.

Run: python tools/banner.py   (needs Pillow for the ASCII silhouette)
"""
import math, os
from PIL import Image, ImageDraw

W, H = 1200, 340
FRAMES = 36
DUR = 7.2  # seconds per full turn
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

THEMES = {
    "dark":  {"bg": "#0d1117", "fg": "#e6edf3", "muted": "#7d8590", "accent": "#3fb950", "ascii": "#6e7681"},
    "light": {"bg": "#ffffff", "fg": "#1f2328", "muted": "#59636e", "accent": "#1a7f37", "ascii": "#8c959f"},
}

# ---------- 3D padlock point cloud ----------
def padlock_points():
    pts = []
    # body: rounded box surface, x in [-1,1], y in [-1.1,0.1], z in [-0.45,0.45]
    bx, by0, by1, bz = 1.0, -1.15, 0.1, 0.42
    step = 0.13
    def rng(a, b):
        n = max(2, int((b - a) / step) + 1)
        return [a + (b - a) * i / (n - 1) for i in range(n)]
    for x in rng(-bx, bx):
        for y in rng(by0, by1):
            pts.append((x, y, bz)); pts.append((x, y, -bz))
    for z in rng(-bz, bz):
        for y in rng(by0, by1):
            pts.append((bx, y, z)); pts.append((-bx, y, z))
        for x in rng(-bx, bx):
            pts.append((x, by1, z)); pts.append((x, by0, z))
    # keyhole on front face (denser dots, marked)
    key = []
    for i in range(14):
        a = 2 * math.pi * i / 14
        key.append((0.17 * math.cos(a), -0.38 + 0.17 * math.sin(a), bz + 0.01))
    for t in rng(-0.85, -0.5):
        key.append((0.0, t, bz + 0.01))
    # shackle: half torus tube above body
    R, r = 0.62, 0.13
    for i in range(22):
        u = math.pi * i / 21
        cx, cy = R * math.cos(u), 0.1 + 0.55 + R * math.sin(u) * 0.95
        for j in range(8):
            v = 2 * math.pi * j / 8
            nx, ny = math.cos(u), math.sin(u)
            pts.append((cx + r * math.cos(v) * nx, cy + r * math.cos(v) * ny, r * math.sin(v)))
    # shackle legs down into body
    for leg in (-R, R):
        for y in rng(0.1, 0.65):
            for j in range(8):
                v = 2 * math.pi * j / 8
                pts.append((leg + r * math.cos(v), y, r * math.sin(v)))
    return pts, key

def project(p, ang, cx, cy, scale):
    x, y, z = p
    ca, sa = math.cos(ang), math.sin(ang)
    x, z = x * ca + z * sa, -x * sa + z * ca
    tilt = 0.32
    ct, st = math.cos(tilt), math.sin(tilt)
    y, z = y * ct - z * st, y * st + z * ct
    d = 4.2
    f = d / (d - z)
    return cx + x * scale * f, cy - y * scale * f, z

def frame_paths(pts, key, ang, cx, cy, scale):
    buckets = {0: [], 1: [], 2: []}
    for p in pts:
        X, Y, z = project(p, ang, cx, cy, scale)
        b = 0 if z < -0.25 else (1 if z < 0.25 else 2)
        buckets[b].append(f"M{X:.1f} {Y:.1f}h0")
    keyd = []
    for p in key:
        X, Y, z = project(p, ang, cx, cy, scale)
        if z > 0: keyd.append(f"M{X:.1f} {Y:.1f}h0")
    return buckets, "".join(keyd)

# ---------- ASCII Charminar ----------
def charminar_ascii(cols=46, rows=22):
    S = 8
    w, h = cols * S, rows * S * 2
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    gx = w / 100.0; gy = h / 100.0
    def R(x0, y0, x1, y1): d.rectangle([x0 * gx, y0 * gy, x1 * gx, y1 * gy], fill=255)
    def E(x0, y0, x1, y1, v=255): d.ellipse([x0 * gx, y0 * gy, x1 * gx, y1 * gy], fill=v)
    # four minarets (two visible pairs, front view): outer tall towers
    for mx in (6, 86):
        R(mx, 18, mx + 8, 100)
        for by in (30, 46, 62):  # balconies
            R(mx - 2, by, mx + 10, by + 2.5)
        E(mx - 1, 8, mx + 9, 22)            # onion dome
        R(mx + 3.4, 2, mx + 4.6, 9)          # finial
    # main body
    R(14, 50, 86, 100)
    R(12, 46, 88, 51)  # cornice
    # upper storey with small arches
    R(18, 36, 82, 47)
    for ax in range(22, 80, 8):
        E(ax, 38, ax + 5, 44, 0)
    # big central arch (cut out)
    E(36, 60, 64, 84, 0); d.rectangle([36 * gx, 72 * gy, 64 * gx, 100 * gy], fill=0)
    # side arches
    E(20, 66, 29, 80, 0); d.rectangle([20 * gx, 73 * gy, 29 * gx, 100 * gy], fill=0)
    E(71, 66, 80, 80, 0); d.rectangle([71 * gx, 73 * gy, 80 * gx, 100 * gy], fill=0)
    ramp = " .:-=+*#%@"
    small = im.resize((cols, rows), Image.BILINEAR)
    lines = []
    for yy in range(rows):
        row = ""
        for xx in range(cols):
            v = small.getpixel((xx, yy)) / 255.0
            row += ramp[min(len(ramp) - 1, int(v * (len(ramp) - 1) + 0.15))]
        lines.append(row.rstrip())
    return lines

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build(theme):
    t = THEMES[theme]
    pts, key = padlock_points()
    cx, cy, scale = 190, 190, 92
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Sushanth Kasturi: rotating point-cloud padlock next to the Charminar drawn in ASCII">']
    step = DUR / FRAMES
    out.append("<style>")
    out.append(f".f{{opacity:0;animation:s {DUR}s steps(1,end) infinite}}")
    out.append(f"@keyframes s{{0%{{opacity:1}}{100 / FRAMES:.4f}%{{opacity:0}}100%{{opacity:0}}}}")
    out.append(f".a{{stroke:{t['muted']};stroke-width:2.2;stroke-linecap:round;opacity:.35}}"
               f".b{{stroke:{t['fg']};stroke-width:2.6;stroke-linecap:round;opacity:.6}}"
               f".c{{stroke:{t['fg']};stroke-width:3.1;stroke-linecap:round}}"
               f".k{{stroke:{t['accent']};stroke-width:3.4;stroke-linecap:round}}")
    out.append("@media (prefers-reduced-motion:reduce){.f{animation:none}.f0{opacity:1}}")
    out.append("</style>")
    out.append(f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>')
    for i in range(FRAMES):
        ang = 2 * math.pi * i / FRAMES
        b, keyd = frame_paths(pts, key, ang, cx, cy, scale)
        out.append(f'<g class="f f{i}" style="animation-delay:{i * step:.3f}s">'
                   f'<path class="a" d="{"".join(b[0])}"/><path class="b" d="{"".join(b[1])}"/>'
                   f'<path class="c" d="{"".join(b[2])}"/>' + (f'<path class="k" d="{keyd}"/>' if keyd else "") + "</g>")
    # text block
    mono = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
    sans = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
    out.append(f'<text x="400" y="150" font-family="{sans}" font-size="46" font-weight="700" fill="{t["fg"]}">Sushanth Kasturi</text>')
    out.append(f'<text x="402" y="188" font-family="{mono}" font-size="16" fill="{t["muted"]}">AI systems that do useful work. Security first.</text>')
    out.append(f'<text x="402" y="222" font-family="{mono}" font-size="14" fill="{t["accent"]}">$ whoami --short</text>')
    out.append(f'<text x="402" y="246" font-family="{mono}" font-size="14" fill="{t["muted"]}">founder @ avlokai · hyderabad · linux</text>')
    # ascii charminar
    lines = charminar_ascii()
    out.append(f'<text font-family="{mono}" font-size="10.5" fill="{t["ascii"]}" xml:space="preserve">')
    for i, ln in enumerate(lines):
        out.append(f'<tspan x="895" y="{48 + i * 12.4:.1f}">{esc(ln)}</tspan>')
    out.append("</text></svg>")
    return "\n".join(out)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for th in THEMES:
        p = os.path.join(OUT, f"banner-{th}.svg")
        open(p, "w", encoding="utf-8").write(build(th))
        print(p, os.path.getsize(p))
    print("\n".join(charminar_ascii()))
