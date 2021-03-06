"""Representation of the Pragbot game world."""

# Copyright (C) 2013 Israel Geselowitz, Kenton Lee, and Constantine Lignos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import heapq
import math
from threading import Lock, RLock
import logging

ROW_DELIMITER = ';'
DEFAULT_MAP = 'pragbot/Maps/ScenarioEnv.txt'
STARTING_AREA = "entrance"
# Turn on for extremely verbose logging of path planning
PATH_DEBUG = False


class Cell:
    """Class representing a cell in grid world"""
    def __init__(self, location, celltype):
        # Cell coordinates
        self.location = location
        self.celltype = celltype
        self.neighbors = []

    def add_neighbor(self, n):
        if n.is_open():
            self.neighbors.append(n)

    def is_open(self):
        """Whether an agent can be at this cell"""
        return self.celltype == ' '

    def to_world(self):
        """Returns the center of the cell in world coordinates"""
        return tuple(to_world_coordinate(c) for c in self.location)

    def distance(self, other):
        return math.sqrt(sum((c2 - c1) * (c2 - c1) for c1, c2 in zip(self.location, other.location)))

    def world_distance(self, location):
        # Given location is in world coordinates
        return math.sqrt(sum((c2 - c1) * (c2 - c1) for c1, c2 in zip(self.to_world(), location)))

    def closer_point(self, location):
        """Returns a location that is slightly closer to
        the cell than the given location"""
        dist = self.world_distance(location)
        if dist == 0:
            return location
        delta = tuple(0.2 * (c1 - c2) / dist for c1, c2 in zip(self.to_world(), location))
        return tuple(c1 + d for c1, d in zip(location, delta))

    def __str__(self):
        return str(self.location)

    def __repr__(self):
        return str(self)

