@echo off
setlocal enabledelayedexpansion
title Compilation clean de backup.py

set EXENAME=backup
set RELEASEDIR=..\release

echo === Compilation en cours...
pyinstaller --noconsole --onefile --icon=icon.ico --name %EXENAME% backup.py

IF %ERRORLEVEL% NEQ 0 (
    echo Erreur lors de la compilation.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo  Compilation terminée.

:: Créer release/ si nécessaire
if not exist %RELEASEDIR% (
    mkdir %RELEASEDIR%
)

:: Supprimer ancienne version
if exist %RELEASEDIR%\\%EXENAME%.exe (
    del /q %RELEASEDIR%\\%EXENAME%.exe
)

:: Déplacer l'exe dans release/
move /y dist\\%EXENAME%.exe %RELEASEDIR%\\%EXENAME%.exe > nul

:: Nettoyage total
echo Nettoyage des dossiers et fichiers temporaires...
rd /s /q build
rd /s /q dist
rd /s /q __pycache__ 2>nul
del /q *.pyc *.log *.manifest *.spec~ *.tmp 2>nul

echo.
echo Fichier final : %RELEASEDIR%\\%EXENAME%.exe
echo.

pause
endlocal
