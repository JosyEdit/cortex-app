@echo off
REM Installation du module OSINT du Cortex. A lancer seulement apres l'accord de JOSY.
REM Le Cortex ne lance jamais ce script lui-meme. Google Maps n'est pas scrape : pas de Playwright.
setlocal
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
  echo Python 3.10 ou plus recent est requis.
  exit /b 1
)
echo Paquets a installer : python-wappalyzer, sherlock-project, beautifulsoup4
echo Aucun scanner de vulnerabilites n'est installe.
set /p OK=Confirmer l'installation ? (oui/non) :
if /i not "%OK%"=="oui" (
  echo Installation annulee.
  exit /b 0
)
python -m pip install "python-wappalyzer>=0.3.1" "sherlock-project>=0.14.0" "beautifulsoup4>=4.12.0"
if errorlevel 1 (
  echo Echec de l'installation.
  exit /b 1
)
python -c "import Wappalyzer, sherlock_project, bs4; print('Module OSINT pret.')"
endlocal
