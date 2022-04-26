"""The tile class."""

from typing import Iterable
from queue import Queue
from time import monotonic_ns, perf_counter_ns

timer = perf_counter_ns
NS2MS = 1e-6


class Tile(object):
    """Tile: Minimum unit of minesweeper."""

    MINE = -1  # opcode: MINE, 15
    BLAST = -2  # opcode: BLAST, 14
    WRONGFLAG = -3  # opcode: WRONGFLAG, 13
    UNFLAGGED = -4  # opcode: UNFLAGGED, 12
    COVERED = 9  # opcode: COVERED, 9
    DOWN = 10  # opcode: DOWN, 10
    FLAGGED = 11  # opcode: FLAGGED, 11

    def __init__(self, x: int, y: int):
        """Initialize a tile."""
        self.x: int = x  # coordinate X
        self.y: int = y  # coordinate Y
        self.value: int = 0  # value: -1 for mines, 0-8 for numbers
        self.flagged: bool = False  # flag indicator
        self.covered: bool = True  # cover indicator
        self.down: bool = False  # pressed indicator
        self.status: int = Tile.COVERED  # status for upper layer
        self.neighbours: set[Tile] = set()  # neighbours
        self.neighbour_flags: int = 0  # number of neighbour flags

    def __repr__(self) -> str:
        """Print a tile."""
        return f'Tile[v: {self.value}]: (x: {self.x}, y: {self.y})'

    def get_coordinate(self) -> tuple[int, int]:
        """Get the coordinate of the tile."""
        return (self.x, self.y)

    def get_status(self) -> int:
        """Get the status of the tile."""
        return self.status

    def set_mine(self):
        """Set a tile with a mine."""
        self.value = Tile.MINE

        # set the value of a mine's neighbour
        # this will simplify board construction process
        for t in self.neighbours:
            if not t.is_mine():
                t.value += 1  # update a neighbour's value

    def is_mine(self) -> bool:
        """Judge whether the tile is a mine by its value."""
        return self.value == Tile.MINE

    def get_neighbours(self) -> set:
        """Get the neighbours of a tile."""
        return self.neighbours

    def set_neighbours(self, neighbours: Iterable):
        """Set the neighbours of a tile."""
        self.neighbours = set(neighbours)

    def recover(self):
        """Recover the status of the tile."""
        self.flagged = False  # flag indicator
        self.covered = True  # cover indicator
        self.down = False  # pressed indicator
        self.status = Tile.COVERED  # status for upper layer
        self.neighbour_flags = 0  # number of neighbour flags

    def update(self):
        """Update status of a tile."""
        if self.flagged:
            self.status = Tile.FLAGGED
        elif self.down:
            self.status = Tile.DOWN
        elif self.covered:
            self.status = Tile.COVERED
        else:
            self.status = self.value

    def update_finish(self):
        """Update status of a tile after finishing a game."""
        self.update()
        if not self.flagged and self.is_mine():
            self.status = Tile.UNFLAGGED

    def update_blast(self):
        """Update status of a tile after failing a game."""
        self.update()
        if self.flagged and not self.is_mine():
            self.status = Tile.WRONGFLAG
        elif not self.covered and self.is_mine():
            self.status = Tile.BLAST
        elif not self.flagged and self.is_mine():
            self.status = Tile.MINE

    def left_hold(self):
        """Change status when holding the left mouse key."""
        if self.covered and not self.flagged:
            self.down = True

    def double_hold(self):
        """Change status when holding the left and right mouse key."""
        self.left_hold()
        for t in self.neighbours:
            t.left_hold()

    def unhold(self):
        """Change status when unholding a single mouse key."""
        if not self.flagged:
            self.down = False

    def basic_open(self, BFS: bool = False):
        """Handle basic opening."""
        if self.flagged or not self.covered:
            return False, set()
        self.covered = False
        if self.value == 0 or (BFS and self.value == self.neighbour_flags):
            return True, self.neighbours
        return True, set()

    def open(self, BFS: bool = False, test_op: bool = False):
        """Handle normal opening."""
        search = Queue()
        search.put(self)
        searched = set()
        changed = set()
        # sa = sb = sc = sd = 0
        # p = 0
        while not search.empty():
            # a = timer()
            t = search.get()
            # p += 1
            # sa += timer() - a
            # b = timer()
            eff, to_search = t.basic_open(BFS)
            # sb += timer() - b
            # c = timer()
            for tt in to_search:
                search.put(tt)
            # sc += timer() - c
            # if test_op:
            #     searched.add(t)
            # d = timer()
            if eff:
                changed.add(t)
            # sd += timer() - d
        # print(p, sa * NS2MS, sb * NS2MS, sc * NS2MS, sd * NS2MS)
        return changed if not test_op else searched

    def double(self, BFS: bool = False):
        """Handle chording."""
        if not self.covered and self.value == self.neighbour_flags:
            return set.union(*(t.open(BFS) for t in self.neighbours))
        return set()

    def flag(self, easy_flag: bool = False):
        """Handle flagging and easy flagging."""
        if self.flagged:
            self.flagged = False
            for t in self.neighbours:
                t.neighbour_flags -= 1  # update the number of neighbour flags
            return set((self, ))
        elif self.covered:
            self.flagged = True
            for t in self.neighbours:
                t.neighbour_flags += 1  # update the number of neighbour flags
            return set((self, ))
        elif easy_flag:
            covered_neighbours = set(t for t in self.neighbours if t.covered)
            unflagged_neighbours = set(t for t in self.neighbours
                                       if t.covered and not t.flagged)
            if self.value == len(covered_neighbours):
                for t in covered_neighbours:
                    t.flagged = True
                    for tt in t.get_neighbours():
                        tt.neighbour_flags += 1
                return unflagged_neighbours
        return set()
