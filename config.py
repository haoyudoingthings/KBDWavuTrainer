"""
Centralized configuration for KBD / Wavu Trainer.
Edit values here to customize behavior without touching other files.
"""

# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------
POLL_FPS = 60                   # Controller polling rate (frames per second)
GAME_LOOP_MS = 16               # Main loop interval in ms (~60 FPS)
REFRESH_INTERVAL_MS = 66        # UI refresh interval in ms (~15 FPS)

# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------
STICK_THRESHOLD = 0.35          # Analog stick deadzone (0.0–1.0)
DEFAULT_CONTROLLER_SLOT = 0     # XInput slot index (0–3)

# ---------------------------------------------------------------------------
# Input history
# ---------------------------------------------------------------------------
MAX_SEGMENTS = 0                # Max direction segments kept in history (0 = unlimited)
DISPLAY_MAX_FRAMES = 99        # Cap the frame count shown in the history display (0 = no cap)

# ---------------------------------------------------------------------------
# Routines (pattern sequences)
# ---------------------------------------------------------------------------
ROUTINES: dict[str, tuple[str, ...]] = {
    "KBD":  ('b', 'n', 'b', 'db'),
    "Wavu": ('f', 'n', 'd', 'df', 'n'),
}
DEFAULT_ROUTINE = "KBD"

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
FREQUENCY_WINDOW_SEC = 60.0     # Rolling window for per-minute calculation
SCORES_FILENAME = "scores.json" # High-score file (relative to project root)

# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------
WINDOW_TITLE = "KBD / Wavu Trainer"
WINDOW_MIN_W = 260              # Minimum window width
WINDOW_MIN_H = 100              # Minimum window height

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
COMBO_FONT = ("Segoe UI", 14, "bold")
HISTORY_SYM_FONT = ("Segoe UI", 11)
HISTORY_NUM_FONT = ("Consolas", 8)

# ---------------------------------------------------------------------------
# Input history display
# ---------------------------------------------------------------------------
HISTORY_CANVAS_HEIGHT = 40      # Pixel height of the history bar
HISTORY_COLUMN_GAP = 4          # Horizontal gap between entries (px)
HISTORY_RIGHT_MARGIN = 4        # Right-edge padding (px)
HISTORY_SYM_OFFSET = -7         # Symbol Y offset from canvas center (px)
HISTORY_NUM_OFFSET = 9          # Frame-count Y offset from canvas center (px)

# ---------------------------------------------------------------------------
# Direction display symbols (Unicode)
# ---------------------------------------------------------------------------
DIRECTION_SYMBOLS = {
    "b":  "\u2190",   # ←
    "f":  "\u2192",   # →
    "u":  "\u2191",   # ↑
    "d":  "\u2193",   # ↓
    "db": "\u2199",   # ↙
    "df": "\u2198",   # ↘
    "ub": "\u2196",   # ↖
    "uf": "\u2197",   # ↗
    "n":  "\u00b7",   # ·
}
