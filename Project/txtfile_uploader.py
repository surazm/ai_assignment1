"""Load and validate Futoshiki TXT files.

Required sections (in this order): GRID, GIVEN_VALUES, COMPARISON.
TXT positions are 1-based; Python positions in returned dictionaries are 0-based.
Empty GIVEN_VALUES / COMPARISON sections are permitted: some valid Futoshiki
puzzles contain no fixed numbers or no inequalities. The headings are required.

This validates *file format* and directly conflicting clues, not whether a
complete solution exists. That belongs to the CSP solver.
"""

from pathlib import Path
import re


SUPPORTED_SIZES = tuple(range(2, 10))
MAX_FILE_BYTES = 1_000_000
HEADINGS = ("GRID", "GIVEN_VALUES", "COMPARISON")


class FileError(ValueError):
    """Invalid puzzle file; safe to display directly in a GUI message box."""


def _split_fields(line, expected_count, line_number, section, example):
    fields = [field.strip() for field in line.split(",")]
    if len(fields) != expected_count or any(not field for field in fields):
        raise FileError(
            f"Line {line_number} ({section}): incorrect number of fields "
            f"or an empty field. Expected: {example}"
        )
    return fields


def _integer(text, line_number, field_name):
    # Avoid accepting signs, decimal points or non-integer forms as coordinates.
    if not text.isascii() or not text.isdecimal():
        raise FileError(
            f"Line {line_number}: {field_name} must be a positive whole "
            f"number; received {text!r}."
        )
    return int(text)


def _read_file(file_path):
    """Read a small UTF-8 TXT file with understandable failure messages."""
    path = Path(file_path)

    if path.suffix.lower() != ".txt":
        raise FileError(
            "Invalid file type. Choose a .txt file containing "
            "GRID, GIVEN_VALUES and COMPARISON."
        )
    try:
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise FileError(
                "File too large. Puzzle TXT files must be 1 MB or smaller."
            )
        with path.open("r", encoding="utf-8-sig") as file:
            contents = file.read()
    except FileNotFoundError as error:
        raise FileError("File not found. Select an existing .txt file.") from error
    except IsADirectoryError as error:
        raise FileError("The selected path is a folder, not a TXT file.") from error
    except PermissionError as error:
        raise FileError(
            "Permission denied. Close programs locking the file or select "
            "a file you have permission to read."
        ) from error
    except UnicodeError as error:
        raise FileError(
            "Invalid text encoding. Save the file as UTF-8 text in Notepad "
            "and try again."
        ) from error
    except OSError as error:
        raise FileError(f"Could not read the selected file: {error}") from error

    if "\x00" in contents or any(
        ord(char) < 32 and char not in "\r\n\t" for char in contents
    ):
        raise FileError(
            "The file contains binary or invalid control characters. "
            "Choose a plain-text .txt file."
        )
    if not contents.strip():
        raise FileError(
            "The TXT file is empty. Required format:\n"
            "GRID\n5\nGIVEN_VALUES\n1,1,1\n"
            "COMPARISON\n1,1,<,1,2"
        )
    return contents


