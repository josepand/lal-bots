#! /usr/bin/env python
# 
# based on a python libirc example by Joel Rosdahl <joel@rosdahl.net>

import irc.bot
#import irc.strings
#from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
import threading
import random
from datetime import date
import urllib2, re
import time
from pprint import pprint
import sys
from whitelist import BUZZPLAYERS, WHITELIST

class CurveBot(irc.bot.SingleServerIRCBot):
    
    def __init__(self, channel, nickname='curve', server='irc.rd.tandberg.com', port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        
        self.version = 'v1.2'
        
        self.more_players_re = re.compile('([1234567]) more')
        self.command_re = re.compile('%s: (.+)' % nickname)
        #self.booking_type_re = re.compile('mario: book (.+)')
        #self.booking_types = {'mario kart':'Mario Kart',
        #                      'mario':'Mario Kart',
        #                      'kart':'Mario Kart',
        #                      'f0':'F-Zero GX',
        #                      'fzero':'F-Zero GX',
        #                      'f-zero':'F-Zero GX',
        #                      'f zero':'F-Zero GX',
        #                      'f-zero gx':'F-Zero GX',
        #                      'smash bros':'Super Smash Bros Brawl',
        #                      'smash':'Super Smash Bros Brawl',
        #                      'ssbb':'Super Smash Bros Brawl',
        #                      }
        #
        #_future_helptext = ['''Type "mario: book [game name]" to book the Wii for your chosen game.''',
        #                    '''Available games are F-Zero, Mario Kart and Smash Bros.''']
        
        self.isBooked = False
        self.booker = ''
        self.bookingtime = 0
        self.required = 0
        self.helptimer = time.time() - 12100
        self.capstimer = time.time() - 12100
        self.rulestimer = time.time() - 12100
        self.buzztimer = time.time() - 12100
        self.allow_eggs = True
        
        self.ready_players = []
        
        self.helptext = ['''CurveFever organiser %s''' % self.version,
                         '''Type "curve: [1234567] more" to start a game!''',
                         '''Type "curve: where" for a quick hotlink.''',
                         '''Type "curve: end" to end the game.''',
                         ]
        
        self.possible_yes = ('yes', 'aye', 'yeah', 'y', 'yup', 'yer', 'yeh', 'yah', 'ja', 'yarr', 'yar', 'si', 'oui', 'yesz', 'yep', 'ok', 'go on then', 'alright', 'okay', 'why not',
                             'fine', 'damn right', 'absolutely', 'obviously', 'seems reasonable', 'fuck yeah', 'jawohl', 'hell yes', 'k', '-.-- . ...')
        
        self.buzz_players = BUZZPLAYERS
        
        self.player_whitelist = WHITELIST
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        c.privmsg(self.channel, 'CurveBot %s. Type "curve: help" for more information.' % self.version)
    
    def on_join(self, c, e):
        source = e.source.nick
        if source in ('lutomlin','patrolbot','mario'):
            self.connection.mode(self.channel,'+o %s' % source)

    def on_kick(self, c, e):
        if e.arguments[0] == c.get_nickname():
            c.join(self.channel)
            c.privmsg(self.channel, 'CurveBot %s. Type "curve: help" for more information.' % self.version)
            
    #def on_privmsg(self, c, e):
    #    source = e.source.nick
    #    text = e.arguments[0].lower()
    #    if source == 'lutomlin' and text == 'op':
    #        self.connection.mode(self.channel,'+o %s' % source)
            
    def on_pubmsg(self, c, e):
        a = e.arguments[0]
        self.check_and_answer(e, a)
        return
    
    def check_and_answer(self, e, text):
        c = self.connection
        source = e.source.nick
        text = text.lower()
        
        command_match = self.command_re.match(text)
        if command_match is not None:
            command = command_match.groups()[0]
        else:
            return
        
        ### Help
        if command == 'help' and time.time() - self.helptimer > 60:
            self.helptimer = time.time()
            for text in self.helptext:
                c.privmsg(self.channel, text)
                time.sleep(0.5)
        
        lfgre = self.more_players_re.match(command) ### 'mario: X more'
        if lfgre:
            if source not in self.player_whitelist:
                c.privmsg(self.channel,'Go away, %s.' % source)
            else:
                self.isBooked = True
                self.booker = source
                self.ready_players = [source]
                self.bookingtime = time.time()
                #self.buzztimer = time.time() - 12100
                self.required = int(lfgre.groups()[0])
                c.privmsg(self.channel, '%s is looking for %d more players; type "curve: yes" to join!' % (self.booker,self.required))
                time.sleep(0.5)
                c.privmsg(self.channel, 'Quick link: http://curvefever.com/play2.php')
                time.sleep(0.5)
                c.privmsg(self.channel, 'Room "langley", password "telepresence"')
                if 6 <= self.required <= 7:
                    time.sleep(0.5)
                    c.privmsg(self.channel, 'Premium 8 player game required!')
            #else:
            #    c.privmsg(self.channel, 'Game already created by %s!' % self.booker)
        
        if command in self.possible_yes and 1 <= self.required <= 7:
            if source not in self.player_whitelist:
                c.privmsg(self.channel,'Go away, %s.' % source)
            else:
                self.required -= 1
                if self.required > 0:
                    self.ready_players.append(source)
                    c.privmsg(self.channel, '%s joined, room for %s more; type "curve: yes" to join!' % (source,self.required))
                elif self.required == 0:
                    self.bookingtime = time.time()
                    self.ready_players.append(source)
                    c.privmsg(self.channel, '%s joined; the game is now full!' % source)
                    self.ready_players = []
                    
        elif command == 'check':
            if self.isBooked:
                c.privmsg(self.channel, 'Game already created by %s!' % self.booker)
                self.ready_players = []
            else:
                c.privmsg(self.channel, 'No game at the moment.')
        
        elif command == 'where':
            c.privmsg(self.channel,'http://curvefever.com/play2.php')
            
        elif command == 'end' and (self.booker == source or source == 'lutomlin'):
            self.isBooked = False
            self.required = 0
            self.booker = ''
            self.ready_players = []
            c.privmsg(self.channel, 'Game is over. Type "curve: [1234567] more" to start a new one!')
            
        elif command == 'buzz' and self.booker == source and time.time() - self.buzztimer > 60:
            self.buzztimer = time.time()
            c.privmsg(self.channel,' '.join(self.buzz_players))
        
        elif command == 'version':
            c.privmsg(self.channel,self.version)
        
        ### Easter Eggs
        elif command == 'crash':
            c.privmsg(self.channel,'No.')
            
        elif command == 'yes?':
            c.privmsg(self.channel,', '.join(self.possible_yes))
            
def main():
    import sys
    if len(sys.argv) != 4:
        print "Usage: curvebot.py  <channel> <nickname> [<server[:port]>]"
        sys.exit(1)

    #s = sys.argv[1].split(":", 1)
    #server = s[0]
    #if len(s) == 2:
    #    try:
    #        port = int(s[1])
    #    except ValueError:
    #        print "Error: Erroneous port."
    #        sys.exit(1)
    #else:
    #    port = 6667
    #channel = sys.argv[2]
    #nickname = sys.argv[3]

    bot = CurveBot(*sys.argv[1:])#channel, nickname, server, port)
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()
    c = bot.connection