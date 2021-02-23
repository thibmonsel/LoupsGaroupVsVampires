import numpy as np

class GameState:

    def __init__(self):
        self.STATE = None

    def set_board(self,size):
        n,m = size
        self.STATE = np.array([[[0,0,0]]*n]*m)

    def update_board(self,cases):
        for i,j,a,b,c in cases:
            self.STATE[i,j,:] = np.array([a,b,c])

    def update_game_state(self,message):
        message_handler = {
            "set": self.set_board,
            "hum": None,
            "hme": None,
            "map": self.update_board,
            "upd":self.update_board
        }
        info_type,data = message
        if  message_handler[info_type]:
            message_handler[info_type](data)
