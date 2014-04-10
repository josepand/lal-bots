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

class TrainBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname='trains', server='irc.rd.tandberg.com', port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        
        self.version = 'v0.6'
        self.command_re = re.compile('trains: (.+)')
        self.site_reader_re = re.compile('''>(\d\d:\d\d).+?<td class="status.+?(?:(\d{1,2}) <abbr title="minutes">mins</abbr> late|(On time)|(Cancelled)|(Delayed)|(No report))''',re.DOTALL)
        #self.site_reader_re = re.compile('''(\d\d:\d\d).+(?:>(\d+) <abbr title="minutes">mins</abbr> late</span>|>(On time)</td>)''',re.DOTALL)
        
        self.dst_strings = {'ealing':'EAL',
                            'ealing broadway':'EAL',
                            'slough':'SLO',
                            'reading':'RDG',
                            'oxford':'OXF',
                            'london':'PAD',
                            'paddington':'PAD',
                            'london paddington':'PAD',
                            
                            'eal':'EAL',
                            'slo':'SLO',
                            'rdg':'RDG',
                            'oxf':'OXF',
                            'pad':'PAD',
                           }
        
        self.helptimer = time.time() - 12100
        self.dst_timer = time.time() - 12100
        self.helptext = ['''TrainBot %s''' % self.version,
                         '''Type "trains: [dst]" to see your train times!''',
                         '''[dst] must be your station code (e.g. LNY for langley, EAL for ealing)''',
                         ]
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        c.privmsg(self.channel, 'TrainBot %s is available! Type "trains: help" for more information.' % self.version)
        t = threading.Timer(1, self.post_stats)
        t.daemon = True
        t.start()
    
    def on_join(self, a, b):
        #c = self.connection
        pass
    
    def on_kick(self, c, e):
        #print e.arguments
        if e.arguments[0] == c.get_nickname():
            c.join(self.channel)
            
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
        
        ### Find times for dst
        elif command in self.dst_strings.keys() or len(command) == 3:
            if time.time() - self.dst_timer > 10:
                info = self.retrieve_times(command)
                self.dst_timer = time.time()
            else:
                c.privmsg(self.channel,'[messages are throttled - please wait 10 seconds]')
            
        ### Easter eggs...
        #elif text.startswith('mario: nick ') and len(text.split()) == 3 and source == 'lutomlin':
        #    oldnick = c.get_nickname()
        #    c.nick(text.split()[2])
        
        elif 'mario kart' in command:
            time.sleep(2)
            c.privmsg(self.channel,"Yeah...")
            time.sleep(2)
            c.privmsg(self.channel,"mario: 3 more")
        elif 'late' in command:
            time.sleep(2)
            c.privmsg(self.channel,'The trains are never late. They arrive precisely when they mean to.')
        elif 'snow' in command:
            time.sleep(2)
            c.privmsg(self.channel,"Snow! You're all stuck here.")
        elif command.endswith('?'):
            lastword = command.split(' ')[-1].rstrip('?')
            response_choices = ['No.',
                                'Yes.',
                                'Probably, it would make sense.',
                                'Figure it out yourself.',
                                "Nobody knows.",
                                'Obviously.',
                                'Why not?',
                                'I doubt it.',
                                'rwge knows...?',]
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
                                lastword + '! \o/',
                                'Uh. If you say so.',
                                'Unrecognised command! If you do it enough, I might crash.',
                                'What?',
                                'Unrecognised command! *crashes*']
            time.sleep(2)
            response = random.choice(response_choices)
            c.privmsg(self.channel,response)
            if '*crashes*' in response:
                time.sleep(1)
                c.part(self.channel,message = ':quit: Read error: Connection reset by peer')
                time.sleep(10)
                c.join(self.channel)
                c.privmsg(self.channel,"Please don't do that again.")
            
            
        #elif command == 'timeset': ### Minimum number of minutes late to be shown automatically
        #    pass
        
        #else:
        #    c.privmsg(self.channel,'Command not recognised')
        
    def retrieve_times(self,dst):
        c = self.connection
        try:
            if dst in self.dst_strings:
                dststring = self.dst_strings[dst]
            else:
                dststring = dst.upper()
            train_site = urllib2.urlopen('http://ojp.nationalrail.co.uk/service/ldbboard/dep/LNY/%s/To' % dststring)
            html_page = train_site.read()
            if '<span class="from">Langley (Berks) [<abbr>LNY</abbr>]<span><img height="' not in html_page:
                raise KeyError('Oh Dear.')
            info = self.site_reader_re.findall(html_page)
            c.privmsg(self.channel,'Trains to %s:' % dststring)
            #pprint(info)
            self.print_info(info)
            return info
        except KeyError as err:
            print 'Key Error! Destination match not found - %s' % dststring
            c.privmsg(self.channel,'%s not recognised...' % dststring)
            return None
        except AttributeError as err:
            print 'Found error %s' % str(err)
            return None
        except urllib2.URLError as err:
            print 'Error trying to open webpage! Returning None'
            return None
        
    def print_info(self,info):
        c = self.connection
        if info is None or info == []:
            c.privmsg(self.channel,'No direct trains found!')
            return
        for ttime in info:
            if ttime[1]:
                timestr = '%s minutes late' % ttime[1]
            elif ttime[2] == 'On time':
                timestr = 'on time'
            elif ttime[3] == 'Cancelled':
                timestr = 'cancelled!'
            elif ttime[4] == 'Delayed':
                timestr = 'delayed indefinitely'
            elif ttime[5] == 'No report':
                timestr = 'not reported'
            else:
                timestr = 'unknown %s' % str(ttime)
            c.privmsg(self.channel,'%s is %s' % (ttime[0],timestr))
            time.sleep(0.2)
        
    def post_stats(self):
        c = self.connection
        while True:
            time.sleep(30)

def main():
    import sys
    if len(sys.argv) != 4:
        print "Usage: trainbot.py <server[:port]> <channel> <nickname>"
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

    bot = TrainBot(channel, nickname, server, port)
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()
    c = bot.connection