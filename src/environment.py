import os

import numpy as np
import xml.etree.ElementTree as ET

MINIMUM_SIZE = 5
MAXIMUM_SIZE = 40
MINIMUM_HOMES = 2
MAXIMUM_HOMES = 10

class Environment:
    def __init__(self):
        self.map = None
        self.width = None
        self.height = None

    def generate_map(self, width=None, height=None, n_homes=None):
        """Generate map using `MapGenerator.exe` executable

        Args:
            width (int, optional): Width of the map. Defaults to None.
            height (int, optional): Height of the map. Defaults to None.
            n_homes (int, optional): Number of homes. Defaults to None.
        """
        if width is None:
            width = np.random.randint(MINIMUM_SIZE, MAXIMUM_SIZE)
        if height is None:
            height = np.random.randint(MINIMUM_SIZE, MAXIMUM_SIZE)
        
        self.width = width
        self.height = height
        self.map = np.array([[[0, 0, 0]]*width]*height)

        if n_homes is None:
            n_homes = np.random.randint(MINIMUM_HOMES, MAXIMUM_HOMES)
        
        os.system(f"MapGenerator.exe {width} {height} {n_homes} map.xml")
        root = ET.parse('map.xml').getroot()

        for child in root:
            if child.tag == 'Humans':
                self.map[int(child.attrib['Y'])][int(child.attrib['X'])][0] = int(child.attrib['Count'])
            if child.tag == 'Vampires':
                self.map[int(child.attrib['Y'])][int(child.attrib['X'])][1] = int(child.attrib['Count'])
            if child.tag == 'Werewolves':
                self.map[int(child.attrib['Y'])][int(child.attrib['X'])][2] = int(child.attrib['Count'])
        
        os.remove('map.xml')
    
    def print_map(self):
        print(self.map)
    
    def compute_number_groups(self, player):
        """Compute number of groups of units a player has

        Args:
            player (int): Number of the player (must be in [1, 2])

        Returns:
            int: The number of groups
        """
        number_groups = 0
        for x in range(self.width):
            for y in range(self.height):
                number_groups += int(self.map[y][x][player] > 0)
        return number_groups
    
    def next_step(self, player, moves):
        """Compute the state of the next step

        Args:
            player (int): Number of the player (must be in [1, 2])
            moves (list): List of moves

        Raises:
            RuntimeError: [description]
            RuntimeError: [description]
            RuntimeError: [description]
            RuntimeError: [description]
            RuntimeError: [description]

        Returns:
            array: Resulting map
        """
        ennemy_player = 2 - player

        if len(moves) == 0:
            raise RuntimeError('Illegal move: there must be at least one move')

        number_groups = self.compute_number_groups(player)
        if len(moves) > number_groups:
            raise RuntimeError('Illegal move: the number of moves must be less than your number of groups')

        for (x_start, y_start), n_units, (x_end, y_end) in moves:
            if x_start == x_end and y_start == y_end:
                raise RuntimeError('Illegal move: start and end must be different positions')
            elif abs(x_start - x_end) > 1 or abs(y_start - y_end) > 1:
                raise RuntimeError('Illegal move: end is unreachable from start')
            elif self.map[y_start][x_start][player] < n_units:
                raise RuntimeError('Illegal move: not enough available units')
            else:
                destination_content = self.map[y_end][x_end]

                # If there are no units or allied units
                if destination_content == [0, 0, 0] or destination_content[player] > 0:
                    self.map[y_end][x_end][player] += n_units
                    self.map[y_start][x_start][player] -= n_units
                
                # If there are humans
                elif destination_content[0] > 0:
                    n_humans = destination_content[0]

                    # No battle
                    if n_units >= n_humans:
                        self.map[y_end][x_end] = [0, 0, 0]
                        self.map[y_end][x_end][player] = n_units + n_humans
                        self.map[y_start][x_start][player] -= n_units
                    
                    # Battle
                    else:
                        p = n_units / (2 * n_humans)
                        victory = np.random.random() < p
                        if victory:
                            n_survivors = sum(np.random.rand((n_units)) < p)
                            n_converted = sum(np.random.rand((n_humans)) < p)
                            
                            self.map[y_end][x_end] = [0, 0, 0]
                            self.map[y_end][x_end][player] = n_survivors + n_converted
                            self.map[y_start][x_start][player] -= n_units
                        else:
                            n_survivors = sum(np.random.rand((n_humans)) < 1 - p)

                            self.map[y_end][x_end][0] = n_survivors
                            self.map[y_start][x_start][player] -= n_units
                
                # If there are enemies
                elif destination_content[ennemy_player] > 0:
                    n_ennemies = destination_content[ennemy_player]

                    # No battle
                    if n_units >= 1.5 * n_ennemies:
                        self.map[y_end][x_end] = [0, 0, 0]
                        self.map[y_end][x_end][player] = n_units
                        self.map[y_start][x_start][player] -= n_units
                    
                    # Battle
                    else:
                        p = n_units / (2 * n_ennemies)
                        victory = np.random.random() < p
                        if victory:
                            n_survivors = sum(np.random.rand((n_units)) < p)
                            
                            self.map[y_end][x_end] = [0, 0, 0]
                            self.map[y_end][x_end][player] = n_survivors
                            self.map[y_start][x_start][player] -= n_units
                        else:
                            n_survivors = sum(np.random.rand((n_ennemies)) < 1 - p)

                            self.map[y_end][x_end][0] = n_survivors
                            self.map[y_start][x_start][player] -= n_units

        return self.map      
