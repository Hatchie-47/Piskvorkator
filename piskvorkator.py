# -*- coding: utf-8 -*-
"""
Created on Wed Dec 30 17:51:22 2020

@author: Hatch
"""

import gameboard
import requests
import sys
import time
import configparser
import logging
import os
import getopt
from sty import fg, rs

class Piskvorkator():
    def __init__(self,debug):
        self.config = configparser.ConfigParser()
        self.debug = debug
        self.game_in_progress = 0
        self.logger = logging.getLogger('piskvorkator')
        self.logger.setLevel(logging.DEBUG)
        
    def start_game(self,force_game,force_reg):       
        if not os.path.exists('piskvorkator.ini'):
            self.config.add_section('config')
            self.config['config']['address'] = 'https://piskvorky.jobs.cz'
            self.config['config']['player_id'] = ''
            self.config['config']['player_token'] = ''
            
            self.config.add_section('ai')
            self.config['ai']['defense_parameter_1'] = '1.2'
            self.config['ai']['defense_parameter_tick_1'] = '-0.075'
            self.config['ai']['stochastic_rate_1'] = '0.01'
            self.config['ai']['defense_parameter_2'] = '1.2'
            self.config['ai']['defense_parameter_tick_2'] = '-0.075'
            self.config['ai']['stochastic_rate_2'] = '0.01'
            
            self.config.add_section('saved')
            self.config['saved']['game_token'] = ''
            
            with open('piskvorkator.ini', 'w') as configfile:
                self.config.write(configfile)
                
            print(fg(15)+'Configuration file was not found, created new!'+fg.rs)

        self.config.read('piskvorkator.ini')
        self.player_token = self.config['config']['player_token']
        self.player_id = self.config['config']['player_id']
        self.address = self.config['config']['address']
        
        if self.handle_login(force_reg)==0: return 0
        
        if len(self.config['saved']['game_token'])!=0:
            if force_game:
                print(fg(10)+'Saved game abandoned!'+fg.rs)   
            else:
                print(fg(10)+'Saved game found!'+fg.rs)
                return 4
        
        response = requests.post(self.address+'/api/v1/connect', json={'userToken':self.player_token})
        content = response.json()
        
        if response.status_code==201:
            print(fg(10)+'New game successfully started!'+fg.rs)
            self.game_token = content['gameToken']
            self.config['saved']['game_token'] = content['gameToken']
            with open('piskvorkator.ini', 'w') as configfile:
                self.config.write(configfile)
                
            self.gb = gameboard.Gameboard((40,58),self.debug,self.logger)  
            self.game_in_progress = 1
            self.configure_logger()
            return 1
        else:
            print(fg(9)+'Something went wrong! {}'.format(content['errors'])+fg.rs)
            return 0
     
    def check_status(self):
        response = requests.post(self.address+'/api/v1/checkStatus', json={'userToken':self.player_token,'gameToken':self.game_token})
        content = response.json()
        
        if response.status_code==200:
            self.player = 1 if content['playerCrossId']==self.player_id else 2
            self.opponent = 1 if self.player==2 else 2
            self.configure_ai()
            
            if content['playerCrossId']==None or content['playerCircleId']==None:
                print(fg(15)+'Connected, waiting for opponent...'+fg.rs)
                return 1
            else:
                print(fg(10)+'Game started!'+fg.rs)
                return 2

        elif response.status_code==226:
            self.game_in_progress = 0
            print(fg(10)+'Game already ended!'+fg.rs)
            return 5
        else:
            print(fg(9)+'Something went wrong! {}'.format(content['errors'])+fg.rs)
            return 0  
    
    def check_if_opponent_played(self):
        response = requests.post(self.address+'/api/v1/checkLastStatus', json={'userToken':self.player_token,'gameToken':self.game_token})
        content = response.json()
        
        if response.status_code==200:
            if content['actualPlayerId']==self.player_id:
                if len(content['coordinates'])==0:
                    print(fg(14)+'I start the game...'+fg.rs)
                else:
                    if content['coordinates'][0]['playerId']!=self.player_id:
                        coordinates = (content['coordinates'][0]['x'],content['coordinates'][0]['y'])
                        print(fg(12)+'Opponent played on coordinates {}!'.format(coordinates)+fg.rs)
                        self.gb.place_symbol(self.opponent,self.translate_coordinates(coordinates,0))
                    else:
                        print(fg(9)+'Jobs mixed up the turn order again...'+fg.rs)
                        return 4
                return 3
            else:
                print(fg(12)+'Opponent haven\'t played yet, waiting...'+fg.rs)
                return 2

        elif response.status_code==226:
            self.game_in_progress = 0
            print(fg(10)+'Game already ended!'+fg.rs)
            return 5
        else:
            print(fg(9)+'Something went wrong! {}'.format(content['errors'])+fg.rs)
            return 0  
    
    def play(self):
        coordinates = self.gb.get_play(self.player)
        jobs_coordinates = self.translate_coordinates(coordinates,1) 
        response = requests.post(self.address+'/api/v1/play', json={'userToken':self.player_token,'gameToken':self.game_token,'positionX':int(jobs_coordinates[0]),'positionY':int(jobs_coordinates[1])})
        content = response.json()
        
        if response.status_code==201:
            print(fg(14)+'I played on coordinates {}!'.format(jobs_coordinates)+fg.rs)
            self.gb.place_symbol(self.player,coordinates)
            return 2
        elif response.status_code==226:
            self.game_in_progress = 0
            print(fg(10)+'Game already ended!'+fg.rs)
            return 5
        else:
            print(fg(9)+'Something went wrong! {}'.format(content['errors'])+fg.rs)
            return 0

    def reconnect(self):
        if self.game_in_progress==0:
                self.game_token = self.config['saved']['game_token']
        
        print(fg(15)+'Attempting to reconnect...'+fg.rs)
        self.gb = gameboard.Gameboard((40,58),self.debug,self.logger)
        self.clear_log()
        self.configure_logger()
        response = requests.post(self.address+'/api/v1/checkStatus', json={'userToken':self.player_token,'gameToken':self.game_token})
        content = response.json()
        
        if response.status_code==200:
            if self.game_in_progress==0:
                self.player = 1 if content['playerCrossId']==self.player_id else 2
                self.opponent = 1 if self.player==2 else 2
                self.configure_ai()
            
            if content['playerCrossId']==None or content['playerCircleId']==None:
                print(fg(15)+'Connected, waiting for opponent...'+fg.rs)
                self.game_in_progress = 1
                return 1
            
            if len(content['coordinates'])==0:
                print(fg(10)+'Game started!'+fg.rs)
                self.game_in_progress = 1
                return 2
                
            last_coordinates = None
            for turn in reversed(content['coordinates']):
                coordinates = (turn['x'],turn['y'])
                pl = self.player if turn['playerId']==self.player_id else self.opponent
                self.gb.place_symbol(pl,self.translate_coordinates(coordinates,0))
                if pl==self.opponent: last_coordinates = coordinates
                if self.game_in_progress==0:
                    if pl==self.player:
                        print(fg(14)+'I played on coordinates {}!'.format(coordinates)+fg.rs)
                    else:
                        print(fg(12)+'Opponent played on coordinates {}!'.format(coordinates)+fg.rs)                        
                    
            if self.game_in_progress==1:
                print(fg(12)+'Reconnected, opponents last play was on coordinates {}'.format(last_coordinates)+fg.rs)   
             
            if content['actualPlayerId']==self.player_id:
                print(fg(14)+'It\'s my turn now...'+fg.rs)
                self.game_in_progress = 1
                return 3
            else:
                print(fg(12)+'It\'s opponents turn now, waiting...'+fg.rs)
                self.game_in_progress = 1
                return 2
                    
        elif response.status_code==226:
            self.game_in_progress = 0
            print(fg(10)+'Game already ended!'+fg.rs)
            return 5
        else:
            print(fg(9)+'Something went wrong! {}'.format(content['errors'])+fg.rs)
            if self.game_in_progress==1:
                self.config['saved']['game_token'] = ''
                with open('piskvorkator.ini', 'w') as configfile:
                    self.config.write(configfile)
            return 0  

    def check_winner(self):
        response = requests.post(self.address+'/api/v1/checkStatus', json={'userToken':self.player_token,'gameToken':self.game_token})
        content = response.json()
        
        if content['winnerId']==None: 
            print(fg(9)+'Something is weird, there is no winner...'+fg.rs)
            
        if content['winnerId']==self.player_id:
            print(fg(11)+'I won! GG!'+fg.rs)
        else:
            print(fg(9)+'I lost, I\'m sad...'+fg.rs)
        
        self.config['saved']['game_token'] = ''
        with open('piskvorkator.ini', 'w') as configfile:
            self.config.write(configfile)
        return 0                       
        
    def translate_coordinates(self,coordinates,direction):
        if direction==1:    #from Python to jobs
            return (-28+coordinates[1],20-coordinates[0])
        else:               #from Jobs to Python
            return (20-coordinates[1],28+coordinates[0])
        
    def configure_ai(self):
        self.gb.set_player(self.player,float(self.config['ai']['defense_parameter_'+str(self.player)]),float(self.config['ai']['defense_parameter_tick_'+str(self.player)]),float(self.config['ai']['stochastic_rate_'+str(self.player)]))

    def configure_logger(self):
        formatter = logging.Formatter('%(message)s')
        fileHandler = logging.FileHandler('saves/'+self.game_token+'.replay')
        fileHandler.setLevel(logging.DEBUG)
        fileHandler.setFormatter(formatter)
        self.logger.addHandler(fileHandler)
    
    def clear_log(self):
        with open('saves/'+self.game_token+'.replay', 'w'):
            pass
        
    def handle_login(self,force_reg):
        if self.config['config']['player_token']!='' and self.config['config']['player_id']!='' and not force_reg:
            return 1
        
        print(fg(15)+'New registration:')
        nickname = input('Input your nickname:')
        email = input('Input your email:'+fg.rs)
        
        response = requests.post(self.address+'/api/v1/user', json={'nickname':nickname, 'email':email})
        content = response.json()
        
        if response.status_code==201:
            print(fg(10)+'New user successfully created!'+fg.rs)
            self.config['config']['player_token'] = content['userToken']
            self.config['config']['player_id'] = content['userId']
            with open('piskvorkator.ini', 'w') as configfile:
                self.config.write(configfile)
            
            self.player_token = self.config['config']['player_token']
            self.player_id = self.config['config']['player_id']
            return 1
        else:
            print(fg(9)+'Something went wrong! {}'.format(content['errors'])+fg.rs)
            return 0
        

if __name__ == '__main__':
    ps = Piskvorkator(0)
    force_game = False
    force_reg = False
    
    msg = fg(9)+'Possible flags are -g to force new game even if one is saved and -r to force registration of new player!'+fg.rs   
    if len(sys.argv)>1:
        try:
            opts, args = getopt.getopt(sys.argv[1:],"gr")
        except getopt.GetoptError:
            print(msg)
            sys.exit()
            
        for opt, arg in opts:
            if opt=='-g':
                force_game = True
            elif opt=='-r':
                force_reg = True

    status = ps.start_game(force_game,force_reg)
    while status>0:
        if status==1:
            time.sleep(10)
            status = ps.check_status()
        if status==2:
            time.sleep(5)
            status = ps.check_if_opponent_played()
        if status==3:
            status = ps.play()
        if status==4:
            status = ps.reconnect()
        if status==5:
            status = ps.check_winner()