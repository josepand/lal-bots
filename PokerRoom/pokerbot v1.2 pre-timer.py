#!/usr/bin/env python
# -*- coding=utf-8 -*-
from lalbot import LalBot
from pokerroom import PokerRoom
from pprint import pprint
import time
import threading

class PokerBot(LalBot):
    
    versionstr = 'v1.2'
    
    helpfile = [u'''PokerBot {}'''.format(versionstr),
                u'''This is a poker bot!''',
                u'''Type "poker: join" to join the table.''',
                u'''Type "poker: leave" to leave the table.''',
                u'''Type "poker: rules" to show rules.''',
                u'''Type "poker: cards" for a reminder of your cards.''',
                u'''Type "poker: board" for a reminder of the board cards.''',
                u'''Type "poker: pots" to show who has a stake in which pot, and how much.''',
                u'''Type "poker: stacks" to see the players and stacks.''',
                u'''Type "poker: stack db" to see the whole stack database.''',
                u'''Type "poker: action" to prod the person whose turn it is.''',
                u'''Type "poker: challenge" to challenge a player to a game!''',
                u'''If you are out of chips, type "poker: rebuy" to get a new stack.''',
                u'''Type "poker: fold/check/call/shove/jam/all in" to take the appropriate action.''',
                u'''Type "poker: bet [x]/raise by [x]/raise to [x]" to make the appropriate bet.''',
                u'''Good luck!''',
                ]
                
    welcome_message = u'Internet Relay Poker {}. Type "poker: help" for more information.'.format(versionstr)
    
    player_whitelist = ['aa',
                        'ianp',
                        'ob',
                        'aj',
                        'Christina',
                        'coread',
                        'ea',
                        'jobrandh',
                        'joe_and',
                        'littlerob',
                        'lutomlin',
                        #'rwge',
                        'shamayl',
                        'srj',
                        'tjw',
                        'uu',]
    
    _currency = u'$'
    
    def setup(self):
        self.hand_running = False
        self.allow_hand = True
        self.room = PokerRoom()
        
        self.join_wait = []
        self.leave_wait = []
        
        new_commands = {'join':self.add_player,
                        'leave':self.remove_player,
                        'rules':self.print_rules,
                        'cards':self.tell_cards,
                        'stacks':self.tell_stacks,
                        'stack db':self.tell_stack_db,
                        'pots':self.tell_sidepots,
                        'action':self.remind_action,
                        'challenge (.+)':self.challenge,
                        'board':self.tell_boardcards,
                        'rebuy':self.rebuy,
                        'dbg_newhand':self.run_hand,
                        '(fold|check|call|bet|raise by|raise to|jam|shove|all in)(?: (\d+))?\s+$':self.advance_action,
                        }
        
        self.commandlist.update(new_commands)
    
        self.rulesfile = [u'''Texas Hold 'Em Poker is played at this table.''',
                          u'''Blinds are {}{} and {}{} with no Ante.'''.format(self._currency,self.room.SMALL_BLIND,self._currency,self.room.SMALL_BLIND*2),
                          u'''Visit http://en.wikipedia.org/wiki/Texas_hold_'em#Rules for an in-depth look at the rules.''',
                          u'''Visit http://en.wikipedia.org/wiki/List_of_poker_hands for a list of the possible hands you can make.''',
                          ]
        
    def add_player(self,source='',*pargs):
        if source in self.player_whitelist:
            if self.room.hand_running:
                self.join_wait.append(source)
                self.queue_message(u'Player {} joined the table; will play next hand.'.format(source))
            else:
                if self.room.add_player(source):
                    self.queue_message(u'Player {} joined the table.'.format(source))
        else:
            self.queue_message(u'Sorry, {}, but you are barred from this table.'.format(source))
    
    def remove_player(self,source='',*pargs):
        if self.room.hand_running:
            self.leave_wait.append(source)
            self.queue_message(u'Player {} left the table; will be out next hand.'.format(source))
        else:
            if self.room.remove_player(source):
                self.queue_message(u'Player {} left the table.'.format(source))
                
    def change_out_table(self,source='',*pargs):
        if self.room.hand_running:
            return
        else:
            for player in self.join_wait:
                self.add_player(player)
                self.join_wait = []
            for player in self.leave_wait:
                self.remove_player(player)
                self.leave_wait = []
            self.check_busts()
                
    def check_busts(self,source='',*pargs):
        if not self.room.hand_running:
            for player in self.room.players:
                if player['chips'] <= 0:
                    #self.room.remove_player(player['name']) ### Doesn't work - modifying something you are currently iterating over...
                    self.queue_message(u'{} is busted!'.format(player['name']))
            self.room.players = [p for p in self.room.players[:] if p['chips'] > 0]
            
    def rebuy(self,source,*pargs):
        if source in self.room.db_data:
            if self.room.db_data[source] == 0:
                self.room.db_data[source] = 5000
                self.add_player(source)
    
    def print_rules(self,source='',*pargs):
        for message in self.rulesfile:
            self.queue_message(message)
    
    def challenge(self,source,*pargs):
            self.queue_message(u'{} has challenged you, {}!'.format(source,pargs[0]))
    
    def tell_cards(self,source='',*pargs):
        cards = self.room.cards.get(source,None)
        if cards:
            self.queue_message(u'Your cards are: {} {}'.format(self.room.CARDNAMES[cards[0]],self.room.CARDNAMES[cards[1]]), important=True, channel=source)
        else:
            self.queue_message(u'You have no cards!', important=False, channel=source)
    
    def tell_all_cards(self,source='',*pargs):
        for player in self.room.players:
            cards = self.room.cards.get(player['name'],None)
            if cards:
                self.queue_message(u'Your cards are: {} {}'.format(self.room.CARDNAMES[cards[0]],self.room.CARDNAMES[cards[1]]), important=True, channel=player['name'])
            else:
                self.queue_message(u'You have no cards!', important=False, channel=player['name'])
    
    def tell_stacks(self,source='',*pargs):
        pl = [u'{} (Stack: {}{})'.format(p['name'],self._currency,p['chips']) for p in self.room.players]
        self.queue_message(u'Players sitting at table (in order): {}'.format(' '.join(pl)))
        
    def tell_stack_db(self,source='',*pargs):
        pl = [u'{} (Stack: {}{})'.format(p,self._currency,s) for p,s in self.room.db_data.iteritems()]
        self.queue_message(u'Player stacks: {}'.format(' '.join(pl)))
        
    def tell_sidepots(self,source='',*pargs):
        pots = self.room.pots
        if self.room.current_pot:
            self.queue_message(u'Main pot (before this street) contains {}{}.'.format(self._currency,self.room.current_pot))
        else:
            self.queue_message(u'Main pot (before this street) is empty!')
            pass
        if not pots:
            #self.queue_message('No side pots to play for.')
            pass
        for pot in pots:
            self.queue_message(u'A sidepot of {}{} contested by {}'.format(self._currency,pot['prize'],', '.join([p['name'] for p in pot['playerlist']])),True)
            
    def remind_action(self,source='',newboard=False,*pargs):
        if self.room.hand_running:
            if newboard:
                self.queue_message(u'Action is on {}. Main pot is {}{}. Bet is at {}{}.'.format(self.room.get_action_player()['name'],
                                                                                                self._currency,self.room.current_pot,
                                                                                                self._currency,self.room.current_bet))
            else:
                self.queue_message(u'Action is on {}. Bet is at {}{}.'.format(self.room.get_action_player()['name'],
                                                                              self._currency,self.room.current_bet))
        else:
            self.queue_message(u'No hand in progress.')
            
    def tell_boardcards(self,source='',*pargs):
        self.queue_message(u'Board: {}'.format(' '.join([self.room.CARDNAMES[a] for a in self.room.boardcards])),important=True,channel=source)
        
    def tell_all_boardcards(self,source='',*pargs):
        self.tell_boardcards(source=self.main_channel_name)#self.queue_message(u'Board: {}'.format(' '.join([self.room.CARDNAMES[a] for a in self.room.boardcards])),important=True)
        for player in self.room.players:
            self.tell_boardcards(source=player['name'])#self.queue_message(u'Board: {}'.format(' '.join([self.room.CARDNAMES[a] for a in self.room.boardcards])),important=True,channel=player['name'])
        
    def advance_action(self,source='',*pargs):
        boardnum = len(self.room.boardcards)
        #try:
        success = self.room.advance_action(source, *pargs)
        #except Exception as err:
        #    success = str(err)
        if success is True:
            if pargs[0] == 'fold':
                self.queue_message(u'{} folds.'.format(source))
            if pargs[0] == 'check':
                self.queue_message(u'{} checks.'.format(source))
            if pargs[0] == 'call':
                self.queue_message(u'{} calls.'.format(source))
            if pargs[0] == 'bet':
                self.queue_message(u'{} bets {}{}.'.format(source,self._currency,pargs[1]))
            if pargs[0] == 'raise by':
                self.queue_message(u'{} raises another {}{}.'.format(source,self._currency,pargs[1]))
            if pargs[0] == 'raise to':
                self.queue_message(u'{} raises to {}{}.'.format(source,self._currency,pargs[1]))
            if pargs[0] in ['jam','all in','shove']:
                self.queue_message(u'{} moves all in!'.format(source))
            if self.room.hand_running:
                if boardnum != len(self.room.boardcards):
                    self.tell_all_boardcards()
                    self.remind_action(newboard=True)
                else:
                    self.remind_action(newboard=False)
            else:
                self.queue_message(u'Hand complete!')
                if self.room.return_cards():
                    self.tell_boardcards(source=self.main_channel_name)
                for player,cards in self.room.return_cards().iteritems():
                    self.queue_message(u'{} shows {}'.format(player,''.join(self.room.CARDNAMES[card] for card in cards)))
                for pot in self.room.return_pot_winners():
                    self.queue_message(u'Pot of {}{} won by {}'.format(self._currency,pot[0],', '.join(pot[1])))
        else:
            self.queue_message(u'Not a valid action! {}'.format(success.format(self._currency)))
            
    def run_hand(self,source='',*pargs):
        self.room.next_hand()
        self.room.deal_cards()
        print u'start of new hand'
        pprint(self.room.players)
        self.tell_stacks()
        dl, sb, bb = self.room.post_blinds()
        self.queue_message(u'{} is dealer, {} is small blind for {}{}, {} is big blind for {}{}'.format(dl,
                                                                                                        sb,self._currency,self.room.SMALL_BLIND,
                                                                                                        bb,self._currency,self.room.SMALL_BLIND*2))
        self.tell_all_cards()
        self.remind_action()
        
    def loop_thread(self):
        while True:
            if len(self.room.players) > 1 and not self.room.hand_running and self.allow_hand:
                self.change_out_table()
                if len(self.room.players) > 1:
                    self.queue_message(u'Next hand in 10...')
                    time.sleep(10)
                    self.check_busts()
                    if len(self.room.players) > 1:
                        self.run_hand()
                    else:
                        self.queue_message(u'Hand aborted - too few players.')
                else:
                    self.queue_message(u'Table suspended - too few players.')
            else:
                self.room.nudge() ### This probably isn't how you're meant to do it ### Not used :)
                time.sleep(1)
                
def main():
    import sys
    if len(sys.argv) <= 1:
        print "Usage: 'python -i lalbot.py <channel> [<nickname> [<server> [<port>]]]'"
        print "bot=self, c=self.connection"
        sys.exit(1)
    bot = PokerBot(*sys.argv[1:])
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()