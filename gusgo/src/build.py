#!/usr/bin/env python3
"""GUSGO · pipeline de marca.

Genera desde los originales:
  ../web/index.html          web de un solo archivo (fotos y fuentes incrustadas)
  ../dossier/GUSGO-Dossier.pdf  dossier A4 imprimible (vía Chromium)

Uso:  python3 build.py
"""
import base64, io, json, subprocess, pathlib
from PIL import Image, ImageEnhance, ImageOps, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent
OUT_WEB = ROOT.parent / "web"; OUT_DOS = ROOT.parent / "dossier"
OUT_WEB.mkdir(exist_ok=True); OUT_DOS.mkdir(exist_ok=True)

# ───────────────────────── Imagen ─────────────────────────
def grade(im, warmth=1.04, contrast=1.06, sat=1.05):
    """Tratamiento editorial: un punto más cálido, contraste suave."""
    im = im.convert("RGB")
    r, g, b = im.split()
    r = r.point(lambda v: min(255, int(v * warmth)))
    b = b.point(lambda v: int(v * (2 - warmth)))
    im = Image.merge("RGB", (r, g, b))
    im = ImageEnhance.Contrast(im).enhance(contrast)
    return ImageEnhance.Color(im).enhance(sat)

def uri(im, q=82, fmt="JPEG"):
    buf = io.BytesIO()
    if fmt == "PNG": im.save(buf, "PNG", optimize=True)
    else: im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()

def upscale(im, w):
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS) if im.width < w else im

src = lambda n: Image.open(ROOT / "img" / n)
hero = grade(src("i1.jpeg"))
pack = grade(src("i2.jpeg"))
room = grade(src("p-004.jpg"), warmth=1.03)


IMG = {
    "hero": uri(upscale(hero, 2000), 80),
    "cup": uri(upscale(hero.crop((820, 0, 1350, 530)), 1100), 84),          # taza de chocolate
    "macro": uri(upscale(hero.crop((180, 120, 760, 700)), 1100), 84),       # estría del lazo
    "pack": uri(upscale(pack, 1800), 80),
    "packmacro": uri(upscale(pack.crop((400, 420, 1000, 820)), 1200), 84),
    "room": uri(upscale(room, 2000), 80),
    "roomdet": uri(upscale(room.crop((300, 170, 760, 430)), 1200), 84),
}

# Sello: líneas marfil sobre transparente, extraídas por luminancia.
seal = src("p-003.ppm").convert("RGB")
L = ImageOps.grayscale(seal).point(lambda v: 0 if v < 120 else min(255, (v - 120) * 3))
mark = Image.new("RGBA", seal.size, (241, 234, 221, 0)); mark.putalpha(L.filter(ImageFilter.SMOOTH))
mark = mark.resize((600, 600), Image.LANCZOS)
IMG["seal"] = uri(mark, fmt="PNG")
dark = Image.new("RGBA", mark.size, (24, 59, 35, 0)); dark.putalpha(mark.getchannel("A"))
IMG["seal_dark"] = uri(dark, fmt="PNG")

# ───────────────────────── Fuentes ─────────────────────────
def fonts_css():
    rules = []
    for f in sorted((ROOT / "fonts").glob("*.woff2")):
        fam, spec = f.stem.split("-"); w, st = spec[:-1], ("italic" if spec[-1] == "i" else "normal")
        fam = {"CormorantGaramond": "Cormorant Garamond"}.get(fam, fam)
        data = base64.b64encode(f.read_bytes()).decode()
        rules.append(f"@font-face{{font-family:'{fam}';font-style:{st};font-weight:{w};"
                     f"src:url(data:font/woff2;base64,{data}) format('woff2');font-display:swap}}")
    return "\n".join(rules)
FONTS = fonts_css()

# ───────────────────────── Contenido ─────────────────────────
CARTA = [
    ("Lazos", [
        ("Lazos de la casa", "Masa al natural, azúcar fino al salir de la tanda.", "3 piezas", "4,20"),
        ("Avellana tostada", "Bastón relleno de praliné de avellana y un punto de sal.", "2 piezas", "5,60"),
        ("Pera y limón", "Bastón de temporada: pera asada y piel de limón.", "2 piezas", "5,40"),
    ]),
    ("A la taza", [
        ("Chocolate de la casa", "Cobertura negra al 70 % de cacao, ligada con leche.", "150 ml", "3,80"),
        ("Café de filtro", "Especialidad de tostador rotativo, preparado al momento.", "180 ml", "3,20"),
        ("Verbena y limón", "Infusión de hierbaluisa con piel de limón.", "200 ml", "2,80"),
    ]),
    ("Para compartir", [
        ("Mesa para dos", "Seis lazos y dos tazas de chocolate de la casa.", "2 personas", "14,80"),
        ("La pausa corta", "Tres lazos y un café de filtro.", "1 persona", "6,90"),
    ]),
]