class Agent:
    """Class representing an agent in the continuous world"""
    def __init__(self, cell, location=None):
        # World coordinates
        self.cell = cell
        self.cell_lock = Lock()
        self.location = location
        if not self.location:
            self.fix_location()

        # Causes initial position to be relayed
        self._waypoints = [self.cell]
        # Reentrant lock so one can get and set while holding the lock to assure consistency
        self._waypoint_lock = RLock()
        self.flip = False
        self.flipped = False
        # A rotation of pi radians on the Z axis
        self.flip_matrix = [-1, 0, 0, 0, -1, 0, 0, 0, 1]
        self.unflip_matrix = [1, 0, 0, 0, 1, 0, 0, 0, 1]

    def set_waypoints(self, waypoints):
        """Get the waypoint lock and set the waypoints."""
        with self._waypoint_lock:
            self._waypoints = waypoints

    def get_waypoints(self):
        """Get the waypoints, which may not reflect latest changes."""
        return self._waypoints

    def follow_waypoints(self, callback):
        """Take one step towards next waypoint"""
        # TODO: Change this to ensure coherent reads of coordinates for cell/location
        # Take care of the flip/flipped cases
        if self.flip:
            # Flip or unflip JR
            self.flipped = not self.flipped
            self.flip = False
            new_coords = ([self.location[0], 0, self.location[1]] +
                          (self.flip_matrix if self.flipped else self.unflip_matrix))
            callback('PLAYER_MOVE_3D', ','.join(str(s) for s in new_coords))
            return
        elif self.flipped:
            # If we're flipped, we can't move
            return

        # Get waypoints and move
        waypoints = self.get_waypoints()
        rotationmatrix = [0, 0, 1, 0, 1, 0, -1, 0, 0]
        old_location = self.location
        if len(waypoints) > 0:
            if waypoints[0].world_distance(self.location) < 0.3:
                # Make sure movement is only from center to center
                # to prevent stuck-in-the wall bugs
                callback('MOVE_PLAYER_CELL',
                    ','.join(str(s) for s in
                             (waypoints[0].location[0], self.cell.location[0],
                              waypoints[0].location[1], self.cell.location[1])))
                # Update our location to the waypoint
                self.set_cell(waypoints[0])
                # Update the waypoints if no once changed them from under us
                with self._waypoint_lock:
                    if self.get_waypoints() == waypoints:
                        self.set_waypoints(waypoints[1:])
            else:
                # Take a step toward the waypoint
                self.location = waypoints[0].closer_point(self.location)
            deltaX = old_location[0] - self.location[0]
            deltaZ = old_location[1] - self.location[1]
            angle = math.atan2(deltaX, deltaZ)
            rotationmatrix = [math.cos(angle), 0, math.sin(angle), 0, 1, 0,
                              - 1 * math.sin(angle), 0, math.cos(angle)]
            callback('PLAYER_MOVE_3D',
                     ','.join(str(s) for s in
                              [self.location[0], 0, self.location[1]] + rotationmatrix))

    def fix_location(self):
        """Moves the agent to the center of its cell"""
        self.location = self.cell.to_world()

    def set_cell(self, cell):
        """Sets the agent's cell and the location to the center of it"""
        # TODO: Make reads of cell coherent as well
        with self.cell_lock:
            self.cell = cell
            self.fix_location()

    def plan_path(self, goal):
        """Plan to reach a goal using A* search."""
        start_node = Node(self.cell, goal, None)
        nodes = {self.cell.location: start_node}
        # Seems redundant, but makes sure all operations are constant time
        frontier_heap = [(start_node.future_cost, start_node)]
        frontier_set = set([self.cell.location])
        explored = set()
        logging.info("Planning path from %s to %s...", self.cell.location, goal.location)
        while True:
            try:
                _, current = heapq.heappop(frontier_heap)
            except IndexError:
                break
            
            # Skip voided nodes
            if current.void:
                continue
            
            # Remove location from the frontier
            current_location = current.cell.location
            frontier_set.remove(current_location)

            # Set PATH_DEBUG for extremely verbose details about path planning
            if PATH_DEBUG:
                logging.debug('Exploring: %s (%d)', str(current.cell), current.future_cost)

            # Check whether we are at the goal or should keep exploring
            if current.cell is goal:
                # Reconstruct the path to the goal
                waypoints = []
                while current is not None:
                    waypoints.append(current.cell)
                    current = current.parent
                waypoints.reverse()
                self.set_waypoints(waypoints)
                logging.info("Found path: %s", waypoints)
                return waypoints
            else:
                # Mark as explored
                explored.add(current_location)

                # Set PATH_DEBUG for extremely verbose details about path planning
                if PATH_DEBUG:
                    logging.debug("Neighbors: %s", current.cell.neighbors)

                # Explore all unexplored neighbors
                for neighbor in current.cell.neighbors:
                    neighbor_node = Node(neighbor, goal, current)
                    try:
                        neighbor_past_cost = nodes[neighbor.location].past_cost
                    except KeyError:
                        neighbor_past_cost = sys.maxint

                    # Skip this neighbor if it's already been explored for lower/equal cost
                    if (neighbor.location in explored and
                            neighbor_node.past_cost >= neighbor_past_cost):
                        continue
                    else:
                        # Void the last node at this location, then update the current cost
                        if neighbor.location in nodes:
                            nodes[neighbor.location].void = True
                        nodes[neighbor.location] = neighbor_node

                        # Add to the frontier if needed
                        if neighbor.location not in frontier_set:
                            frontier_set.add(neighbor.location)

                        # Set PATH_DEBUG for extremely verbose details about path planning
                        if PATH_DEBUG:
                            logging.debug('Adding: %s (%d)', str(neighbor), neighbor_node.future_cost)

                        # Always add to the heap
                        heapq.heappush(frontier_heap,
                                       (neighbor_node.future_cost, neighbor_node))

        # Failure
        logging.error("Could not find path from %s to %s...", self.cell.location, goal.location)
        return None

    def flip_junior(self):
        """Sets Junior to flipped"""
        self.flip = True



class Node:
    """"Node for A* pathing"""
    def __init__(self, cell, goal, parent):
        self.cell = cell
        self.parent = parent
        self.past_cost = (parent.past_cost + 1) if parent else 0
        self.future_cost = self.cell.distance(goal)
        self.void = False


