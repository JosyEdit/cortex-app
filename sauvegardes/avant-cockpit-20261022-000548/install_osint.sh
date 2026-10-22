#!/bin/sh
# Installation du module OSINT du Cortex. A lancer seulement apres l'accord de JOSY.
# Le Cortex ne lance jamais ce script lui-meme. Google Maps n'est pas scrape : pas de Playwright.
set -e
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" || { echo "Python 3.10+ requis."; exit 1; }
echo "Paquets a installer : python-wappalyzer, sherlock-project, beautifulsoup4"
echo "Aucun scanner de vulnerabilites n'est installe."
printf "Confirmer l'installation ? (oui/non) : "
read -r OK
[ "$OK" = "oui" ] || { echo "Installation annulee."; exit 0; }
python3 -m pip install "python-wappalyzer>=0.3.1" "sherlock-project>=0.14.0" "beautifulsoup4>=4.12.0"
python3 -c "import Wappalyzer, sherlock_project, bs4; print('Module OSINT pret.')"
