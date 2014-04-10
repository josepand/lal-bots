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

class PatrolBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname='patrolbot', server='irc.rd.tandberg.com', port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.command_re = re.compile('%s: (.+)' % nickname)
        self.version = 'v0.3'
        self.helptimer = time.time() - 12100
        self.helptext = ['''%s. Don't mess with this bot.''' % self.version,
                         ]
        
        self.channel_whitelist = [  'aa',
                                    'ianp',
                                    'ob',
                                    'aj',
                                    'bowser',
                                    'coread',
                                    'curve',
                                    'dh',
                                    'ea',
                                    'eah',
                                    'jobrandh',
                                    'joe_and',
                                    'jr',
                                    'littlerob',
                                    'lutomlin',
                                    'mario',
                                    'patrolbot',
                                    'rwge',
                                    'seabee',
                                    'srj',
                                    'tjw',
                                    'uu',
                                    'daisy',
                                    'diddykong',
                                    'drybones',
                                    'kingboo',
                                    'luigi',
                                    'toadette',
                                    ]
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        c.privmsg(self.channel, 'PatrolBot %s in operation. Do not resist.' % self.version)
    
    def on_join(self, c, e):
        source = e.source.nick
        if source in ('lutomlin','mario','curve'):
            self.connection.mode(self.channel,'+o %s' % source)
        elif source not in self.channel_whitelist:
            self.connection.kick(self.channel,source,'Detected resistance! Resistance is futile.')
    
    def on_pubmsg(self, c, e):
        text = e.arguments[0]
        self.check_and_answer(e, text)
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
        
        ### Easter eggs...
        elif command.endswith('?'):
            lastword = command.split(' ')[-1].rstrip('?')
            response_choices = ['No.',
                                'Yes.',
                                "Nobody knows.",
                                'Obviously.',
                                'I doubt it.',]
            time.sleep(2)
            c.privmsg(self.channel,random.choice(response_choices))
            
        else:
            lastword = command.split(' ')[-1].rstrip('?')
            response_choices = ['Go away, %s.' % source,
                                'Your mother is %s %s.' % ('an' if (lastword.startswith('a')
                                                                 or lastword.startswith('e')
                                                                 or lastword.startswith('i')
                                                                 or lastword.startswith('o')
                                                                 or lastword.startswith('u')) else 'a', lastword),
                                'What?']
            time.sleep(2)
            c.privmsg(self.channel,random.choice(response_choices))
    
    def kick(self,target):
        self.connection.kick(self.channel,target,'Detected resistance! Resistance is futile.')
    
    def blacklist(self,target):
        self.connection.kick(self.channel,target,'Banned for resisting!')
        self.channel_whitelist.remove(target)
    
    def whitelist(self,target):
        self.channel_whitelist.append(target)
        
def main():
    import sys
    if len(sys.argv) != 4:
        print "Usage: patrolbot.py <server[:port]> <channel> <nickname>"
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

    bot = PatrolBot(channel, nickname, server, port)
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()
    c = bot.connection