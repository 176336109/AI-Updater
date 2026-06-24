---
description: Scan and upgrade all AI open-source projects on your machine
---

# AI Updater

Run the AI Updater skill to find and upgrade all AI-related open-source projects on this machine.

## Steps

1. Navigate to the ai-updater directory:
   ```bash
   cd ~/.claude/skills/ai-updater
   ```

2. Run the scanner:
   ```bash
   python ai_updater.py
   ```

3. Read the output and present the summary to the user.

4. If the user wants to upgrade, run the script interactively — the user selects which projects to upgrade by number.

5. Report the results (success/fail/skip counts) back to the user.
