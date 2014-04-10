#! /usr/bin/env python
# 
# based on a python libirc example by Joel Rosdahl <joel@rosdahl.net>

import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
import threading
import random
from datetime import date
import urllib2, re
import time
from pprint import pprint
import sys
import csv


class TestBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        
        self.version = 'v1.0'
        self.name = nickname
        self.target = ''
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        if self.target:
            c.privmsg(self.channel, 'hello, %s.' % self.target)
        t = threading.Timer(1, self.heckle)
        t.daemon = True
        t.start()
    
    def on_join(self, a, b):
        #c = self.connection
        pass

    def on_pubmsg(self, c, e):
        a = e.arguments[0]
        self.check_and_answer(e, a)
        return
    
    def heckle(self):
        c = self.connection
        while True:
            if random.randint(1,60) < 5 and self.target:
                c.privmsg(self.channel,'watcha up to, %s?' % self.target)
            elif random.randint(1,60) < 6 and self.target:
                c.privmsg(self.channel,'%s: hi!' % self.target)
            elif random.randint(1,60) < 7 and self.target:
                c.privmsg(self.channel,'%s: guess what?' % self.target)
            time.sleep(30)
    
    def check_and_answer(self, e, text):
        c = self.connection
        source = e.source.nick
        text = text.lower()
        
        if source == self.target and source != 'lutomlin':
            delay,response = self.clever_response(source,text)
            time.sleep(delay)
            c.privmsg(self.channel,response)
            
        elif text.startswith('heckle: '):
            splittext = text.split(': ')
            if len(splittext) == 2:
                self.target = splittext[1]
                c.privmsg(self.channel,'hello, %s.' % splittext[1])
    
    def clever_response(self,source,text):
        if 'what?' in text or 'what!' in text:
            delay, response = random.choice((3,'%s: nothing!' % source),
                                            (2,'good guess!'),
                                            )
        elif random.randint(1,100) < 71:
            delay,response = random.choice(((4,'hey %s, guess what?' % source),
                                  (1,"%s: i'm not interested in %s, talk about something else" % (source,text.split(' ')[-1].rstrip('?'))),
                                  (1,'%s: boring' % source),
                                  (3,'%s: ask rwge?' % source),
                                  (1,'%s: omgwtfbbq' % source),
                                  (1,'%s: how dare you talk to me like that' % source),
                                  (2,'%s: rubbish' % source),
                                  (0,'%s: %s!' % (source,text.lstrip('%s: ' % self.name))),
                                  ))
        else: delay,response = 0,''
        print delay, response
        return delay, response
    
def main():
    import sys
    if len(sys.argv) != 4:
        print "Usage: bot.py <server[:port]> <channel> <nickname>"
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

    bot = TestBot(channel, nickname, server, port)
    bot.start()

if __name__ == "__main__":
    main()
