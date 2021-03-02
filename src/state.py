import numpy as np

class GameState:

    def __init__(self):
        self.STATE = None
        self.TEAM = None
        self.ENEMY_TEAM = None
        self.START = None
        self.TEAM_POSITIONS = set()
        self.ENEMY_POSITIONS = set()
        self.HUMAN_POSITIONS = set()

    def set_board(self,size):
        n,m = size
        self.STATE = np.array([[[0,0,0]]*n]*m)

    def update_board(self,changes):
        for i,j,a,b,c in changes:
            people = [a,b,c]

            #Update the teams positions
            if people[self.TEAM] > 0 and self.STATE[i,j,self.TEAM] == 0:
                self.TEAM_POSITIONS.add((i,j))
            if people[self.TEAM] == 0 and self.STATE[i,j,self.TEAM] > 0:
                self.TEAM_POSITIONS.remove((i,j))
            if people[self.ENEMY_TEAM] > 0 and self.STATE[i,j,self.ENEMY_TEAM] == 0:
                self.ENEMY_POSITIONS.add((i,j))
            if people[self.ENEMY_TEAM] == 0 and self.STATE[i,j,self.ENEMY_TEAM] > 0:
                self.ENEMY_POSITIONS.remove((i,j))
            if people[0] > 0 and self.STATE[i,j,0] == 0:
                self.HUMAN_POSITIONS.add((i,j))
            if people[0] == 0 and self.STATE[i,j,0] > 0:
                self.HUMAN_POSITIONS.remove((i,j))
            self.STATE[i,j,:] = people


    def update_start_position(self,start):
        self.TEAM_POSITIONS.add(tuple(start))
        self.START = start

    def init_board(self,changes):
        # At the start we need to get which team we are in with the start position
        i,j = self.START
        for i2,j2,_,b,c in changes:
            if i == i2 and j == j2 and b > 1:
                self.TEAM = 1
                self.ENEMY_TEAM = 2
                break
            if  i == i2 and j == j2 and c > 1:
                self.TEAM = 2
                self.ENEMY_TEAM = 1
                break
        self.update_board(changes)

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

    def get_possible_moves(self,team_positions=None,current_move={},current_move_dests=set(), current_move_sources=set()):
        if team_positions is None:
            team_positions = { (i,j):self.STATE[i,j,self.TEAM] for i,j in self.TEAM_POSITIONS}
        all_moves = set()
        for i,j in team_positions:
            units = team_positions[(i,j)]
            if (i,j) not in current_move_dests:
                for nb in range(1,units+1):
                    for k,l in self.get_possible_directions(i,j):
                        if (i,j,k,l) in current_move or (k,l) in current_move_sources:
                            continue
                        new_current = current_move.copy()
                        new_current[(i,j,k,l)] = nb
                        frozen_current = frozenset({((i,j),nb,(k,l)) for (i,j,k,l),nb in new_current.items()})
                        if frozen_current in all_moves:
                            continue
                        all_moves.add(frozen_current)
                        new_current_move_dests = current_move_dests.copy()
                        new_current_move_dests.add((k,l))
                        new_current_move_sources = current_move_sources.copy()
                        new_current_move_sources.add((i,j))
                        remaining_team_positions = team_positions.copy()
                        remaining_team_positions[(i,j)] = remaining_team_positions[(i,j)] - nb
                        if remaining_team_positions[(i,j)] == 0:
                            del remaining_team_positions[(i,j)]
                        recurrent_moves = self.get_possible_moves(
                            remaining_team_positions,
                            new_current,
                            new_current_move_dests,
                            new_current_move_sources)
                        all_moves = all_moves.union(recurrent_moves)
        return all_moves

    # def get_possible_moves(self):
    #     possible_moves_dic = {}
    #     for i,j in self.TEAM_POSITIONS:
    #         units = self.STATE[i,j,self.TEAM]
    #         possible_moves_dic[(i,j)] = [
    #                 [nb, (k,l)] 
    #                 for k,l in self.get_possible_directions(i,j)
    #                 for nb in range(1,units+1)
    #             ]
    #     return [[source,nb,dest] for source,moves in possible_moves_dic.items()  for nb,dest in moves]