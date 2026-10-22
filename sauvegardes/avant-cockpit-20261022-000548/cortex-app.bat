@echo off
rem Cortex - interface locale. Ouvre ta journee dans le navigateur (127.0.0.1).
chcp 65001 >nul
cd /d "%~dp0"
echo Demarrage de l'interface locale du Cortex...
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo Python n'a pas ete trouve sur le PATH.
  echo Essaie : py app.py --ouvrir
  echo.
  pause
  exit /b 1
)
echo Garde cette fenetre ouverte : c'est le moteur de l'interface.
echo Ferme-la ou fais Ctrl+C pour arreter l'interface.
echo.
python app.py --ouvrir
echo.
echo L'interface est arretee. Details dans cortex-app.log
echo Appuie sur une touche pour fermer.
pause >nul
