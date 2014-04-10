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
import copy

class AlphaBot(irc.bot.SingleServerIRCBot):
    
    def __init__(self, channel, nickname='alpha', server='irc.rd.tandberg.com', port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        
        self.version = 'v0.2'
        
        self.command_re = re.compile('%s: (.+)' % nickname)
        
        self.alphabet = 'abcdefghijklmnopqrstuvwxyz'
        
        self._dictionary = {'a':['Alpha','Application'],
                           'b':['Border'],
                           'c':['Cisco','Communications','Conferencing'],
                           'd':['Development','Data','Digital','Database'],
                           'e':['Element','Environment'],
                           'f':['Field'],
                           'g':['General'],
                           'h':['H?'],
                           'i':['IP','Internal'],
                           'j':['Jabber','Joint'],
                           'k':['K?'],
                           'l':['License'],
                           'm':['Manager'],
                           'n':['Network'],
                           'o':['Option'],
                           'p':['Provider'],
                           'q':['Query'],
                           'r':['Realtime','Remote'],
                           's':['System','Server','Solution'],
                           't':['Telepresence'],
                           'u':['Unified'],
                           'v':['Video','Voice'],
                           'w':['WebEx','Web'],
                           'x':['eXtended'],
                           'y':['Y?'],
                           'z':['Zone'],}
        
        self.dictionary = copy.copy(self._dictionary)
        
        self.helptimer = time.time() - 12100
        
        self.helptext = ['''AlphaBot %s! Early build, some letters still missing.''' % self.version,
                         '''Type "alpha: [anything]" to see what it stands for!''',
                         '''Type "alpha: letter [letter] [string]" to replace the letter with your own text!'''
                         ]
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        c.privmsg(self.channel, 'AlphaBot %s. Type "alpha: help" for more information.' % self.version)
    
    def on_join(self, c, e):
        source = e.source.nick
        if source in ('lutomlin','patrolbot','mario','curve'):
            self.connection.mode(self.channel,'+o %s' % source)

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
                
        elif command.startswith('letter ') and len(command.split()) == 3 and len(command.split()[1]) == 1 and source == 'lutomlin':
            commands = command.split()
            if commands[1] in self.alphabet and commands[2].capitalize() not in self.dictionary[commands[1]]:
                self.dictionary[commands[1]].append(commands[2].capitalize())
                print 'Adding word %s to letter %s' % (commands[2],commands[1])
        
        elif command == 'reset' and source == 'lutomlin':
            self.dictionary = copy.copy(self._dictionary)
            
        elif command:
            stringlist = []
            for letter in command:
                if letter in self.alphabet:
                    newword = random.choice(self.dictionary[letter])
                    stringlist.append(newword)
            c.privmsg(self.channel,' '.join(stringlist))

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

    bot = AlphaBot(channel, nickname, server, port)
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()
    c = bot.connection