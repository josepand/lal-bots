import numbers
import time
from pprint import pprint,pformat
from SevenEval import SevenEval
#from FiveEval import FiveEval
import irc.bot
import threading
import random
import urllib2, re
import sys
import csv
import pickle

SEVENEVAL = SevenEval().getRankOfSeven

STARTCHIPS = 10000

class PokerRoom(object):
    def __init__(self):
        self.new_deck()
        
        self.players = []
        
        #[{'name':'abc',
        #  'chips':1234},
        # {'name':'def',
        #  'chips':5678}]
        
        self.cards = {}
        
        self.boardcards = []
        
        #{'abc':(1,2),
        # 'def':(3,4)}
        
        self.pots = []
        
        #{1234:['abc','def'],
        # 5678:['ghi','jkl']}
        
        self.dealer_index = 0
        
        self.db = open('pokerdb.dat','w+')
        
        self.load_db_data() #db = open('pokerdb.dat','w+')
        
        #self.db_data = pickle.load(self.db)
        
        #{'abc':1234,
        # 'def':5678,
        # 'ghi':9012}
        
    def add_player(self,player_name):
        for player in self.players:
            if player['name'] == player_name:
                print 'attempting to add duplicate player'
                return False
        self.players.insert(self.dealer_index,{'name':player_name,
                                               'chips':self.db_data.get(player_name,STARTCHIPS)})
        return True
        
    def remove_player(self, player_name):
        for player in self.players:
            if player['name'] == player_name:
                self.db_data[player['name']] = player['chips']
            self.players.remove(player)
            return True
        else:
            print 'Warning: Player not found: {}'.format(player_name)
            return False
    
    def new_deck(self):
        self.deck = [i for i in xrange(52)]
    
    def reset_hand(self):
        self.cards = {}
        self.new_deck()
        self.award_pots() ### Just in case there are any left
    
    def next_hand(self):
        self.cards = {}
        self.new_deck()
        self.award_pots() ### Just in case there are any left
        self.dealer_index += 1
        self.dealer_index %= len(self.players)
        
    def save_db_data(self):
        print 'saving db'
        for player in self.players:
            self.db_data[player['name']] = player['chips']
        pickle.dump(self.db_data, self.db)
    
    def load_db_data(self):
        print 'loading db'
        try:
            self.db_data = pickle.load(self.db)
        except EOFError as err:
            print 'DB Empty! Creating new.'
            self.db_data = {}
            self.save_db_data()
        for player in self.players:
            player['chips'] = self.db_data[player['name']]
        
    def pull_card(self):
        card = self.deck.pop(random.randint(0,len(self.deck)-1))
        return card
    
    def deal_cards(self):
        for player in self.players:
            self.cards[player['name']] = (self.pull_card(),self.pull_card())
            #self.connection.privmsg(player['name'],'Your cards this hand are: %s, %s' %(CARDNAMES[self.cards[player['name']][0]],CARDNAMES[self.cards[player['name']][1]]))
    
    def create_pot(self,amount,*players):
        pot = {'prize':amount,
               'playerlist':list(players)}
        self.pots.append(pot)
    
    def ftr(self):
        board = len(self.boardcards)
        
        if board == 0:
            for i in xrange(3):
                self.boardcards.append(self.pull_card())
        elif board == 3:
            self.boardcards.append(self.pull_card())
        elif board == 4:
            self.boardcards.append(self.pull_card())
        elif board == 5:
            print 'Calling ftr() with 5 cards out?'
        else:
            print 'Calling ftr() and something is bad; {}'.format(pformat(self.boardcards))
            
    def post_blinds(self):
        pass
    
    def award_pots(self):
        for pot in self.pots.iteritems():
            prize, playerlist = pot['prize'], pot['playerlist']
            playerorder = sorted(((SEVENEVAL(*(tuple(self.cards[player['name']]) + self.boardcards)),player) for player in playerlist),key = lambda p: p[0])
            winningplayers = [player for handrank,player in self.playerorder if handrank == playerorder[-1][0]]
            print 'awarding pot'
            pprint(prize)
            pprint(playerlist)
            pprint(winningplayers)
            for player in winningplayers:
                piece = (prize/len(winningplayers))
                prize -= piece
                self.players[player['name']] += piece
            if prize == 0:
                print 'pot awarded'
            elif prize >= 0:
                roundplayer = random.choice(winningplayers)
                prize -= prize
                self.players[roundplayer['name']] += prize
                print 'pot awarded, extra goes to {}'.format(roundplayer['name'])
            else:
                raise Exception('Awarded too many chips!')