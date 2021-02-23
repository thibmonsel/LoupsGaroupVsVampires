import numpy as np

class GameState:

    def __init__(self):
        self.STATE = None
        self.TEAM = None
        self.START = None

    def set_board(self,size):
        n,m = size
        self.STATE = np.array([[[0,0,0]]*n]*m)

    def update_board(self,changes):
        for i,j,a,b,c in changes:
            self.STATE[i,j,:] = np.array([a,b,c])

    def update_start_position(self,start):
        self.START = start
    
    def init_board(self,changes):
        self.update_board(changes)
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
    
    def get_possible_moves():
        
