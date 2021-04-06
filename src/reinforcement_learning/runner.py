import matplotlib.pyplot as plt
import numpy as np

from copy import deepcopy
from tqdm import tqdm

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
        
        for n_game in tqdm(range(self.n_games)):

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

                rewards = self.players[current_player].compute_rewards(results)

                if self.players[current_player].is_trainable:
                    maps = [initial_map] + maps

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
            
            winner = self.environment.winner()

            for player in self.players:
                player.save_statistics(winner)
                
                if player.is_trainable:
                    player.update_epsilon(n_game)

            self.first_player = 1 - self.first_player
    
    def plot_results(self, all_time_result=False):
        t = range(self.n_games)

        player_1_legend = 'Player 1'
        if self.player_1.is_random:
            player_1_legend += ' (random)'
        elif not self.player_1.is_trainable:
            player_1_legend += ' (not trainable)'
        
        player_2_legend = 'Player 2'
        if self.player_2.is_random:
            player_2_legend += ' (random)'
        elif not self.player_2.is_trainable:
            player_2_legend += ' (not trainable)'

        plt.subplot(211)
        plt.plot(t, self.player_1.cumulated_rewards[-self.n_games:], 'r')
        plt.plot(t, self.player_2.cumulated_rewards[-self.n_games:], 'g')
        plt.title('Rewards over time')
        plt.legend([player_1_legend, player_2_legend])

        len_mask = 1 + self.n_games // 100
        mask = np.ones((len_mask))
        plt.subplot(212)
        plt.plot(t, 
                np.concatenate((
                    np.zeros((len_mask - 1)),
                    np.convolve(self.player_1.score_rounds[-self.n_games:], 
                                mask, 
                                mode='valid') / len_mask)),
                'r')
        plt.plot(t, 
                np.concatenate((
                    np.zeros((len_mask - 1)),
                    np.convolve(self.player_2.score_rounds[-self.n_games:], 
                                mask, 
                                mode='valid') / len_mask)),
                'g')
        plt.title('Winning rounds over time')
        plt.legend([player_1_legend, player_2_legend])

        plt.show()