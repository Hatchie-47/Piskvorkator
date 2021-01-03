# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 20:07:45 2020

@author: Hatch
"""

import numpy as np
import math as m
import random as r
import logging
from sty import fg, rs

class Player():
    def __init__(self):
        self.dp = 1.1
        self.dpt = -0.5
        self.st = 0.05
    
    def set_parameters(self,dp,dpt,st):
        self.dp = dp
        self.dpt = dpt
        self.st= st

class Gameboard():
    
    def __init__(self,size,debug,logger):
        self.size = size
        self.board = np.zeros((3,size[0],size[1]))
        #self.score_connected = (20,30,40,50,0,50,40,30,20)
        #self.score_space = (0,0,0,0,0,1,1.0001,1.0002,1.0003,1.0004)
        self.score_connected = (2.6,3.4,4.2,5,0,5,4.2,3.4,2.6)
        self.score_space = (0,0,0,0,0,1,1.1,1.2,1.3,1.4)
        self.free_space_bonus = (1,1.5,2)
        self.winner = 0
        self.completed = False
        self.debug = debug
        self.players = [Player(),Player()]
        self.get_digits_vectorized = np.vectorize(self.get_digits)
        self.logger = logger
        
        for i in range(size[0]):
            for j in range(size[1]):
                self.calc_potential((i,j),True)

    def place_symbol(self,player,coordinates):
        if self.completed:
            print(fg(9)+'Symbol not placed, game is already concluded! Winner is player {}.'.format(int(self.winner))+fg.rs)
            return 0, None
        
        self.board[0,coordinates[0],coordinates[1]] = player
        
        if self.debug>0:print(fg(10)+'Player {} placed symbol on coordinates {}.'.format(int(player), coordinates)+fg.rs)
        self.logger.debug('gb.place_symbol({},{})'.format(int(player), coordinates))
        
        self.calc_potential(coordinates, False)
        for x in range(1,5):
            if (coordinates[0]+x < self.size[0]): self.calc_potential((coordinates[0]+x,coordinates[1]), False)
            if (coordinates[0]+x < self.size[0]) and (coordinates[1]+x < self.size[1]): self.calc_potential((coordinates[0]+x,coordinates[1]+x), False)
            if (coordinates[0]+x < self.size[0]) and (coordinates[1]-x >= 0): self.calc_potential((coordinates[0]+x,coordinates[1]-x), False)
            if (coordinates[1]+x < self.size[1]): self.calc_potential((coordinates[0],coordinates[1]+x), False)
            if (coordinates[1]-x >= 0): self.calc_potential((coordinates[0],coordinates[1]-x), False)
            if (coordinates[0]-x >= 0): self.calc_potential((coordinates[0]-x,coordinates[1]), False)
            if (coordinates[0]-x >= 0) and (coordinates[1]+x < self.size[1]): self.calc_potential((coordinates[0]-x,coordinates[1]+x), False)
            if (coordinates[0]-x >= 0) and (coordinates[1]-x >= 0): self.calc_potential((coordinates[0]-x,coordinates[1]-x), False)
        
        for axis in range(4):
            line = self.get_line(coordinates,axis)
            self.check_winner(line)

        if self.completed:
            print(fg(9)+'Game concluded! Winner is player {}, congratulations!'.format(int(self.winner))+fg.rs)     
            return 2, self.winner
        
        if not 0 in self.board[0,:,:]:
            self.completed = True
            print(fg(9)+'The game board is full and noone won... it\'s a tie!'+fg.rs)
            return 3, None
        
        return 1, None
        
    def get_line(self,coordinates,axis):
        freezei = True if axis==2 else False
        freezej = True if axis==0 else False
        
        i = coordinates[0] - (-4 if axis==3 else 0 if freezei else 4)
        j = coordinates[1] - (0 if freezej else 4)
        
        line = []
        
        for x in range(9):
            if x==4:
                line.append(8)
            else:
                line.append(9 if (i < 0) or (i > self.size[0]-1) or (j < 0) or (j > self.size[1]-1) else self.board[0,i,j])
            i += -1 if axis==3 else 1 if not freezei else 0
            j += 1 if not freezej else 0

        return np.array(line)             

    def check_winner(self,line):
        prev = 0
        cnt = 0
        for x in line:
            if x==prev and x!=0:
                cnt += 1
                if cnt==5:
                    self.winner = x
                    self.completed = True
            else:
                cnt = 1
            prev = x

    def line_potential(self,line,player):
        opponent = 1 if player==2 else 2
        line[line==9] = opponent            # 9 = beyond boundary
        line[line==8] = player              # 8 = the coordinate

        try:
            first = line.tolist()[3::-1].index(opponent)
        except ValueError:
            first = 4
        try:
            last = line.tolist()[5:].index(opponent)
        except ValueError:
            last = 4       
        
        left = 4 - 1 - first
        right = 5  + last 
        line[0:left+1] = opponent
        line[right:9] = opponent

        line_connected = line.copy()
        line_space = line.copy()
        
        line_space[line_space==0] = player
        line_space[line_space==opponent] = 0
        line_space[line_space==player] = 1
        line_connected[line_connected==opponent] = 0
        line_connected[line_connected==player] = 1
        line_score = self.score_connected*line_connected 

        first_my = line_connected.tolist().index(1)
        last_my = 8-line_connected.tolist()[::-1].index(1)
        free_space = line_space[max(0,first_my-1)] + line_space[min(8,last_my+1)]
        
        surewin = False
        sw_line = 0
        for sw in line_connected:
            sw_line += sw
            sw_line *= sw
            if sw_line==5 or (sw_line==4 and free_space==2): surewin = True
            
        return np.prod(line_score[line_score!=0])*self.score_space[int(sum(line_space))]*self.free_space_bonus[int(free_space)]*(10 if surewin else 1)
        
    def calc_potential(self,coordinates,init):
        potential = 0
        if self.board[0,coordinates[0],coordinates[1]] != 0:
            self.board[1,coordinates[0],coordinates[1]] = -999
            self.board[2,coordinates[0],coordinates[1]] = -999
            return

        potential += 1/round(abs(((self.size[0]-1)/2)-coordinates[0])+0.1)
        potential += 1/round(abs(((self.size[1]-1)/2)-coordinates[1])+0.1)
        
        potential1 = potential
        potential2 = potential

        for axis in range(4):
            line = self.get_line(coordinates,axis)
            potential1 += self.line_potential(line.copy(),1)
            potential2 += self.line_potential(line.copy(),2)  
        
        self.board[1,coordinates[0],coordinates[1]] = potential1
        self.board[2,coordinates[0],coordinates[1]] = potential2

    def get_play(self,player):       
        if player==1:
            priority_matrix = self.board[1,:,:]+(self.board[2,:,:]*np.maximum(np.full(self.size,self.players[player-1].dp)+(self.get_digits_vectorized(self.board[2,:,:])*self.players[player-1].dpt),np.full(self.size,0.75)))
        else:
            priority_matrix = self.board[2,:,:]+(self.board[1,:,:]*np.maximum(np.full(self.size,self.players[player-1].dp)+(self.get_digits_vectorized(self.board[1,:,:])*self.players[player-1].dpt),np.full(self.size,0.75)))
       
        maxv = np.max(priority_matrix)
        minv = maxv*(1-self.players[player-1].st)  
        p = 0
        maxp = 0
        winner = 0
        
        possibilities = np.nonzero(priority_matrix >= minv)
        
        for coordinate in zip(possibilities[0],possibilities[1]):
            if self.debug==2: print(fg(11)+'Player {} is considering coordinates {} with value {}...'.format(player,coordinate,priority_matrix[coordinate])+fg.rs)
            p = (priority_matrix[coordinate] - minv) * r.random()
            if p>maxp:
                maxp = p
                winner = coordinate
                
        return winner

    def get_digits(self,x):
        return len(str(int(x)))
    
    def set_player(self,player,dp,dpt,st):
        self.players[player-1].set_parameters(dp,dpt,st)
        