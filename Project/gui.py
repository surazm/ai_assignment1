"""TXT-only Tkinter GUI for Futoshiki Backtracking and AC-3 solvers."""

import tkinter as tk

SUPPORTED_SIZES = tuple(range(2, 10))
BACKGROUND = "#F5F7FA"


def create_gui():
    root = tk.Tk()
    root.title("FUTOSHIKI PUZZLE")
    root.geometry("1000x900")
    root.minsize(780, 670)
    root.configure(bg=BACKGROUND)

    tk.Label(
        root, text="FUTOSHIKI PUZZLE", font=("Times New Roman", 22, "bold"),
        fg="#17365D", bg=BACKGROUND,
    ).pack(pady=(15, 8))

    button_frame = tk.Frame(root, bg=BACKGROUND)
    button_frame.pack(pady=(2, 8))
    button_style = {"font": ("Times New Roman", 12), "padx": 10, "pady": 5}

    load_button = tk.Button(button_frame, text="Load TXT Puzzle", **button_style)
    load_button.pack(side="left", padx=6)

    solve_button = tk.Button(
        button_frame, text="Solve: Backtracking", state="disabled", **button_style
    )
    solve_button.pack(side="left", padx=6)

    ac3_button = tk.Button(
        button_frame, text="Solve: AC-3 + Heuristics", state="disabled",
        **button_style,
    )
    ac3_button.pack(side="left", padx=6)

    reset_button = tk.Button(
        button_frame, text="Reset Puzzle", state="disabled", **button_style
    )
    reset_button.pack(side="left", padx=6)

    timeout_frame = tk.Frame(root, bg=BACKGROUND)
    timeout_frame.pack(pady=2)
    tk.Label(
        timeout_frame, text="Timeout (seconds):", bg=BACKGROUND,
        font=("Times New Roman", 12),
    ).pack(side="left", padx=(0, 8))
    timeout_var = tk.StringVar(value="10")
    tk.Entry(timeout_frame, textvariable=timeout_var, width=7,
             justify="center", font=("Times New Roman", 12)).pack(side="left")

    grid_info_label = tk.Label(root, text="No puzzle loaded",
                               font=("Times New Roman", 12), bg=BACKGROUND)
    grid_info_label.pack(pady=(5, 2))

    grid_frame = tk.Frame(root, bg=BACKGROUND)
    grid_frame.pack(pady=(8, 8))

    status_label = tk.Label(
        root, text="Status: Ready — click Load TXT Puzzle",
        font=("Times New Roman", 12), bg=BACKGROUND, fg="#17365D",
    )
    status_label.pack(pady=4)

    runtime_label = tk.Label(root, text="Runtime: --",
                             font=("Times New Roman", 12), bg=BACKGROUND)
    runtime_label.pack(pady=2)

    nodes_label = tk.Label(root, text="Nodes explored: --",
                           font=("Times New Roman", 12), bg=BACKGROUND)
    nodes_label.pack(pady=2)

    comparison_label = tk.Label(
        root, text="Comparison: run each solver on the same TXT puzzle",
        font=("Times New Roman", 11), bg=BACKGROUND, justify="left",
    )
    comparison_label.pack(pady=(12, 4))

    return (
        root, grid_frame, grid_info_label, status_label,
        load_button, solve_button, reset_button,
        runtime_label, nodes_label, timeout_var, ac3_button, comparison_label,
    )


def create_grid(grid_frame, size):
    """Replace the current grid and create N x N editable number cells."""
    if size not in SUPPORTED_SIZES:
        raise ValueError(f"Supported sizes: {SUPPORTED_SIZES}")

    for widget in grid_frame.winfo_children():
        widget.destroy()

    def valid_number(proposed):
        return proposed == "" or (len(proposed) == 1 and proposed in "123456789"[:size])

    validation = grid_frame.register(valid_number)
    cells = []
    for row in range(size):
        cell_row = []
        for col in range(size):
            entry = tk.Entry(
                grid_frame, width=2, justify="center", relief="solid", bd=1,
                font=("Times New Roman", 20 if size <= 6 else 15),
                validate="key", validatecommand=(validation, "%P"),
            )
            padding = 6 if size <= 6 else 3
            entry.grid(row=2 * row, column=2 * col,
                       padx=padding, pady=padding, ipady=3)
            cell_row.append(entry)
        cells.append(cell_row)
    return cells
