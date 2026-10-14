# KESTRAL x SKIT001: Start Here (Team Quad Core)

Repo: https://github.com/aayushkkhandelwal/kestral.git  (branch `main`)
Stack in the repo today: FastAPI + OpenCV YuNet + YOLOv8n/ByteTrack (backend), React 19 + Vite (frontend).

## Where files go
```
kestral/
  AGENTS.md              <- repo ROOT (Antigravity reads rules from here; also copy into its Rules setting if your version needs it)
  docs/
    PROJECT_BRIEF.md  CONTRACTS.md  TASKS.md  GIT_WORKFLOW.md
    TECH_NOTES.md     CONTEXT_LOG.md  PROMPTS.md
```
Commit them on a branch `docs/guardrails` and merge first, so everyone gets the same files.

## Team (PROPOSED. Change in docs/CONTEXT_LOG.md if you disagree)
| Person | Owns | Branch prefix |
|---|---|---|
| Ayush | Backend vision: detector, tracker, GPU, face detect, embeddings + face search API | `ayush/` |
| Anshika | Quality scoring v2, best-frame/runner-ups, evaluation set, pitch. Integrator: merges PRs to `main` | `anshika/` |
| Aditi | Transactions, ROI, linking, audit log + demo login (backend) | `aditi/` |
| Charvi | All of `frontend/` | `charvi/` |

## One-time setup per person (15 min)
1. Ayush adds Anshika, Charvi, Aditi as repo collaborators (GitHub > Settings > Collaborators). Without this nobody else can push.
2. Each person: `git clone https://github.com/aayushkkhandelwal/kestral.git`, then log in to GitHub on their machine (GitHub CLI `gh auth login` or the Git credential manager). NEVER paste tokens or passwords into the AI chat or into files.
3. In Antigravity, open the cloned folder as the workspace. In its terminal/command permission settings (names vary by version), allow `git status/diff/add/commit/pull/push` and require approval for anything destructive. See docs/GIT_WORKFLOW.md.
4. Backend: create venv, `pip install -r backend/requirements.txt`. Frontend: `cd frontend && npm install`.
5. Every AI session starts with the Session Start Prompt in docs/PROMPTS.md.

## Golden rules
- Never work on `main`. One branch per task: `<name>/<task-id>-<short-name>`.
- The AI commits and pushes to YOUR branch after every verified step. Anshika merges to `main`.
- Contracts in docs/CONTRACTS.md are additive-only. Charvi builds against them from the start, using mock data.
- Not done until it was RUN and the output seen.
- Code freeze 3 hours before the deadline.
