"""Gera o fundo em gradiente Creme para os slides.

O pptxgenjs nao suporta preenchimento em gradiente, entao o gradiente vai
como imagem de fundo. Reproduz a paleta do deck anterior: creme claro no
topo esquerdo, creme medio ao centro e creme mais quente no rodape direito,
com dois realces radiais suaves.
"""
from PIL import Image, ImageDraw, ImageFilter
import math, sys

L, A = 1920, 1080

CREME_CLARO = (254, 252, 247)
CREME = (249, 242, 228)
CREME_MEDIO = (242, 231, 210)
CREME_QUENTE = (232, 216, 188)


def mistura(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


img = Image.new("RGB", (L, A), CREME)
px = img.load()

# gradiente diagonal: claro -> creme -> quente
for y in range(A):
    for x in range(0, L, 2):
        t = (x / L * 0.45 + y / A * 0.55)
        if t < 0.45:
            cor = mistura(CREME_CLARO, CREME, t / 0.45)
        else:
            cor = mistura(CREME, CREME_MEDIO, (t - 0.45) / 0.55)
        px[x, y] = cor
        if x + 1 < L:
            px[x + 1, y] = cor

# realces radiais: branco no alto a esquerda, quente no rodape a direita
realce = Image.new("RGB", (L, A), (0, 0, 0))
d = ImageDraw.Draw(realce)
d.ellipse([-L * 0.25, -A * 0.45, L * 0.55, A * 0.55], fill=(60, 58, 54))
realce = realce.filter(ImageFilter.GaussianBlur(220))
img = Image.blend(img, Image.new("RGB", (L, A), (255, 255, 255)),
                  0.0)  # base
rp = realce.load()
for y in range(A):
    for x in range(0, L, 2):
        k = rp[x, y][0] / 255 * 0.55
        cor = mistura(px[x, y], CREME_CLARO, k)
        px[x, y] = cor
        if x + 1 < L:
            px[x + 1, y] = cor

quente = Image.new("RGB", (L, A), (0, 0, 0))
d2 = ImageDraw.Draw(quente)
d2.ellipse([L * 0.55, A * 0.55, L * 1.3, A * 1.5], fill=(60, 58, 54))
quente = quente.filter(ImageFilter.GaussianBlur(240))
qp = quente.load()
for y in range(A):
    for x in range(0, L, 2):
        k = qp[x, y][0] / 255 * 0.75
        cor = mistura(px[x, y], CREME_QUENTE, k)
        px[x, y] = cor
        if x + 1 < L:
            px[x + 1, y] = cor

img = img.filter(ImageFilter.GaussianBlur(1.2))
img.save(sys.argv[1] if len(sys.argv) > 1 else "fundo-creme.png", quality=95)
print("fundo gerado")
