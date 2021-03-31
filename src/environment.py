import os

import numpy as np
import xml.etree.ElementTree as ET

from copy import deepcopy

MINIMUM_SIZE = 5
MAXIMUM_SIZE = 40
MINIMUM_HOMES = 2
MAXIMUM_HOMES = 10

class Environment:
    def __init__(self):
        self.map = None
        self.races = ['humans', 'vampires', 'werewolves']
        self.width = None
        self.height = None
        self.current_step = None
        self.limit_steps = None
    
    def initialize_game(self, limit_rounds: int = None, width: int = None, 
                        height: int = None, n_homes: int = None):
        """Initialize a game by generating map and resetting steps counter

        Args:
            limit_rounds (int, optional): Number of rounds (a round contains 
                the turn of both players). When the game reaches this limit, 
                it is considered as finished. If `None`, there is no limit. 
                Defaults to None.
            width (int, optional): Width of the map. Defaults to None.
            height (int, optional): Height of the map. Defaults to None.
            n_homes (int, optional): Number of homes. Defaults to None.
        """
        self.generate_map(width=width, height=height, n_homes=n_homes)
        
        if limit_rounds is not None:
            self.limit_steps = limit_rounds * 2
        self.current_step = 0
        

    def generate_map(self, width: int = None, height: int = None, 
                     n_homes: int = None):
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
        self.map = {
            'humans': set(),
            'vampires': set(),
            'werewolves': set()
        }

        if n_homes is None:
            n_homes = np.random.randint(MINIMUM_HOMES, MAXIMUM_HOMES)
        
        os.system(f"MapGenerator.exe {width} {height} {n_homes} map.xml")
        root = ET.parse('map.xml').getroot()

        for child in root:
            if child.tag == 'Humans':
                self.map['humans'].add((int(child.attrib['X']), int(child.attrib['Y']), int(child.attrib['Count'])))
            if child.tag == 'Vampires':
                self.map['vampires'].add((int(child.attrib['X']), int(child.attrib['Y']), int(child.attrib['Count'])))
            if child.tag == 'Werewolves':
                self.map['werewolves'].add((int(child.attrib['X']), int(child.attrib['Y']), int(child.attrib['Count'])))
        
        os.remove('map.xml')
    
    def set_map_from_server(self, width, height, map_array):
        self.width = width
        self.height = height
        self.map = {
            'humans': set(),
            'vampires': set(),
            'werewolves': set()
        }
        for x, y, n_humans, n_vampires, n_werewolves in map_array:
            if n_humans > 0:
                self.map['humans'].add((x, y, n_humans))
            elif n_vampires > 0:
                self.map['vampires'].add((x, y, n_vampires))
            else:
                self.map['werewolves'].add((x, y, n_werewolves))
    
    def update_map_from_server(self, update_array):
        for x, y, n_humans, n_vampires, n_werewolves in update_array:
            race, number = self.find_group(x, y)
            if race is not None:
                self.map[race].remove((x, y, number))
            
            if n_humans > 0:
                self.map['humans'].add((x, y, n_humans))
            elif n_vampires > 0:
                self.map['vampires'].add((x, y, n_vampires))
            elif n_werewolves > 0:
                self.map['werewolves'].add((x, y, n_werewolves))


    def print_map(self):
        print(self.map)
    
    def compute_number_groups(self, player):
        """Compute number of groups of units a player has

        Args:
            player (str): Name of the player (must be in ['vampires', 'werewolves'])

        Returns:
            int: The number of groups
        """
        return len(self.map[player])
    
    def count_units(self, race):
        return sum([n_units for (_, _, n_units) in self.map[race]])

    def find_group(self, x, y):
        for race in self.races:
            for (x_unit, y_unit, number) in self.map[race]:
                if x == x_unit and y == y_unit:
                    return (race, number)
        return (None, 0)

    def next_step(self, player, moves):
        """Compute the state of the next step

        Args:
            player (str): Name of the player (must be in ['vampires', 'werewolves'])
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
        result_model = {
            'lost_units': 0,
            'converted_humans': 0,
            'killed_humans': 0,
            'killed_enemies': 0,
            'has_won': False,
            'has_lost': False
        }

        results = list()
        maps = list()

        enemy_player = 'vampires' if player == 'werewolves' else 'werewolves'

        if len(moves) == 0:
            raise RuntimeError('Illegal move: there must be at least one move')

        # number_groups = self.compute_number_groups(player)
        # if len(moves) > number_groups:
        #     raise RuntimeError('Illegal move: the number of moves must be less than your number of groups')

        move_ends = list()

        for (x_start, y_start), n_units, (x_end, y_end) in moves:
            if x_start == x_end and y_start == y_end:
                raise RuntimeError('Illegal move: start and end must be different positions')
            elif abs(x_start - x_end) > 1 or abs(y_start - y_end) > 1:
                raise RuntimeError('Illegal move: end is unreachable from start')
            elif (x_start, y_start) in move_ends:
                raise RuntimeError('Illegal move: start can not be the end position of another move')
            elif n_units <= 0:
                raise RuntimeError('Illegal move: number of units must be strictly positive')
            
            race_start, n_units_start = self.find_group(x_start, y_start)

            if race_start != player or n_units_start < n_units:
                raise RuntimeError('Illegal move: not enough available units')
            else:
                move_ends.append((x_end, y_end))

                result = result_model.copy()
                race_end, n_units_end = self.find_group(x_end, y_end)

                # If there are no units
                if race_end == None:
                    self.map[player].add((x_end, y_end, n_units))
                    self.map[player].remove((x_start, y_start, n_units_start))
                    if n_units_start - n_units > 0:
                        self.map[player].add((x_start, y_start, n_units_start - n_units))

                # If there are allied units
                if race_end == player:
                    self.map[player].remove((x_end, y_end, n_units_end))
                    self.map[player].add((x_end, y_end, n_units + n_units_end))
                    self.map[player].remove((x_start, y_start, n_units_start))
                    if n_units_start - n_units > 0:
                        self.map[player].add((x_start, y_start, n_units_start - n_units))
                
                # If there are humans
                elif race_end == 'humans':

                    # No battle
                    if n_units >= n_units_end:
                        self.map['humans'].remove((x_end, y_end, n_units_end))
                        self.map[player].add((x_end, y_end, n_units + n_units_end))
                        self.map[player].remove((x_start, y_start, n_units_start))
                        if n_units_start - n_units > 0:
                            self.map[player].add((x_start, y_start, n_units_start - n_units))

                        result['converted_humans'] += n_units_end
                    
                    # Battle
                    else:
                        p = n_units / (2 * n_units_end)
                        victory = np.random.random() < p
                        if victory:
                            n_survivors = sum(np.random.rand((n_units)) < p)
                            n_converted = sum(np.random.rand((n_units_end)) < p)
                            
                            self.map['humans'].remove((x_end, y_end, n_units_end))
                            if n_survivors + n_converted > 0:
                                self.map[player].add((x_end, y_end, n_survivors + n_converted))
                            self.map[player].remove((x_start, y_start, n_units_start))
                            if n_units_start - n_units > 0:
                                self.map[player].add((x_start, y_start, n_units_start - n_units))

                            result['converted_humans'] += n_converted
                            result['killed_humans'] += n_units_end - n_converted
                            result['lost_units'] += n_units - n_survivors
                        else:
                            n_survivors = sum(np.random.rand((n_units_end)) < 1 - p)

                            self.map['humans'].remove((x_end, y_end, n_units_end))
                            if n_survivors > 0:
                                self.map['humans'].add((x_end, y_end, n_survivors))
                            self.map[player].remove((x_start, y_start, n_units_start))
                            if n_units_start - n_units > 0:
                                self.map[player].add((x_start, y_start, n_units_start - n_units))
                            
                            result['lost_units'] += n_units
                            result['killed_humans'] += n_units_end - n_survivors
                
                # If there are enemies
                elif race_end == enemy_player:
                    
                    # No battle
                    if n_units >= 1.5 * n_units_end:
                        self.map[enemy_player].remove((x_end, y_end, n_units_end))
                        self.map[player].add((x_end, y_end, n_units))
                        self.map[player].remove((x_start, y_start, n_units_start))
                        if n_units_start - n_units > 0:
                            self.map[player].add((x_start, y_start, n_units_start - n_units))

                        result['killed_enemies'] += n_units_end
                    
                    # Battle
                    else:
                        p = n_units / (2 * n_units_end)
                        victory = np.random.random() < p
                        if victory:
                            n_survivors = sum(np.random.rand((n_units)) < p)

                            self.map[enemy_player].remove((x_end, y_end, n_units_end))
                            if n_survivors > 0:
                                self.map[player].add((x_end, y_end, n_survivors))
                            self.map[player].remove((x_start, y_start, n_units_start))
                            if n_units_start - n_units > 0:
                                self.map[player].add((x_start, y_start, n_units_start - n_units))
                            
                            result['lost_units'] += n_units - n_survivors
                            result['killed_enemies'] += n_units_end
                        else:
                            n_survivors = sum(np.random.rand((n_units_end)) < 1 - p)

                            self.map[enemy_player].remove((x_end, y_end, n_units_end))
                            if n_survivors > 0:
                                self.map[enemy_player].add((x_end, y_end, n_survivors))
                            self.map[player].remove((x_start, y_start, n_units_start))
                            if n_units_start - n_units > 0:
                                self.map[player].add((x_start, y_start, n_units_start - n_units))
                            
                            result['lost_units'] += n_units
                            result['killed_enemies'] += n_units_end - n_survivors

            winner = self.winner()
            if winner == player:
                result['has_won'] = True
            elif winner is not None:
                result['has_lost'] = True

            results.append(result)
            maps.append(deepcopy(self.map))

        self.current_step += 1

        return results, maps

    def is_game_finished(self) -> bool:
        if self.limit_steps is not None and self.current_step >= self.limit_steps:
            return True
        
        if len(self.map['vampires']) == 0 or len(self.map['werewolves']) == 0:
            return True
        
        return False
    
    def winner(self) -> str:
        if self.limit_steps is not None and self.current_step >= self.limit_steps:
            n_vampires = self.count_units('vampires')
            n_werewolves = self.count_units('werewolves')
            
            if n_vampires > n_werewolves:
                return 'vampires'
            
            if n_werewolves > n_vampires:
                return 'werewolves'
            
            return None
            
        if len(self.map['vampires']) == 0:
            return 'werewolves'

        if len(self.map['werewolves']) == 0:
            return 'vampires'
        
        return None
