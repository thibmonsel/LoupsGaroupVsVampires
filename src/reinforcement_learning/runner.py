import numpy as np

from copy import deepcopy

from src.reinforcement_learning.player import Player
from src.environment import Environment

class Runner:

    def __init__(self, player_1: Player, player_2: Player, n_games: int, limit_rounds: int = None):
        self.player_1 = player_1
        self.player_2 = player_2
        self.players = [player_1, player_2]
        self.n_games = n_games
        self.limit_rounds = limit_rounds
        
        self.environment = Environment()
        self.first_player = 0
    

    def run(self):
        
        for n_game in range(self.n_games):
            print(f"Playing game n°{n_game}")

            self.environment.initialize_game(limit_rounds=self.limit_rounds)

            current_player = self.first_player
            step = 0

            while not self.environment.is_game_finished():
                initial_map = deepcopy(self.environment.map)
                indexes, moves = self.players[current_player].play(self.environment)
                results, maps = self.environment.next_step(
                    self.players[current_player].player, 
                    moves
                )
                maps = [initial_map] + maps
                rewards = self.players[current_player].compute_rewards(results)

                encoded_initial_map = self.players[current_player].encode_map(
                        maps[0], 
                        (moves[0][0][0], moves[0][0][1], moves[0][1])
                    )

                for index in range(len(indexes)):
                    
                    encoded_final_map = self.players[current_player].encode_map(
                        maps[index], 
                        (moves[index][0][0], moves[index][0][1], moves[index][1])
                    )

                    self.players[current_player].memory.add_sample(
                        (encoded_initial_map, 
                         indexes[index], 
                         rewards[index], 
                         encoded_final_map)
                    )

                    encoded_initial_map = encoded_final_map
                
                self.players[current_player].replay()

                step += 1
                current_player = 1 - current_player

            for player in self.players:
                print(f"{player.player}: cumulated reward = {player.cumulated_reward}")
                player.reset_cumulated_reward()
                player.update_epsilon(n_game)
            
            print('')
            
            self.first_player = 1 - self.first_player
