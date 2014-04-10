#!/usr/bin/env python
# -*- coding=utf-8 -*- 
import numbers
import time
import datetime
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

class PokerRoom(object):
    
    #_HEART = unichr(0x2661)
    #_DIAMOND = unichr(0x2662)
    
    SUITS = [u'01♠',u'04♥',u'04♦',u'01♣']
    RANKS = [u'010',u'011',u'012',u'013',u'014',u'015',u'016',
             u'017',u'018',u'019',u'0110',u'01J',u'01Q',u'01K',u'01A']
    
    ### Cards are integers from 0 to 51 - AAAAKKKKQQQQJJJJTTTT etc
    #CARDNAMES = ['{} of {}'.format(RANKS[-a],SUITS[b]) for a in xrange(-14,-1) for b in 'SHDC']
    CARDNAMES = [u'{}{}'.format(RANKS[-a],SUITS[b]) for a in xrange(-14,-1) for b in xrange(4)]
    
    DEBUG = 1
    def log(self,msg,level=1):
        if self.DEBUG >= level:
            pprint(msg)
            
    #self.SMALL_BLIND = 25
    @property
    def SMALL_BLIND(self):
        dates = [10, ### Mon
                 25,
                 50,
                 75,
                 125,
                 200,
                 400] ### Sun
        #sb = 5 * datetime.date.isoweekday(datetime.date.today()) * datetime.date.isoweekday(datetime.date.today())
        sb = dates[datetime.date.weekday(datetime.date.today())] ### Don't play at midnight ¬_¬
        return sb
        
    def __init__(self):
        
        self.dealer_index = 0
        
        self.players = []
        
        self.reset_hand()
        
        self.hand_running = False
        self.hu_hand = False
        
        self.load_db_data() #db = open('PokerRoom/pokerdb.dat','w+')
        
    def add_player(self,player_name):
        self.log('add_player {}'.format(player_name),1)
        for player in self.players:
            if player['name'] == player_name:
                self.log('attempting to add duplicate player',0)
                return False
        if self.players:
            new_index = (self.dealer_index+2)%len(self.players)
        else:
            new_index = 0
        self.players.insert(new_index,{'name':player_name,
                                       'chips':self.db_data.get(player_name,{}).get('chips',STARTCHIPS),
                                       'in':0,
                                       'eligible':True,
                                       'last_rebuy':self.db_data.get(player_name,{}).get('last_rebuy',datetime.date(2013,12,10))})
        return True
        
    def remove_player(self, player_name):
        self.log('remove_player {}'.format(player_name))
        for player in self.players:
            if player['name'] == player_name:
                self.db_data[player['name']]['chips'] = player['chips']
                self.db_data[player['name']]['last_rebuy'] = player['last_rebuy']
                self.players.remove(player)
                return True
        else:
            self.log('Warning: Player not found: {}'.format(player_name),0)
            return False
    
    def get_action_player(self):
        self.log('get_action_player',2)
        if self.players and self.hand_running:
            playerindex = (self.action_player + self.dealer_index) + (1 if self.hu_hand and len(self.boardcards)> 0 else 0)
            player = self.players[playerindex%len(self.players)]
            return player
        else:
            return None
        
    def get_action_close(self):
        self.log('get_action_close',2)
        if self.players and self.hand_running:
            playerindex = (self.action_close+self.dealer_index) + (1 if self.hu_hand  and len(self.boardcards)> 0 else 0)
            player = self.players[playerindex%len(self.players)]
            return player
        else:
            return None
        
    def new_deck(self):
        self.deck = [i for i in xrange(52)]
    
    def reset_hand(self):
        self.log('reset_hand called',2)
        self.cards = {}
        self.new_deck()
        self.boardcards = []
        self.action_player = 1
        self.action_close = 0
        self.current_bet = 0
        self.current_pot = 0
        self.previous_raise_size = 0
        for p in self.players:
            p['eligible'] = True
        self.pots = []
    
    def next_hand(self):
        self.log('next_hand called',2)
        self.reset_hand()
        for player in self.players:
            if player['chips'] == 0:
                self.log('Warning! Player with 0 chips found ! {}'.format(player['name']),0)
                self.log(pformat(self.players),0)
        self.players = [p for p in self.players[:] if p['chips'] > 0] ### As a fix, breaks if we don't
        self.dealer_index += 1
        self.dealer_index %= len(self.players)
        
    ### db_data = {'abc':{'chips':123,
    #                     'last_rebuy':datetime.date}}
    
    
    def save_db_data(self):
        self.log('saving db')
        with open('PokerRoom/pokerdb.dat','w+') as self.db:
            for player in self.players:
                self.db_data[player['name']]['chips'] = player['chips']
                self.db_data[player['name']]['last_rebuy'] = player['last_rebuy']
            pprint(self.db_data)
            pickle.dump(self.db_data, self.db)
    
    def load_db_data(self):
        self.log('loading db')
        with open('PokerRoom/pokerdb.dat','r+') as self.db:
            try:
                self.db_data = pickle.load(self.db)
            except EOFError as err:
                self.log('DB Empty! Creating new.',0)
                self.db_data = {}
                self.save_db_data()
            for player in self.players:
                player['chips'] = self.db_data[player['name']]['chips']
                player['last_rebuy'] = self.db_data[player['name']]['last_rebuy']
        
    def player_rebuy_allowed(self,player_name):
        if player_name not in self.db_data or self.db_data[player_name]['last_rebuy'] >= datetime.date.today() or self.db_data[player_name]['chips'] > 0:
            self.log('rebuy not allowed for {}'.format(player_name),0)
            return False
        else:
            self.log('rebuy allowed for {}'.format(player_name))
            return True
    
    def rebuy_chips(self,player_name):
        self.log('trying rebuy for {}'.format(player_name),2)
        if self.player_rebuy_allowed(player_name):
            self.db_data[player_name]['chips'] = STARTCHIPS
            self.db_data[player_name]['last_rebuy'] = datetime.date.today()
            return True
        else:
            return False
            
    def pull_card(self):
        card = self.deck.pop(random.randint(0,len(self.deck)-1))
        return card
    
    def deal_cards(self):
        for player in self.players:
            self.cards[player['name']] = (self.pull_card(),self.pull_card())
            
    def post_blinds(self):
        self.hand_running = True
        di = self.dealer_index
        pc = len(self.players)
        
        if len(self.players) == 2:
            self.hu_hand = True
            dl = self.players[(di+1)%pc]
        else:
            self.hu_hand = False
            dl = self.players[di%pc]
        
        sb = self.players[(1+di)%pc]
        bb = self.players[(2+di)%pc]
        
        self.advance_action(sb['name'],'bet',self.SMALL_BLIND,forcesize=True)
        self.advance_action(bb['name'],'raise to',self.SMALL_BLIND*2,react=True,forcesize=True)
        
        self.previous_raise_size = self.SMALL_BLIND*2 ### Hax but normal raising thinks min reraise is 25...
        
        self.log('blinds posted')
        self.log(pformat(self.players),2)
        
        return dl['name'], sb['name'], bb['name']
        
    def advance_action(self,player_name,action,amount=None,react=False,forcesize=False):
        ### Actions in [fold, check, call, bet, raise]
        self.log('advance_action: {}, {}, {}, {}, {}'.format(player_name,action,amount,react,forcesize),1)
        player = self.get_action_player()
        if amount is not None:
            amount = int(amount)
        if player and player['name'] == player_name and self.hand_running:
            if action == 'fold':
                self.cards.pop(player_name)
            
            elif action == 'fold and show':
                self.cards.pop(player_name)
            
            elif action == 'check':
                if self.current_bet == 0 or self.current_bet == player['in']:
                    pass
                else:
                    return u'Bet is at {}{}.'.format('{}',self.current_bet)
            
            elif action == 'call':
                if self.current_bet == 0:
                    #self.log('player chose "call" with no bet - using check instead')
                    #return self.advance_action(player_name, 'check', amount, react, forcesize)
                    return u'No bet to call.'
                difference = self.current_bet - player['in']
                if difference <= 0:
                    #self.log('player chose "call" with no raise - using check instead')
                    #return self.advance_action(player_name, 'check', amount, react, forcesize) ### bad idea to do this in here...?
                    return u'Bet is already matched!'
                elif player['chips'] >= difference:
                    player['in'] += difference
                    player['chips'] -= difference
                else:
                    player['in'] += player['chips']
                    player['chips'] -= player['chips']
            
            elif action == 'bet':
                if amount > player['chips']:
                    return "You don't have that many chips."
                elif self.current_bet > 0:
                    return 'There is already a bet. Use "raise to" to raise.'
                elif amount < self.SMALL_BLIND*2 and not forcesize:
                    return "Minimum bet is {}.".format(self.SMALL_BLIND*2)
                else:
                    player['in'] += amount
                    player['chips'] -= amount
                self.action_close = (self.action_player-1)%len(self.players)
                self.current_bet = amount
                self.previous_raise_size = amount
            
            elif action == 'raise by':
                total = amount + self.current_bet
                difference = total - player['in']
                if difference > player['chips']:
                    return "You don't have that many chips."
                if self.current_bet == 0:
                    #self.log('player chose "raise by" with no bet - using bet instead')
                    #return self.advance_action(player_name,'bet',amount,react)
                    return u"Can't raise with no previous bet!"
                if amount < self.previous_raise_size and not forcesize:
                    return u'Too small a raise - minimum raise is {}{} more.'.format('{}',self.previous_raise_size)
                player['in'] += difference
                player['chips'] -= difference
                self.action_close = (self.action_player-1)%len(self.players)
                self.previous_raise_size = total - self.current_bet
                self.current_bet = total
                    
            elif action == 'raise to':
                difference = amount - player['in']
                if difference > player['chips']:
                    return "You don't have that many chips."
                if amount < self.current_bet:
                    return 'Bet is less than current bet.'
                if amount == self.current_bet:
                    return 'Bet is already that amount.'
                if self.current_bet == 0:
                    #self.log('player chose "raise to" with no bet - using bet instead')
                    #return self.advance_action(player_name,'bet',amount,react)
                    return u"Can't raise with no previous bet!"
                if amount - self.current_bet < self.previous_raise_size and not forcesize:
                    return u'Too small a raise - minimum raise is {}{} more.'.format('{}',self.previous_raise_size)
                player['in'] += difference
                player['chips'] -= difference
                self.action_close = (self.action_player-1)%len(self.players)
                self.previous_raise_size = amount - self.current_bet
                self.current_bet = amount
                
            elif action in ['jam','all in','shove',]:
                raise_amt = player['chips'] + player['in'] - self.current_bet
                if raise_amt <= 0: ### i.e. a call
                    if self.current_bet == 0:
                        return ". . You have no chips."
                    difference = self.current_bet - player['in']
                    if player['chips'] >= difference:
                        player['in'] += difference
                        player['chips'] -= difference
                    else:
                        player['in'] += player['chips']
                        player['chips'] -= player['chips']
                else:
                    amount = player['chips'] + player['in']
                    difference = amount - player['in']
                    if difference > player['chips']:
                        return "You don't have that much - probably an error here! lutomlin"
                    player['in'] += difference
                    player['chips'] -= difference
                    self.action_close = (self.action_player - 1)%len(self.players)
                    self.current_bet = amount
                    #print '{} raises ai'.format(player['name'])
            else:
                return 'Action not found - {}, {}, {}, {}, {}'.format(player_name,action,amount,react,forcesize)
            
            self.advance_player(react=react)
        else:
            self.log('Action is not on you, {}'.format(player_name))
            return 'Action is not on you, {}'.format(player_name)
        return True
    
    def advance_player(self,react=False):
        if self.action_player == self.action_close or len([p for p in self.players if p['eligible']]) <= 1:
            self.log('action_player {}, action_close {}, closing the action'.format(self.get_action_player()['name'], self.get_action_close()['name']),2)
            self.advance_street()
        else:
            self.action_player += 1
            self.action_player %= len(self.players)
            if react:
                self.log('player can re-act!',2)
                self.action_close += 1
                self.action_close %= len(self.players)
            #print 'action_player {}, action_close {}'.format(self.get_action_player()['name'], self.get_action_close()['name'])
            self.check_for_valid_player() ### Recursion can do weird things! This needs to be the last thing run.
                
        #10.47.196.215
    
    def check_for_valid_player(self):
        player = self.get_action_player()
        action_players = [p for p in self.players if p['name'] in self.cards and p['chips'] > 0]
        if len(action_players) == 1:
            self.log('1 action player - {}'.format(action_players[0]))
            
            self.log(action_players[0]['in'])
            self.log('current bet is {}'.format(self.current_bet),2)
            
            pass
        if len(action_players) == 1 and action_players[0]['in'] >= self.current_bet: ### Please let this not bork
            self.log('ready_to_skip',2)
            ready_to_skip = True
        elif len(action_players) == 0:
            self.log('ready_to_skip 0!',2)
            ready_to_skip = True
        else:
            ready_to_skip = False
        if player and player['name'] not in self.cards or player['chips'] == 0 or ready_to_skip:
            self.log('check_for_valid_player skipping {}'.format(player['name']),2)
            self.advance_player()
                
    def advance_street(self):
        print 'advance_street called'
        p_with_cards = [p for p in self.players if p['name'] in self.cards]
        #print 'pwc'
        #pprint(p_with_cards)
        sorted_p_with_in = sorted([pl for pl in self.players if pl['in'] > 0],key=lambda p: p['in'])
        while len(sorted_p_with_in) > 1:
            #print 'spwi'
            #pprint(sorted_p_with_in)
            amount = sorted_p_with_in[0]['in']
            if amount < sorted_p_with_in[1]['in'] and sorted_p_with_in[0]['name'] in self.cards or sorted_p_with_in[0]['chips'] == 0:
                self.create_pot(amount*len(sorted_p_with_in) + self.current_pot,[p for p in sorted_p_with_in if p['name'] in self.cards])
                for p in sorted_p_with_in:
                    p['in'] -= amount
                for p in self.players:
                    if p['name'] == sorted_p_with_in[0]['name']:
                        p['eligible'] = False
                self.current_pot = 0
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
            
            sorted_p_with_in.pop(0)
        if len(sorted_p_with_in) == 1:
            self.current_pot += sorted_p_with_in[0]['in']
            sorted_p_with_in[0]['in'] -= sorted_p_with_in[0]['in']
                
        ### Last: reset all 'in's, and if final street is over, make one last pot
        for p in self.players:
            p['in'] = 0
            
        if len(self.boardcards) == 5:
            self.create_pot(self.current_pot,(p for p in self.players if p['eligible'] and p['name'] in self.cards))
            self.current_pot = 0
            
        self.action_player = 1
        self.action_close = 0
        self.current_bet = 0
        
        if len([p for p in self.players if p['name'] in self.cards]) <= 1:
            self.create_pot(self.current_pot,(p for p in self.players if p['eligible'] and p['name'] in self.cards))
            self.current_pot = 0
            self.award_pots()
            self.hand_running = False
            #self.ftr()
            #self.advance_player()
        else:
            self.ftr()
    
    def ftr(self):
        board = len(self.boardcards)
        
        if board == 0:
            for i in xrange(3):
                self.boardcards.append(self.pull_card())
            #print 'Board is',
            #pprint([self.CARDNAMES[c] for c in self.boardcards])
            self.check_for_valid_player()
        elif board == 3:
            self.boardcards.append(self.pull_card())
            #print 'Board is',
            #pprint([self.CARDNAMES[c] for c in self.boardcards])
            self.check_for_valid_player()
        elif board == 4:
            self.boardcards.append(self.pull_card())
            #print 'Board is',
            #pprint([self.CARDNAMES[c] for c in self.boardcards])
            self.check_for_valid_player()
        elif board == 5:
            #print 'Final board is',
            #pprint([self.CARDNAMES[c] for c in self.boardcards])
            self.award_pots()
            self.save_db_data()
            self.hand_running = False
        else:
            print 'Calling ftr() and something is bad; {}'.format(pformat(self.boardcards))
            
    def nudge(self):
        pass
    
    def create_pot(self,amount,players):
        playerlist = list(players)
        
        print 'creating pot of {}'.format(amount)
        pprint(playerlist)
        
        if amount > 0:
            pot = {'prize':amount,
                   'playerlist':playerlist}
            self.pots.append(pot)
        else:
            print 'skipping empty pot'
    
    def return_cards(self):
        if len(self.cards) >= 2:
            return self.cards
        else:
            return {}
        
    def return_pot_winners(self):
        potwin = []
        p_with_cards = [p for p in self.players if p['name'] in self.cards]
        for pot in self.pots: ### TODO: De-duplicate this code
            prize, playerlist = pot['prize'], pot['playerlist']
            if len(p_with_cards) == 1:
                winningplayers = p_with_cards
            else:
                playerorder = sorted(((SEVENEVAL(*(self.cards[player['name']] + tuple(self.boardcards))),player) for player in playerlist if player['name'] in self.cards),key = lambda p: p[0])
                winningplayers = [player for handrank,player in playerorder if handrank == playerorder[-1][0]]
            
            potwin.append((pot['prize'],(p['name'] for p in winningplayers)))
        
        return potwin
    
    def award_pots(self):
        print 'awarding pots'
        pprint(self.pots)
        #for p,c in self.cards.iteritems():
        #    print p, self.CARDNAMES[c[0]], self.CARDNAMES[c[1]]
        #pprint([self.CARDNAMES[c] for c in self.boardcards])
        print 'pl before'
        pprint(self.players)
        p_with_cards = [p for p in self.players if p['name'] in self.cards]
        for pot in self.pots:
            prize, playerlist = pot['prize'], pot['playerlist']
            if len(p_with_cards) == 1:
                winningplayers = p_with_cards
            else:
                playerorder = sorted(((SEVENEVAL(*(self.cards[player['name']] + tuple(self.boardcards))),player) for player in playerlist if player['name'] in self.cards),key = lambda p: p[0])
                winningplayers = [player for handrank,player in playerorder if handrank == playerorder[-1][0]]
            print 'wp'
            pprint(winningplayers)
            piece = (prize/len(winningplayers))
            for player in winningplayers:
                prize -= piece
                for p in self.players:
                    if p['name'] == player['name']:
                        p['chips'] += piece
            if prize == 0:
                pass
            elif prize >= 0:
                roundplayer = random.choice(winningplayers)
                for p in self.players:
                    if p['name'] == roundplayer['name']:
                        p['chips'] += prize
                        prize -= prize
                print 'pot awarded, extra goes to {}'.format(roundplayer['name'])
            else:
                raise Exception('Awarded too many chips!')
            print 'pl after'
            pprint(self.players)
    
    def _unittest1(self):
        self.reset_hand()
        self.add_player('bb')
        self.add_player('sb')
        self.add_player('btn')
        self.deal_cards()
        self.post_blinds()
        self.advance_action('btn','all in')
        self.advance_action('sb','all in')
        self.advance_action('bb','all in')
        
    def _unittest2(self):
        self.reset_hand()
        self.add_player('bb')
        self.add_player('sb')
        self.add_player('btn')
        self.deal_cards()
        self.players[0]['chips'] = 100
        self.players[1]['chips'] = 1000
        self.post_blinds()
        self.advance_action('btn','call')
        self.advance_action('sb','call')
        self.advance_action('bb','call')
        self.advance_action('sb','all in')
        self.advance_action('bb','call')
        self.advance_action('btn','fold')
        
    def _unittest3(self):
        self.reset_hand()
        self.add_player('bb')
        self.add_player('sb')
        self.add_player('btn')
        self.deal_cards()
        self.players[0]['chips'] = 100
        self.players[1]['chips'] = 1000
        self.post_blinds()
        pprint(self.players)
        pprint(self.current_pot)
        self.advance_action('btn','call')
        self.advance_action('sb','call')
        self.advance_action('bb','call')
        pprint(self.players)
        pprint(self.current_pot)
        self.advance_action('sb','all in')
        self.advance_action('bb','call')
        self.advance_action('btn','all in')
        
    def _unittest4(self):
        self.reset_hand()
        self.add_player('utg')
        self.add_player('bb')
        self.add_player('sb')
        self.add_player('btn')
        self.deal_cards()
        self.players[0]['chips'] = 100
        self.players[1]['chips'] = 1000
        self.players[2]['chips'] = 10000
        self.players[3]['chips'] = 100000
        self.post_blinds()
        pprint(self.players)
        pprint(self.current_pot)
        self.advance_action('utg','call')
        self.advance_action('btn','call')
        self.advance_action('sb','call')
        self.advance_action('bb','call')
        pprint(self.players)
        pprint(self.current_pot)
        self.advance_action('sb','all in')
        self.advance_action('bb','call')
        self.advance_action('utg','call')
        self.advance_action('btn','call')
        pprint(self.players)
        pprint(self.current_pot)
        self.advance_action('bb','check')
        self.advance_action('utg','jam')
        self.advance_action('bb','fold')
        
    def _unittest5(self):
        self.reset_hand()
        self.add_player('utg')
        self.add_player('bb')
        self.add_player('sb')
        self.add_player('btn')
        self.deal_cards()
        self.players[0]['chips'] = 100
        self.players[1]['chips'] = 1000
        self.players[2]['chips'] = 10000
        self.players[3]['chips'] = 100000
        self.post_blinds()
        print 'debug:'
        pprint(self.players)
        pprint(self.current_pot)
        pprint(self.pots)
        print 'end debug'
        self.advance_action('utg','call')
        self.advance_action('btn','call')
        self.advance_action('sb','call')
        self.advance_action('bb','call')
        print 'debug:'
        pprint(self.players)
        pprint(self.current_pot)
        pprint(self.pots)
        print 'end debug'
        self.advance_action('sb','all in')
        self.advance_action('bb','call')
        self.advance_action('utg','call')
        self.advance_action('btn','call')
        print 'debug:'
        pprint(self.players)
        pprint(self.current_pot)
        pprint(self.pots)
        print 'end debug'
        self.advance_action('bb','check')
        self.advance_action('utg','jam')
        self.advance_action('bb','fold')
        
    def _unittest6(self):
        self.reset_hand()
        self.add_player('bb')
        self.add_player('sb')
        self.add_player('btn')
        self.deal_cards()
        self.players[0]['chips'] = 300
        self.players[1]['chips'] = 1000
        self.post_blinds()
        print self.advance_action('btn','rais', '300')
        print self.advance_action('btn','raise to', '300')
        #print self.advance_action('btn','raise to', '100')
        print self.advance_action('sb','call')
        print self.advance_action('bb','jam')
        #print self.advance_action('btn','call')
        print self.advance_action('sb','fold')
        
    def _unittest7(self):
        self.reset_hand()
        self.add_player('bb')
        self.add_player('sb')
        self.add_player('btn')
        self.deal_cards()
        self.players[0]['chips'] = 1000
        self.players[1]['chips'] = 1000
        self.post_blinds()
        print self.advance_action('btn','rais', '300')
        print self.advance_action('btn','raise by', '300')
        print 'debug:'
        pprint(self.players)
        #print self.advance_action('btn','raise to', '100')
        print self.advance_action('sb','call')
        print self.advance_action('bb','jam')
        print self.advance_action('btn','fold')
        print self.advance_action('sb','fold')
        
    def _unittest8(self):
        self.reset_hand()
        self.add_player('bb')
        self.add_player('sb')
        self.add_player('btn')
        self.deal_cards()
        self.players[0]['chips'] = 1000
        self.players[1]['chips'] = 1000
        self.post_blinds()
        print self.advance_action('btn','raise by', '10')
        print self.advance_action('btn','raise to', '10')
        print self.advance_action('btn','raise to', '70')
        print self.advance_action('btn','raise to', '99')
        print self.advance_action('btn','raise to', '50')
        print self.advance_action('btn','raise to', '20')
        print self.advance_action('btn','raise by', '49')
        print self.advance_action('btn','raise by', '50')
        print 'debug:'
        pprint(self.players)
        #print self.advance_action('btn','raise to', '100')
        # print self.advance_action('sb','call')
        # print self.advance_action('bb','jam')
        # print self.advance_action('btn','fold')
        # print self.advance_action('sb','fold')
        
if __name__ == "__main__":
    room = PokerRoom()