def load_puzzle(file_path):
    """Load puzzle and return size, givens, horizontal_clues, vertical_clues."""
    text = _read_file(file_path)
    sections = {heading: [] for heading in HEADINGS}
    seen = set()
    current = None

    # A '#' starts a comment, including one after a data line.
    for line_number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue

        upper = line.upper()
        if upper in HEADINGS:
            if upper in seen:
                raise FileError(
                    f"Line {line_number}: duplicate {upper} heading. "
                    "Each heading must appear once."
                )
            expected = HEADINGS[len(seen)]
            if upper != expected:
                raise FileError(
                    f"Line {line_number}: incorrect section order. "
                    f"Expected {expected} before {upper}. "
                    "Use GRID, then GIVEN_VALUES, then COMPARISON."
                )
            seen.add(upper)
            current = upper
            continue

        if re.fullmatch(r"[A-Za-z][A-Za-z_0-9 -]*", line) and not (
            current == "GRID" and not sections["GRID"]
        ):
            raise FileError(
                f"Line {line_number}: unknown heading {line!r}. "
                "Required headings: GRID, GIVEN_VALUES, COMPARISON."
            )
        if current is None:
            raise FileError(
                f"Line {line_number}: data before GRID heading. "
                "Begin the file with GRID on its own line."
            )
        sections[current].append((line_number, line))

    missing = [heading for heading in HEADINGS if heading not in seen]
    if missing:
        raise FileError(
            "Missing required section(s): " + ", ".join(missing) + ". "
            "Required order: GRID, GIVEN_VALUES, COMPARISON."
        )

    # GRID must contain exactly one number, on one line.
    grid_lines = sections["GRID"]
    if len(grid_lines) != 1:
        raise FileError(
            "GRID must contain exactly one size, for example:\nGRID\n5"
        )
    grid_line, grid_value = grid_lines[0]
    size = _integer(grid_value, grid_line, "GRID size")
    if size not in SUPPORTED_SIZES:
        raise FileError(
            f"Line {grid_line}: unsupported GRID size {size}. "
            "Supported sizes are 2 through 9."
        )

    givens = {}
    row_seen = {}
    column_seen = {}
    for line_number, line in sections["GIVEN_VALUES"]:
        fields = _split_fields(
            line, 3, line_number, "GIVEN_VALUES", "row,column,value"
        )
        row, col, value = (
            _integer(fields[0], line_number, "row"),
            _integer(fields[1], line_number, "column"),
            _integer(fields[2], line_number, "given value"),
        )
        if not (1 <= row <= size and 1 <= col <= size):
            raise FileError(
                f"Line {line_number}: GIVEN_VALUES cell ({row},{col}) "
                f"is outside the {size}x{size} grid."
            )
        if not 1 <= value <= size:
            raise FileError(
                f"Line {line_number}: GIVEN_VALUES at ({row},{col}) is "
                f"{value}, but allowed values are 1 through {size}."
            )
        if (row - 1, col - 1) in givens:
            raise FileError(
                f"Line {line_number}: duplicate GIVEN_VALUES cell "
                f"({row},{col})."
            )
        if (row, value) in row_seen:
            raise FileError(
                f"Line {line_number}: number {value} appears twice in row "
                f"{row} (previously on line {row_seen[(row, value)]})."
            )
        if (col, value) in column_seen:
            raise FileError(
                f"Line {line_number}: number {value} appears twice in column "
                f"{col} (previously on line {column_seen[(col, value)]})."
            )
        row_seen[(row, value)] = line_number
        column_seen[(col, value)] = line_number
        # Convert to zero-based indexing for the GUI / solver.
        givens[(row - 1, col - 1)] = value

    horizontal = {}
    vertical = {}
    for line_number, line in sections["COMPARISON"]:
        fields = _split_fields(
            line, 5, line_number, "COMPARISON",
            "row1,column1,<,row2,column2 (or >)",
        )
        row1 = _integer(fields[0], line_number, "first row")
        col1 = _integer(fields[1], line_number, "first column")
        operator = fields[2]
        row2 = _integer(fields[3], line_number, "second row")
        col2 = _integer(fields[4], line_number, "second column")

        if operator not in ("<", ">"):
            raise FileError(
                f"Line {line_number}: COMPARISON operator {operator!r} "
                "is invalid; use '<' or '>'."
            )
        for row, col in ((row1, col1), (row2, col2)):
            if not (1 <= row <= size and 1 <= col <= size):
                raise FileError(
                    f"Line {line_number}: comparison cell ({row},{col}) "
                    f"is outside the {size}x{size} grid."
                )

        if row1 == row2 and col2 == col1 + 1:
            position = (row1 - 1, col1 - 1)
            clues = horizontal
            symbol = operator
        elif col1 == col2 and row2 == row1 + 1:
            position = (row1 - 1, col1 - 1)
            clues = vertical
            symbol = "∧" if operator == "<" else "∨"
        else:
            raise FileError(
                f"Line {line_number}: comparisons must join adjacent "
                "cells, listed left-to-right or top-to-bottom."
            )

        if position in clues:
            raise FileError(
                f"Line {line_number}: duplicate or conflicting "
                "COMPARISON for this adjacent pair."
            )
        clues[position] = symbol

        # Reject direct contradiction when both compared values are fixed.
        first = givens.get((row1 - 1, col1 - 1))
        second = givens.get((row2 - 1, col2 - 1))
        if first is not None and second is not None:
            works = first < second if operator == "<" else first > second
            if not works:
                raise FileError(
                    f"Line {line_number}: COMPARISON contradicts fixed "
                    f"values ({first} {operator} {second} is false)."
                )

    return {
        "size": size,
        "givens": givens,
        "horizontal_clues": horizontal,
        "vertical_clues": vertical,
    }
