from lalbot import LalBot
from pokerroom import PokerRoom
from pprint import pprint
import threading

class PokerBot(LalBot):
    
    _versionstr = 'v0.1'
    
    helpfile = ['''PokerBot %s''' % _versionstr,
                '''This is a poker bot that does basically nothing.''']
    def setup(self):
        self.hand_running = False
        self.room = PokerRoom()
        
        new_commands = {'join':self.add_player,
                        'leave':self.remove_player,
                        'rules':self.print_rules,
                        'cards':self.tell_cards,
                        'dbg_newhand':self.run_hand,
                        '(fold|check|call|bet|raise to|jam|shove|all in)( \d+)?':self.advance_action,
                        }
        
        self.commandlist.update(new_commands)
    
    def add_player(self,source,*pargs):
        if self.room.add_player(source):
            self.queue_message('Player {} joined the table.'.format(source))
    
    def remove_player(self,source,*pargs):
        if self.room.remove_player(source):
            self.queue_message('Player {} left the table.'.format(source))
            
    def print_rules(self,source,*pargs):
        self.queue_message('These are the rules. There are no rules.')
    
    def tell_stacks(self):
        pass
    
    def tell_cards(self,source,*pargs):
        cards = self.room.cards.get(source,None)
        if cards:
            self.queue_message('Your cards are: {} {}'.format(self.room.CARDNAMES[cards[0]],self.room.CARDNAMES[cards[1]]), important=True, channel=source)
        else:
            self.queue_message('You have no cards!', important=False, channel=source)
    
    def tell_all_cards(self,source,*pargs):
        for player in self.room.players:
            cards = self.room.cards.get(player['name'],None)
            if cards:
                self.queue_message('Your cards are: {} {}'.format(self.room.CARDNAMES[cards[0]],self.room.CARDNAMES[cards[1]]), important=True, channel=player['name'])
            else:
                self.queue_message('You have no cards!', important=False, channel=player['name'])
    
    def tell_sidepots(self,source,*pargs):
        pots = self.room.pots
        if self.room.current_pot:
            self.queue_message('Main pot contains ${}.'.format(self.room.current_pot))
        else:
            self.queue_message('Main pot is empty!')
        if not pots:
            self.queue_message('No side pots to play for.')
        for pot in pots:
            self.queue_message('A sidepot of ${} between {}'.format(pot['prize'],', '.join(pot['playerlist'])),True)
        
    def advance_action(self,source,*pargs):
        success = self.room.advance_action(source, *pargs)
        if success:
            if pargs[0] == 'fold':
                self.queue_message('{} folds.'.format(source))
            if pargs[0] == 'check':
                self.queue_message('{} checks.'.format(source))
            if pargs[0] == 'call':
                self.queue_message('{} calls ${}.'.format(source,pargs[1]))
            if pargs[0] == 'bet':
                self.queue_message('{} bets ${}.'.format(source,pargs[1]))
            if pargs[0] == 'raise to':
                self.queue_message('{} raises to ${}.'.format(source,pargs[1]))
            if pargs[0] in ['jam','all in','shove']:
                self.queue_message('{} moves all in!'.format(source))
            if not self.room.hand_running:
                self.queue_message('Action is on {}.'.format(self.room.get_action_player()))
            
    def run_hand(self):
        self.next_hand()
        self.room.deal_cards()
        for player in self.room.players:
            self.tell_cards(player['name'])
        self.room.post_blinds()
        
    def end_hand(self):
        self.hand_running = False
        
    def loop_thread(self):
        while True:
            if len(self.room.players) > 1 and not self.hand_running:
                self.run_hand()
            else:
                self.room.nudge() ### This probably isn't how you're meant to do it
                time.sleep(1)
                
    #def run_hands(self):
    #    while True:
    #        if len(self.players) > 1:
    #            ### Start a hand
    #            deck = [i for i in xrange(52)]
    #            self.privmsg(self.channel,'Dealing hand!')
    #            for player in self.players:
    #                self.cards[player['name']] = (deck.pop(random.randint(0,len(deck)-1)),deck.pop(random.randint(0,len(deck)-1)))
    #                self.connection.privmsg(player['name'],'Your cards this hand are: %s, %s' %(CARDNAMES[self.cards[player['name']][0]],CARDNAMES[self.cards[player['name']][1]]))
    #            self.action_player = self.players[(self.dealer_index+3)%len(self.players)]
    #            self.privmsg(self.channel,'Action is on %s' % self.action_player)
    #            
    #            ### Loop while we wait for response
    #            self.action_timer = time.time()
    #            while self._next_action is None and time.time() - self.action_timer < 300 and not hand_over:
    #                sleep(0.1)
    #                
    #            ### If we get no response
    #            if self._next_action is None:
    #                #self.privmsg(self.channel,'% folds!')
    #                self._next_action = (self.action_player,'fold')
    #                ### Do something to fold them
    #                
    #            
    #        else:
    #            sleep(1)
    
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
    c = bot.connection