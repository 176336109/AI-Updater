---
name: ai-updater
description: 一键扫描并更新电脑上所有 AI 开源软件（69 预设 + AI 关键词智能发现，Git/pip/brew/winget/conda/npm），Win+Mac 双平台
---

# AI Updater

One command to find and upgrade every AI open-source project on your machine.

## Quick Start

```bash
pip install -r requirements.txt
python ai_updater.py
```

## What it does

1. **Preset matching** — scans your directories + package managers against 69 known AI projects in `projects.csv`
2. **Smart discovery** — scans ALL installed packages (pip/npm/brew/winget/conda) and identifies AI-related ones by keyword matching
3. **Version comparison** — checks current vs latest (git remote / PyPI API / brew info)
4. **Interactive upgrade** — pick what to upgrade: `p` preset only, `d` discovered only, `1,3,5` specific, or `all`

## Files

| File | Purpose |
|---|---|
| `ai_updater.py` | Main script — no changes needed |
| `projects.csv` | Project database — **edit with Excel/WPS** to add your own |
| `config.yaml` | Your settings — scan paths, package manager toggles |
| `requirements.txt` | Python dependencies |

## Add your own projects

Open `projects.csv` in Excel/WPS/Google Sheets, append a row:

```
MyProject,llm-tools,github.com/my/project,myproject/main.py,https://...,git_pull,win|mac,,,,
```

## Supported package managers

| Manager | Platform | Capability |
|---|---|---|
| pip (PyPI) | Win / Mac | Version check via PyPI API |
| Homebrew | Mac | brew info + upgrade |
| winget | Win | winget list + upgrade |
| conda | Win / Mac | AI package matching |
| npm | Win / Mac | Global package matching |
| Git | Win / Mac | git fetch + pull + stash |

## CLI

```bash
python ai_updater.py                  # scan + interactive upgrade
python ai_updater.py --scan-only      # scan only, no upgrade
python ai_updater.py --update-all     # auto-upgrade everything
python ai_updater.py --config my.yaml # custom config
```
