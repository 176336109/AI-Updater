---
description: Scan and upgrade all AI open-source projects on your machine
---

# AI Updater

Find and upgrade all AI-related open-source projects on this machine.

## Steps

1. Run the scanner:
   ```bash
   cd ~/.codex/skills/ai-updater && python ai_updater.py
   ```

2. Read the scan results. Present the summary to the user — which projects are updatable, which are latest.

3. Ask the user which projects to upgrade. Options:
   - `all` — upgrade everything
   - `p` — preset projects only
   - `d` — discovered packages only
   - `1,3,5` or `1-5` — specific items
   - `q` — quit without upgrading

4. Report results back to the user.
