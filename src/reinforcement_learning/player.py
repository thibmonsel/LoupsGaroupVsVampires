import numpy as np

from typing import Dict, Set, Tuple

import torch
from torch import nn

class Player:

    def __init__(self, player: str, epsilon: float):
        self.player = player
        self.enemy_player = 'vampires' if player == 'werewolves' else 'werewolves'

        self.max_len_seen_humans = 10
        self.max_len_seen_enemies = 10
        self.n_possible_moves = 8

        self.epsilon = epsilon

        self.size_fc_1 = 100
        self.size_fc_2 = 100

        self.relu = torch.nn.ReLU()
        self.fc_1 = nn.Linear(
            (self.max_len_seen_humans + self.max_len_seen_enemies) * 3, 
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

    def encode_environment(self, 
                           environment: Dict[str, Set[Tuple]], 
                           group: Tuple):
        (x, y, _) = group

        humans = list()
        for (x_humans, y_humans, n_humans) in environment['humans']:
            humans.append((x_humans - x, y_humans - y, n_humans))
        
        humans.sort(key=lambda item: abs(item[0] - x) + abs(item[1] - y))
        humans = humans[:self.max_len_seen_humans]
        humans = nn.functional.pad(
            torch.tensor(humans), 
            (0, self.max_len_seen_humans - len(humans))
        )
        
        enemies = list()
        for (x_enemies, y_enemies, n_enemies) in environment[self.enemy_player]:
            enemies.append((x_enemies - x, y_enemies - y, n_enemies))
        
        enemies.sort(key=lambda item: abs(item[0] - x) + abs(item[1] - y))
        enemies = enemies[:self.max_len_seen_enemies]
        enemies = nn.functional.pad(
            torch.tensor(enemies), 
            (0, self.max_len_seen_enemies - len(enemies))
        )
        
        input = torch.flatten(torch.tensor([humans, enemies]))
        return input

    def forward(self, inputs, rewards = None):
        outputs = self.fc_1(inputs)
        outputs = self.relu(outputs)
        outputs = self.fc_2(outputs)
        outputs = self.relu(outputs)
        outputs = self.fc_3(outputs)

        if rewards is not None:
            criterion = nn.CrossEntropyLoss()
            loss = criterion(outputs, rewards)
            return loss
        
        return outputs

    def predict_one(self, input):
        pass

    def train(self):
        pass

    def choose_move(self,
                    environment: Dict[str, Set[Tuple]], 
                    group: Tuple):
        if np.random.random() < self.epsilon:
            return np.random.randint(0, self.n_possible_moves)
        
        input = self.encode_environment(environment, group)
        return self.predict_one(input)
