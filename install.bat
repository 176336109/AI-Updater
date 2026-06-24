@echo off
REM AI Updater — install for Claude Code / Codex / Cursor / Reasonix (Windows)
REM Run from the repo root:
REM   install.bat

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"

echo AI Updater - Installer
echo ======================
echo.

REM ----- Claude Code -----
if exist "%USERPROFILE%\.claude" (
    echo [Claude Code]
    mkdir "%USERPROFILE%\.claude\skills\ai-updater" 2>nul
    mkdir "%USERPROFILE%\.claude\commands" 2>nul
    copy /Y "%SCRIPT_DIR%SKILL.md" "%USERPROFILE%\.claude\skills\ai-updater\SKILL.md" >nul
    copy /Y "%SCRIPT_DIR%ai_updater.py" "%USERPROFILE%\.claude\skills\ai-updater\ai_updater.py" >nul
    copy /Y "%SCRIPT_DIR%projects.csv" "%USERPROFILE%\.claude\skills\ai-updater\projects.csv" >nul
    copy /Y "%SCRIPT_DIR%config.yaml" "%USERPROFILE%\.claude\skills\ai-updater\config.yaml" >nul
    copy /Y "%SCRIPT_DIR%requirements.txt" "%USERPROFILE%\.claude\skills\ai-updater\requirements.txt" >nul
    copy /Y "%SCRIPT_DIR%.claude\commands\ai-updater.md" "%USERPROFILE%\.claude\commands\ai-updater.md" >nul
    echo   -^> %%USERPROFILE%%\.claude\skills\ai-updater\
    echo   -^> %%USERPROFILE%%\.claude\commands\ai-updater.md
    echo   /ai-updater ready
) else (
    echo [Claude Code] skipped (not found)
)

echo.

REM ----- Codex -----
if exist "%USERPROFILE%\.codex" (
    echo [Codex]
    mkdir "%USERPROFILE%\.codex\skills\ai-updater" 2>nul
    mkdir "%USERPROFILE%\.codex\commands" 2>nul
    copy /Y "%SCRIPT_DIR%SKILL.md" "%USERPROFILE%\.codex\skills\ai-updater\SKILL.md" >nul
    copy /Y "%SCRIPT_DIR%ai_updater.py" "%USERPROFILE%\.codex\skills\ai-updater\ai_updater.py" >nul
    copy /Y "%SCRIPT_DIR%projects.csv" "%USERPROFILE%\.codex\skills\ai-updater\projects.csv" >nul
    copy /Y "%SCRIPT_DIR%config.yaml" "%USERPROFILE%\.codex\skills\ai-updater\config.yaml" >nul
    copy /Y "%SCRIPT_DIR%requirements.txt" "%USERPROFILE%\.codex\skills\ai-updater\requirements.txt" >nul
    copy /Y "%SCRIPT_DIR%.codex\commands\ai-updater.md" "%USERPROFILE%\.codex\commands\ai-updater.md" >nul
    echo   -^> %%USERPROFILE%%\.codex\skills\ai-updater\
    echo   -^> %%USERPROFILE%%\.codex\commands\ai-updater.md
) else (
    echo [Codex] skipped (not found)
)

echo.

REM ----- Cursor -----
if exist "%USERPROFILE%\.cursor" (
    echo [Cursor]
    mkdir "%USERPROFILE%\.cursor\commands" 2>nul
    copy /Y "%SCRIPT_DIR%.cursor\commands\ai-updater.md" "%USERPROFILE%\.cursor\commands\ai-updater.md" >nul
    echo   -^> %%USERPROFILE%%\.cursor\commands\ai-updater.md
) else (
    echo [Cursor] skipped (not found)
)

echo.

REM ----- Reasonix (self-contained, already in repo) -----
if exist "%SCRIPT_DIR%.reasonix" (
    echo [Reasonix]
    mkdir "%SCRIPT_DIR%.reasonix\skills\ai-updater" 2>nul
    copy /Y "%SCRIPT_DIR%SKILL.md" "%SCRIPT_DIR%.reasonix\skills\ai-updater\SKILL.md" >nul
    echo   -^> .reasonix\skills\ai-updater\SKILL.md
)

echo.
echo Done. Now install Python dependencies:
echo   pip install -r "%SCRIPT_DIR%requirements.txt"
echo.
echo Then open your AI coding tool and type: /ai-updater

endlocal
