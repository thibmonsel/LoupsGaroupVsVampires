import numpy as np

class GameState:

    def __init__(self):
        self.STATE = None
        self.TEAM = None
        self.START = None
        self.TEAM_POSITIONS = set()

    def set_board(self,size):
        n,m = size
        self.STATE = np.array([[[0,0,0]]*n]*m)

    def update_board(self,changes):
        for i,j,a,b,c in changes:
            people = [a,b,c]

            #Update the teams positions
            if people[self.TEAM] > 0 and self.STATE[i,j,self.TEAM] == 0:
                self.TEAM_POSITIONS.remove((i,j))
            if people[self.TEAM] == 0 and self.STATE[i,j,self.TEAM] > 0:
                self.TEAM_POSITIONS.add((i,j))
            self.STATE[i,j,:] = people


    def update_start_position(self,start):
        self.TEAM_POSITIONS.add(tuple(start))
        self.START = start

    def init_board(self,changes):
        for i,j,a,b,c in changes:
            self.STATE[i,j,:] = [a,b,c]        
        # At the start we need to get which team we are in with the start position
        i,j = self.START
        if self.STATE[i,j,1] > 1:
            self.TEAM = 1
        elif self.STATE[i,j,1] > 2:
            self.TEAM = 2
        else: raise Exception("We don't have a team !! :(")

    def update_game_state(self,message):
        message_handler = {
            "set": self.set_board,
            "hum": None,
            "hme": self.update_start_position,
            "map": self.init_board,
            "upd":self.update_board
        }
        info_type,data = message
        if  message_handler[info_type]:
            message_handler[info_type](data)

    def get_possible_directions(self,i,j):
        return [(i+k,j+l) for k in range(-1,2) for l in range(-1,2) if (k!=0 or l!=0) and 0<=i+k<self.STATE.shape[0] and 0<=j+l<self.STATE.shape[1]  ]

    
    def get_possible_moves(self):
        possible_moves = {}
        for i,j in self.TEAM_POSITIONS:
            units = self.STATE[i,j,self.TEAM]
            possible_moves[(i,j)] = [
                    [nb, (k,l)] 
                    for k,l in self.get_possible_directions(i,j)
                    for nb in range(1,units+1)
                ]
        return possible_moves