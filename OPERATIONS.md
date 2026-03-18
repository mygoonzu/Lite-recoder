# Operations

## Purpose

Operational notes for continuing work on `/home/ruby/win11-recorder` in a new session.

## Repo Basics

- Repo path: `/home/ruby/win11-recorder`
- Remote: `origin = https://github.com/mygoonzu/Lite-recoder.git`
- Primary branch: `main`

## Common Commands

Run the app:

```bash
python app.py
```

Check syntax:

```bash
python3 -m py_compile app.py recorder.py
```

Inspect Git status:

```bash
git status --short --branch
```

## Publishing Notes

- The user wants changes published to GitHub when requested.
- GitHub authentication may rely on a token stored in environment variables.
- Before pushing, check available env vars and use the existing token rather than assuming interactive login.
- If HTTPS push fails due to missing username/password, inspect environment-based auth options first.

## Working Conventions

- Do not change the app title away from `Litle Recoder` unless the user explicitly asks.
- Keep the visible UI language in English.
- Prefer concise commits with clear messages.
- Do not revert unrelated user changes in the repo.

## Validation Checklist

- `Browse...` for FFmpeg opens without freezing.
- `Browse...` for output folder opens without freezing.
- `Start` begins recording or shows a specific FFmpeg/device error.
- `Stop` returns the UI to idle state.
- Tray actions stay in sync with recorder state.
