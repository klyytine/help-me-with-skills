---
name: help-skill
description: Finds the right Claude skill for a task. Matches the user's task and requirements against every installed skill, reads the candidates, and recommends one with reasons; when none fits, searches for a new skill or plugin to install. Use when the user asks which skill to use, whether a skill exists for something, "is there a skill for", "find a skill for this", "what skills are installed for", wants to find or install a new skill, or invokes /help-skill.
---

# Help Skill

The user should never have to browse or read skills. You read them; the user gets a verdict.

## Quick start

```bash
python scripts/skill_inventory.py invoice pdf extract table
```

`scripts/` is relative to this skill's base directory. The script reads the frontmatter of every
SKILL.md on disk and ranks the skills against the keywords. Run it with `--help` for all options.
Where `python` is not a command, use `python3`.

## Workflow

1. **Pin down the task.** One sentence for the task, plus the requirements that decide the choice:
   input at hand, output wanted, language, tools or constraints. Take these from the conversation.
   Ask one question only when the choice between candidates hinges on the answer.

2. **Gather candidates from three views.** None is complete alone.
   - *Session skill list* (already in context): the authority on what can be invoked now. It often
     lacks descriptions, so never judge from it alone.
   - *Inventory script*: full descriptions for skills on disk. Pass 6–10 keywords with synonyms,
     also in the language the skills are written in. Re-run with `--deep` when results are thin.
   - *`ListSkills` tool with keywords*, where it exists: account skills that are not on disk.

3. **Verify by reading.** Read the SKILL.md of the top 3–5 candidates. Check each against the task:
   - Does it do this task, or only something nearby?
   - Do its inputs and outputs match the requirements?
   - Prerequisites: API key, MCP server, CLI, login, paid service.
   - Side effects: files written, messages sent, things installed.

   A skill found on disk but absent from the session skill list is installed but not active: say so.
   If five candidates do not fit, stop reading and go to *When nothing fits*.

4. **Give the verdict** in the format below.

5. **Use it.** If the user asked for the task to be done and one skill clearly fits, name the pick
   in one line, invoke it with the Skill tool, and carry on with the task. If they only asked
   which skill to use, stop at the verdict.

## Verdict format

```
**Use: `resume-tailor`**, fits fully
Why: tailors an existing resume to one job posting, which is the task.
Needs: your current resume and the job ad.
Does not cover: the cover letter (run `cover-letter-generator` after).
Start: /resume-tailor

Passed over
- `resume-architect`, rebuilds from the full career history; more than this task needs.
- `resume-ats-optimizer`, keyword pass only, no tailoring.
```

- Fit is one of: *fits fully*, *fits partly*, *no fit*.
- One recommendation. At most three passed-over skills, each with the reason in one line.
- When the task needs several skills, give them as an ordered chain.
- The same skill under two names (personal copy and plugin copy): name one, mention the twin.
- "No skill needed, this is a plain request" is a valid verdict. Say it when true.

## When nothing fits

Look for a new skill, in this order, and stop at the first source that yields a good candidate:

1. `python scripts/skill_inventory.py <keywords> --available` for marketplaces and the plugin
   directory already cached on this machine.
2. Account catalog tools, where they exist: `SearchSkills`, `SearchPlugins`.
3. Web search.

Read a candidate before recommending it, and install nothing without the user's explicit yes.
Vetting checklist, presentation format and install commands:
[references/finding-new-skills.md](references/finding-new-skills.md).

If the search finds nothing either, say so plainly and offer two ways forward: do the task
without a skill, or write a new one (`write-a-skill` or `skill-creator`, whichever is installed).

## Rules

- Never recommend on the name or description alone. Read the skill first.
- Never dump the full skill list on the user. Shortlist, then decide.
- A partial fit is reported as partial, with what is missing.
- Bad:  "You could try resume-tailor, resume-architect or resume-ats-optimizer."
- Good: "Use `resume-tailor`. The other two rebuild or only keyword-scan."
