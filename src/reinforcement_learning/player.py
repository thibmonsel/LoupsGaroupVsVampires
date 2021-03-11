import numpy as np

from typing import Dict, Set, Tuple
from itertools import chain

import torch
from torch import nn

from src.reinforcement_learning.memory import Memory

class Player:

    def __init__(self, player: str, max_memory: int, batch_size: int, epsilon: float, gamma: float, lr: float):
        self.player = player
        self.enemy_player = 'vampires' if player == 'werewolves' else 'werewolves'

        self.max_len_seen_humans = 10
        self.max_len_seen_enemies = 10
        self.n_possible_moves = 8

        self.memory = Memory(max_memory)
        self.batch_size = batch_size

        self.epsilon = epsilon
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

    def encode_environment(self, 
                           environment: Dict[str, Set[Tuple]], 
                           group: Tuple):
        (x, y, _) = group

        humans = list()
        for (x_humans, y_humans, n_humans) in environment['humans']:
            humans.append((x_humans - x, y_humans - y, n_humans))
        
        humans.sort(key=lambda item: max(abs(item[0]), abs(item[1])))
        humans = humans[:self.max_len_seen_humans]
        humans += [(0, 0, 0)]*(self.max_len_seen_humans - len(humans))
        
        enemies = list()
        for (x_enemies, y_enemies, n_enemies) in environment[self.enemy_player]:
            enemies.append((x_enemies - x, y_enemies - y, n_enemies))
        
        enemies.sort(key=lambda item: max(abs(item[0]), abs(item[1])))
        enemies = enemies[:self.max_len_seen_enemies]
        enemies += [(0, 0, 0)]*(self.max_len_seen_enemies - len(enemies))
        
        input = torch.flatten(torch.tensor([humans, enemies], dtype=torch.float))
        return input

    def forward(self, inputs, rewards=None):
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

    def predict_batch(self, inputs):
        outputs = self.forward(inputs)
        return torch.argmax(outputs, dim=1)


    def train(self, X, y):
        self.optimizer.zero_grad()
        loss = self.forward(X, y)
        loss.backward()
        self.optimizer.step()


    def choose_move(self,
                    environment: Dict[str, Set[Tuple]], 
                    group: Tuple):
        if np.random.random() < self.epsilon:
            return np.random.randint(0, self.n_possible_moves)
        
        input = self.encode_environment(environment, group)
        return self.predict_one(input)
    
    def replay(self):
        batch = self.memory.sample(self.batch_size)

        states = np.array([item[0] for item in batch])
        next_states = np.array(
                [(np.zeros(self.size_input) if item[3] is None
                                                    else item[3])
                 for item in batch])
        
        with torch.no_grad():
            q_s_a = self.predict_batch(states)
            q_s_a_d = self.predict_batch(next_states)
        
        X = np.zeros((len(batch), self.size_input))
        y = np.zeros((len(batch), self.n_possible_moves))
        
        for i, b in enumerate(batch):
            state, action, reward, next_state = b[0], b[1], b[2], b[3]
            current_q = q_s_a[i]
            
            if next_state is None:
                current_q[action] = reward
            else:
                current_q[action] = reward + self.gamma*np.amax(q_s_a_d[i])
            X[i] = state
            y[i] = current_q
            
        self.train(X, y)

