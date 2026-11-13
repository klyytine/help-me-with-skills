# help-me-with-skills

A Claude skill that finds the right skill for your task.

When you have many skills installed, you cannot tell which one fits a task without opening and
reading them. `help-skill` does that reading for you. You describe the task, Claude checks every
skill you have, reads the likely ones in full, and gives you one recommendation with reasons. If
nothing you have fits, it looks for a new skill to install and vets it first.

## What it does

**A. Finds an installed skill that matches the task**

1. Pins down the task and the requirements that decide the choice.
2. Gathers candidates from the session's skill list, from a script that reads every skill on
   disk, and from your claude.ai account skills.
3. Reads the top 3 to 5 candidates in full and checks fit, prerequisites and side effects.
4. Gives one verdict.
5. Starts the chosen skill if you asked for the task to be done.

**B. Looks for a new skill when none fits**

1. Searches the plugin marketplaces and plugin directory already cached on your machine.
2. Searches your account catalog, where Claude has the tools for it.
3. Searches the web.
4. Reads the candidate's files and checks them for red flags before recommending anything.
5. Installs nothing without your yes.

## What a verdict looks like

```
Use: resume-tailor, fits fully
Why: tailors an existing resume to one job posting, which is the task.
Needs: your current resume and the job ad.
Does not cover: the cover letter (run cover-letter-generator after).
Start: /resume-tailor

Passed over
- resume-architect, rebuilds from the full career history; more than this task needs.
- resume-ats-optimizer, keyword pass only, no tailoring.
```

## Install

Pick one way.

### 1. As a Claude Code plugin

```bash
claude plugin marketplace add klyytine/help-me-with-skills
```

```bash
claude plugin install help-me-with-skills@help-me-with-skills
```

The skill is then called `help-me-with-skills:help-skill`.

### 2. As a personal skill, with the installer

Clone the repository, then run the installer for your system.

```bash
git clone https://github.com/klyytine/help-me-with-skills.git
```

Windows (PowerShell), from inside the cloned folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

macOS and Linux, from inside the cloned folder:

```bash
sh install.sh
```

Both installers copy the skill to `~/.claude/skills/help-skill`. If a copy is already there, it
is moved to `~/.claude/skills-backup/` first. Add `-Project` (PowerShell) or `--project` (shell)
to install into `.claude/skills/` of the current folder instead.

### 3. By hand, or in the Claude apps

- Claude Code: copy the folder `skills/help-skill` to `~/.claude/skills/help-skill`.
- Claude desktop and claude.ai: download `help-skill.zip` from the
  [latest release](https://github.com/klyytine/help-me-with-skills/releases/latest) and upload
  it in the skills section of the settings.

If the skill does not show up, start a new session.

## Use

Call it by name with your task:

```
/help-skill I need to turn a scanned invoice PDF into a spreadsheet
```

Or ask in plain words. These trigger it too:

- "Is there a skill for writing release notes?"
- "Which skill should I use to check my Finnish grammar?"
- "Find me a skill for Figma design tokens."

## The inventory script on its own

The skill ships one script, [skill_inventory.py](skills/help-skill/scripts/skill_inventory.py).
Claude runs it for you, but it also works by hand. It uses the Python standard library only.

```bash
python skills/help-skill/scripts/skill_inventory.py resume tailor job
```

| Command | Result |
|---|---|
| `skill_inventory.py` | count of skills per source |
| `skill_inventory.py pdf form fill` | installed skills ranked against the keywords |
| `skill_inventory.py pdf form --deep` | also matches inside the skill body |
| `skill_inventory.py pdf form --available` | ranks skills and plugins that are not installed |
| `skill_inventory.py --all` | every installed skill, one line each |
| `skill_inventory.py pdf --json` | JSON output with full descriptions |

It scans personal skills, project skills, installed plugins and account-synced plugins. With
`--available` it scans the marketplaces you have added and the plugin directory cache.

## Requirements

- Claude Code, the Claude desktop app, or claude.ai with skills enabled
- Python 3.9 or newer on the machine where Claude runs commands

## Limits

- The script sees only skills that exist as files. Skills that live only in a claude.ai account
  are reached through Claude's own skill tools, so in a setup without those tools they can be
  missed.
- Ranking is by keyword. It builds the shortlist; the judgement comes from Claude reading the
  shortlisted skills.
- The plugin directory search works offline from a cache written by Claude Code. If that cache
  is absent, the skill goes on to the account catalog and the web.
- A skill found on disk is not always active in the current session. The skill reports that
  case instead of hiding it.

## Repository layout

```
help-me-with-skills/
├── skills/help-skill/
│   ├── SKILL.md                         instructions Claude follows
│   ├── references/finding-new-skills.md  search order, vetting, install commands
│   └── scripts/skill_inventory.py       inventory and ranking
├── .claude-plugin/                      plugin and marketplace manifests
├── install.ps1                          installer for Windows
├── install.sh                           installer for macOS and Linux
├── CHANGELOG.md
└── LICENSE
```

## Licence

MIT. See [LICENSE](LICENSE).
