"""Icônes de l'application (PWA), à relancer après avoir changé d'image.

    python pwa\\creer_icones.py             # icône générée : « C » blanc sur bleu nuit
    python pwa\\creer_icones.py photo.jpg   # photo recadrée carrée, dans un cercle sur bleu nuit

Produit icon-192.png et icon-512.png (usage « any » : cercle avec marge, rien n'est coupé) et
icon-maskable-512.png (usage « maskable » : sujet dans la zone sûre centrale de 80 %, pour les
systèmes qui découpent l'icône en rond ou en goutte).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ICI = Path(__file__).resolve().parent
BLEU_NUIT = (11, 21, 48)
BLEU = (91, 157, 255)
SUR = 4  # suréchantillonnage : bords du cercle lisses


def sujet(chemin, cote):
    """Carré du sujet : la photo recadrée sur le visage, ou le « C » du Cortex."""
    if chemin:
        im = ImageOps.exif_transpose(Image.open(chemin)).convert("RGB")  # sens réel de la photo
        carre = ImageOps.fit(im, (2000, 2000), method=Image.LANCZOS, centering=(0.5, 0.3))
        # Zoom sur le buste : lisible même en petit (barre des tâches, écran d'accueil).
        cx, cy, demi = 1000, 1020, 620
        return carre.crop((cx - demi, cy - demi, cx + demi, cy + demi)).resize((cote, cote), Image.LANCZOS)
    im = Image.new("RGB", (cote, cote), BLEU_NUIT)
    police = ImageFont.load_default(size=int(cote * 0.6))
    ImageDraw.Draw(im).text((cote / 2, cote / 2), "C", font=police, fill="white", anchor="mm")
    return im


def icone(chemin, taille, zone):
    """Fond bleu nuit plein ; sujet dans un cercle occupant `zone` de la largeur, liseré bleu."""
    grand = taille * SUR
    fond = Image.new("RGB", (grand, grand), BLEU_NUIT)
    diametre = int(grand * zone)
    marge = (grand - diametre) // 2
    masque = Image.new("L", (diametre, diametre), 0)
    ImageDraw.Draw(masque).ellipse([0, 0, diametre - 1, diametre - 1], fill=255)
    fond.paste(sujet(chemin, diametre), (marge, marge), masque)
    ImageDraw.Draw(fond).ellipse([marge, marge, marge + diametre - 1, marge + diametre - 1],
                                 outline=BLEU, width=max(2, grand // 64))
    return fond.resize((taille, taille), Image.LANCZOS)


if __name__ == "__main__":
    photo = sys.argv[1] if len(sys.argv) > 1 else None
    for t in (192, 512):
        icone(photo, t, 0.86).save(ICI / f"icon-{t}.png", optimize=True)
    icone(photo, 512, 0.72).save(ICI / "icon-maskable-512.png", optimize=True)
    print("icônes écrites dans", ICI)
