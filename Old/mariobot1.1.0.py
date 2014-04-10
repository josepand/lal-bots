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
import csv

class MarioBot(irc.bot.SingleServerIRCBot):
    
    def __init__(self, channel, nickname='mario', server='irc.rd.tandberg.com', port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        
        self.version = 'v1.1.0.0.1'
        
        self.mario_stats_ip = '10.47.196.80'
        
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
        self.waittime = 0
        self.required = 0
        self.helptimer = time.time() - 12100
        self.capstimer = time.time() - 12100
        self.rulestimer = time.time() - 12100
        self.dancetimer = time.time() - 12100
        self.buzztimer = time.time() - 12100
        self.allow_eggs = True
        
        self.ready_players = []
        
        self.helptext = ['''Mario Kart Booking system %s''' % self.version,
                         '''Mario Kart results and handicaps are now reported automagically.''',
                         '''Type "mario: book" to book the Wii for Mario Kart.''',
                         '''Type "mario: [123] more" to book and look for more players.''',
                         '''Type "mario: [123] more in [x] minutes" to book in advance (under 30 minutes only).''',
                         '''Type "mario: yes" to join a game.''',
                         '''Type "mario: yes for [name] in [x] minutes" to add another person to a game.''',
                         '''Type "mario: no" to leave a game.''',
                         '''Type "mario: no for [name]" to remove another person from a game.''',
                         '''Only players already involved in the game can remove other players.''',
                         '''Type "mario: buzz" to buzz potential players when looking for more.''',
                         '''Type "mario: check" to check if it's booked, and who by.''',
                         '''Type "mario: rules" to see the current rules we have in place.''',
                         '''Type "mario: handicaps" to show a list of handicaps.''',
                         '''Type "mario: unbook" if you hold the booking and want to cancel it.''',
                         '''It will automagically be unbooked when someone submits results to the stats tracker!''']
        
        self.rules = ['''Using a Lightning at any point takes 10 points from your team's final score and increases your opponent's score by 10.''',
                      '''Any player with a handicap of 0 or lower may use Lightning items with no penalty!''']
        
        self.possible_yes = ('yes', 'aye', 'yeah', 'y', 'yup', 'yer', 'yeh', 'yah', 'ja', 'yarr', 'yar', 'si', 'oui', 'yesz', 'yep', 'ok', 'go on then', 'alright', 'okay', 'why not',
                             'fine', 'damn right', 'absolutely', 'obviously', 'seems reasonable', 'fuck yeah', 'jawohl', 'hell yes', 'k', '-.-- . ...', 'i could go for that', 'could go for that')
        
        self.possible_no = ('no', 'nay', 'n', 'nope', 'nah', 'nar', 'nein', 'narr', 'non', 'get lost', 'go away', '-. ---')
        
        self.buzz_players = ['aa',
                             'ianp',
                             'ob',
                             'aj',
                             'Christina',
                             'coread',
                             'cosmin',
                             'dh',
                             'ea',
                             'eah',
                             'jamie',
                             'jobrandh',
                             'joe_and',
                             #'jr',
                             'lutomlin',
                             'philcoll',
                             #'rwge',
                             #'seabee',
                             'srj',
                             'tjw',
                             'uu',
                             ]
        
        self.player_whitelist = ['aa',
                                'ianp',
                                'ob',
                                'aj',
                                'Christina',
                                'coread',
                                'cosmin',
                                'dh',
                                'ea',
                                'eah',
                                'jamie',
                                'jobrandh',
                                'joe_and',
                                'jr',
                                'littlerob',
                                'lutomlin',
                                'philcoll',
                                #'rwge',
                                'seabee',
                                'shamayl',
                                'srj',
                                'tjw',
                                'uu',]
        
        self.stats_check = re.compile('''\[timestamp\] \=\> (.+)\s+\[changes\] => (.+): ([a-zA-Z]+)(?:\+| and) ([a-zA-Z]+)(?:\+| vs) ([a-zA-Z]+)(?:\-| and) ([a-zA-Z]+)(?:\-|)''')
        self.handicap_check = re.compile('((\[.+\] => .+\s+){22,})')
        #self.gen_check = re.compile('''\[timestamp\] \=\> (.+)\\n.+\\n(?:\s+\[(.+)\] \=\> Array\\n(?:\s+\[(\d)\] \=\> .+\\n){4}){3}''') ### Doesn't work - for log.php
        #self.gen_check = re.compile('')
        self.more_players_re = re.compile('mario: ([123]) more(?: in (\d+) minutes)?')#[|in (\d hours)|in (\d+ minutes)]')
        self.yes_for_re = re.compile('mario: (?:{})(?: for ([a-zA-Z]+))?(?: in (\d+) minutes)?'.format('|'.join(self.possible_yes)))
        self.no_for_re = re.compile('mario: (?:{}) for ([a-zA-Z]+)'.format('|'.join(self.possible_no)))
        #self.booking_type_re = re.compile('mario: book (.+)')
        
        self.old_playerinfo = self.retrieve_stats()
        self.old_gen_log = self.retrieve_gen()
        
        self.latest_timestamp_stat = self.old_playerinfo[0]
        self.latest_timestamp_gen = self.old_gen_log[0][0]
        
        t = threading.Timer(1, self.post_stats)
        t.daemon = True
        t.start()
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)
        c.privmsg(self.channel, 'Mario Kart booking and reporting system %s is available! Type "mario: help" for more information.' % self.version)
    
    def on_kick(self, c, e):
        print e.arguments
        if e.arguments[0] == c.get_nickname():
            c.join(self.channel)
            c.privmsg(self.channel, 'Mario Kart booking and reporting system %s is available! Type "mario: help" for more information.' % self.version)
    
    def on_join(self, c, e):
        source = e.source.nick
        if source in ('lutomlin','patrolbot','curve'):
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
    
    def post_stats(self):
        c = self.connection
        while True:
            playerinfo = self.retrieve_stats()
            handicapdata = self.retrieve_caps()
            gen_log = self.retrieve_gen()
            
            if playerinfo != self.old_playerinfo and playerinfo is not None:
                self.post_stats_to_channel(playerinfo)
                self.old_playerinfo = playerinfo
                
            if gen_log != self.old_gen_log and gen_log is not None:
                self.post_gen_to_channel(gen_log)
                self.old_gen_log = gen_log
                
            if self.isBooked and time.time() - self.bookingtime > 1800.0:
                c.privmsg(self.channel, 'Booking has expired for %s!' % self.booker)
                self.unbook()
            
            if self.waittime > 0 and self.required == 0 and time.time() > self.waittime:
                c.privmsg(self.channel, 'Players are ready! %s GOGOGO!' % ' '.join(self.ready_players))
                self.bookingtime = time.time()
                self.waittime = 0
                
            time.sleep(10)
            
    def check_and_answer(self, e, text):
        c = self.connection
        source = e.source.nick
        if source == 'resist':
            return
        #text = text.lower()
        
        ### Help
        if text == 'mario: help' and time.time() - self.helptimer > 60:
            self.helptimer = time.time()
            for text in self.helptext:
                c.privmsg(self.channel, text)
                time.sleep(0.5)
                
        ### Booking functions
        if text == 'mario: book':
            if source not in self.player_whitelist:
                c.privmsg(self.channel,'Go away, %s.' % source) 
            elif not self.isBooked:
                self.isBooked = True
                self.booker = source
                self.ready_players.append(source)
                self.bookingtime = time.time()
                c.privmsg(self.channel, 'Booked! Ready to play for %s' % self.booker)
            else:
                c.privmsg(self.channel, 'Not available; booked recently by %s' % self.booker)
                
        lfgre = self.more_players_re.match(text) ### 'mario: X more in X minutes'
        if lfgre:
            print lfgre.groups()
            if 'trains' in source:
                c.privmsg(self.channel,'trains: No chance.')
            elif source not in self.player_whitelist:
                c.privmsg(self.channel,'Go away, %s.' % source)
            elif not self.isBooked:
                self.isBooked = True
                self.booker = source
                self.ready_players = [source]
                self.bookingtime = time.time()
                self.required = int(lfgre.groups()[0])
                if lfgre.groups()[1] is not None and int(lfgre.groups()[1] < 30): ###!!! should probably not allow it rather than assuming 0.
                    self.waittime = time.time() + int(lfgre.groups()[1])*60
                    c.privmsg(self.channel, 'Booked for %s in %s minutes, looking for %d more; type "mario: yes" to join! (type mario: cpu to add the CPU as a player)' % (self.booker,lfgre.groups()[1],self.required))
                else:
                    self.waittime = time.time()
                    c.privmsg(self.channel, 'Booked for %s, looking for %d more; type "mario: yes" to join! (type mario: cpu to add the CPU as a player)' % (self.booker,self.required))
            else:
                c.privmsg(self.channel, 'Not available; booked recently by %s' % self.booker)
        
        if text in ['mario: %s' % s for s in self.possible_yes] and 1 <= self.required <= 3:
            if 'clvr' == source:
                c.privmsg(self.channel,'clvr: Go away.')
            elif source not in self.player_whitelist:
                c.privmsg(self.channel,'Go away, %s.' % source)
            else:
                self.required -= 1
                if self.required > 0:
                    self.ready_players.append(source)
                    c.privmsg(self.channel, '%s joined, looking for %s more; type "mario: yes" to join! (type mario: cpu to add the CPU as a player)' % (source,self.required))
                elif self.required == 0:
                    self.bookingtime = time.time()
                    self.ready_players.append(source)
                    if time.time() > self.waittime:
                        c.privmsg(self.channel, '%s joined; %s GOGOGO!' % (source,' '.join(self.ready_players)))
                        self.waittime = 0
                    else:
                        c.privmsg(self.channel, '%s joined; %d more minutes.' % (source,int((self.waittime-time.time())/60.0)))
                    
        yesre = self.yes_for_re.match(text)
        if yesre:
            newplayer = yesre.groups()[0]
            if newplayer is None:
                newplayer = source
            if source not in self.player_whitelist:
                c.privmsg(self.channel,'Go away, %s.' % source)
            elif newplayer not in self.player_whitelist:
                c.privmsg(self.channel,'Go away, %s.' % newplayer)
            else:
                self.required -= 1
                #print yesre.groups()
                if yesre.groups()[1] is not None:
                    pause = int(yesre.groups()[1])
                    if pause < 30 and pause*60 > self.waittime - time.time():
                        self.waittime = time.time() + pause*60
                if self.required > 0:
                    self.ready_players.append(newplayer)
                    c.privmsg(self.channel, '%s added %s, looking for %s more; type "mario: yes" to join! (type mario: cpu to add the CPU as a player)' % (source,newplayer,self.required))
                elif self.required == 0:
                    self.bookingtime = time.time()
                    self.ready_players.append(newplayer)
                    if time.time() > self.waittime:
                        c.privmsg(self.channel, '%s added %s; %s GOGOGO!' % (source,newplayer,' '.join(self.ready_players)))
                        self.waittime = 0
                    else:
                        c.privmsg(self.channel, '%s added %s; %d more minutes.' % (source,newplayer,int((self.waittime-time.time())/60.0)))
        
        if text in ['mario: %s' % s for s in self.possible_no]:
            if source in self.ready_players:
                self.ready_players.remove(source)
                self.required += 1
                if not self.ready_players:
                    self.unbook()
                    c.privmsg(self.channel, '%s left; game ended.' % source)
                else:
                    c.privmsg(self.channel, '%s left; looking for %s more! Type "mario: yes" to join! (type mario: cpu to add the CPU as a player)' % (source,self.required))
                    if self.booker not in self.ready_players:
                        self.booker = self.ready_players[0]
                        c.privmsg(self.channel,'%s now owns the booking.' % self.booker)
            else:
                c.privmsg(self.channel,'Thanks, %s.' % source)
                
        nore = self.no_for_re.match(text)
        if nore:
            newplayer = nore.groups()[0]
            if source not in self.ready_players:
                c.privmsg(self.channel,'Go away, %s.' % source)
            elif newplayer not in self.ready_players:
                c.privmsg(self.channel,'Thanks, %s.' % source)
            else:
                self.ready_players.remove(newplayer)
                self.required += 1
                if not self.ready_players:
                    self.unbook()
                    c.privmsg(self.channel, '%s removed %s; game ended.' % source, newplayer)
                else:
                    c.privmsg(self.channel, '%s removed %s; looking for %s more! Type "mario: yes" to join! (type mario: cpu to add the CPU as a player)' % (source,newplayer,self.required))
                    if self.booker not in self.ready_players:
                        self.booker = self.ready_players[0]
                        c.privmsg(self.channel,'%s now owns the booking.' % self.booker)
        
        if text == 'mario: cpu' and 1 <= self.required <= 3:
            self.required -= 1
            if self.required > 0:
                c.privmsg(self.channel, 'CPU is in, still looking for %s more; type "mario: yes" to join!' % self.required)
            elif self.required == 0:
                self.bookingtime = time.time()
                c.privmsg(self.channel, 'CPU is playing as 4th player; %s GOGOGO!' % ' '.join(self.ready_players))
            
        if text == 'mario: check':
            if self.isBooked:
                c.privmsg(self.channel, 'Booked recently by %s - Player list: %s' % (self.booker,' '.join(self.ready_players)))
            else:
                c.privmsg(self.channel, 'Not currently booked')
        
        if text == 'mario: unbook' and (self.booker == source or source == 'lutomlin'):
            self.unbook()
            c.privmsg(self.channel, 'Booking cancelled.')
            
        if text == 'mario: handicaps' and time.time() - self.capstimer > 60:
            self.capstimer = time.time()
            handicapdata = self.retrieve_caps()
            if handicapdata is not None:
                handicaplines = handicapdata.split('\n')
                for line in handicaplines:
                    c.privmsg(self.channel, line.strip())
                    time.sleep(1)
                
        if text == 'mario: rules' and time.time() - self.rulestimer > 300:
            self.rulestimer = time.time()
            for line in self.rules:
                c.privmsg(self.channel, line.strip())
                time.sleep(1)
                
        if text == 'mario: buzz' and self.booker == source and time.time() - self.buzztimer > 60:
            self.buzztimer = time.time()
            c.privmsg(self.channel,' '.join(self.buzz_players))
        
        ### Debug
        if text == 'mario: test1' and (source == 'lutomlin' or source == 'tjw'):
            self.old_playerinfo = 'Stats'
            c.privmsg(self.channel,'Hang on...')
        if text == 'mario: test2' and (source == 'lutomlin' or source == 'tjw'):
            self.old_gen_log = 'Stats'
            c.privmsg(self.channel,'Hang on...')
            
        if text == 'mario: version':
            c.privmsg(self.channel,self.version)
        
        ### Easter Eggs
        if text == 'mario: stop' and source == 'lutomlin':
            self.allow_eggs = False
            c.privmsg(self.channel,'Okay...')
        if text == 'mario: go' and source == 'lutomlin':
            self.allow_eggs = True
            c.privmsg(self.channel,'Yaaay')
        if self.allow_eggs:
            
            if text == 'mario: yes?':
                c.privmsg(self.channel,', '.join(self.possible_yes))
                
            if text == 'mario: no?':
                c.privmsg(self.channel,', '.join(self.possible_no))
                
            if text.startswith('mario: nick ') and len(text.split()) > 2:
                oldnick = c.get_nickname()
                c.nick(text.split()[2])
                if source != 'lutomlin':
                    time.sleep(1)
                    c.privmsg(self.channel,'Ehh... Nah.')
                    time.sleep(1)
                    c.nick(oldnick)
            
            rubbishre = re.compile('r\s{0,}u\s{0,}b\s{0,}b\s{0,}i\s{0,}s\s{0,}h')
            if '''mario: Fuck you mario bot. It's just rubbish!''' in text and 'rwge' in source:
                c.privmsg(self.channel,'Oh, not this again...')
                
            elif rubbishre.search(text) and 'rwge' in source:
                c.privmsg(self.channel,'''It really isn't. It's just MARIO KART!''')
                
            elif 'rubb!sh' in text and 'rwge' in source:
                c.privmsg(self.channel,'''It really isn't. It's just MAR!O KART!''')
                
            elif 'ubb' in text and 'rwge' in source:
                c.privmsg(self.channel,'''It really isn't. It's just MARIO KART!''')
                
            if text == 'mario: crash':
                c.privmsg(self.channel,'gack *dies*')
                c.part(self.channel,message = ':quit: Read error: Connection reset by peer')
                time.sleep(5)
                c.join(self.channel)
                c.privmsg(self.channel,'Just kidding...')
            
            if text == 'mario: kirby':
                c.privmsg(self.channel,'<(^_^)> eii!')
                
            if text == 'mario: dance' and time.time() - self.dancetimer > 60:
                msglist = ['vo/',
                           '\ov',
                           'vov',
                           '\o/']
                for msg in msglist:
                    c.privmsg(self.channel,msg)
                    time.sleep(0.5)
                for msg in msglist:
                    c.privmsg(self.channel,msg)
                    time.sleep(0.5)
                
            if text == 'mario: be rwgebot':
                time.sleep(random.randint(1,12))
                c.privmsg(self.channel,random.choice(['no','good to know','seems reasonable','interesting','not too bad for once','rubbish','80 characters should be enough for anyone']))
                
            if text.startswith('wario:'):
                c.privmsg(self.channel,'WAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
                
            if text == 'wario: help' and time.time() - self.helptimer > 60:
                self.helptimer = time.time()
                for text in self.helptext:
                    c.privmsg(self.channel, text[::-1])
                    time.sleep(0.5)
    
    def unbook(self):
        self.isBooked = False
        self.required = 0
        self.booker = ''
        self.ready_players = []
        self.waittime = 0
        
    def refresh_and_gogogo(self):
        self.bookingtime = time.time()
        c.privmsg(self.channel, '%s minutes has elapsed; %s GOGOGO!' % (self.waittime,' '.join(self.ready_players)))
        
    def solve_hangman(self):
        c.privmsg(self.channel,'hubot hangman')
        for letter in 'etaoinshrdlcumwfgypbvkjxqz':
            c.privmsg(self.channel,'hubot hangman {}'.format(letter))
            time.sleep(1)
            
    def retrieve_stats(self):
        if 'rw'+'ge' in self.player_whitelist:
            self.player_whitelist.remove('rw'+'ge')
        try:
            mario_stats_site = urllib2.urlopen('http://%s/handicaphistory.php' % self.mario_stats_ip)
            stats_page = mario_stats_site.read()
            return self.stats_check.search(stats_page).groups()
        except AttributeError as err:
            print 'Found error %s' % str(err)
            return None
        except urllib2.URLError as err:
            print 'Error trying to open webpage! Returning None'
            return None
            
    def retrieve_caps(self):
        try:
            mario_stats_site = urllib2.urlopen('http://%s/handicaphistory.php' % self.mario_stats_ip)
            stats_page = mario_stats_site.read()
            return self.handicap_check.search(stats_page).groups()[0]
        except AttributeError as err:
            print 'Found error %s' % str(err)
            return None
        except urllib2.URLError as err:
            print 'Error trying to open webpage! Returning None'
            return None
    
    def retrieve_4_caps(self,p1,p2,p3,p4):
        try:
            mario_stats_site = urllib2.urlopen('http://%s/handicaphistory.php' % self.mario_stats_ip)
            stats_page = mario_stats_site.read()
            handicapdata = self.handicap_check.search(stats_page).groups()[0]
            hs1,hs2,hs3,hs4 = re.compile('\[%s\] => (.+)\s' % p1), re.compile('\[%s\] => (.+)\s' % p2), re.compile('\[%s\] => (.+)\s' % p3), re.compile('\[%s\] => (.+)\s' % p4)
            h1,h2,h3,h4 = hs1.search(handicapdata).groups()[0], hs2.search(handicapdata).groups()[0], hs3.search(handicapdata).groups()[0], hs4.search(handicapdata).groups()[0]
            return h1,h2,h3,h4
        except AttributeError as err:
            print 'Found error %s' % str(err)
            return None
        except urllib2.URLError as err:
            print 'Error trying to open webpage! Returning None'
            return None
    
    def retrieve_gen(self):
        try:
            mario_log_page = urllib2.urlopen('http://%s/lukelog.php' % self.mario_stats_ip)
            log_page = mario_log_page.read()
            gen_log_page = [logline.split(',') for logline in log_page.split('<br />')]
            gen_log_page[0][0] = gen_log_page[0][0].lstrip('<font size="5">')
            return gen_log_page
        except AttributeError as err:
            print 'Found error %s' % str(err)
            return None
        except urllib2.URLError as err:
            print 'Error trying to open webpage! Returning None'
            return None
        
    def post_stats_to_channel(self, playerinfo):
        c = self.connection
        try:
            timestamp = playerinfo[0]
            if not timestamp >= self.latest_timestamp_stat:
                return
            self.latest_timestamp_stat = timestamp
            print playerinfo
            p1,p2,p3,p4 = playerinfo[2],playerinfo[3],playerinfo[4],playerinfo[5]
            pa1,pa2,pa3,pa4 = p1,p2,p3,p4
            if p1 == 'computer': p1 = 'arvinda'
            if p2 == 'computer': p2 = 'arvinda'
            if p3 == 'computer': p3 = 'arvinda'
            if p4 == 'computer': p4 = 'arvinda'
            h1,h2,h3,h4 = self.retrieve_4_caps(p1,p2,p3,p4)
            if playerinfo[1] == 'Red win':
                winners = 'News: Mario Kart result in! %s and %s beat %s and %s' % (pa1.capitalize(),pa2.capitalize(),pa3.capitalize(),pa4.capitalize())
                newhandicaps = 'New handicaps: %s: %s, %s: %s, %s: %s, %s: %s' % (p1.capitalize(),h1,p2.capitalize(),h2,p3.capitalize(),h3,p4.capitalize(),h4)
                teamResult = 'Red team is the best!'
            elif playerinfo[1] == 'Blue win':
                winners = 'News: Mario Kart result in! %s and %s beat %s and %s' % (pa1.capitalize(),pa2.capitalize(),pa3.capitalize(),pa4.capitalize())
                newhandicaps = 'New handicaps: %s: %s, %s: %s, %s: %s, %s: %s' % (p1.capitalize(),h1,p2.capitalize(),h2,p3.capitalize(),h3,p4.capitalize(),h4)
                teamResult = 'Blue team is the best!'
            elif playerinfo[1] == 'No Change':
                winners = 'News: Mario Kart result in! %s and %s drew with %s and %s' % (pa1.capitalize(),pa2.capitalize(),pa3.capitalize(),pa4.capitalize())
                newhandicaps = 'Handicaps: %s: %s, %s: %s, %s: %s, %s: %s' % (p1.capitalize(),h1,p2.capitalize(),h2,p3.capitalize(),h3,p4.capitalize(),h4)
                teamResult = 'No Change!'
                
            postmsgs = [winners,
                        newhandicaps,
                        teamResult,
                        #'Played at %s' % timestamp,
                       ]
            for msg in postmsgs:
                print msg
                c.privmsg(self.channel,msg)
                time.sleep(0.3)
            if not playerinfo[1] == 'No Change':
                if 'computer' in [pa1,pa2]:
                    c.privmsg(self.channel,'CPU wins! All players go down 0.25.')
                if 'computer' in [pa3,pa4]:
                    c.privmsg(self.channel,'CPU loses! All players go up 0.25.')
            self.unbook()
        except (AttributeError, TypeError) as err:
            print 'Found error %s' % str(err)
            
    def post_gen_to_channel(self, gen_log):
        c = self.connection
        try:
            timestamp = gen_log[0][0]
            if not timestamp > self.latest_timestamp_gen:
                return
            self.latest_timestamp_gen = timestamp
            print gen_log
            redteam = tuple([' '.join([w.capitalize() for w in s.split(' ')]) for pl in (p[1:] for p in gen_log if p[0]=='red') for s in pl])
            blueteam = tuple([' '.join([w.capitalize() for w in s.split(' ')]) for pl in (p[1:] for p in gen_log if p[0]=='blue') for s in pl])
            p1,p2,p3,p4 = redteam[0].lower(),redteam[3].lower(),blueteam[0].lower(),blueteam[3].lower()
            h1,h2,h3,h4 = self.retrieve_4_caps(p1,p2,p3,p4)
            handicap_rvb = float(h1)+float(h2)-float(h3)-float(h4)
            if 0.1 > handicap_rvb > -0.1:
                handicapmsg = 'No handicap advantage!'
            elif handicap_rvb < 0:
                handicapmsg = 'Blue team is handicapped by %s points!' % str(handicap_rvb*(-1))
            elif handicap_rvb > 0:
                handicapmsg = 'Red team is handicapped by %s points!' % str(handicap_rvb)
            postmsgs = ['News: Mario Kart match starting!',
                        'Red team: %s is %s on the %s  &  %s is %s on the %s' % redteam,
                        'Blue team: %s is %s on the %s  &  %s is %s on the %s' % blueteam,
                        handicapmsg,
                       ]
            #rb1 = tuple(redteam[:3]+blueteam[:3])
            #rb2 = tuple(redteam[3:]+blueteam[3:])
            #postmsgs = ['News: Match starting!',
            #            '%s is %s on the %s    Red  vs  Blue   %s is %s on the %s' % rb1,
            #            '%s is %s on the %s                    %s is %s on the %s' % rb2,
            print timestamp
            for msg in postmsgs:
                print msg
                c.privmsg(self.channel,msg)
                time.sleep(0.3)
        except (AttributeError, TypeError, IndexError) as err:
            print 'Found error %s' % str(err)
    
def main():
    import sys
    if len(sys.argv) != 4:
        print "Usage: mariobot.py <server[:port]> <channel> <nickname>"
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

    bot = MarioBot(channel, nickname, server, port)
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()
    c = bot.connection