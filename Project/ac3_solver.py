"""Futoshiki enhanced backtracking: AC-3 + MRV/MCV + degree + LCV.

Arc consistency reduces candidate domains, but it is NOT generally a
complete solver by itself. Backtracking is required when several choices
remain after propagation.

Node counting matches backtracking.py: each tried candidate assignment
counts as one node. Domain revisions do not count as search nodes.
"""

from collections import deque
import math
import time

from backtracking import SolveResult
from csp_model import FutoshikiCSP


class _SearchTimedOut(Exception):
    """Signal a wall-clock timeout during propagation or search."""


def enforce_ac3(csp, domains, check_timeout=lambda: None, initial_arcs=None):
    """Enforce arc consistency in-place on a COPY of CSP domains.

    Args:
        csp: FutoshikiCSP containing row/column != and inequality constraints.
        domains: dict {cell: set(values)}, mutated by propagation.
        check_timeout: callback that raises when the deadline has passed.
        initial_arcs: optional sequence of (Xi,Xj) for incremental AC-3.

    Returns:
        False if a domain becomes empty (inconsistent); True otherwise.
    """
    if initial_arcs is None:
        queue = deque(
            (cell, neighbor)
            for cell in csp.variables
            for neighbor in csp.neighbors[cell]
        )
    else:
        queue = deque(initial_arcs)

    while queue:
        check_timeout()
        xi, xj = queue.popleft()

        # REVISE: remove any xi value having no support in domain(xj).
        original = domains[xi]
        supported = set()
        for vi in original:
            check_timeout()
            if any(csp.values_compatible(xi, vi, xj, vj) for vj in domains[xj]):
                supported.add(vi)

        if len(supported) == len(original):
            continue

        domains[xi] = supported
        if not supported:
            return False

        # Xi's smaller domain might invalidate constraints from other nodes.
        for neighbor in csp.neighbors[xi]:
            if neighbor != xj:
                queue.append((neighbor, xi))

    return True


def select_mrv_degree(csp, domains):
    """MRV (most constrained) variable, with degree tie-breaking."""
    undecided = [cell for cell in csp.variables if len(domains[cell]) > 1]
    if not undecided:
        return None

    def rank(cell):
        # Primary: fewest values (MRV/MCV).
        # Secondary: most neighbors that are still unassigned (degree).
        degree = sum(len(domains[n]) > 1 for n in csp.neighbors[cell])
        return (len(domains[cell]), -degree, cell)

    return min(undecided, key=rank)


def order_lcv(csp, domains, cell):
    """Least-constraining values first: minimize removed neighbor options."""
    remaining_neighbors = [
        n for n in csp.neighbors[cell] if len(domains[n]) > 1
    ]

    def eliminated(value):
        return sum(
            not csp.values_compatible(cell, value, neighbor, neighbor_value)
            for neighbor in remaining_neighbors
            for neighbor_value in domains[neighbor]
        )

    return sorted(domains[cell], key=lambda value: (eliminated(value), value))


def solve_ac3(puzzle, timeout_seconds=10.0):
    """Solve using AC-3 propagation integrated with heuristic backtracking.

    The original TXT data and the CSP's initial domains are never mutated.
    A zero timeout is allowed for deterministic timeout testing.
    """
    if (not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds) or timeout_seconds < 0):
        raise ValueError("Timeout must be a nonnegative finite number of seconds")

    start = time.perf_counter()
    deadline = start + timeout_seconds
    csp = FutoshikiCSP(puzzle)
    domains = {cell: set(values) for cell, values in csp.domains.items()}
    nodes = 0

    def check_timeout():
        if time.perf_counter() >= deadline:
            raise _SearchTimedOut

    def search(current_domains):
        nonlocal nodes
        check_timeout()

        cell = select_mrv_degree(csp, current_domains)
        if cell is None:
            assignment = {
                variable: next(iter(current_domains[variable]))
                for variable in csp.variables
            }
            return assignment if csp.is_solution(assignment) else None

        for value in order_lcv(csp, current_domains, cell):
            check_timeout()
            nodes += 1
            child = {variable: set(domain) for variable, domain in current_domains.items()}
            child[cell] = {value}
            # Propagate every consequence of this decision before recursing.
            changed_neighbors = [(neighbor, cell) for neighbor in csp.neighbors[cell]]
            if enforce_ac3(csp, child, check_timeout, changed_neighbors):
                answer = search(child)
                if answer is not None:
                    return answer
        return None

    status, grid = "No solution", None
    try:
        check_timeout()
        if csp.givens_are_consistent() and enforce_ac3(csp, domains, check_timeout):
            assignment = search(domains)
            if assignment is not None:
                status = "Solved"
                grid = [
                    [assignment[(row, col)] for col in range(csp.size)]
                    for row in range(csp.size)
                ]
    except _SearchTimedOut:
        status = "Timeout"

    elapsed = time.perf_counter() - start
    return SolveResult(status, grid, elapsed, nodes)
