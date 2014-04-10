import numbers
import time
from pprint import pprint,pformat
from SevenEval import SevenEval
#from FiveEval import FiveEval
import threading
import random
import urllib2, re
import sys
import csv
import pickle

SEVENEVAL = SevenEval().getRankOfSeven

STARTCHIPS = 10000
SMALL_BLIND = 25

class PokerRoom(object):
    
    SUITS = [u's',u'h',u'd',u'c']
    RANKS = ['0','1','2','3','4','5','6','7','8','9','10','J','Q','K','A']
    
    ### Cards are integers from 0 to 51 - AAAAKKKKQQQQJJJJTTTT etc
    #CARDNAMES = ['{} of {}'.format(RANKS[-a],SUITS[b]) for a in xrange(-14,-1) for b in 'SHDC']
    CARDNAMES = ['{}{}'.format(RANKS[-a],SUITS[b]) for a in xrange(-14,-1) for b in xrange(4)]

    def __init__(self):
        self.new_deck()
        
        self.players = []
        self.action_player = 1
        self.action_close = 0
        self.current_bet = 0
        self.current_pot = 0
        
        #[{'name':'abc',
        #  'chips':1234,
        #  'in':123},
        # {'name':'def',
        #  'chips':5678,
        #  'in':567}]
        
        self.boardcards = []
        
        self.cards = {}
        
        #{'abc':(1,2),
        # 'def':(3,4)}
        
        self.pots = []
        
        #{1234:['abc','def'],
        # 5678:['ghi','jkl']}
        
        self.dealer_index = 0
        
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
                                               'chips':self.db_data.get(player_name,STARTCHIPS),
                                               'in':0,
                                               'eligible':True})
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
    
    def get_action_player(self):
        player = self.players[(self.action_player+self.dealer_index)%len(self.players)]
        return player
        
    def get_action_close(self):
        player = self.players[(self.action_close+self.dealer_index)%len(self.players)]
        return player
        
    def new_deck(self):
        self.deck = [i for i in xrange(52)]
    
    def reset_hand(self):
        self.cards = {}
        self.new_deck()
        self.boardcards = []
        self.action_player = 1
        self.action_close = 0
        self.current_bet = 0
        self.current_pot = 0
        for p in self.players:
            p['eligible'] = True
        self.award_pots() ### Just in case there are any left
        self.save_db_data()
    
    def next_hand(self):
        self.reset_hand()
        for player in self.players:
            if player['chips'] == 0:
                self.players.remove(player)
        self.dealer_index += 1
        self.dealer_index %= len(self.players)
        
    def save_db_data(self):
        print 'saving db'
        with open('pokerdb.dat','w+') as self.db:
            for player in self.players:
                self.db_data[player['name']] = player['chips']
            pickle.dump(self.db_data, self.db)
    
    def load_db_data(self):
        print 'loading db'
        with open('pokerdb.dat','r+') as self.db:
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
    
    def post_blinds(self):
        self.hand_running = True
        di = self.dealer_index
        pc = len(self.players)
        sb = self.players[(1+di)%pc]
        bb = self.players[(2+di)%pc]
        
        if sb['chips'] < SMALL_BLIND:
            sb['in'] = sb['chips']
            sb['chips'] = 0
        else:
            sb['in'] = SMALL_BLIND
            sb['chips'] -= SMALL_BLIND
            
        if bb['chips'] < SMALL_BLIND*2:
            bb['in'] = bb['chips']
            bb['chips'] = 0
        else:
            bb['in'] = SMALL_BLIND*2
            bb['chips'] -= SMALL_BLIND*2
            
        self.action_player += 1
        self.action_close = 1
        self.current_bet = SMALL_BLIND*2
        self.advance_player()
        
    def ftr(self):
        board = len(self.boardcards)
        
        if board == 0:
            for i in xrange(3):
                self.boardcards.append(self.pull_card())
            print 'Board {}'.format(' '.join([self.CARDNAMES[card] for card in self.boardcards]))
        elif board == 3:
            self.boardcards.append(self.pull_card())
            print 'Board {}'.format(' '.join([self.CARDNAMES[card] for card in self.boardcards]))
        elif board == 4:
            self.boardcards.append(self.pull_card())
            print 'Board {}'.format(' '.join([self.CARDNAMES[card] for card in self.boardcards]))
        elif board == 5:
            print 'Final board {}'.format(' '.join([self.CARDNAMES[card] for card in self.boardcards]))
            for player,cards in self.cards.iteritems():
                print player,self.CARDNAMES[cards[0]]+self.CARDNAMES[cards[1]]
            self.award_pots()
            self.hand_running = False
        else:
            print 'Calling ftr() and something is bad; {}'.format(pformat(self.boardcards))
            
    def advance_action(self,player_name,action,amount=None):
        ### Actions in [fold, check, call, bet, raise]
        player = self.get_action_player()
        if player['name'] == player_name:
            if action == 'fold':
                self.cards.pop(player_name)
                print '{} folds'.format(player['name'])
            
            elif action == 'check':
                if self.current_bet == 0:
                    pass
                else:
                    return False
                print '{} checks'.format(player['name'])
            
            elif action == 'call':
                if self.current_bet == 0:
                    return False
                difference = self.current_bet - player['in']
                if player['chips'] >= difference:
                    player['in'] += difference
                    player['chips'] -= difference
                else:
                    player['in'] += player['chips']
                    player['chips'] -= player['chips']
                print '{} calls'.format(player['name'])
            
            elif action == 'bet':
                if amount > player['chips']:
                    return False
                elif self.current_bet > 0:
                    return False
                else:
                    player['in'] += amount
                    player['chips'] -= amount
                self.action_close = (self.action_player - 1)%len(self.players)
                self.current_bet = amount
                print '{} bets'.format(player['name'])
            
            elif action == 'raise to':
                difference = amount - player['in']
                if difference > player['chips']:
                    return False
                player['in'] += difference
                player['chips'] -= difference
                self.action_close = (self.action_player - 1)%len(self.players)
                self.current_bet = amount
                print '{} raises'.format(player['name'])
            
            elif action in ['jam','all in','shove',]:
                raise_amt = player['chips'] + player['in'] - self.current_bet
                if raise_amt <= 0: ### i.e. a call
                    if self.current_bet == 0:
                        return False
                    difference = self.current_bet - player['in']
                    if player['chips'] >= difference:
                        player['in'] += difference
                        player['chips'] -= difference
                    else:
                        player['in'] += player['chips']
                        player['chips'] -= player['chips']
                    print '{} calls ai'.format(player['name'])
                else:
                    amount = player['chips'] + player['in']
                    difference = amount - player['in']
                    if difference > player['chips']:
                        return False
                    player['in'] += difference
                    player['chips'] -= difference
                    self.action_close = (self.action_player - 1)%len(self.players)
                    self.current_bet = amount
                    print '{} raises ai'.format(player['name'])
                    
            
            self.advance_player()
        else:
            return False
        return True
    
    def advance_player(self):
        print 'action_player {}, action_close {}'.format(self.get_action_player()['name'], self.get_action_close()['name'])
        if self.action_player == self.action_close or len([p for p in self.players if p['eligible']]) <= 1:
            self.advance_street()
        else:
            self.action_player += 1
            self.action_player %= len(self.players)
            player = self.get_action_player()
            if player['name'] not in self.cards or player['chips'] == 0:
                self.advance_player()
                
        #10.47.196.215
        
    def advance_street(self):
        p_with_cards = [p for p in self.players if p['name'] in self.cards]
        sorted_p_with_in = sorted(self.players,key=lambda p: p['in'])
        while len(sorted_p_with_in) > 1:
            amount = sorted_p_with_in[0]['in']
            if amount < sorted_p_with_in[1]['in'] and sorted_p_with_in[0]['name'] in self.cards:
                self.create_pot(amount*len(sorted_p_with_in) + self.current_pot,[p for p in sorted_p_with_in if p['name'] in self.cards])
                for p in sorted_p_with_in:
                    p['in'] -= amount
            elif amount < sorted_p_with_in[1]['in'] and sorted_p_with_in[0]['name'] not in self.cards:
                self.current_pot += amount
                sorted_p_with_in[0]['in'] -= amount
                #sorted_p_with_in[0]['eligible'] = False
            elif amount == sorted_p_with_in[1]['in']:
                self.current_pot += amount
                sorted_p_with_in[0]['in'] -= amount
            else:
                pprint(self.players)
                pprint(sorted_p_with_in)
                raise Exception('How are we here?')
            
            if amount < sorted_p_with_in[-1]['in']:
                for p in self.players:
                    if p['name'] == sorted_p_with_in[0]['name']:
                        p['eligible'] = False
            #else:
            #    for p in self.players:
            #        if p['name'] == sorted_p_with_in[0]['name']:
            #            p['eligible'] = True
                        
            sorted_p_with_in.pop(0)
        else:
            if len(sorted_p_with_in) == 1:
                self.current_pot += sorted_p_with_in[0]['in']
                sorted_p_with_in[0]['in'] -= sorted_p_with_in[0]['in']
                
        ### Last: reset all 'in's, and if final street is over, make one last pot
        for p in self.players:
            p['in'] = 0
            
        if len(self.boardcards) == 5:
            self.create_pot(self.current_pot,(p for p in self.players if p['eligible']))
            self.current_pot = 0
            
        self.action_player = 1
        self.action_close = 0
        self.current_bet = 0
        if len([p for p in self.players if p['eligible']]) <= 1 and len(self.boardcards) < 5:
            self.ftr()
            self.advance_player()
        else:
            self.ftr()
    
        ### NOPE.
        #for player in self.players:
        #    if player['name'] not in self.cards:
        #        self.current_pot += player['in']
        #        player['in'] -= player['in']
                
        ### NOPE.
        #new_playerlist = sorted([p for p in self.players if p['name'] in self.cards],key=lambda p: p['in'])
        #while not all(player['in'] == new_playerlist[0]['in'] for player in new_playerlist if player['name'] in self.cards):
        #    if new_playerlist[0]['in'] > 0:
        #        prize = new_playerlist[0]['in']*len(new_playerlist)
        #        self.create_pot(prize+self.current_pot,[p for p in new_playerlist if p['name'] in self.cards])
        #        self.current_pot = 0
        #        for xp in new_playerlist:
        #            xp['in'] -= new_playerlist[0]['in']
        #    new_playerlist.remove(new_playerlist[0])
        #self.current_pot += new_playerlist[0]['in']*len(new_playerlist)

    def nudge(self):
        pass
    
    def create_pot(self,amount,players):
        pot = {'prize':amount,
               'playerlist':list(players)}
        self.pots.append(pot)
    
    def award_pots(self):
        for pot in self.pots:
            prize, playerlist = pot['prize'], pot['playerlist']
            playerorder = sorted(((SEVENEVAL(*(self.cards[player['name']] + tuple(self.boardcards))),player) for player in playerlist),key = lambda p: p[0])
            winningplayers = [player for handrank,player in playerorder if handrank == playerorder[-1][0]]
            for player in winningplayers:
                piece = (prize/len(winningplayers))
                prize -= piece
                for p in self.players:
                    if p['name'] == player['name']:
                        p['chips'] += piece
            if prize == 0:
                self.pots.remove(pot)
            elif prize >= 0:
                roundplayer = random.choice(winningplayers)
                prize -= prize
                self.players[roundplayer['name']] += prize
                print 'pot awarded, extra goes to {}'.format(roundplayer['name'])
                self.pots.remove(pot)
            else:
                raise Exception('Awarded too many chips!')
            
if __name__ == "__main__":
    room = PokerRoom()
    room.add_player('bb')
    room.add_player('sb')
    room.add_player('btn')
    room.deal_cards()
    room.post_blinds()
    pprint(room.players)
    room.advance_action('btn','raise to',200)
    room.advance_action('sb','call')
    room.advance_action('bb','fold')
    room.advance_action('sb','check')
    room.advance_action('btn','check')
    room.advance_action('sb','check')
    room.advance_action('btn','check')
    room.advance_action('sb','check')
    room.advance_action('btn','check')
    pprint(room.players)