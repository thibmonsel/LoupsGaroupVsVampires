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
        copy.ENEMY_TEAM = self.ENEMY_TEAM
        copy.START = self.START
        copy.TEAM_POSITIONS = self.TEAM_POSITIONS.copy()
        copy.ENEMY_POSITIONS = self.ENEMY_POSITIONS.copy()
        copy.HUMAN_POSITIONS = self.HUMAN_POSITIONS.copy()
        return copy

    def change_teams(self):
        self.TEAM,self.ENEMY_TEAM = self.ENEMY_TEAM,self.TEAM
        self.TEAM_POSITIONS,self.ENEMY_POSITIONS = self.ENEMY_POSITIONS,self.TEAM_POSITIONS

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
        directions = []
        if np.sum(self.STATE[i+1:,j+1:,self.ENEMY_TEAM])>0 or np.sum(self.STATE[i+1:,j+1:,0]) > np.sum(self.STATE[i+1:,j+1:,self.TEAM]):
            directions.append((i+1,j+1))
        if j>0 and (np.sum(self.STATE[i+1:,:j,self.ENEMY_TEAM]) >0 or np.sum(self.STATE[i+1:,:j,0]) > np.sum(self.STATE[i+1:,:j,self.TEAM])):
            directions.append((i+1,j-1))
        if np.sum(self.STATE[i+1:,j,self.ENEMY_TEAM])>0 or np.sum(self.STATE[i+1:,j,0]) > np.sum(self.STATE[i+1:,j,self.TEAM]):
            directions.append((i+1,j))
        if i>0 and (np.sum(self.STATE[:i,j,self.ENEMY_TEAM])>0 or np.sum(self.STATE[:i,j,0]) > np.sum(self.STATE[:i,j,self.TEAM])):
            directions.append((i-1,j))
        if i>0 and (np.sum(self.STATE[:i,j+1:,self.ENEMY_TEAM])>0 or np.sum(self.STATE[:i,j+1:,0]) > np.sum(self.STATE[:i,j+1:,self.TEAM])):
            directions.append((i-1,j+1))
        if i>0 and j>0 and (np.sum(self.STATE[:i,:j,self.ENEMY_TEAM])>0 or np.sum(self.STATE[:i,:j,0]) > np.sum(self.STATE[:i,:j,self.TEAM])):
            directions.append((i-1,j-1))
        if j>0 and (np.sum(self.STATE[i,:j,self.ENEMY_TEAM])>0 or np.sum(self.STATE[i,:j,0])> np.sum(self.STATE[i,:j,self.TEAM])):
            directions.append((i,j-1))
        if (np.sum(self.STATE[i,j+1:,self.ENEMY_TEAM])>0 or np.sum(self.STATE[i,j+1:,0]) > np.sum(self.STATE[i,j+1:,self.TEAM])):
            directions.append((i,j+1))
        return directions

    def check_move_is_allowed(self,move):
        starts,_,ends = zip(*move)
        return len(set(starts).intersection(set(ends))) == 0

    
    def get_next_moves(self,with_split=False):
        """only consider restrained list of moves"""
        all_moves = set()

        for i,j in self.TEAM_POSITIONS:
            units = self.STATE[i,j,self.TEAM]
            new_moves = set([frozenset({((i,j),units,(k,l))}) for k,l in  self.get_possible_directions(i,j)])
            combination_moves = [ move.union(new_move) for move in all_moves for new_move in new_moves]
            combination_moves = set([m for m in combination_moves if self.check_move_is_allowed(m)])
            all_moves.update(new_moves)
            all_moves.update(combination_moves)

        if with_split and len(self.TEAM_POSITIONS)<2:
            all_moves.update(self.get_next_moves_with_one_split())
        return all_moves

    def get_next_moves_with_one_split(self,max_split_interval=2):
        all_moves = set()
        for i,j in self.TEAM_POSITIONS:
            units = self.STATE[i,j,self.TEAM]
            split_interval = min(max_split_interval,units//2)
            if split_interval>0:
                for nb in map(int,np.linspace(units//2//split_interval,units//2,split_interval)): #only consider 3 possible split sizes
                    for k,l in self.get_possible_directions(i,j):
                        for k2,l2 in self.get_possible_directions(i,j):
                            if k!=k2 or l!=l2:
                                all_moves.add(frozenset({((i,j),nb,(k,l)),((i,j),units-nb,(k2,l2))}))
        return all_moves
    

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
                elif n_units >= n_humans*1.5:
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
            if destination_content[self.ENEMY_TEAM] > 0:
                n_ennemies = destination_content[self.ENEMY_TEAM]
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
                        new_content[self.ENEMY_TEAM] = n_surv
                        state = state.copy()
                        state.update_board([(x_end, y_end,*new_content)])
                        new_states.append((proba1*proba2,state))
                states = new_states

        #Change the player after the move has been done        
        for _,state in states:
            state.change_teams()
        return states

