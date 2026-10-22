@echo off
rem Arrete l'interface locale du Cortex (celle qui affiche ta journee).
rem La surveillance la relancera dans les 5 minutes : pour l'arreter vraiment,
rem desactive la tache "JOSY EI Cortex Interface" dans le Planificateur de taches.
chcp 65001 >nul
echo Arret de l'interface locale du Cortex...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'pythonw.exe' -and $_.CommandLine -like '*app.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo.
echo Fait. Elle redemarrera seule dans les 5 minutes (c'est voulu).
echo Pour l'arreter durablement : Planificateur de taches, tache
echo "JOSY EI Cortex Interface", clic droit, Desactiver.
echo.
timeout /t 10 /nobreak >nul
