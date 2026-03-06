# Branch Protection Policy (Production)

Apply to branch: `main`

## Required settings
1. Require pull request before merging
2. Require at least 1 approving review
3. Dismiss stale approvals when new commits are pushed
4. Require status checks to pass before merging
5. Restrict who can push to matching branches
6. Do not allow force pushes
7. Do not allow deletions

## Required status checks (recommended)
- `phase5-test-gate / gate (soft)`
- `phase5-test-gate / gate (strict)`

## Notes
- `CODEOWNERS` is added to support ownership-based review requirements.
- Repository admin must enforce branch rule in GitHub settings.
