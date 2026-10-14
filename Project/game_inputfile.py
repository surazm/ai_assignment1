"""Display the fixed values and inequalities from a loaded Futoshiki TXT file.

Nothing is generated randomly here. All clues come from puzzle_loader.py.
Positions use zero-based (row, column) coordinates.
"""

import tkinter as tk


def display_fixed_numbers(cells, givens):
    """Place given numbers in their specified cells and make them read-only."""
    size = len(cells)
    if any(len(row) != size for row in cells):
        raise ValueError("The displayed board must be square.")

    for (row, col), value in givens.items():
        if not (0 <= row < size and 0 <= col < size):
            raise ValueError("A fixed number is outside the board.")
        if type(value) is not int or not (1 <= value <= size):
            raise ValueError(f"Fixed numbers must be between 1 and {size}.")

    for (row, col), value in givens.items():
        cell = cells[row][col]
        cell.config(state="normal")
        cell.delete(0, tk.END)
        cell.insert(0, str(value))
        cell.config(state="readonly", readonlybackground="#DCEBFA")


def display_inequalities(grid_frame, size, horizontal_clues, vertical_clues):
    """Place the exact arrow symbols supplied by the loaded puzzle."""
    horizontal_labels = {}
    vertical_labels = {}
    background = grid_frame.cget("bg")
    font_size = 18 if size <= 6 else 15

    # Horizontal arrows appear between adjacent columns: < or >.
    for row in range(size):
        for col in range(size - 1):
            sign = horizontal_clues.get((row, col), " ")
            label = tk.Label(
                grid_frame, text=sign,
                font=("Times New Roman", font_size, "bold"),
                bg=background,
            )
            label.grid(row=2 * row, column=2 * col + 1)
            horizontal_labels[(row, col)] = label

    # Vertical: ∧ means top < bottom; ∨ means top > bottom.
    for row in range(size - 1):
        for col in range(size):
            sign = vertical_clues.get((row, col), " ")
            label = tk.Label(
                grid_frame, text=sign,
                font=("Times New Roman", font_size, "bold"),
                bg=background,
            )
            label.grid(row=2 * row + 1, column=2 * col)
            vertical_labels[(row, col)] = label

    return horizontal_labels, vertical_labels


def display_game_input(grid_frame, cells, puzzle):
    """Display all TXT-defined givens and inequality arrows on the board."""
    display_fixed_numbers(cells, puzzle["givens"])
    return display_inequalities(
        grid_frame, puzzle["size"],
        puzzle["horizontal_clues"], puzzle["vertical_clues"],
    )
