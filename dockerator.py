# -*- coding: utf-8 -*-
"""
Created on Sat Jan  9 14:32:02 2021

@author: Hatch
"""

import gameboard as gb
import piskvorkator
import signal
import time
from sty import fg, rs

class Dockerator():
    def __init__(self):
        self.ps = piskvorkator.Piskvorkator(0)
        self.run = True
        self.restart = False
        self.new_game = False
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        signal.signal(signal.SIGUSR1, self.handle_restart)
        signal.signal(signal.SIGUSR2, self.handle_newgame)
        
    def work(self):
        self.run = True
        while self.run:
            if self.new_game:
                status = self.ps.start_game(True,False)
                self.new_game = False
            else:
                status = self.ps.start_game(False,False)

            while status>0:
                if status==1:
                    time.sleep(10)
                    status = self.ps.check_status()
                if status==2:
                    time.sleep(5)
                    status = self.ps.check_if_opponent_played()
                if status==3:
                    status = self.ps.play()
                if status==4:
                    status = self.ps.reconnect()
                if status==5:
                    status = self.ps.check_winner()
                if self.restart:
                    status = 0
                    self.restart = False   
        gb.custom_print('Run ended!',15)

    def handle_sigterm(self,signum,frame):
        gb.custom_print('Stop command received, will not start another game!',15)
        self.run = False
    
    def handle_restart(self,signum,frame):
        gb.custom_print('Restart command received, will restart Piskvorkator!',15)
        self.restart = True

    def handle_newgame(self,signum,frame):
        gb.custom_print('New game command received, will start a new game!',15)
        self.new_game = True
        self.restart = True
    
if __name__ == '__main__':
    dc = Dockerator()
    dc.work()