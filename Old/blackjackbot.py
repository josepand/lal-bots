import numbers
import time
from pprint import pprint
#from FiveEval import FiveEval
import irc.bot
import threading
import random
import urllib2, re
import sys
import csv
import pickle
import copy

SUITS = [u'♠',u'♥',u'♦',u'♣']
RANKS = ['0','1','2','3','4','5','6','7','8','9','10','J','Q','K','A']
#RANKS = ['A','K','Q','J','10','9','8','7','6','5','4','3','2']

### Cards are integers from 0 to 51 - AAAAKKKKQQQQJJJJTTTT etc
CARDNAMES = ['{}{}'.format(RANKS[-a],SUITS[b]) for a in xrange(-14,-1) for b in xrange(4)]
NUM_DECKS = 4

class PokerBot(irc.bot.SingleServerIRCBot):
    
    def __init__(self, channel, nickname='jackbot', server='irc.rd.tandberg.com', port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        
        self.command_re = re.compile('%s: (.+)' % nickname)
        self.bet_re = re.compile('bet %d+')
        
        self.helptimer = time.time() - 12100
        
        self.helptext = ['''BlackjackBot %s - Alpha build! Not finished.''' % self.version,
                         ]
        
        self.rules = ['''rules''',
                      '''rules''']
        
        self.version = 'v0.1'
        
        self.players = []
        
        #[{'name':'abc',
        #  'chips':1234},
        # {'name':'def',
        #  'chips':5678}]
        
        self.cards = {}
        
        #{'abc':(1,2),
        # 'def':(3,4)}
        
        self.dealer_index = 0
        
        self.db = open('blackjackdb.dat','r+')
        
        self.db_data = pickle.load(self.db)
        
        #{'abc':1234,
        # 'def':5678,
        # 'ghi':9012}
        
        t = threading.Timer(1, self.run_hands)
        t.daemon = True
        t.start()
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        c.privmsg(self.channel, 'Blackjack Table %s. Type "sit in" to play!' % self.version)
    
    def on_join(self, c, e):
        source = e.source.nick
        if source in ('lutomlin','patrolbot','curve'):
            self.connection.mode(self.channel,'+o %s' % source)

    def on_pubmsg(self, c, e):
        a = e.arguments[0]
        self.check_and_answer(e, a)
        return
    
    def check_and_answer(self, e, text):
        c = self.connection
        source = e.source.nick
        text = text.lower()
        
        command_match = self.command_re.match(text)
        
        ### Help
        if command == 'help' and time.time() - self.helptimer > 60:
            self.helptimer = time.time()
            for text in self.helptext:
                self.c_pm(text)
                time.sleep(0.5)
                
        elif text == 'sit in':
            if source not in self.db_data:
                self.db_data[source] = STARTING_STACK
            self.players.insert((self.dealer_index+3)%len(self.players),self.db_data[source])
            self.save_db_data()
            
        elif text == 'sit out':
            self._next_action = (source,'fold')
            self.save_db_data()
            for player in self.players:
                if player['name'] == source:
                    self.players.remove(player)
        
        #elif text == '' and source == self.action_player:
        #    self._next_action = (source,text)
        #('bet xxx', 'check', 'shove', 'all in', 'fold', 'raise xxx', 'raise to xxx', 'call', 'stacks', 'action')
        
    def save_db_data(self):
        for player in self.players:
            self.db_data[player['name']] = player['chips']
        pickle.dump(self.db_data, self.db)
        
    
    def run_hand(self):
        players_in_hand = (player['name'] for player in self.players)
        deck = self.new_shuffle()
        self.privmsg(self.channel,'Dealing hand!')
        dealer_cards = [deck.pop(random.randint(0,len(deck)-1)),deck.pop(random.randint(0,len(deck)-1))]
        for player in players_in_hand:
            self.run_1p_hand(deck)
            self.cards[player] = [deck.pop(random.randint(0,len(deck)-1)),deck.pop(random.randint(0,len(deck)-1))]
            self.c_pm('%s: your cards this hand are: %s, %s' %(player,CARDNAMES[self.cards[player['name']][0]],CARDNAMES[self.cards[player['name']][1]]))
        for player in players_in_hand:
            if self.check_for_royalty(self.cards[player]):
                self.c_pm('%s: you have Blackjack! awarding 3 to 2.')
        
        self.cards = {}
    
    def run_1p_hand(self, deck):
        self.cards[player] = [deck.pop(random.randint(0,len(deck)-1)),deck.pop(random.randint(0,len(deck)-1))]
        self.privmsg(self.channel,'%s: your cards this hand are: %s, %s' %(player,CARDNAMES[self.cards[player['name']][0]],CARDNAMES[self.cards[player['name']][1]]))
        
    def new_shuffle(self):
        deck = [i for i in xrange(52)]*NUM_DECKS
        return deck
    
    def check_for_royalty(self, cards):
        for card in cards:
            if card in [0,1,2,3,52,53,54,55,104,105,106,107,156,157,158,159]:
                for card in cards:
                    pass
                
    def run_hands(self):
        while True:
            if len(self.players) > 1:
                ### Start a hand
                deck = [i for i in xrange(52)]
                for player in self.players:
                    self.cards[player['name']] = (deck.pop(random.randint(0,len(deck)-1)),deck.pop(random.randint(0,len(deck)-1)))
                self.action_player = self.players[(self.dealer_index+3)%len(self.players)]
                self.c_pm('Action is on %s' % self.action_player)
                
                ### Loop while we wait for response
                self.action_timer = time.time()
                while self._next_action is None and time.time() - self.action_timer < 300 and not hand_over:
                    sleep(0.1)
                    
                ### If we get no response
                if self._next_action is None:
                    #self.privmsg(self.channel,'% folds!')
                    self._next_action = (self.action_player,'fold')
                    ### Do something to fold them
                    
                
            else:
                sleep(1)
                
                
    def c_pm(self,msg,important=False):
        try:
            if important:
                self.connection.privmsg(self.channel,msg)
            else:
                self.connection.privmsg(self.channel,msg)
        except irc.client.ServerNotConnectedError as err:
            print 'Warning: {}'.format(err)
               