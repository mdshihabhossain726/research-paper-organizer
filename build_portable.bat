@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo Research Paper Organizer - Portable EXE Builder
echo ================================================

where py >nul 2>nul
if errorlevel 1 (
  set PYTHON=python
) else (
  set PYTHON=py -3
)

%PYTHON% -m pip install --upgrade pip
if errorlevel 1 goto failed
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 goto failed
%PYTHON% -m pip install pyinstaller
if errorlevel 1 goto failed

REM Build as a folder-based portable app. PyInstaller's PyQt6 hooks collect Qt WebEngine files.
%PYTHON% -m PyInstaller --noconfirm --clean --windowed --onedir --name ResearchPaperOrganizer --collect-all PyQt6.QtWebEngineCore --collect-all PyQt6.QtWebEngineWidgets app.py
if errorlevel 1 goto failed

echo.
echo Build complete!
echo App folder: %CD%\dist\ResearchPaperOrganizer
echo Run: dist\ResearchPaperOrganizer\ResearchPaperOrganizer.exe
echo Copy the ENTIRE ResearchPaperOrganizer folder to another PC; do not copy only the EXE.
echo Keep the folder in a location where you have write permission for portable database storage.
pause
exit /b 0

:failed
echo.
echo BUILD FAILED. Read the error above, then send a screenshot of this window.
pause
exit /b 1
