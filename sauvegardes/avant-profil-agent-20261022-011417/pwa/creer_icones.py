"""Icônes de l'application (PWA). Relancer après avoir remplacé source.png par une autre image.

    python pwa\\creer_icones.py             # icône générée : « C » blanc sur bleu nuit
    python pwa\\creer_icones.py photo.jpg   # icône tirée d'une image (recadrée au centre, carrée)
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ICI = Path(__file__).resolve().parent
BLEU_NUIT = (11, 21, 48)


def generee(taille):
    im = Image.new("RGB", (taille, taille), BLEU_NUIT)
    d = ImageDraw.Draw(im)
    marge = taille // 10
    d.ellipse([marge, marge, taille - marge, taille - marge], outline=(91, 157, 255), width=taille // 24)
    police = ImageFont.load_default(size=int(taille * 0.5))
    d.text((taille / 2, taille / 2), "C", font=police, fill="white", anchor="mm")
    return im


def depuis_image(chemin, taille):
    im = ImageOps.exif_transpose(Image.open(chemin)).convert("RGB")  # photo de téléphone : sens réel
    return ImageOps.fit(im, (taille, taille), centering=(0.5, 0.3))  # cadrage haut : le visage


if __name__ == "__main__":
    for t in (192, 512):
        im = depuis_image(sys.argv[1], t) if len(sys.argv) > 1 else generee(t)
        im.save(ICI / f"icon-{t}.png")
        print(ICI / f"icon-{t}.png")
