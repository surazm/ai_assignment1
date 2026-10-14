"""Basic recursive backtracking for Futoshiki (NO AC-3 or MRV here).

The node counter increments for each candidate value considered by search.
Time is wall-clock time measured with time.perf_counter().
"""

from dataclasses import dataclass
import math
import time

from csp_model import FutoshikiCSP


@dataclass
class SolveResult:
    status: str                 # "Solved", "No solution", or "Timeout"
    grid: list | None           # N x N list of integers, or None
    runtime_seconds: float
    nodes_explored: int


class _SearchTimedOut(Exception):
    """Internal signal used to stop recursive search immediately."""


def solve_backtracking(puzzle, timeout_seconds=10.0):
    """Solve the original TXT puzzle, preserving its fixed values.

    Args:
        puzzle: validated dict returned by puzzle_loader.load_puzzle().
        timeout_seconds: maximum wall-clock seconds; 0 yields immediate Timeout.

    Returns:
        SolveResult with status, grid, elapsed seconds and candidate attempts.
    """
    if not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds):
        raise ValueError("Timeout must be a finite number of seconds")
    if timeout_seconds < 0:
        raise ValueError("Timeout cannot be negative")

    start = time.perf_counter()
    deadline = start + timeout_seconds
    nodes = 0
    csp = FutoshikiCSP(puzzle)
    assignment = dict(csp.givens)
    unassigned = [cell for cell in csp.variables if cell not in assignment]

    def check_timeout():
        if time.perf_counter() >= deadline:
            raise _SearchTimedOut

    def backtrack(index):
        nonlocal nodes
        check_timeout()
        if index == len(unassigned):
            return csp.is_solution(assignment)

        cell = unassigned[index]  # Basic row-major backtracking.
        for value in sorted(csp.domains[cell]):
            check_timeout()
            nodes += 1          # One attempted candidate = one explored node.
            if not csp.is_consistent(cell, value, assignment):
                continue

            assignment[cell] = value
            if backtrack(index + 1):
                return True
            del assignment[cell]  # Undo the decision on backtracking.

        return False

    status = "No solution"
    grid = None
    try:
        check_timeout()
        if csp.givens_are_consistent() and backtrack(0):
            status = "Solved"
            grid = [
                [assignment[(row, col)] for col in range(csp.size)]
                for row in range(csp.size)
            ]
    except _SearchTimedOut:
        status = "Timeout"

    elapsed = time.perf_counter() - start
    return SolveResult(status, grid, elapsed, nodes)
