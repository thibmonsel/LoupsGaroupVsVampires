import numpy as np
import pickle

from typing import Dict, List, Set, Tuple
from itertools import chain

import torch
from torch import nn

from src.environment import Environment
from src.reinforcement_learning.memory import Memory

class Player:

    def __init__(self, 
                 player: str, 
                 from_file: str = None,
                 is_random: bool = False, 
                 is_trainable: bool = True, 
                 max_memory: int = None, 
                 batch_size: int = None, 
                 max_epsilon: float = None, 
                 min_epsilon: float = None, 
                 decay: float = None, 
                 gamma: float = None, 
                 lr: float = None):
        self.player = player
        self.enemy_player = 'vampires' if player == 'werewolves' else 'werewolves'

        self.max_len_seen_humans = 10
        self.max_len_seen_enemies = 2
        self.n_possible_moves = 8

        self.is_random = is_random and from_file is None
        self.is_trainable = is_trainable and not self.is_random

        if not self.is_random and self.is_trainable and from_file is None:
            assert (max_memory is not None and
                batch_size is not None and
                max_epsilon is not None and
                min_epsilon is not None and
                decay is not None and
                gamma is not None and
                lr is not None), "Some parameters are missing"

        if not self.is_random and from_file is None:
            self.memory = Memory(max_memory)
            self.batch_size = batch_size

            self.max_epsilon = max_epsilon
            self.min_epsilon = min_epsilon
            self.epsilon = max_epsilon
            self.decay = decay
            self.gamma = gamma

            self.size_input = (self.max_len_seen_humans + self.max_len_seen_enemies) * 3
            self.size_fc_1 = 100
            self.size_fc_2 = 100

            self.relu = torch.nn.ReLU()
            self.fc_1 = nn.Linear(
                self.size_input, 
                self.size_fc_1
            )
            self.fc_2 = nn.Linear(
                self.size_fc_1, 
                self.size_fc_2
            )
            self.fc_3 = nn.Linear(
                self.size_fc_2, 
                self.n_possible_moves
            )

            self.lr = lr
            self.optimizer = torch.optim.AdamW(
                chain(self.fc_1.parameters(), 
                    self.fc_2.parameters(), 
                    self.fc_3.parameters()), 
                lr=lr
            )

        if from_file is None:
            self.reward_attribution = {
                'nothing': -1,
                'lost_units': -10,
                'converted_humans': 15,
                'killed_humans': 0,
                'killed_enemies': 12,
                'has_won': 1200,
                'has_lost': -1200
            }
            self.cumulated_rewards = list()
            self.score_rounds = list()

        else:
            if batch_size is not None:
                self.batch_size = batch_size
            if max_epsilon is not None:
                self.max_epsilon = max_epsilon
                self.epsilon = max_epsilon
            if min_epsilon is not None:
                self.min_epsilon = min_epsilon
            if decay is not None:
                self.decay = decay
            if gamma is not None:
                self.gamma = gamma
            if lr is not None:
                self.lr = lr
            
            self.load(from_file)
        
        self.current_cumulated_reward = 0

    def set_race(self, race):
        self.player = race
        self.enemy_player = 'vampires' if race == 'werewolves' else 'werewolves'

    def encode_map(self, 
                   map: Dict[str, Set[Tuple]], 
                   group: Tuple):
        (x, y, n_units) = group

        humans = list()
        for (x_humans, y_humans, n_humans) in map['humans']:
            humans.append((x_humans - x, y_humans - y, n_humans / n_units))
        
        humans.sort(key=lambda item: max(abs(item[0]), abs(item[1])))
        humans = humans[:self.max_len_seen_humans]
        humans += [(0, 0, 0)]*(self.max_len_seen_humans - len(humans))
        
        enemies = list()
        for (x_enemies, y_enemies, n_enemies) in map[self.enemy_player]:
            enemies.append((x_enemies - x, y_enemies - y, n_enemies / n_units))
        
        enemies.sort(key=lambda item: max(abs(item[0]), abs(item[1])))
        enemies = enemies[:self.max_len_seen_enemies]
        enemies += [(0, 0, 0)]*(self.max_len_seen_enemies - len(enemies))
        
        # print(humans)
        # print(enemies)
        # print(torch.tensor([humans, enemies], dtype=torch.float))

        input = torch.flatten(torch.tensor(humans + enemies, dtype=torch.float))
        return input

    def forward(self, inputs, rewards=None):
        outputs = self.fc_1(inputs)
        outputs = self.relu(outputs)
        outputs = self.fc_2(outputs)
        outputs = self.relu(outputs)
        outputs = self.fc_3(outputs)

        if rewards is not None:
            criterion = nn.MSELoss()
            loss = criterion(outputs, rewards)
            return loss
        
        return outputs

    def predict_one(self, input):
        with torch.no_grad():
            return self.forward(input)

    def predict_batch(self, inputs):
        return self.forward(inputs)
        # torch.argmax(outputs, dim=1)


    def train(self, X, y):
        self.optimizer.zero_grad()
        loss = self.forward(X, y)
        loss.backward()
        self.optimizer.step()


    def choose_move(self,
                    map: Dict[str, Set[Tuple]], 
                    group: Tuple):
        if self.is_random or np.random.random() < self.epsilon:
            return np.random.randint(0, self.n_possible_moves)
        
        input = self.encode_map(map, group)
        output = self.predict_one(input)
        return torch.argmax(output)
    
    def play(self, environment: Environment):
        move_to_tuple = [
            (-1, -1), (0, -1), (1, -1), 
            (1, 0), 
            (1, 1), (0, 1), (-1, 1), 
            (-1, 0)
        ]
        moves = list()
        indexes = list()
        
        for (x, y, n_units) in environment.map[self.player]:
            move = self.choose_move(environment.map, (x, y, n_units))
            indexes.append(move)

            # The moves correspond to the following pattern:

            # +---+---+---+
            # | 0 | 1 | 2 |
            # +---+---+---+
            # | 7 | X | 3 |
            # +---+---+---+
            # | 6 | 5 | 4 |
            # +---+---+---+

            # We have to handle illegal moves (that make a group go out of 
            # the board)

            # Corners
            if x == 0 and y == 0 and (move <= 2 or move >= 6):
                move = 3
            elif x == environment.width - 1 and y == 0 and move <= 4:
                move = 5
            elif x == environment.width - 1 and y == environment.height - 1 and 2 <= move <= 6:
                move = 7
            elif x == 0 and y == environment.height - 1 and (move == 0 or move >= 4):
                move = 1
            
            # Border line
            elif y == 0 and move <= 2:
                if move == 0:
                    move = 7
                else:
                    move = 3
            elif y == environment.height - 1 and 4 <= move <= 6:
                if move == 4:
                    move = 3
                else:
                    move = 7
            elif x == 0 and (move == 0 or move >= 6):
                if move == 6:
                    move = 5
                else:
                    move = 1
            elif x == environment.width - 1 and 2 <= move <= 4:
                if move == 2:
                    move = 1
                else:
                    move = 5
            
            tuple_move = move_to_tuple[move]
            moves.append(((x, y), 
                          n_units, 
                          (x + tuple_move[0], y + tuple_move[1])))
        
        return indexes, moves

    
    def replay(self):
        batch = self.memory.sample(self.batch_size)

        states = torch.stack([item[0] for item in batch])
        
        next_states = torch.stack(
            [(torch.zeros(self.size_input) if item[3] is None
                                            else item[3])
                for item in batch]
        )
        
        with torch.no_grad():
            q_s_a = self.predict_batch(states)
            q_s_a_d = self.predict_batch(next_states)
        
        X = torch.zeros((len(batch), self.size_input))
        y = torch.zeros((len(batch), self.n_possible_moves))
        
        for i, b in enumerate(batch):
            state, action, reward, next_state = b[0], b[1], b[2], b[3]
            current_q = q_s_a[i]
            
            if next_state is None:
                current_q[action] = reward
            else:
                current_q[action] = reward + self.gamma*torch.argmax(q_s_a_d[i])
            X[i] = state
            y[i] = current_q
            
        self.train(X, y)

    def update_epsilon(self, steps):
        self.epsilon = self.min_epsilon + \
            (self.max_epsilon - self.min_epsilon)*np.exp(- self.decay * steps)
    
    def compute_rewards(self, results: List[Dict[str, int]], update_reward=True) -> List[int]:
        rewards = list()

        for result in results:
            if sum(result.values()) == 0:
                rewards.append(self.reward_attribution['nothing'])
            
            else:
                reward = 0
                for key in result.keys():
                    reward += result[key] * self.reward_attribution[key]
                rewards.append(reward)
        
        if update_reward:
            self.current_cumulated_reward += sum(rewards)

        return rewards
    
    def save_statistics(self, winner):
        self.cumulated_rewards.append(self.current_cumulated_reward)
        self.current_cumulated_reward = 0
        
        if winner == self.player:
            self.score_rounds.append(1)
        elif winner is None:
            self.score_rounds.append(0)
        else:
            self.score_rounds.append(-1)

    def save(self, filename):
        with open(f"saved_models/{filename}.pkl", 'wb') as file:
            pickle.dump(self.__dict__, file)
    
    def load(self, filename):
        with open(f"saved_models/{filename}.pkl", 'rb') as file:
            self.__dict__.update(pickle.load(file))
