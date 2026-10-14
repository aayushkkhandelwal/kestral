# PROMPTS (copy-paste)

## A. Session Start Prompt (EVERY chat)
```
Read AGENTS.md, docs/PROJECT_BRIEF.md, docs/CONTRACTS.md, docs/CONTEXT_LOG.md, docs/GIT_WORKFLOW.md and my task in docs/TASKS.md.
I am <Ayush/Anshika/Aditi/Charvi>, task <ID>.
First run: git fetch origin && git branch --show-current && git status. If I am on main, create branch <name>/<ID>-<short> from an up-to-date main.
Reply in max 8 lines: my files, contract risk, what you cannot verify. No code until I say go.
```

## B. Verify-before-code
```
Before using <library or model>, inspect the INSTALLED version (pip show / help() / source or npm ls) and list the exact calls with signatures. Mark anything unconfirmed as UNVERIFIED. Write a 15-line smoke test and RUN it before the real code.
```

## C. Role kickoffs
Ayush:
```
Task <T0.x/T1.x/T4.x> from docs/TASKS.md. Keep existing JSON keys. Add new features as routers in backend/routers/. After each verified step: commit "<ID>: ...", pull --rebase origin main, push to my branch. Show me the commands you ran and their output.
```
Anshika:
```
Task <T2.x/T5.x>. Quality terms and constants live in backend/config.py (my section). Write the test that prints sub-scores for sharp/blurry/dark/side-angle crops first. Add new fields to results.json ONLY as listed in CONTRACTS section B. Commit and push after each verified step. I also review and merge PRs: when I say "review PR <n>", use prompt H.
```
Aditi:
```
Task <T3.x/T6.x>. Build linking as a pure function in backend/services/linking.py with unit tests on synthetic trajectories before any endpoint. Endpoints follow CONTRACTS section C exactly. Until T0.8 is merged, use a MOCK trajectory fixture and label it MOCK_.
```
Charvi:
```
Task <U1..U6>. Only edit frontend/. Use API_BASE_URL from src/config.js and axios as in the existing pages. Build against contract-valid mock data (src/mocks/MOCK_*.js) until the backend route is real. If you need a field that is not in CONTRACTS, add it to REQUESTS in docs/CONTEXT_LOG.md and stop. Run npm run lint and npm run build before each push and show the output. Keep the existing dark theme tokens in index.css.
```

## D. Debugging
```
Here is the exact error and the command that produced it: <paste>. Do not guess. List 3 likely causes ranked, plus the one command that confirms each. Run the cheapest check first.
```

## E. Anti-drift
```
Stop. Re-read AGENTS.md sections 2 to 4. Revert anything outside my task and my files. List what you changed vs what I asked.
```

## F. Context reset
```
We are losing context. Summarize in 10 lines: done and verified, stubbed/mocked, pushed (branch + last commit), next. I will start a new chat and paste it after the Session Start Prompt.
```

## G. Session End (paste the result into docs/CONTEXT_LOG.md, then commit and push)
```
Write the session log entry in the format of docs/CONTEXT_LOG.md: Done, Files touched, Verified by running (command + result), Not verified, Pushed (commit hash / PR), Next. Only things that happened this session. List new mocks and any REQUESTS.
```

## H. PR review (Anshika)
```
Review the diff of PR <n> / branch <name> against docs/CONTRACTS.md. List: renamed/removed/retyped fields, hard-coded constants that belong in config.py, unlabeled mocks, files outside the owner's area, committed weights/videos/results/secrets, and claims not backed by a test. Then give the commands to run it locally.
```

## I. Open the PR
```
Push my branch, then give me the PR title "<ID>: <name>" and a body with: what changed, how I tested (command + output), contract additions. If gh is installed and authenticated, open it; otherwise give me the compare URL steps.
```
