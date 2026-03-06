"""
Trainer window: input history with frame counts, KBD/wavu streaks, combo-style score, pin-to-top.
Optional: show directions as Tekken-style icons if assets are present.
"""
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from controller import ControllerReader
    from history import InputHistory
    from patterns import PatternMatcher
    from scoring import Scoring

# Display last N segments in history
HISTORY_DISPLAY_LIMIT = 20
DIRECTIONS = ("b", "f", "u", "d", "db", "df", "ub", "uf")
# Unicode arrows as fallback when no icon assets (readable approximation of notation)
DIRECTION_SYMBOLS = {
    "b": "\u2190",   # ←
    "f": "\u2192",   # →
    "u": "\u2191",   # ↑
    "d": "\u2193",   # ↓
    "db": "\u2198",  # ↘ (down-right, used for db)
    "df": "\u2199",  # ↙ (down-left, used for df)
    "ub": "\u2196",  # ↖
    "uf": "\u2197",  # ↗
    "n": "\u00b7",   # · (neutral / no input)
}
REFRESH_INTERVAL_MS = 66  # ~15 FPS for history display to avoid flashing
ICON_SIZE = 24
ASSETS_DIR = Path(__file__).resolve().parent / "assets"


class TrainerWindow:
    def __init__(
        self,
        root: tk.Tk,
        history: "InputHistory",
        scoring: "Scoring",
        matcher: "PatternMatcher",
        controller: "ControllerReader",
    ) -> None:
        self._root = root
        self._history = history
        self._scoring = scoring
        self._matcher = matcher
        self._controller = controller
        self._icons: dict[str, tk.PhotoImage] = {}
        self._load_icons()

        root.title("KBD / Wavu Trainer")
        root.resizable(True, True)
        root.attributes("-topmost", True)
        root.minsize(280, 320)

        main = ttk.Frame(root, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        # Pin to top
        self._topmost_var = tk.BooleanVar(value=True)
        pin_cb = ttk.Checkbutton(main, text="Pin to top", variable=self._topmost_var, command=self._on_pin_toggle)
        pin_cb.pack(anchor=tk.W)

        # Combo / streak display (DMC-style)
        combo_frame = ttk.LabelFrame(main, text="Combo", padding=4)
        combo_frame.pack(fill=tk.X, pady=(8, 4))
        self._combo_label = ttk.Label(combo_frame, text="0", font=("Segoe UI", 24, "bold"))
        self._combo_label.pack()

        # Stats: KBD and Wavu current (best) + per minute
        stats_frame = ttk.LabelFrame(main, text="Streaks", padding=4)
        stats_frame.pack(fill=tk.X, pady=4)
        self._kbd_label = ttk.Label(stats_frame, text="KBD: 0 (best 0)  —  0/min")
        self._kbd_label.pack(anchor=tk.W)
        self._wavu_label = ttk.Label(stats_frame, text="Wavu: 0 (best 0)  —  0/min")
        self._wavu_label.pack(anchor=tk.W)

        # Input history (scrollable list: icon or symbol + frames)
        hist_frame = ttk.LabelFrame(main, text="Input history (direction, frames)", padding=4)
        hist_frame.pack(fill=tk.BOTH, expand=True, pady=4)
        self._history_canvas = tk.Canvas(hist_frame, highlightthickness=0)
        self._history_inner = ttk.Frame(self._history_canvas)
        self._history_win_id = self._history_canvas.create_window((0, 0), window=self._history_inner, anchor=tk.NW)
        self._history_inner.bind("<Configure>", lambda e: self._history_canvas.configure(scrollregion=self._history_canvas.bbox("all")))
        self._history_canvas.bind("<Configure>", self._on_canvas_configure)
        scrollbar = ttk.Scrollbar(hist_frame, orient=tk.VERTICAL, command=self._history_canvas.yview)
        self._history_canvas.configure(yscrollcommand=scrollbar.set)
        self._history_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._history_row_widgets: list[tk.Widget] = []
        self._refresh_after_id: Optional[str] = None

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
                # Scale down if larger than ICON_SIZE
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

    def on_poll_tick(self) -> None:
        """Called from controller poll thread: read direction, update history and matcher. UI refresh is throttled separately."""
        direction = self._controller.get_current_direction()
        self._history.tick(direction)
        self._matcher.update()
        self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        """Schedule a single UI refresh if none pending (throttles to ~15 FPS)."""
        if self._refresh_after_id is not None:
            return
        self._refresh_after_id = self._root.after(REFRESH_INTERVAL_MS, self._do_refresh)

    def _do_refresh(self) -> None:
        self._refresh_after_id = None
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        segs = self._history.segments_list()
        display = segs[-HISTORY_DISPLAY_LIMIT:] if len(segs) > HISTORY_DISPLAY_LIMIT else segs
        cur_dir, cur_frames = self._history.current_segment()
        rows: list[tuple[str, int]] = [(d, n) for d, n in display]
        if cur_dir is not None and cur_frames > 0:
            rows.append((cur_dir, cur_frames))  # includes "n" for neutral

        # Rebuild history rows: direction (icon or symbol/text) + frames
        for w in self._history_row_widgets:
            w.destroy()
        self._history_row_widgets.clear()
        if not rows:
            no_input = ttk.Label(self._history_inner, text="No input yet.")
            no_input.pack(anchor=tk.W)
            self._history_row_widgets.append(no_input)
        else:
            for d, n in rows:
                row_frame = ttk.Frame(self._history_inner)
                if d in self._icons:
                    dir_label = ttk.Label(row_frame, image=self._icons[d])
                else:
                    sym = DIRECTION_SYMBOLS.get(d, d)
                    dir_label = ttk.Label(row_frame, text=sym, font=("Segoe UI", 12), width=2)
                frame_label = ttk.Label(row_frame, text=str(n), font=("Consolas", 10))
                dir_label.pack(side=tk.LEFT, padx=(0, 4))
                frame_label.pack(side=tk.LEFT)
                row_frame.pack(anchor=tk.W)
                self._history_row_widgets.append(row_frame)

        # Combo: show max of current KBD and Wavu streak
        combo = max(self._scoring.kbd_current(), self._scoring.wavu_current())
        self._combo_label.configure(text=str(combo))

        self._kbd_label.configure(
            text=f"KBD: {self._scoring.kbd_current()} (best {self._scoring.kbd_high})  —  {self._scoring.kbd_per_minute():.1f}/min"
        )
        self._wavu_label.configure(
            text=f"Wavu: {self._scoring.wavu_current()} (best {self._scoring.wavu_high})  —  {self._scoring.wavu_per_minute():.1f}/min"
        )
