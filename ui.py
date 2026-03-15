"""
Compact trainer window: menu bar, combo score, horizontal input history.
"""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import TYPE_CHECKING, Callable

from patterns import ROUTINES, DEFAULT_ROUTINE

if TYPE_CHECKING:
    from controller import ControllerReader
    from history import InputHistory
    from scoring import Scoring

DIRECTION_SYMBOLS = {
    "b": "\u2190",   # ←
    "f": "\u2192",   # →
    "u": "\u2191",   # ↑
    "d": "\u2193",   # ↓
    "db": "\u2199",  # ↙
    "df": "\u2198",  # ↘
    "ub": "\u2196",  # ↖
    "uf": "\u2197",  # ↗
    "n": "\u00b7",   # ·
}
REFRESH_INTERVAL_MS = 66  # ~15 FPS
SYM_FONT_SPEC = ("Segoe UI", 11)
NUM_FONT_SPEC = ("Consolas", 8)
COLUMN_GAP = 4
COMBO_FONT = ("Segoe UI", 14, "bold")
TITLE_BASE = "KBD / Wavu Trainer"


class TrainerWindow:
    def __init__(
        self,
        root: tk.Tk,
        history: InputHistory,
        scoring: Scoring,
        controller: ControllerReader,
        on_reset: Callable[[], None],
        on_switch: Callable[[str], None],
        on_side: Callable[[bool], None],
    ) -> None:
        self._root = root
        self._history = history
        self._scoring = scoring
        self._controller = controller
        self._on_reset = on_reset
        self._on_switch = on_switch
        self._on_side = on_side

        root.title(TITLE_BASE)
        root.resizable(True, True)
        root.attributes("-topmost", True)
        root.minsize(260, 100)

        # --- Menu bar ---
        menubar = tk.Menu(root)
        root.config(menu=menubar)

        options_menu = tk.Menu(menubar, tearoff=False)
        options_menu.add_command(label="Reset", command=self._on_reset)
        options_menu.add_separator()
        self._topmost_var = tk.BooleanVar(value=True)
        options_menu.add_checkbutton(label="Pin to top", variable=self._topmost_var,
                                     command=self._on_pin_toggle)
        menubar.add_cascade(label="Options", menu=options_menu)

        routine_menu = tk.Menu(menubar, tearoff=False)
        self._routine_var = tk.StringVar(value=DEFAULT_ROUTINE)
        for name in ROUTINES:
            routine_menu.add_radiobutton(label=name, variable=self._routine_var,
                                         value=name, command=self._on_routine_change)
        menubar.add_cascade(label="Routine", menu=routine_menu)

        side_menu = tk.Menu(menubar, tearoff=False)
        self._side_var = tk.StringVar(value="P1")
        side_menu.add_radiobutton(label="P1 (face right)", variable=self._side_var,
                                  value="P1", command=self._on_side_change)
        side_menu.add_radiobutton(label="P2 (face left)", variable=self._side_var,
                                  value="P2", command=self._on_side_change)
        menubar.add_cascade(label="Side", menu=side_menu)

        # --- Combo label ---
        self._combo_label = tk.Label(root, text="", font=COMBO_FONT)
        self._combo_label.pack(fill=tk.X, pady=(2, 0))

        # --- Horizontal input history canvas ---
        self._canvas = tk.Canvas(root, height=40, highlightthickness=0)
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._sym_font = tkfont.Font(family=SYM_FONT_SPEC[0], size=SYM_FONT_SPEC[1])
        self._num_font = tkfont.Font(family=NUM_FONT_SPEC[0], size=NUM_FONT_SPEC[1])

        self._start_refresh_loop()

    def _on_pin_toggle(self) -> None:
        self._root.attributes("-topmost", self._topmost_var.get())

    def _on_routine_change(self) -> None:
        self._on_switch(self._routine_var.get())

    def _on_side_change(self) -> None:
        self._on_side(self._side_var.get() == "P2")

    def _start_refresh_loop(self) -> None:
        self._refresh_ui()
        self._root.after(REFRESH_INTERVAL_MS, self._start_refresh_loop)

    def _refresh_ui(self) -> None:
        # --- Title bar connection status ---
        status = "Connected" if self._controller.connected else "Disconnected"
        self._root.title(f"{TITLE_BASE} \u2014 {status}")

        # --- Combo ---
        routine = self._scoring.routine
        cur = self._scoring.current()
        best = self._scoring.high()
        self._combo_label.configure(text=f"{routine}: {cur} (best {best})")

        # --- Horizontal history (symbol on top, frame count below) ---
        self._canvas.delete("all")
        segs = self._history.segments_list()
        cur_dir, cur_frames = self._history.current_segment()
        entries: list[tuple[str, int]] = list(segs)
        if cur_dir is not None and cur_frames > 0:
            entries.append((cur_dir, cur_frames))

        canvas_w = self._canvas.winfo_width()
        canvas_h = self._canvas.winfo_height()
        sym_y = canvas_h // 2 - 7
        num_y = canvas_h // 2 + 9
        x = canvas_w - 4
        for d, n in reversed(entries):
            sym = DIRECTION_SYMBOLS.get(d, d)
            num_str = str(n)
            col_w = max(self._sym_font.measure(sym), self._num_font.measure(num_str))
            cx = x - col_w // 2
            self._canvas.create_text(cx, sym_y, text=sym, font=self._sym_font)
            self._canvas.create_text(cx, num_y, text=num_str, font=self._num_font)
            x -= col_w + COLUMN_GAP
            if x < 0:
                break