def carta_html():
    out = []
    for cat, items in CARTA:
        rows = "".join(f"""<li class="dish"><div class="dish-h"><span class="dish-n">{n}</span>
          <span class="dots"></span><span class="dish-p">{p}<small>€</small></span></div>
          <p>{d}<em>{r}</em></p></li>""" for n, d, r, p in items)
        out.append(f'<div class="carta-col"><h3 class="carta-cat">{cat}</h3><ul>{rows}</ul></div>')
    return "".join(out)

STEAM = """<svg class="steam" viewBox="0 0 200 320" aria-hidden="true"><defs>
<filter id="wisp" x="-50%" y="-20%" width="200%" height="140%">
<feTurbulence type="fractalNoise" baseFrequency="0.012 0.03" numOctaves="2" seed="4"><animate attributeName="seed" values="1;30" dur="9s" repeatCount="indefinite" calcMode="discrete"/></feTurbulence>
<feDisplacementMap in="SourceGraphic" scale="34"/><feGaussianBlur stdDeviation="5"/></filter>
<linearGradient id="fade" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".25" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
<g filter="url(#wisp)" stroke="url(#fade)" fill="none" stroke-linecap="round">
<path class="w w1" stroke-width="14" d="M100 320 C 70 260, 130 220, 100 160 S 70 60, 110 0"/>
<path class="w w2" stroke-width="10" d="M80 320 C 60 270, 110 230, 80 170 S 60 80, 85 10"/>
<path class="w w3" stroke-width="12" d="M120 320 C 150 260, 95 210, 125 150 S 150 60, 120 0"/>
</g></svg>"""

# ───────────────────────── Web ─────────────────────────
WEB = (ROOT / "web.html").read_text()
DOS = (ROOT / "dossier.html").read_text()

def fill(tpl):
    tpl = tpl.replace("{{FONTS}}", FONTS).replace("{{CARTA}}", carta_html()).replace("{{STEAM}}", STEAM)
    for k, v in IMG.items(): tpl = tpl.replace("{{" + k + "}}", v)
    return tpl

(OUT_WEB / "index.html").write_text(fill(WEB))
print("web  →", OUT_WEB / "index.html")

# Captura de la web para el dossier (mockup) y PDF final con Chromium.
shots = ROOT / ".shots"; shots.mkdir(exist_ok=True)
NODE = f"""
const {{chromium}} = require('playwright');
(async () => {{
  const b = await chromium.launch();
  let p = await b.newPage({{viewport:{{width:1440,height:900}}, deviceScaleFactor:1.5}});
  await p.goto('file://{OUT_WEB/"index.html"}'); await p.waitForTimeout(2600);
  await p.screenshot({{path:'{shots}/desk.jpg', quality:85}});
  await p.evaluate(() => document.querySelector('#carta').scrollIntoView()); await p.waitForTimeout(1200);
  await p.screenshot({{path:'{shots}/desk2.jpg', quality:85}});
  p = await b.newPage({{viewport:{{width:390,height:844}}, deviceScaleFactor:2, isMobile:true}});
  await p.goto('file://{OUT_WEB/"index.html"}'); await p.waitForTimeout(2600);
  await p.screenshot({{path:'{shots}/mob.jpg', quality:85}});
  p = await b.newPage();
  await p.goto('file://{OUT_DOS/"dossier.html"}'); await p.waitForTimeout(800);
  await p.pdf({{path:'{OUT_DOS/"GUSGO-Dossier.pdf"}', format:'A4', printBackground:true, preferCSSPageSize:true}});
  await b.close();
}})();"""
def run_node():
    subprocess.run(["node", "-e", NODE], check=True, cwd="/tmp")

(OUT_DOS / "dossier.html").write_text("")  # placeholder para la primera pasada
run_node()
for k in ("desk", "desk2", "mob"):
    IMG[k] = uri(Image.open(shots / f"{k}.jpg"), 82)
(OUT_DOS / "dossier.html").write_text(fill(DOS))
run_node()
print("pdf  →", OUT_DOS / "GUSGO-Dossier.pdf")
