from lalbot import LalBot
from pokerroom import PokerRoom
from pprint import pprint
import threading

SUITS = [u's',u'h',u'd',u'c']
RANKS = ['0','1','2','3','4','5','6','7','8','9','10','J','Q','K','A']

### Cards are integers from 0 to 51 - AAAAKKKKQQQQJJJJTTTT etc
#CARDNAMES = ['{} of {}'.format(RANKS[-a],SUITS[b]) for a in xrange(-14,-1) for b in 'SHDC']
CARDNAMES = ['{}{}'.format(RANKS[-a],SUITS[b]) for a in xrange(-14,-1) for b in xrange(4)]

class PokerBot(LalBot):
    
    _versionstr = 'v0.1'
    
    helpfile = ['''PokerBot %s''' % _versionstr,
                '''This is a poker bot that does basically nothing.''']
    def setup(self):
        
        self.room = PokerRoom()
        
        new_commands = {'join':self.add_player,
                        'leave':self.remove_player,
                        'rules':self.print_rules,
                        'cards':self.tell_cards,
                        'dbg_newhand':self.run_hand,
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
        
    def tell_cards(self,source,*pargs):
        cards = self.room.cards.get(source,None)
        if cards:
            self.queue_message('Your cards are: {} {}'.format(cards[0],cards[1]), important=True, channel=source)
            
    def run_hand(self):
        self.room.deal_cards()
        for player in self.room.players:
            self.tell_cards(player['name'])
            
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