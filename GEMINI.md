# Workspace Guidelines

## Git Workflow
- **Automatic Git Synchronization**:
  - Always stage, commit, and push changes to the remote git repository after completing and verifying any task, bug fix, or feature.
  - Verification check: ensure the project builds with 0 errors (e.g. `dotnet build`) before pushing.
  - Steps:
    1. `git add .` (or specific modified/created files).
    2. `git commit -m "descriptive message in English"`.
    3. `git push origin main` (or `git push`).
