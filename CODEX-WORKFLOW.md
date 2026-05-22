# CODEX-WORKFLOW.md

## Start Codex

From the repository root:

    source ~/venvs/tracking/bin/activate
    codex --sandbox workspace-write --ask-for-approval on-request --search

Codex should use:

- `AGENTS.md` for project rules
- `MIGRATION-PLAN.md` for milestones and progress

---

## Milestone cycle

### 1. Ask Codex to plan

Prompt:

    Read AGENTS.md and MIGRATION-PLAN.md. Inspect git status.

    Do not edit code yet.

    Identify the Current next milestone in MIGRATION-PLAN.md.

    Propose a concrete implementation plan for that milestone only.

    Keep the plan narrow. Do not broaden scope. Stop after proposing the plan and wait for my approval.

---

### 2. Approve and implement

After reviewing the plan, prompt:

    Proceed with the approved milestone plan only.

    Implement only this milestone. Do not broaden scope.

    Run the relevant validation commands.

    Update MIGRATION-PLAN.md:
    - set this milestone's Status to Ready for review
    - add a short Review note with files changed, commands run, test results, and remaining risks
    - do not mark the milestone Done
    - do not advance Current next milestone

    Summarize the diff and stop.

---

### 3. Human review

Run:

    git status
    git diff
    python -m pytest

For dashboard/browser milestones, also run the relevant app or Playwright command.

---

### 4. If changes are needed

Prompt:

    The milestone is not accepted yet.

    Fix only these review issues:

    1. ...
    2. ...

    Do not broaden scope. Do not mark the milestone Done. Do not advance Current next milestone.

---

### 5. If accepted

Prompt:

    Make no code changes.

    Update MIGRATION-PLAN.md only:
    - change this milestone's Status to Done
    - add a short Accepted note if useful
    - advance Current next milestone to the next incomplete milestone

Then commit:

    git add .
    git commit -m "Complete milestone N: short description"

Repeat from step 1.