# Session State

## Project

- Repo: `win11-recorder`
- Path: `/home/ruby/win11-recorder`
- Main branch: `main`

## Current Status

- Desktop audio recorder app for Windows 11 written in Python.
- UI language has been switched to English.
- Window title is now `Litle Recoder`.
- File picker and output folder picker were changed to non-native Qt dialogs to avoid UI freezes on Windows.
- Recording flow was improved to surface FFmpeg errors instead of failing silently.
- Recorder state is now pushed back to the UI so button state stays correct after failures.

## Recent Work

- Commit created locally: `a97161e` - `Fix file pickers and recording errors`
- Push to GitHub was attempted but failed because Git credentials were not available in the shell at the time.

## Known User Requirements

- Keep the UI in English.
- Keep the title spelled exactly as `Litle Recoder`.
- When possible, publish changes to GitHub after the user confirms.
- The user said a GitHub token exists in environment variables.

## Known Risks

- Real recording behavior still needs validation on an actual Windows 11 machine with working audio devices and FFmpeg installed.
- System Audio recording depends on loopback/WASAPI availability on the target machine.

## Next Suggested Steps

1. Detect which GitHub token environment variable is available in the shell.
2. Configure authenticated push for the current session.
3. Push `main` to `origin`.
4. Run manual validation on Windows:
   - browse for `ffmpeg.exe`
   - browse for output folder
   - start microphone recording
   - start system audio recording
5. If recording still fails, inspect the new log message shown in the app.
