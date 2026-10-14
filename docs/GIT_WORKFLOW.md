# GIT WORKFLOW (4 people, 1 repo, fast)

Repo: https://github.com/aayushkkhandelwal/kestral.git   Default branch: `main`

## Branches
`<name>/<task-id>-<short>` e.g. `ayush/T1-detector-gpu`, `anshika/T2-quality-v2`, `aditi/T3-linking`, `charvi/U2-transactions-page`.
One task = one branch = one PR. Keep branches short-lived (merge within a few hours).

## Ownership (to avoid conflicts)
| Area | Owner |
|---|---|
| `backend/services/person_detector.py`, `face_detector.py`, `video_processor.py`, `backend/routers/search.py`, `services/embeddings.py` | Ayush |
| `backend/services/face_quality.py`, `best_frame.py`, `backend/tests/test_quality*.py`, `eval/` | Anshika |
| `backend/routers/transactions.py`, `rois.py`, `audit.py`, `services/linking.py`, `db.py` | Aditi |
| `frontend/**` | Charvi |
| `backend/main.py`, `backend/config.py`, `docs/**`, `.gitignore` | Shared. Small edits only, pull first. Anshika merges |
`config.py` has one section per owner (`# --- AYUSH ---`, etc.). Only edit your own section.

## Loop (the AI should do this after each verified step)
```
git fetch origin
git status                          # confirm branch, not main
git add <specific files>
git diff --staged                   # no weights, videos, results, secrets
git commit -m "T2.3: pose proxy from 5 landmarks"
git pull --rebase origin main
git push -u origin <branch>
```
Push at least every 30 to 45 minutes of work, even if unfinished (prefix commit with `WIP`).

## Pull requests
- Open PR to `main`, title `<TASK-ID>: <name>`, body = what changed, how you tested (command + output), any contract additions.
- Anshika merges after running the backend (`uvicorn main:app --port 8000` from `backend/`) and loading the UI. Use "Squash and merge".
- After a merge, everyone: `git checkout main && git pull`, then `git checkout <branch> && git rebase main`.

## Conflicts
Stop. Show the conflicted files. The file's OWNER resolves it. Never accept "theirs/ours" wholesale without reading. Never force-push.

## Never commit
`*.pt`, `*.onnx` (models), videos, `backend/uploads/`, `backend/results/`, `node_modules/`, `.venv/`, `.env`, tokens/passwords. Models are fetched with `backend/scripts/download_models.py` (task T0.2).

## Antigravity terminal permissions
Allow: `git status`, `git diff`, `git add`, `git commit`, `git pull --rebase`, `git push` (to non-main branches), `git fetch`, `git checkout`/`switch`.
Deny or require approval: `git push --force`, `git reset --hard`, `git clean`, `git push origin main`, deleting branches. (Setting names vary by Antigravity version; check yours.)
