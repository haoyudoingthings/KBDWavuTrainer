# KBDWavuTrainer

A simple app that lets you practice KBD / wavu mindlessly

## Project

Lightweight Windows overlay to practice Korean Back Dash (KBD) and wave dash (wavu) while doing something else (e.g. watching Netflix). The app reads your gamepad via XInput, shows input history with duration in frames (60 FPS), detects when your input sequence matches KBD or wavu, and tracks current and highest consecutive streaks plus frequency. The window can be pinned on top.

## Architecture

- **60 FPS poll** → read XInput state → **map** to 8 directions (b, f, u, d, db, df, ub, uf) or neutral.
- **Input history**: Bounded list of segments `(direction, duration_frames)`. When direction changes, the previous segment is finalized and a new one starts.
- **Pattern matcher**: Sliding window over the tail of history; matches KBD (e.g. b, db, b, db, …) and wavu (e.g. d, df, d, df, …). On match, updates streaks and frequency.
- **UI**: One small window: input history with frame counts, current/highest streak per technique, combo-style score, and a "Pin to top" toggle.

## How to run

1. Install dependencies: `conda env create -f environment.yml`  
   (XInput-Python is Windows-only; the app runs without it but will not read controller input.)
2. Use an XInput-compatible controller (Xbox or generic "Xbox mode" gamepad). DualShock users can use DS4Windows to expose the pad as XInput.
3. Run the app: `python main.py`

## Building a standalone executable

You can package the app into a single `.exe` that runs on any Windows 10+ machine without Python installed.

1. Install build dependencies: `pip install -r requirements.txt`
2. Run the build script: `build.bat`
3. The executable is created at `dist/KBDWavuTrainer.exe`.

High scores (`scores.json`) are saved next to the `.exe` at runtime.
