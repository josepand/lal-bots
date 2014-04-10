import numbers
import time
from pprint import pprint
from SevenEval import SevenEval
#from FiveEval import FiveEval
import irc.bot
import threading
import random
import urllib2, re
import sys
import csv
import pickle

#SUITS = [u'♠',u'♥',u'♦',u'♣']
SUITS = [u's',u'h',u'd',u'c']
RANKS = ['0','1','2','3','4','5','6','7','8','9','10','J','Q','K','A']

### Cards are integers from 0 to 51 - AAAAKKKKQQQQJJJJTTTT etc
#CARDNAMES = ['{} of {}'.format(RANKS[-a],SUITS[b]) for a in xrange(-14,-1) for b in 'SHDC']
CARDNAMES = ['{}{}'.format(RANKS[-a],SUITS[b]) for a in xrange(-14,-1) for b in xrange(4)]

SEVENEVAL = SevenEval().getRankOfSeven
print 'Seven'

STARTCHIPS = 10000
###

class PokerRoom(object):
    def __init__(self):
        
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
        
        self.db = open('pokerdb.dat','r+')
        
        self.db_data = pickle.load(self.db)
        
        #{'abc':1234,
        # 'def':5678,
        # 'ghi':9012}
        
    def add_player(self,player_name):
        for player in self.players:
            if player['name'] == player_name:
                print 'attempting to add duplicate player'
                return False
        self.players.insert(self.dealer_index,{player_name:self.db_data.get(player_name,STARTCHIPS)})
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
    
    def reset_hand(self):
        self.cards = {}
        self.award_pots() ### Just in case there are any left
    
    def next_hand(self):
        self.cards = {}
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
        self.db_data = pickle.load(self.db)
        for player in self.players:
            player['chips'] = self.db_data[player['name']]
    
    def deal_cards(self):
        for player in self.players:
            self.cards[player['name']] = (deck.pop(random.randint(0,len(deck)-1)),deck.pop(random.randint(0,len(deck)-1)))
            #self.connection.privmsg(player['name'],'Your cards this hand are: %s, %s' %(CARDNAMES[self.cards[player['name']][0]],CARDNAMES[self.cards[player['name']][1]]))
    
    def create_pot(self,amount,*players):
        pot = {'prize':amount,
               'playerlist':list(players)}
        self.pots.append(pot)
    
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