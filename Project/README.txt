FUTOSHIKI ASSIGNMENT 1 - TXT GUI + BASIC BACKTRACKING
===================================================

REQUIRES: Python 3.10+ with tkinter (Anaconda/Spyder compatible).

FILES:
  Futoshiki.py        - run this file (F5 in Spyder)
  gui.py              - Tkinter window, buttons, grid and status labels
  puzzle_loader.py    - strict TXT parser and validation
  game_inputfile.py   - display TXT numbers and inequality arrows
  csp_model.py        - cell variables, 1..N domains, CSP constraints
  backtracking.py     - basic DFS backtracking, timeout, node count
  grid_5.txt          - example loaded Futoshiki puzzle
  tests/              - unit and GUI integration tests

TO RUN:
  1. Extract this folder and keep its Python files together.
  2. Open Futoshiki.py in Spyder and run (F5).
  3. Click Load TXT Puzzle, choose grid_5.txt.
  4. Choose a positive time limit (default 10 seconds).
  5. Click Solve: Backtracking.
  6. Observe status (Solved / No solution / Timeout), runtime and nodes.
  7. Reset Puzzle restores the original TXT clues.

TXT FORMAT:
  GRID
  5

  GIVEN_VALUES
  1,1,1
  2,3,4
  4,5,3

  COMPARISON
  1,1,<,1,2
  1,5,>,2,5
  2,2,<,3,2
  3,3,>,4,3

TXT positions are 1-based. Python uses 0-based.
For vertical arrows, ∧ means top < bottom; ∨ means top > bottom.

CSP MODEL:
  Variables: X(r,c) for all cells
  Domains: 1..N (singletons for fixed values)
  Row constraint: unequal values in the same row
  Column constraint: unequal values in the same column
  Inequality constraint: honor all TXT comparisons

BACKTRACKING:
  Plain recursive depth-first search, row-major order, ascending values.
  No MRV, Degree, LCV, forward checking, or AC-3 (added later).
  A node is counted each time a candidate value is TRIED in search.
  Fixed values are placed initially, and do not increase the count.
  Runtime is measured using time.perf_counter() (wall-clock time).
  During search, the GUI remains responsive using a worker thread and queue.
  A timeout returns status Timeout, not a partial solution.
  An unsolvable puzzle returns No solution, not an input-format error.
  The solver always starts from TXT givens (it ignores any user-typed guesses).

IMPORTANT RUBRIC DISCREPANCY:
  The supplied screenshot describes a binary {0,1} grid with row/column SUM
  constraints, NOT Futoshiki. This code implements Futoshiki as requested.

EXTRA TEST PUZZLES:
  unsolvable_2x2.txt -> valid puzzle format, No solution
  empty_9x9.txt      -> no clues; try a very short timeout to test Timeout

NOTE: The on-screen timeout field must contain a POSITIVE value. A 9x9
puzzle with 0.000001 seconds will normally time out, but actual runtime
may vary by hardware. Internally timeout_seconds=0 always yields Timeout.
