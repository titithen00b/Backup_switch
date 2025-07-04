@echo off
setlocal enabledelayedexpansion
title Compilation clean de backup.py avec .spec personnalisé

set EXENAME=backup
set RELEASEDIR=release

echo === Compilation via backup.spec...
if not exist backup.spec (
    echo Le fichier backup.spec est introuvable !
    echo Assurez-vous de lancer ce script depuis le dossier contenant backup.spec
    pause
    exit /b 1
)

:: Compilation en utilisant le .spec
pyinstaller backup.spec

IF %ERRORLEVEL% NEQ 0 (
    echo Erreur lors de la compilation.
    pause
    exit /b %ERRORLEVEL%
)

:: Créer release/ si nécessaire
if not exist %RELEASEDIR% (
    mkdir %RELEASEDIR%
)

:: Déplacer le .exe dans release/
move /y dist\\%EXENAME%.exe %RELEASEDIR%\\%EXENAME%.exe > nul

:: Nettoyage
echo Nettoyage des fichiers temporaires...
rd /s /q build
rd /s /q dist
rd /s /q __pycache__ 2>nul
del /q *.pyc *.log *.tmp *.manifest *.spec~ 2>nul

echo.
echo Fichier final prêt : %RELEASEDIR%\\%EXENAME%.exe
echo.

pause
endlocal
