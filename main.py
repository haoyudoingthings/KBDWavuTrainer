"""
KBD / Wavu Trainer - Entry point.
Starts controller polling, input history, pattern matcher, scoring, and GUI.
"""
import tkinter as tk
from controller import ControllerReader
from history import InputHistory
from patterns import PatternMatcher
from scoring import Scoring
from ui import TrainerWindow


def main() -> None:
    root = tk.Tk()
    history = InputHistory(max_segments=120)  # ~2 sec at 60 fps if 1 segment/sec
    scoring = Scoring()
    matcher = PatternMatcher(history, scoring)
    controller = ControllerReader()

    app = TrainerWindow(root, history, scoring, matcher, controller)
    controller.start_polling(app.on_poll_tick)

    root.protocol("WM_DELETE_WINDOW", lambda: shutdown(root, controller))
    root.mainloop()


def shutdown(root: tk.Tk, controller: ControllerReader) -> None:
    controller.stop_polling()
    root.destroy()


if __name__ == "__main__":
    main()
