# AGENT RULES for Kestral (read fully at the start of EVERY session)

Project: Kestral, for hackathon problem SKIT001 (AI-based face identification from ATM footage). Repo: https://github.com/aayushkkhandelwal/kestral.git
Team: Ayush (vision/backend), Anshika (quality/eval, integrator), Aditi (transactions/linking/audit), Charvi (frontend). The user tells you who they are in the Session Start Prompt.

## 1. Context load order
1. `AGENTS.md` (this file)  2. `docs/PROJECT_BRIEF.md`  3. `docs/CONTRACTS.md`  4. `docs/CONTEXT_LOG.md` (newest first)  5. `docs/TASKS.md` (only the user's current task)  6. `docs/TECH_NOTES.md` (only sections relevant to the task)  7. `docs/GIT_WORKFLOW.md`
Reply in max 8 lines: user's role, task ID, current branch, files you will touch, contract risk, what you cannot verify. Wait for "go".

## 2. Truthfulness (anti-hallucination)
- NEVER invent package names, function signatures, attributes, CLI flags, model names, file paths or URLs.
- Before using any library API: check the installed version (`pip show`, `npm ls`), inspect it (`python -c "help(...)"`) or read official docs/source. Unsure => write `UNVERIFIED:` and tell the user.
- NEVER say it works unless you ran it THIS session and can quote the output. For UI, say what you saw or that you could not run the browser.
- NEVER state accuracy/speed numbers that were not measured.
- No silent fakes: mock data lives in `backend/mocks/` or `frontend/src/mocks/`, is named `MOCK_*`, and is listed in CONTEXT_LOG "Mocks". Never ship a fabricated default (the old `78.4` average quality in `/api/stats` is exactly what NOT to do). Show `null`/"no data" instead.
- Model files: do not claim a download link works unless you fetched it. Prefer official sources (e.g. the model's official repo). Tell the user to check the license.
- If you do not know: say so and say how to find out.

## 3. Scope and ownership
- Edit only files your owner area covers (see TASKS.md "Ownership"). Do not touch other people's files; if you need a change there, write it under "REQUESTS" in CONTEXT_LOG and tell the user.
- `docs/CONTRACTS.md` is ADDITIVE ONLY: you may propose new fields/endpoints in CONTEXT_LOG, never rename/remove/retype existing ones (the React app depends on them).
- New backend features go in their own router file `backend/routers/<feature>.py` and services in `backend/services/`. `backend/main.py` is a conflict hotspot: only change it to include a router (one line) or for task T0.
- Do not refactor or restyle working code unless the task says so. No new heavy dependencies without asking. Pin versions you actually installed in `backend/requirements.txt`.
- Thresholds/weights go in `backend/config.py`, in your own section, never hard-coded in logic.
- Paths: use `os.path`/`pathlib` (team is on Windows per README). No hard-coded absolute paths.

## 4. Git (hand in hand with GitHub). Full detail in docs/GIT_WORKFLOW.md
- First command of every session: `git fetch origin && git branch --show-current && git status`. If on `main`, create/switch to the task branch. NEVER commit to `main`.
- After each verified step: stage SPECIFIC files (no blind `git add -A`), check `git diff --staged`, commit as `<TASK-ID>: <what>`, then `git pull --rebase origin main`, then `git push -u origin <branch>`.
- NEVER `push --force`, `reset --hard`, or rewrite pushed history. NEVER commit weights (`*.pt`, `*.onnx`), videos, `backend/uploads/`, `backend/results/`, `node_modules`, `.env`, tokens.
- On a merge/rebase conflict: STOP, show the conflicting files, do not auto-resolve other people's code.
- When a task's "Done when" passes: push, then tell the user to open a PR to `main` titled `<TASK-ID>: <name>` (or open it if `gh` is available and authenticated). Anshika merges.

## 5. Working style
- Plan first (max 10 lines) if the task touches more than 3 files or any contract. Otherwise proceed.
- Small steps: write, RUN, show output, commit, push.
- Each backend module gets a smoke test in `backend/tests/` (pytest style) or a runnable `__main__`. Existing `backend/test_camera.py` stays.
- GPU: check `torch.cuda.is_available()` and report the real value; never hard-code it.
- Concise output: file paths and diffs, not essays. When several approaches exist, give 2 to 3 options with a one-line verdict.

## 6. Context hygiene
- If the chat is long or you are unsure about a past decision, RE-READ `docs/CONTEXT_LOG.md` and `docs/CONTRACTS.md` instead of guessing.
- End every session with the Session End summary (docs/PROMPTS.md) and append it to `docs/CONTEXT_LOG.md` (commit and push it too).

## 7. Data and ethics
- Only synthetic, self-recorded (with consent) or properly licensed footage. No real ATM/CCTV footage of real people. No identifying real people: face search returns similarity among our own ingested data, and must be labelled "similarity, needs human review".
- Keep audit logging and role access in scope (investigator tool).
