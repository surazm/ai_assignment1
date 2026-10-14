"""Launch the TXT-based Futoshiki GUI with Backtracking and AC-3.

Run THIS file in Spyder (F5). All other modules must be in the same folder.
"""

from pathlib import Path
from tkinter import filedialog, messagebox
import math
from queue import Empty, Queue
from threading import Thread

from gui import create_gui, create_grid
from game_inputfile import display_game_input
from puzzle_loader import load_puzzle, PuzzleFileError
from backtracking import solve_backtracking
from ac3_solver import solve_ac3


def main():
    (
        root, grid_frame, grid_info_label, status_label,
        load_button, solve_button, reset_button,
        runtime_label, nodes_label, timeout_var, ac3_button, comparison_label,
    ) = create_gui()

    current_puzzle = None
    cells = None
    solving = False
    results_queue = Queue()
    results_history = {}  # Metrics for both algorithms on the SAME loaded puzzle.

    def update_comparison():
        lines = ["Comparison (same TXT puzzle):"]
        for algorithm in ("Backtracking", "AC-3 + MRV/Degree/LCV"):
            result = results_history.get(algorithm)
            if result is None:
                lines.append(f"{algorithm}: not run")
            else:
                lines.append(
                    f"{algorithm}: {result.status} | "
                    f"{result.runtime_seconds:.6f} s | "
                    f"{result.nodes_explored} nodes"
                )
        comparison_label.config(text="\n".join(lines))

    def set_board_values(grid=None):
        """Restore givens if grid=None, otherwise show the solved grid."""
        if current_puzzle is None or cells is None:
            return
        size = current_puzzle["size"]
        for r in range(size):
            for c in range(size):
                cell = cells[r][c]
                cell.config(state="normal", bg="white")
                cell.delete(0, "end")
                if (r, c) in current_puzzle["givens"]:
                    value = current_puzzle["givens"][(r, c)]
                    cell.insert(0, str(value))
                    cell.config(state="readonly", readonlybackground="#DCEBFA")
                elif grid is not None:
                    cell.insert(0, str(grid[r][c]))
                    cell.config(state="readonly", readonlybackground="#E5F3E7")
                # Unfilled, non-given cells remain editable.

    def load_txt():
        nonlocal current_puzzle, cells
        if solving:
            return
        path = filedialog.askopenfilename(
            parent=root, title="Open Futoshiki TXT Puzzle",
            filetypes=[("TXT files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        # Validate BEFORE touching the displayed board.
        try:
            puzzle = load_puzzle(path)
        except PuzzleFileError as error:
            messagebox.showerror(
                "Invalid Puzzle File", f"File: {Path(path).name}\n\n{error}",
                parent=root,
            )
            status_label.config(text="Status: File rejected — previous puzzle unchanged")
            return

        # Nothing random is generated: TXT supplies size, givens and arrows.
        new_cells = create_grid(grid_frame, puzzle["size"])
        display_game_input(grid_frame, new_cells, puzzle)
        cells = new_cells
        current_puzzle = puzzle
        grid_info_label.config(
            text=f"Grid: {puzzle['size']} × {puzzle['size']} | File: {Path(path).name}"
        )
        status_label.config(text="Status: Puzzle loaded — ready to solve")
        runtime_label.config(text="Runtime: --")
        nodes_label.config(text="Nodes explored: --")
        solve_button.config(state="normal")
        ac3_button.config(state="normal")
        reset_button.config(state="normal")
        results_history.clear()
        update_comparison()

    def reset_puzzle():
        if current_puzzle is None or solving:
            return
        set_board_values()
        status_label.config(text="Status: Puzzle reset — ready to solve")
        runtime_label.config(text="Runtime: --")
        nodes_label.config(text="Nodes explored: --")

    def solve_puzzle(algorithm):
        nonlocal solving
        if current_puzzle is None or solving:
            return
        try:
            seconds = float(timeout_var.get().strip())
            if not math.isfinite(seconds) or seconds <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Timeout", "Enter a positive number of seconds, e.g. 10.",
                parent=root,
            )
            return

        solving = True
        # Search starts from TXT givens, not manually entered values.
        set_board_values()
        load_button.config(state="disabled")
        solve_button.config(state="disabled")
        ac3_button.config(state="disabled")
        reset_button.config(state="disabled")
        status_label.config(text=f"Status: Solving with {algorithm}...")
        runtime_label.config(text="Runtime: --")
        nodes_label.config(text="Nodes explored: --")

        # Copy the data so the worker never needs to touch any Tkinter widget.
        snapshot = {
            "size": current_puzzle["size"],
            "givens": dict(current_puzzle["givens"]),
            "horizontal_clues": dict(current_puzzle["horizontal_clues"]),
            "vertical_clues": dict(current_puzzle["vertical_clues"]),
        }

        def work():
            try:
                solver = (solve_backtracking if algorithm == "Backtracking"
                          else solve_ac3)
                result = solver(snapshot, timeout_seconds=seconds)
                results_queue.put(("ok", algorithm, result))
            except Exception as error:
                results_queue.put(("error", algorithm, error))

        Thread(target=work, daemon=True).start()
        root.after(40, check_for_result)

    def check_for_result():
        nonlocal solving
        try:
            kind, algorithm, result = results_queue.get_nowait()
        except Empty:
            root.after(40, check_for_result)
            return

        solving = False
        load_button.config(state="normal")
        solve_button.config(state="normal")
        ac3_button.config(state="normal")
        reset_button.config(state="normal")

        if kind == "error":
            status_label.config(text="Status: Solver error")
            messagebox.showerror("Solver Error", str(result), parent=root)
            return

        runtime_label.config(text=f"Runtime: {result.runtime_seconds:.6f} s")
        nodes_label.config(text=f"Nodes explored: {result.nodes_explored}")
        results_history[algorithm] = result
        update_comparison()
        if result.status == "Solved":
            set_board_values(result.grid)
        status_label.config(text=f"Status: {result.status} ({algorithm})")

    load_button.config(command=load_txt)
    solve_button.config(command=lambda: solve_puzzle("Backtracking"))
    ac3_button.config(command=lambda: solve_puzzle("AC-3 + MRV/Degree/LCV"))
    reset_button.config(command=reset_puzzle)
    root.mainloop()


if __name__ == "__main__":
    main()
