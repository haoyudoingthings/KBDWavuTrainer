"""
Trainer window: input history with frame counts, KBD/wavu streaks, combo-style score, pin-to-top.
Optional: show directions as Tekken-style icons if assets are present.
"""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from controller import ControllerReader
    from history import InputHistory
    from scoring import Scoring

HISTORY_DISPLAY_LIMIT = 20
DIRECTIONS = ("b", "f", "u", "d", "db", "df", "ub", "uf")
DIRECTION_SYMBOLS = {
    "b": "\u2190",   # ←
    "f": "\u2192",   # →
    "u": "\u2191",   # ↑
    "d": "\u2193",   # ↓
    "db": "\u2199",  # ↙ (down-left = down-back)
    "df": "\u2198",  # ↘ (down-right = down-forward)
    "ub": "\u2196",  # ↖
    "uf": "\u2197",  # ↗
    "n": "\u00b7",   # · (neutral / no input)
}
REFRESH_INTERVAL_MS = 66  # ~15 FPS
ICON_SIZE = 24
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

COLOR_CONNECTED = "#2e7d32"
COLOR_DISCONNECTED = "#b71c1c"


class TrainerWindow:
    def __init__(
        self,
        root: tk.Tk,
        history: InputHistory,
        scoring: Scoring,
        controller: ControllerReader,
        on_reset: Callable[[], None],
    ) -> None:
        self._root = root
        self._history = history
        self._scoring = scoring
        self._controller = controller
        self._on_reset = on_reset
        self._icons: dict[str, tk.PhotoImage] = {}
        self._load_icons()

        root.title("KBD / Wavu Trainer")
        root.resizable(True, True)
        root.attributes("-topmost", True)
        root.minsize(220, 280)

        main = ttk.Frame(root, padding=4)
        main.pack(fill=tk.BOTH, expand=True)

        # --- Controller status ---
        self._status_label = tk.Label(
            main, text="\u25cf Controller: Disconnected",
            font=("Segoe UI", 9), fg=COLOR_DISCONNECTED, anchor=tk.W,
        )
        self._status_label.pack(fill=tk.X, pady=(0, 2))

        # --- Controls row: pin + reset ---
        controls_frame = ttk.Frame(main)
        controls_frame.pack(fill=tk.X, pady=2)

        self._topmost_var = tk.BooleanVar(value=True)
        pin_cb = ttk.Checkbutton(controls_frame, text="Pin to top", variable=self._topmost_var, command=self._on_pin_toggle)
        pin_cb.pack(side=tk.LEFT)

        reset_btn = ttk.Button(controls_frame, text="Reset", width=6, command=self._on_reset_click)
        reset_btn.pack(side=tk.RIGHT)

        # --- Combo display ---
        combo_frame = ttk.LabelFrame(main, text="Combo", padding=2)
        combo_frame.pack(fill=tk.X, pady=2)
        self._combo_label = ttk.Label(combo_frame, text="0", font=("Segoe UI", 16, "bold"))
        self._combo_label.pack()

        # --- Streaks ---
        stats_frame = ttk.LabelFrame(main, text="Streaks", padding=2)
        stats_frame.pack(fill=tk.X, pady=2)
        self._kbd_label = ttk.Label(stats_frame, text="KBD: 0 (best 0)  \u2014  0/min", font=("Segoe UI", 9))
        self._kbd_label.pack(anchor=tk.W)
        self._wavu_label = ttk.Label(stats_frame, text="Wavu: 0 (best 0)  \u2014  0/min", font=("Segoe UI", 9))
        self._wavu_label.pack(anchor=tk.W)

        # --- Input history ---
        hist_frame = ttk.LabelFrame(main, text="Input history (direction, frames)", padding=2)
        hist_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        self._history_canvas = tk.Canvas(hist_frame, highlightthickness=0)
        self._history_inner = ttk.Frame(self._history_canvas)
        self._history_win_id = self._history_canvas.create_window((0, 0), window=self._history_inner, anchor=tk.NW)
        self._history_inner.bind("<Configure>", lambda e: self._history_canvas.configure(scrollregion=self._history_canvas.bbox("all")))
        self._history_canvas.bind("<Configure>", self._on_canvas_configure)
        scrollbar = ttk.Scrollbar(hist_frame, orient=tk.VERTICAL, command=self._history_canvas.yview)
        self._history_canvas.configure(yscrollcommand=scrollbar.set)
        self._history_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        max_rows = HISTORY_DISPLAY_LIMIT + 1
        self._row_widgets: list[tuple[ttk.Frame, ttk.Label, ttk.Label]] = []
        for _ in range(max_rows):
            row_frame = ttk.Frame(self._history_inner)
            dir_label = ttk.Label(row_frame, font=("Segoe UI", 10), width=2)
            frame_label = ttk.Label(row_frame, font=("Consolas", 9))
            dir_label.pack(side=tk.LEFT, padx=(0, 4))
            frame_label.pack(side=tk.LEFT)
            self._row_widgets.append((row_frame, dir_label, frame_label))
        self._no_input_label = ttk.Label(self._history_inner, text="No input yet.", font=("Segoe UI", 9))
        self._visible_rows = 0

        self._start_refresh_loop()

    def _load_icons(self) -> None:
        """Load direction icons from assets/ if present; keep references to avoid GC."""
        if not ASSETS_DIR.is_dir():
            return
        for d in DIRECTIONS:
            path = ASSETS_DIR / f"{d}.png"
            if not path.is_file():
                continue
            try:
                img = tk.PhotoImage(file=str(path))
                w, h = img.width(), img.height()
                if w > ICON_SIZE or h > ICON_SIZE:
                    img = img.subsample(max(1, w // ICON_SIZE), max(1, h // ICON_SIZE))
                self._icons[d] = img
            except (tk.TclError, OSError):
                pass

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self._history_canvas.itemconfigure(self._history_win_id, width=event.width)

    def _on_pin_toggle(self) -> None:
        self._root.attributes("-topmost", self._topmost_var.get())

    def _on_reset_click(self) -> None:
        self._on_reset()

    def _start_refresh_loop(self) -> None:
        """Self-scheduling UI refresh at ~15 FPS."""
        self._refresh_ui()
        self._root.after(REFRESH_INTERVAL_MS, self._start_refresh_loop)

    def _refresh_ui(self) -> None:
        # --- Connection status ---
        if self._controller.connected:
            self._status_label.configure(text="\u25cf Controller: Connected", fg=COLOR_CONNECTED)
        else:
            self._status_label.configure(text="\u25cf Controller: Disconnected", fg=COLOR_DISCONNECTED)

        # --- Input history rows ---
        segs = self._history.segments_list()
        display = segs[-HISTORY_DISPLAY_LIMIT:] if len(segs) > HISTORY_DISPLAY_LIMIT else segs
        cur_dir, cur_frames = self._history.current_segment()
        rows: list[tuple[str, int]] = list(display)
        if cur_dir is not None and cur_frames > 0:
            rows.append((cur_dir, cur_frames))

        if not rows:
            for i in range(self._visible_rows):
                self._row_widgets[i][0].grid_forget()
            self._visible_rows = 0
            self._no_input_label.grid(row=0, sticky=tk.W)
        else:
            self._no_input_label.grid_forget()
            for idx, (d, n) in enumerate(rows):
                row_frame, dir_label, frame_label = self._row_widgets[idx]
                if d in self._icons:
                    dir_label.configure(image=self._icons[d], text="")
                else:
                    sym = DIRECTION_SYMBOLS.get(d, d)
                    dir_label.configure(image="", text=sym)
                frame_label.configure(text=str(n))
                if idx >= self._visible_rows:
                    row_frame.grid(row=idx, sticky=tk.W)
            for i in range(len(rows), self._visible_rows):
                self._row_widgets[i][0].grid_forget()
            self._visible_rows = len(rows)

        # --- Combo & streaks ---
        combo = max(self._scoring.kbd_current(), self._scoring.wavu_current())
        self._combo_label.configure(text=str(combo))

        self._kbd_label.configure(
            text=f"KBD: {self._scoring.kbd_current()} (best {self._scoring.kbd_high()})  \u2014  {self._scoring.kbd_per_minute():.1f}/min"
        )
        self._wavu_label.configure(
            text=f"Wavu: {self._scoring.wavu_current()} (best {self._scoring.wavu_high()})  \u2014  {self._scoring.wavu_per_minute():.1f}/min"
        )
