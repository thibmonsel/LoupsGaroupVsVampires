import numpy as np
from scipy.special import binom

class GameState:

    def __init__(self):
        self.STATE = None
        self.TEAM = None
        self.ENEMY_TEAM = None
        self.START = None
        self.TEAM_POSITIONS = set()
        self.ENEMY_POSITIONS = set()
        self.HUMAN_POSITIONS = set()
        
    
    def copy(self):
        copy = GameState()
        copy.STATE = np.copy(self.STATE)
        copy.TEAM = self.TEAM
        copy.START = self.START
        copy.TEAM_POSITIONS = self.TEAM_POSITIONS.copy()
        return copy

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

    def get_possible_moves(
            self,
            min_group_size=1,
            max_number_group=None,
            team_positions=None,
            current_move={},
            current_move_dests=set(),
            current_move_sources=set()
        ):
        if team_positions is None:
            team_positions = { (i,j):self.STATE[i,j,self.TEAM] for i,j in self.TEAM_POSITIONS}
        all_moves = set()
        for i,j in team_positions:
            units = team_positions[(i,j)]
            if (i,j) not in current_move_dests:
                possible_nb_units = [units]
                if max_number_group is not None or len(self.TEAM_POSITIONS) + len(current_move) < max_number_group:
                    possible_nb_units = possible_nb_units + list(range(min_group_size,units+1-min_group_size))
                for nb in possible_nb_units:
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
                            min_group_size,
                            max_number_group,
                            remaining_team_positions,
                            new_current,
                            new_current_move_dests,
                            new_current_move_sources)
                        all_moves = all_moves.union(recurrent_moves)
        return all_moves

    def apply_move(self,moves):
        states = [(1,self.copy())]
        for (x_start, y_start), n_units, (x_end, y_end) in moves:
            for _,state in states:
                new_start = list(state.STATE[x_start, y_start,:])
                new_start[state.TEAM] -= n_units
                state.update_board([(x_start, y_start,*new_start)])
            
            destination_content = self.STATE[x_end, y_end,:]
            #No conflict
            if np.sum(destination_content) == 0 or destination_content[self.TEAM] > 0:
                for _,state in states:
                    new_content = [0,0,0]
                    new_content[state.TEAM] += n_units+destination_content[self.TEAM]
                    state.update_board([(x_end, y_end,*new_content)])
                continue
            
            # If there are humans
            if destination_content[0] > 0:
                n_humans = destination_content[0]

                # No battle
                if n_units >= n_humans:
                    for _,state in states:
                        new_content = [0,0,0]
                        new_content[state.TEAM] += n_units + destination_content[0]
                        state.update_board([(x_end, y_end,*new_content)])
                
                # Battle
                else:
                    p_win = n_units / (2 * n_humans)
                    n = n_units + n_humans
                    n_surv_with_proba = [(p_win*binom(n,k)*p_win**k*(1-p_win)**(n-k),k) for k in range(n+1)]
                    n_surv_human_with_proba = [((1-p_win)*binom(n_humans,k)*(1-p_win)**k*p_win**(n_humans-k),k) for k in range(n_humans+1)]
                    new_states = []
                    for proba1,state in states:
                        #case team win
                        for proba2,n_surv in n_surv_with_proba:
                            new_content = [0,0,0]
                            new_content[state.TEAM] = n_surv
                            state = state.copy()
                            state.update_board([(x_end, y_end,*new_content)])
                            new_states.append((proba1*proba2,state))
                        #case human win
                        for proba2,n_surv in n_surv_human_with_proba:
                            state = state.copy()
                            state.update_board([(x_end, y_end,n_surv,0,0)])
                            new_states.append((proba1*proba2,state))
                    states = new_states
                continue

            # If there are enemies
            if destination_content[self.TEAM] > 0:
                ennemy_player = 3 - self.TEAM 
                n_ennemies = destination_content[ennemy_player]

                # No battle
                if n_units >= 1.5 * n_ennemies:
                    new_content = [0,0,0]
                    new_content[self.TEAM]=n_units
                    for _,state in states:
                        state.update_board([(x_end, y_end,*new_content)])
                    continue
                if 1.5 * n_units <=  n_ennemies:
                    continue
                
                # Battle
                if n_units <= n_ennemies:
                    p_win = n_units / (2 * n_ennemies)
                else:
                    p_win = (n_units / n_ennemies) - 0.5
                
                n_surv_team_with_proba = [(p_win*binom(n_units,k)*(1-p_win)**k*p_win**(n_units-k),k) for k in range(n_units+1)]
                n_surv_ennemy_with_proba = [((1-p_win)*binom(n_ennemies,k)*(1-p_win)**k*p_win**(n_ennemies-k),k) for k in range(n_ennemies+1)]

                new_states = []
                for proba1,state in states:
                    #case team win
                    for proba2,n_surv in n_surv_team_with_proba:
                        new_content = [0,0,0]
                        new_content[state.TEAM] = n_surv
                        state = state.copy()
                        state.update_board([(x_end, y_end,*new_content)])
                        new_states.append((proba1*proba2,state))
                    #case ennemy win
                    for proba2,n_surv in n_surv_ennemy_with_proba:
                        new_content = [0,0,0]
                        new_content[ennemy_player] = n_surv
                        state = state.copy()
                        state.update_board([(x_end, y_end,*new_content)])
                        new_states.append((proba1*proba2,state))
                states = new_states

        #Change the player after the move has been done        
        for _,state in states:
            state.TEAM = 3-state.TEAM
        return states

