"""Futoshiki Constraint Satisfaction Problem (CSP) model.

A variable is (row, column) using zero-based coordinates.
Domains are {1, ..., N}, except given cells whose domains are singletons.
Each pair of cells in a row or column has a binary not-equal constraint.
Adjacent comparisons are strict binary '<' or '>' constraints.
"""


class FutoshikiCSP:
    """Represent the variables, domains, and constraints of a loaded puzzle."""

    def __init__(self, puzzle):
        self.size = puzzle["size"]
        self.givens = dict(puzzle["givens"])
        n = self.size

        self.variables = [(r, c) for r in range(n) for c in range(n)]
        self.domains = {
            cell: ({self.givens[cell]} if cell in self.givens
                   else set(range(1, n + 1)))
            for cell in self.variables
        }

        # Every two distinct cells sharing a row or column must differ.
        self.peers = {}
        for row, col in self.variables:
            same_row = {(row, c) for c in range(n) if c != col}
            same_col = {(r, col) for r in range(n) if r != row}
            self.peers[(row, col)] = same_row | same_col

        # Each relation is represented twice (one view from each endpoint).
        # Operators always describe the left-hand variable relative to 'other'.
        self.inequality_neighbors = {cell: [] for cell in self.variables}
        self.inequalities = []

        for (row, col), symbol in puzzle["horizontal_clues"].items():
            if symbol not in ("<", ">"):
                raise ValueError("Invalid horizontal comparison")
            self._add_inequality((row, col), symbol, (row, col + 1))

        for (row, col), symbol in puzzle["vertical_clues"].items():
            if symbol not in ("∧", "∨"):
                raise ValueError("Invalid vertical comparison")
            operator = "<" if symbol == "∧" else ">"
            self._add_inequality((row, col), operator, (row + 1, col))

        # Binary-constraint graph: each peer shares a != constraint,
        # and inequality pairs add a further restriction.
        self.neighbors = {cell: set(self.peers[cell]) for cell in self.variables}
        self.relations = {
            (cell, other): operator
            for cell in self.variables
            for other, operator in self.inequality_neighbors[cell]
        }

    def _add_inequality(self, first, operator, second):
        if first not in self.domains or second not in self.domains:
            raise ValueError("Comparison lies outside the grid")
        self.inequalities.append((first, operator, second))
        self.inequality_neighbors[first].append((second, operator))
        reverse = ">" if operator == "<" else "<"
        self.inequality_neighbors[second].append((first, reverse))

    def values_compatible(self, first, first_value, second, second_value):
        """Check every binary constraint between two neighboring variables.

        The != row/column constraint and any inequality must BOTH hold.
        This is the same relation used by AC-3 when revising domains.
        """
        if second not in self.neighbors[first]:
            return True
        if first_value == second_value:
            return False
        operator = self.relations.get((first, second))
        if operator == "<":
            return first_value < second_value
        if operator == ">":
            return first_value > second_value
        return True

    def is_consistent(self, cell, value, assignment):
        """Check constraints touching one new cell in a partial assignment.

        'assignment' contains values assigned to OTHER variables. Unassigned
        variables do not create conflicts; the recursion checks them later.
        """
        if cell not in self.domains or value not in self.domains[cell]:
            return False

        for peer in self.peers[cell]:
            if assignment.get(peer) == value:
                return False

        for other, operator in self.inequality_neighbors[cell]:
            other_value = assignment.get(other)
            if other_value is None:
                continue
            if operator == "<" and not (value < other_value):
                return False
            if operator == ">" and not (value > other_value):
                return False

        return True

    def givens_are_consistent(self):
        """Check whether all given values can coexist."""
        for cell, value in self.givens.items():
            others = {k: v for k, v in self.givens.items() if k != cell}
            if not self.is_consistent(cell, value, others):
                return False
        return True

    def is_solution(self, assignment):
        """Verify a complete solution, including all givens and constraints."""
        if set(assignment) != set(self.variables):
            return False
        for cell, value in assignment.items():
            if not self.is_consistent(
                cell, value, {k: v for k, v in assignment.items() if k != cell}
            ):
                return False
        return True
