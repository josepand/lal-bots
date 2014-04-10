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

class BetBot(irc.bot.SingleServerIRCBot):
    
    def __init__(self, channel, nickname='bet', server='irc.rd.tandberg.com', port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.stats_site = 'http://10.47.196.80/average.php'
        
        self.version = 'v0.1'
        
        self.command_re = re.compile('%s: (.+)' % nickname)
        self.odds_re = re.compile('Place your bets please! Odds are (.+) for red, (.+) for blue and (.+) for a draw')
        self.avg_re = re.compile('Red has won (\d+) times and Blue has won (\d+) times.\s+There were (\d+) draws.')
        
    @property
    def balance(self):
        return self._balance
    
    @setter
    def balance(self,newbalance):
        self._balance = newbalance
        self.updated = True
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        #c.privmsg(self.channel, 'CurveBot %s. Type "curve: help" for more information.' % self.version)
    
    def on_join(self, c, e):
        source = e.source.nick
        if source in ('lutomlin','patrolbot','mario','curve'):
            self.connection.mode(self.channel,'+o %s' % source)

    def on_pubmsg(self, c, e):
        a = e.arguments[0]
        self.check_and_answer(e, a)
        return
    
    def on_privmsg(self, c, e):
        source = e.source.nick
        text = e.arguments[0].lower()
        if source == 'bowser':
            balance = float(text.lstrip('you have '))
            bet = self.calculate_f()*balance
    
    def check_and_answer(self, e, text):
        c = self.connection
        source = e.source.nick
        text = text.lower()
        
        command_match = self.command_re.match(text)
        if command_match is not None:
            command = command_match.groups()[0]
        else:
            return
        
        if source == 'bowser':
            odds_re_match = self.odds_re.match(text)
            if odds_re_match is None:
                return
            self.updated = False
            oddsr = odds_re_match.groups()[0]
            oddsb = odds_re_match.groups()[1]
            oddsd = odds_re_match.groups()[2]
            avgr,avgb,avgd = self.get_rbd_probabilities()
            c.privmsg(self.channel,'bowser: balance')
        else:
            possible_responses = ['What?','Go away, %s.' % source,'...','?']
            c.privmsg(self.channel,random.choice(possible_responses))
    
    def calculate_f(self,odds,pwin=0.5):
        f = (pwin*((1.0/odds)+1)-1)*odds
        return f
    
    def get_rbd_probabilities(self):
        try:
            average_url = urllib2.urlopen(self.stats_site)
            average_page = average_url.read()
            average_match = self.avg_re.findall(average_page)[1]
            if len(average_match.groups()) == 3:
                return average_match.groups()
            else:
                print 'Failed to retrieve average recent results! Exception %s. Returning standard values.' % str(err)
                print dir(err)
                return 0.45,0.45,0.1
        except Exception as err:
            print 'Failed to retrieve average recent results! Exception %s. Returning standard values.' % str(err)
            print dir(err)
            return 0.45,0.45,0.1
        
def main():
    import sys
    if len(sys.argv) != 4:
        print "Usage: curvebot.py <server[:port]> <channel> <nickname>"
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print "Error: Erroneous port."
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]

    bot = CurveBot(channel, nickname, server, port)
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()
    c = bot.connection