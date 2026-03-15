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

GAME_LOOP_MS = 16  # ~60 FPS


def main() -> None:
    root = tk.Tk()
    history = InputHistory(max_segments=120)
    scoring = Scoring()
    matcher = PatternMatcher(history, scoring)
    controller = ControllerReader()

    def reset_session() -> None:
        history.clear()
        scoring.reset_session()
        matcher.reset()

    def switch_routine(name: str) -> None:
        history.clear()
        scoring.set_routine(name)
        matcher.set_routine(name)

    app = TrainerWindow(root, history, scoring, controller,
                        on_reset=reset_session, on_switch=switch_routine)
    controller.start_polling()

    def game_loop() -> None:
        for direction in controller.drain():
            history.tick(direction)
            matcher.update()
        root.after(GAME_LOOP_MS, game_loop)

    root.after(GAME_LOOP_MS, game_loop)
    root.protocol("WM_DELETE_WINDOW", lambda: shutdown(root, controller, scoring))
    root.mainloop()


def shutdown(root: tk.Tk, controller: ControllerReader, scoring: Scoring) -> None:
    controller.stop_polling()
    scoring.save()
    root.destroy()


if __name__ == "__main__":
    main()
