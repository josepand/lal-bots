#!/usr/bin/env python
# -*- coding=utf-8 -*-
from LalBot.lalbot import LalBot
from PokerRoom.pokerroom import PokerRoom
from pprint import pprint
import time
import datetime
import threading
from whitelist import WHITELIST

WEEKDAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

class PokerBot(LalBot):
    
    versionstr = 'v1.6.0'
    
    welcome_message = u'Internet Relay Poker {}. Type "poker: help" for more information.'.format(versionstr)
    
    player_whitelist = WHITELIST
    
    _currency = u'Ł'#u'$'
    _action_timeout = 1800
    
    def setup(self):
        self.hand_running = False
        self.allow_hand = True
        self.room = PokerRoom()
        
        self.join_wait = []
        self.leave_wait = []
        
        new_commands = {'demo':self.demo_cardnames,
                        'join':self.add_player,
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
                        'show my hand':self.show_hand,
                        #'dbg_newhand':self.run_hand,
                        'bar me':self.bar_player,
                        '(fold|fold and show|check|call|bet|raise by|raise to|jam|shove|all in)(?: (\d+))?\s{0,}$':self.advance_action,
                        }
        
        self.commandlist.update(new_commands)
    
        self.action_timer = time.time() + self._action_timeout
        
    @property
    def helpfile(self):
        try:
            n = self.connection.get_nickname()
        except AttributeError as err:
            n = 'poker'
        helpfile = [u'''PokerBot {}'''.format(self.versionstr),
                    u'''Type "{}: join" to join the table.'''.format(n),
                    u'''Type "{}: leave" to leave the table.'''.format(n),
                    u'''Type "{}: bar me" to ban yourself from the table (permamently!) if you have work to do.'''.format(n),
                    u'''Type "{}: rules" to show rules.'''.format(n),
                    u'''Type "{}: cards" for a reminder of your cards.'''.format(n),
                    u'''Type "{}: board" for a reminder of the board cards.'''.format(n),
                    u'''Type "{}: pots" to show who has a stake in which pot, and how much.'''.format(n),
                    u'''Type "{}: stacks" to see the players and stacks.'''.format(n),
                    u'''Type "{}: stack db" to see the whole stack database.'''.format(n),
                    u'''Type "{}: action" to prod the person whose turn it is.'''.format(n),
                    u'''Type "{}: challenge" to challenge a player to a game!'''.format(n),
                    u'''If you are out of chips, type "{}: rebuy" to get a new stack.'''.format(n.format(n)),
                    u'''Type "{}: fold/check/call/shove/jam/all in" to take the appropriate action.'''.format(n),
                    u'''Type "{}: bet [x]/raise by [x]/raise to [x]" to make the appropriate bet.'''.format(n),
                    u'''Type "{}: show my hand" to show other people your hand.'''.format(n),
                    u'''Typing "{}: fold and show" will show your hand before folding.'''.format(n),
                    u'''Good luck!''',
                    ]
        return helpfile
                
    @property
    def rulesfile(self):
        rulesfile = [u'''Texas Hold 'Em Poker is played at this table.''',
                     u'''Blinds on {} are {}{} and {}{} with no Ante.'''.format(WEEKDAYS[datetime.date.weekday(datetime.date.today())],
                                                                                self._currency,self.room.SMALL_BLIND,self._currency,self.room.SMALL_BLIND*2),
                     u'''Buyins are {}10000.'''.format(self._currency),
                     u'''Rebuying is allowed once per day.'''.format(self._currency),
                     u'''Visit http://en.wikipedia.org/wiki/Texas_hold_'em#Rules for an in-depth look at the rules.''',
                     u'''Visit http://en.wikipedia.org/wiki/List_of_poker_hands for a list of the possible hands you can make.''',
                     u'''Straight Flush > Quads > Full House > Flush > Straight > Trips > Two Pair > One Pair > High Card.''',
                     ]
        return rulesfile
        
    def add_player(self,source='',resp_dst='',*pargs):
        if source in self.player_whitelist:
            if self.room.hand_running:
                self.join_wait.append(source)
                self.queue_message(u'Player {} joined the table; will play next hand.'.format(source))
            else:
                if self.room.add_player(source):
                    self.queue_message(u'Player {} joined the table.'.format(source))
                else:
                    self.queue_message(u'You are already at the table, {}.'.format(source),False,resp_dst)
        else:
            self.queue_message(u'Sorry, {}, but you are barred from this table.'.format(source),False,resp_dst)
    
    def remove_player(self,source='',resp_dst='',*pargs):
        if self.room.hand_running:
            self.leave_wait.append(source)
            self.queue_message(u'Player {} left the table; will be out next hand.'.format(source))
        else:
            if self.room.remove_player(source):
                self.queue_message(u'Player {} left the table.'.format(source))
            else:
                self.queue_message(u'Thanks, {}.'.format(source),False,resp_dst)
    
    def bar_player(self,source='',resp_dst='',*pargs):
        if source in self.player_whitelist:
            self.player_whitelist.remove(source)
            self.queue_message('Good work, {}.'.format(source),False,resp_dst)
            self.remove_player(source)
            
    def change_out_table(self,source='',resp_dst='',*pargs):
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
                
    def check_busts(self,source='',resp_dst='',*pargs):
        if not self.room.hand_running:
            for player in self.room.players:
                if player['chips'] <= 0:
                    self.queue_message(u'{} is busted!'.format(player['name']))
            self.room.players = [p for p in self.room.players[:] if p['chips'] > 0]
            
    def rebuy(self,source,resp_dst='',*pargs):
        if self.room.rebuy_chips(source):
            self.add_player(source)
        else:
            self.queue_message(u'You cannot rebuy right now, {}.'.format(source),False,resp_dst)
    
    def print_rules(self,source='',resp_dst='',*pargs):
        if source == resp_dst:
            self.queue_message('Listing Rules in private message...',False,self.main_channel_name)
        for message in self.rulesfile:
            self.queue_message(message,True,resp_dst)
    
    def challenge(self,source,resp_dst='',*pargs):
            self.queue_message(u'{} has challenged you, {}!'.format(source,pargs[0]))
    
    def show_hand(self,source,resp_dst='',*pargs):
        if source in self.room.cards:
            cards = self.room.cards[source]
            self.queue_message(u'{} shows: {}{}'.format(source,self.room.CARDNAMES[cards[0]],self.room.CARDNAMES[cards[1]]), important=True, channel=self.main_channel_name)
    
    def demo_cardnames(self,source='',resp_dst='',*pargs):
        if source == 'lutomlin':
            self.queue_message(''.join(n for n in self.room.CARDNAMES[0:8]))
    
    def tell_cards(self,source='',resp_dst='',*pargs):
        cards = self.room.cards.get(source,None)
        if cards:
            self.queue_message(u'Your cards are: {}{}'.format(self.room.CARDNAMES[cards[0]],self.room.CARDNAMES[cards[1]]), important=True, channel=source)
        else:
            self.queue_message(u'You have no cards!',False,resp_dst)
    
    def tell_all_cards(self,source='',resp_dst='',*pargs):
        for player in self.room.players:
            cards = self.room.cards.get(player['name'],None)
            if cards:
                self.queue_message(u'Your cards are: {}{}'.format(self.room.CARDNAMES[cards[0]],self.room.CARDNAMES[cards[1]]), important=True, channel=player['name'])
            else:
                self.queue_message(u'You have no cards!', important=False, channel=player['name'])
    
    def tell_stacks(self,source='',resp_dst='',*pargs):
        pl = [u'{} (Stack: {}{})'.format(p['name'],self._currency,p['chips']) for p in self.room.players]
        self.queue_message(u'Players sitting at table (in order): {}'.format(' '.join(pl)),False,resp_dst)
        
    def tell_stack_db(self,source='',resp_dst='',*pargs):
        pl = [u'{} (Stack: {}{})'.format(p,self._currency,s['chips']) for p,s in self.room.db_data.iteritems()]
        self.queue_message(u'Player stacks: {}'.format(' '.join(pl)),False,resp_dst)
        
    def tell_sidepots(self,source='',resp_dst='',*pargs):
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
            
    def remind_action(self,source='',resp_dst='',newboard=False,*pargs):
        if self.room.hand_running:
            if newboard:
                self.queue_message(u'Action is on {}. Main pot is {}{}. Bet is at {}{}. Timer: {}s.'.format(self.room.get_action_player()['name'],
                                                                                                self._currency,self.room.current_pot,
                                                                                                self._currency,self.room.current_bet,
                                                                                                self.get_action_s()))
            else:
                self.queue_message(u'Action is on {}. Bet is at {}{}. Timer: {}s'.format(self.room.get_action_player()['name'],
                                                                              self._currency,self.room.current_bet,
                                                                              self.get_action_s()))
        else:
            self.queue_message(u'No hand in progress.',False,resp_dst)
            
    def tell_boardcards(self,source='',resp_dst='',*pargs):
        self.queue_message(u'Board: {}'.format(''.join([self.room.CARDNAMES[a] for a in self.room.boardcards])),important=True,channel=source)
        
    def tell_all_boardcards(self,source='',resp_dst='',*pargs):
        self.tell_boardcards(source=self.main_channel_name)#self.queue_message(u'Board: {}'.format(' '.join([self.room.CARDNAMES[a] for a in self.room.boardcards])),important=True)
        for player in self.room.players:
            self.tell_boardcards(source=player['name'])#self.queue_message(u'Board: {}'.format(' '.join([self.room.CARDNAMES[a] for a in self.room.boardcards])),important=True,channel=player['name'])
        
    def advance_action(self,source='',resp_dst='',*pargs):
        boardnum = len(self.room.boardcards)
        #try:
        if pargs[0] == 'fold and show':
            self.show_hand(source=source)
        success = self.room.advance_action(source, *pargs)
        #except Exception as err:
        #    success = str(err)
        if success is True:
            self.reset_action_timer()
            if pargs[0] == 'fold':
                self.queue_message(u'{} folds.'.format(source))
            if pargs[0] == 'fold and show':
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
            ### Sweet, sweet haxarounds
            if success == u"Can't raise with no previous bet!":
                self.advance_action(source,resp_dst,'bet',pargs[1])
            elif success in (u'No bet to call.',u'Bet is already matched!'):
                self.advance_action(source,resp_dst,'check')
            else:
                self.queue_message(u'Not a valid action! {}'.format(success.format(self._currency)),False,resp_dst) ###SMRT!
            
    def run_hand(self,source='',resp_dst='',*pargs):
        self.room.hand_running = True
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
        self.reset_action_timer()
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
            elif self.room.hand_running and self.get_action_s() < 0 and self.room.get_action_player():
                self.queue_message(u'Player {} has not acted in {}s - folding their hand and kicking them from table...'.format(self.room.get_action_player()['name'],
                                                                                                                              self._action_timeout))
                self.remove_player(self.room.get_action_player()['name'])
                self.advance_action(self.room.get_action_player()['name'],'','fold')
                self.reset_action_timer() ### Can get into loop if advance_action() is wrong for some reason
            else:
                #self.room.nudge() ### This probably isn't how you're meant to do it ### Not used :)
                time.sleep(1)
    
    def prevent_hand(self):
        self.queue_message(u'Closing table at the end of this hand for a reboot...')
        self.allow_hand = False
        
    def reset_action_timer(self):
        self.action_timer = time.time() + self._action_timeout
        
    def get_action_s(self):
        return int(self.action_timer - time.time())
        
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