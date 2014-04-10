
import irc.bot
import irc.client
import threading
import random
import datetime 
import urllib2, re
import time
from pprint import pprint
import sys
import csv
from whitelist import BUZZPLAYERS, WHITELIST

from string import maketrans

class MarioBot(irc.bot.SingleServerIRCBot):

    def __init__(self, channel, nickname='mario', server='irc.rd.tandberg.com', port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        
        self.version = 'v1.1.2.1.0'
        
        self.mario_stats_ip = '10.47.196.80'
        
        self.helptext = ['''Mario Kart Booking system %s''' % self.version,
                         '''Mario Kart results and handicaps are now reported automagically.''',
                         '''Type "mario: book" to book the Wii for Mario Kart for 20 minutes.''',
                         '''Type "mario: unbook" if you hold the booking and want to cancel it.''',
                         '''Type "mario: [123] more" to book and look for more players.''',
                         '''Type "mario: [123] more in [x] minutes" to book in advance (under 30 minutes only).''',
                         '''Type "mario: yes" to join a game.''',
                         '''You can type "mario: yes (for [name]) (in [x] minutes)" to add another person to a game, or use a delayed start.''',
                         '''Type "mario: no" to leave a game.''',
                         '''Type "mario: no for [name]" to remove another person from a game.''',
                         '''Only players already involved in the game can remove other players.''',
                         '''Type "mario: challenge [name] and [name] with [name]" to issue a challenge.''',
                         '''Challenges must be completed within 2 working days; if not, the challengees forfeit and lose the match.''',
                         '''If the challengers lose, the loss counts double, and the challengees win double.''',
                         #'''If the handicaps of any of the involved players change, the challenge can be withdrawn by the other players involved (either side).''',
                         '''A player can only issue one challenge at a time and must wait 168 hours before issuing another.''',
                         '''Type "mario: cancel challenge" to cancel a made challenge.''',
                         '''Type "mario: buzz" to buzz potential players when looking for more.''',
                         '''Type "mario: check" to check if it's booked, and who by.''',
                         '''Type "mario: rules" to see the current rules we have in place.''',
                         '''Type "mario: handicaps" to show a list of handicaps.''',
                         '''It will automagically be unbooked when someone submits results to the stats tracker!''']
        
        self.rules = ['''Using a Lightning at any point takes 10 points from your team's final score and increases your opponent's score by 10.''',
                      '''Any player with a handicap of 0 or lower may use Lightning items with no penalty!''',
                      '''Two players may issue a challenge to any other two players:''',
                      '''Failure to accept the challenge results in an automatic loss, but if you accept a challenge and win, the win counts double!''',
                      '''The volcano shortcut on Grumble Volcano is banned.''',]
        
        self.possible_yes = ('yes', 'aye', 'yeah', 'y', 'yup', 'yas', 'yer', 'yeh', 'yah', 'ja', 'yarr', 'yar', 'si', 'oui', 'yesz', 'yep', 'ok', 'go on then', 'alright', 'okay', 'why not',
                             'fine', 'damn right', 'absolutely', 'obviously', 'seems reasonable', 'fuck yeah', 'jawohl', 'hell yes', 'k', '-.-- . ...', 'i could go for that', 'could go for that',
                             'sure','oki','go ahead', 'bring it')
        
        self.possible_no = ('no', 'nay', 'n', 'nope', 'nah', 'nar', 'nein', 'narr', 'non', 'get lost', 'go away', '-. ---')
        
        self.buzz_players = BUZZPLAYERS
        
        self.player_whitelist = WHITELIST
        
        self.last_challenges = {}
        
        self.ready_players = []
        self.required = 0
        self.booker = ''
        self.bookingtime = 0
        self.waittime = 0
        
        self._booking_duration = 1800
        
        self.allow_eggs = True
        self.say_ae = False
        self.no_vowels = False
        self.replace_letters = ''
        
        self.helptimer = time.time() - 12100
        self.capstimer = time.time() - 12100
        self.chaltimer = time.time() - 12100
        self.rulestimer = time.time() - 12100
        self.dancetimer = time.time() - 12100
        self.buzztimer = time.time() - 12100
        
        self._player_re_string = '([a-zA-Z_]+)'
        
        self.stats_check = re.compile('''\[timestamp\] \=\> (.+)\s+\[changes\] => (.+): ([a-zA-Z]+)(?:\+| and) ([a-zA-Z]+)(?:\+| vs) ([a-zA-Z]+)(?:\-| and) ([a-zA-Z]+)(?:\-|)''')
        self.handicap_check = re.compile('((\[.+\] => .+\s+){22,})')
        self.more_players_re = re.compile('(?i)([123]) more(?: in (\d+) minutes)?$')#[|in (\d hours)|in (\d+ minutes)]')
        self.yes_for_re = re.compile('(?i)(?:{})(?: for ([a-zA-Z_]+))?(?: in (\d+) minutes)?$'.format('|'.join(self.possible_yes)))
        self.no_for_re = re.compile('(?i)(?:{})(?: for ([a-zA-Z_]+))?$'.format('|'.join(self.possible_no)))
        self.say_re = re.compile('say (..)$')
        
        self.challenge_re = re.compile('challenge {} and {} with {}'.format(self._player_re_string,self._player_re_string,self._player_re_string))
        self.challenges = {}
        #{'name':([opponent, opponent, ally],datetime.utcnow())}
        
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
        self.c_pm('Mario Kart booking and reporting system %s is available! Type "mario: help" for more information.' % self.version)
    
    def on_kick(self, c, e):
        print e.arguments
        if e.arguments[0] == c.get_nickname():
            c.join(self.channel)
            #self.c_pm('Mario Kart booking and reporting system %s is available! Type "mario: help" for more information.' % self.version)
    
    def on_pubmsg(self, connection, event):
        text = event.arguments[0]
        self.check_and_answer(event, text)
        return
        
    def post_stats(self):
        c = self.connection
        while True:
            playerinfo = self.retrieve_stats()
            handicapdata = self.retrieve_caps()
            gen_log = self.retrieve_gen()
            
            ### New Results
            if playerinfo != self.old_playerinfo and playerinfo is not None:
                self.post_stats_to_channel(playerinfo)
                self.old_playerinfo = playerinfo
            
            ### New Gens
            if gen_log != self.old_gen_log and gen_log is not None:
                self.post_gen_to_channel(gen_log)
                self.old_gen_log = gen_log
                
            ### Booking expiry
            if self.booker and time.time() - self.bookingtime > self._booking_duration:
                self.c_pm('Booking has expired for %s!' % self.booker)
                self.unbook()
            
            ### Booking commencement
            if self.waittime > 0 and self.required == 0 and time.time() > self.waittime:
                self.c_pm('Players are ready! %s GOGOGO!' % ' '.join(p[0] for p in self.ready_players),True)
                self.bookingtime = time.time()
                self.waittime = 0
                
            time.sleep(10)
            
    def check_and_answer(self, e, text):
        c = self.connection
        source = e.source.nick
        if source == 'resist':
            return
        
        nick = c.get_nickname()
        command_re = re.compile('{}: (.+)'.format(nick))
        command_match = command_re.match(text)
        if command_match is None:
            command = ''
        else:
            command = command_match.groups()[0]
        
        
        ### Help
        if command == 'help' and time.time() - self.helptimer > 60:
            self.helptimer = time.time()
            for line in self.helptext:
                self.c_pm(line)
                time.sleep(0.5)
        
        if command == 'rules' and time.time() - self.rulestimer > 60:
            self.rulestimer = time.time()
            for line in self.rules:
                self.c_pm(line.strip())
                time.sleep(1)
                
        if command == 'check':
            if self.booker:
                timer = int(self.waittime - time.time())
                self.c_pm('Booked recently by {}'.format(self.booker))
                if len(self.ready_players) > 1:
                    time.sleep(0.5)
                    self.c_pm('Player list: {}'.format(' '.join(p[0] for p in self.ready_players)))
                if timer > 0:
                    time.sleep(0.5)
                    timer = int(self.waittime - time.time())
                    self.c_pm('Time to start: {} second{}'.format(timer, '' if timer == 1 else 's'))
            else:
                self.c_pm('Not currently booked')
        
        ### Player-only functions
        if source in self.player_whitelist:
        ### Booking functions:
            if command == 'book':
                if self.booker == '':
                    self.booker = source
                    self.ready_players = [(source,0)]
                    self.bookingtime = time.time()
                    self.c_pm('Booked! Ready to play for %s' % self.booker)
                else:
                    self.c_pm('Not available; booked recently by %s' % self.booker)
                    
            if command == 'unbook' and (self.booker == source or source == 'lutomlin'):
                self.unbook()
                self.c_pm('Booking cancelled.')
            
            ### Regexes
            more_re = self.more_players_re.match(command)
            yes_re = self.yes_for_re.match(command)
            no_re = self.no_for_re.match(command)
            challenge_re = self.challenge_re.match(command)
            
            ### Player group functions
            ### mario: 3 more
            if more_re:
                #print more_re.groups()
                if self.booker == '':
                    self.required = int(more_re.groups()[0])
                    timer = more_re.groups()[1]
                    if timer is not None:
                        timer = int(timer)*60
                        if timer > 1200:
                            self.c_pm('Bookings in advance must be 20 minutes or less.')
                            return
                        if timer < 60:
                            timer = 0
                    else:
                        timer = 0
                        
                    self.bookingtime = time.time()
                    self.ready_players = [(source,time.time() + timer)]
                    self.booker = source
                    self.waittime = time.time() + timer
                    
                    if timer:
                        rem = int(timer/60.0)
                        self.c_pm('Booked for %s in %s minute%s, looking for %d more; type "mario: yes" to join! (type mario: yes for cpu to add the CPU as a player)' % (self.booker,str(rem) if rem > 0 else 'less than 1','' if rem <= 1 else 's',self.required))
                    else:
                        self.c_pm('Booked for %s, looking for %d more; type "mario: yes" to join! (type mario: yes for cpu to add the CPU as a player)' % (self.booker,self.required))
                else:
                    self.c_pm('Not available; booked recently by %s' % self.booker)
            
            ### mario: yes for [player] in [x] minutes
            if yes_re:
                #print yes_re.groups()
                if 1 <= self.required <= 3:
                    newplayer = yes_re.groups()[0]
                    if newplayer is None:
                        newplayer = source
                    if newplayer not in self.player_whitelist:
                        self.c_pm('Go away, %s.' % source)
                        return
                    timer = yes_re.groups()[1]
                    if timer is not None:
                        timer = int(timer)*60
                        if timer > 1200:
                            self.c_pm('Bookings in advance must be 20 minutes or less.')
                            return
                        if timer < 60:
                            timer = 0
                    else:
                        timer = 0
                            
                    self.ready_players.append((newplayer,time.time() + timer))
                    self.required -= 1
                    
                    self.waittime = max(p[1] for p in self.ready_players) if self.ready_players else 0
                    
                    if self.required > 0:
                        self.c_pm('%s %s, looking for %d more; type "mario: yes" to join! (type mario: yes for cpu to add the CPU as a player)' % (source,
                                                                                                                                                                 'joined' if source == newplayer else 'added %s' % newplayer,
                                                                                                                                                                 self.required))
                    elif self.required  == 0:
                        if time.time() >= self.waittime:
                            self.c_pm('%s %s; %s GOGOGO!' % (source,
                                                                           'joined' if source == newplayer else 'added %s' % newplayer,
                                                                           ' '.join(p[0] for p in self.ready_players)),True)
                            self.bookingtime = time.time()
                            self.waittime = 0
                        else:
                            rem = int((self.waittime-time.time())/60.0)
                            self.bookingtime = time.time()
                            self.c_pm('%s %s; %s minute%s.' % (source,
                                                                  'joined' if source == newplayer else 'added %s' % newplayer,
                                                                  str(rem) if rem > 0 else 'less than 1','' if rem <= 1 else 's'))
                    
            ### mario: no for [player]
            if no_re:
                #print no_re.groups()
                newplayer = no_re.groups()[0]
                if newplayer is None:
                    newplayer = source
                    
                for player in self.ready_players:
                    if player[0] == source:
                        break
                else: 
                    if source == newplayer:
                        self.c_pm('Thanks, %s.' % source)
                    return ### Not allowed to use this unless you are involved
                    
                for player in self.ready_players:
                    if player[0] == newplayer:
                        self.ready_players.remove(player)
                        self.required += 1
                        self.waittime = max(p[1] for p in self.ready_players) if self.ready_players else 0
                        if not self.ready_players:
                            self.unbook()
                            self.c_pm('%s %s; game ended.' % (source,
                                                                 'left' if source == newplayer else 'removed %s' % newplayer))
                        else:
                            self.c_pm('%s %s; looking for %s more! Type "mario: yes" to join! (type mario: yes for cpu to add the CPU as a player)' % (source,
                                                                                                                                                                     'left' if source == newplayer else 'removed %s' % newplayer,
                                                                                                                                                                     self.required))
                            
                            for player in self.ready_players: ### Check if self.booker in ready_players, if not make new booker
                                if player[0] == self.booker:
                                    break
                            else: 
                                self.booker = self.ready_players[0][0]
                                self.c_pm('%s now owns the booking.' % self.booker)
                        break
                else:
                    self.c_pm('Thanks, %s.' % source)
                    #print 'How did i get here? mario: no_re, player %s not found in ready_players' % newplayer
                    #pprint self.ready_players
                    
            if challenge_re:
                try:
                    players = challenge_re.groups()
                    if source in self.challenges and self.challenges[source][1] > datetime.datetime.utcnow() - datetime.timedelta(2):
                        self.c_pm('You already have a challenge - {} and {} vs {} and {}.'.format(source,self.challenges[source][0][2],self.challenges[source][0][0],self.challenges[source][0][1]))
                    elif source in self.challenges and self.challenges[source][1] > datetime.datetime.utcnow() - datetime.timedelta(7):
                        self.c_pm('You have challenged recently - you must wait one week - last challenge was {}'.format(self.challenges[source][1]))
                    else:
                        self.c_pm('{} issues a challenge with {} to {} and {}!'.format(source,players[2],players[0],players[1]))
                        self.challenges.update({source:(players,datetime.datetime.utcnow())})
                except Exception as err:
                    print err
                    self.c_pm('Nope, it broke.')
                    
            ### Other functions
            if command == 'handicaps' and time.time() - self.capstimer > 60:
                self.capstimer = time.time()
                handicapdata = self.retrieve_caps()
                if handicapdata is not None:
                    handicaplines = handicapdata.split('\n')
                    for line in handicaplines:
                        self.c_pm(line.strip())
                        time.sleep(1)
                
            if command == 'buzz' and self.booker == source and time.time() - self.buzztimer > 60:
                self.buzztimer = time.time()
                self.c_pm(' '.join([p for p in self.buzz_players if p not in [x[0] for x in self.ready_players]]),True)
            
            if command == 'challenges':# and time.time() - self.chaltimer > 60:
                try:
                    chal = sorted([(k,v) for k,v in self.challenges.iteritems()],key = lambda y: y[1][1])
                    if chal:
                        for c in chal:
                            self.chaltimer = time.time()
                            self.c_pm('{} and {} vs {} and {} - Issued: {}'.format(c[0],c[1][0][2],c[1][0][0],c[1][0][1],c[1][1].ctime()))
                            time.sleep(1)
                    else:
                        self.c_pm('No challenges right now.')
                except Exception as err:
                    print err
                    self.c_pm('Nope, it broke.')
            
            if command == 'cancel challenge':
                try:
                    if source in self.challenges:
                        self.challenges.pop(source)
                        self.c_pm('Challenge cancelled for {}.'.format(source))
                    else:
                        self.c_pm('Thanks, {}'.format(source))
                except Exception as err:
                    print err
                    self.c_pm('Nope, it broke.')
                        
            ### Debug
            if command == 'test1' and (source == 'lutomlin' or source == 'tjw'):
                self.old_playerinfo = 'Stats'
                self.c_pm('Hang on...')
                
            if command == 'test2' and (source == 'lutomlin' or source == 'tjw'):
                self.old_gen_log = 'Stats'
                self.c_pm('Hang on...')
                
            if command == 'clear chal' and source == 'lutomlin':
                self.challenges = {}
                self.c_pm('Challenges cleared.')
                
            if command == 'version':
                self.c_pm(self.version)
                
            if command == 'yes?':
                self.c_pm(', '.join(self.possible_yes))
                
            if command == 'no?':
                self.c_pm(', '.join(self.possible_no))
                
        else:
            if any((command in ['book','unbook','handicaps','buzz'],
                    self.more_players_re.match(command),
                    self.yes_for_re.match(command),
                    self.no_for_re.match(command))):
                self.c_pm('Go away, %s.' % source)
                    
        ### Easter Eggs
        if command == 'stop' and source == 'lutomlin':
            self.allow_eggs = False
            self.c_pm('Okay...')
        if command == 'go' and source == 'lutomlin':
            self.allow_eggs = True
            self.c_pm('Yaaay')
        if self.allow_eggs:
            
            if command.startswith('nick ') and len(command.split()) > 1:
                oldnick = c.get_nickname()
                c.nick(command.split()[1])
                if source != 'lutomlin':
                    time.sleep(1)
                    self.c_pm('Ehh... Nah.')
                    time.sleep(1)
                    c.nick(oldnick)
            
            if command == 'crash':
                self.c_pm('gack *dies*')
                c.part(self.channel,message = ':quit: Read error: Connection reset by peer')
                time.sleep(5)
                c.join(self.channel)
                self.c_pm('Just kidding...')
            
            if 'rubbish' in text and 'rwge' in source:
                self.c_pm('''It really isn't. It's just MARIO KART!''')
                
            if command == 'dance' and time.time() - self.dancetimer > 60:
                msglist = ['vo/',
                           '\ov',
                           'vov',
                           '\o/']
                for msg in msglist:
                    self.c_pm(msg)
                    time.sleep(0.5)
                for msg in msglist:
                    self.c_pm(msg)
                    time.sleep(0.5)
                
            if command == 'be rwgebot':
                time.sleep(random.randint(1,12))
                self.c_pm(random.choice(['no','good to know','seems reasonable','interesting','not too bad for once','rubbish','80 characters should be enough for anyone']))
                
            if text.startswith('wario:'):
                self.c_pm('WAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
                
            if text == 'wario: help' and time.time() - self.helptimer > 60:
                self.helptimer = time.time()
                for text in self.helptext:
                    self.c_pm(text[::-1])
                    time.sleep(0.5)
                    
            #if command == 'say ae':
            #    self.say_ae = not self.say_ae
            #    self.c_pm('Okay.')
            
            if command == 'say':
                self.replace_letters == ''
                self.c_pm('Okay.')
                
            if command == 'no vowels!':
                self.no_vowels = True
                self.c_pm('Okay.')
                
            if command == 'vowels!':
                self.no_vowels = False
                self.c_pm('Okay.')
                
            say_re = self.say_re.match(command)
            if say_re is not None:
                self.replace_letters = say_re.groups()[0]
                self.c_pm('Okay.')
                
        #print u'{}: {}'.format(source,text)
        
    def c_pm(self,msg,important=False):
        try:
            if important or not self.allow_eggs:
                self.connection.privmsg(self.channel,msg)
            else:
                if self.no_vowels:
                    msg = self.devowel(msg)
                if self.replace_letters and len(self.replace_letters) == 2:
                    msg = self.reletter(msg)
                self.connection.privmsg(self.channel,msg)
        except irc.client.ServerNotConnectedError as err:
            print 'Warning: {}'.format(err)
               
    def ae(self,msg):
        msg = msg.replace('a','~').replace('e','a').replace('~','e')
        msg = msg.replace('A','~').replace('E','A').replace('~','E')
        return msg
    
    def reletter(self,msg):
        msg2 = msg
        try:
            a = self.replace_letters[0]
            b = self.replace_letters[1]
            #msg = msg.replace(a,'~').replace(b,a).replace('~',b)
            #msg = msg.replace(a.upper(),'~').replace(b.upper(),a.upper()).replace('~',b.upper())
            aa = a.lower() + a.upper()
            bb = b.lower() + b.upper()
            msg = msg.translate(maketrans(aa + bb, bb + aa))
        except Exception as err:
            print err
            msg = msg2
        return msg
    
    def devowel(self,msg):
        msg = msg.replace('a','').replace('e','').replace('i','').replace('o','').replace('u','')
        msg = msg.replace('A','').replace('E','').replace('I','').replace('O','').replace('U','')
        return msg
        
    def book(self,source):
        self.booker = source
        self.ready_players.append(source)
        self.bookingtime = time.time()
        
    def unbook(self):
        self.required = 0
        self.booker = ''
        self.ready_players = []
        self.waittime = 0
        
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
                self.c_pm(msg,True)
                time.sleep(0.3)
            if not playerinfo[1] == 'No Change':
                if 'computer' in [pa1,pa2]:
                    self.c_pm('CPU wins! All players go down 0.25.')
                if 'computer' in [pa3,pa4]:
                    self.c_pm('CPU loses! All players go up 0.25.')
            self.unbook()
        except (AttributeError, TypeError) as err:
            print 'Found error %s' % str(err)
            
    def post_gen_to_channel(self, gen_log):
        c = self.connection
        try:
            timestamp = gen_log[0][0]
            if not timestamp >= self.latest_timestamp_gen:
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
            print timestamp
            for msg in postmsgs:
                print msg
                self.c_pm(msg,True)
                time.sleep(0.3)
        except (AttributeError, TypeError, IndexError) as err:
            print 'Found error %s' % str(err)

def main():
    import sys
    if len(sys.argv) != 4:
        print "Usage: mariobot.py  <channel> <nickname> [<server[:port]>]"
        sys.exit(1)
    #
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

    bot = MarioBot(*sys.argv[1:])
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()
    c = bot.connection