class Room:
    """Class representing rooms in map"""
    def __init__(self, coords, name):
        self.coords = coords
        self.name = name
        self.center = (coords[0] + (coords[2] - coords[0]) / 2, coords[1] + (coords[3] - coords[1]) / 2)

    def __contains__(self, location):
        """Checks if x,z coordinates in a room"""
        x_coords = location[0] >= self.coords[0] and location[0] <= self.coords[2]
        y_coords = location[1] >= self.coords[1] and location[1] <= self.coords[3]
        return x_coords and y_coords


class GameEnvironment:
    """Class representing the game environment"""
    def __init__(self, env):
        self.grid = []
        self.rooms = {}
        self.objects = []
        self.object_positions = {}
        bombs = 0
        badguys = 0
        hostages = 0
        for i, line in enumerate(env.split(ROW_DELIMITER)):
            if line.startswith('r') or line.startswith('h'):
                room_data = line.split(":")
                coords = room_data[0].split(" ")
                coords = coords[1:]
                coords = [int(item) for item in coords]
                # Repack coords from [z1, x1, z2, x2] to [x1, z1, x2, z2]
                coords = [coords[1], coords[0], coords[3], coords[2]]
                name = room_data[1]
                self.rooms[name] = (Room(coords, name))
            elif len(line.strip()) > 0:
                self.grid.append([])
                for j, c in enumerate(line):
                    new_cell = Cell((i, j), to_simple_cell(c))
                    self.grid[-1].append(new_cell)
                    if c == 'C':
                        self.cmdr = Agent(new_cell)
                    elif c == 'J':
                        self.jr = Agent(new_cell)
                    elif c == 'E':
                        badguys = badguys + 1
                        new_badguy = "badguy" + str(badguys)
                        self.objects.append(new_badguy)
                        self.object_positions[new_badguy] = (i, j)
                    elif c == '*':
                        bombs = bombs + 1
                        new_bomb = "bomb" + str(bombs)
                        self.objects.append(new_bomb)
                        self.object_positions[new_bomb] = (i, j)
                    elif c == 'H':
                        hostages = hostages + 1
                        new_hostage = "hostage" + str(hostages)
                        self.objects.append(new_hostage)
                        self.object_positions[new_hostage] = (i, j)

        for i, row in enumerate(self.grid):
            for j, cell in enumerate(row):
                if not cell.is_open():
                    continue
                if i > 0:
                    cell.add_neighbor(self.grid[i - 1][j])
                if i < len(self.grid) - 1:
                    cell.add_neighbor(self.grid[i + 1][j])
                if j > 0:
                    cell.add_neighbor(self.grid[i][j - 1])
                if j < len(row) - 1:
                    cell.add_neighbor(self.grid[i][j + 1])
                # Uncomment to see all neighbors of all cells
                if PATH_DEBUG:
                    logging.debug("Cell ({}, {}) has neighbors: {}".format(i, j, cell.neighbors))

    def update_cmdr(self, location):
        """Updates commander's location"""
        self.cmdr.set_cell(self.get_cell(location))

    def update_jr(self, location):
        """Update junior's location"""
        self.jr.set_cell(self.get_cell(location))

    def cell_contents(self, cell):
        """Returns either the cell if empty or its contents"""
        if cell is self.cmdr.cell:
            return 'C'
        elif cell is self.jr.cell:
            return 'J'
        else:
            return cell.celltype

    def get_cell(self, location):
        """Return the cell corresponding to a location."""
        return self.grid[location[0]][location[1]]

    def __str__(self):
        return '\n'.join(''.join(self.cell_contents(cell) for cell in row) \
                             for row in self.grid)

def to_cell_coordinate(c):
    """Continuous world to grid world"""
    return int(c / 4)

def to_world_coordinate(c):
    """Grid world to continuous world"""
    return c * 4

def to_simple_cell(c):
    """Returns a cell's type as either dead or open space"""
    if c in ('|', '-', '+', '1', '2', '3', '4'):
        # Dead space
        return '-'
    else:
        # Open space
        return ' '
