#!/usr/bin/env python
# -*- coding=utf-8 -*-
import irc.bot
import irc.client
import threading
import random
from datetime import date
import urllib2, re
import time
from pprint import pprint
import sys
import csv

class LalBot(irc.bot.SingleServerIRCBot):
    
    versionstr = 'v0.4'
    
    helpfile = ['''LalBot %s''' % versionstr,
                      '''This is a basic bot that does basically nothing.''']
    
    welcome_message = ''
        
    _msg_rate = 0.8
    
    REQUIRE_PREFIX = True
    
    DEBUG = 0
    def log(self,msg,level=1):
        if self.DEBUG >= level:
            pprint(msg)
    
    def __init__(self, main_channel_name='#ladttest', nickname='lalbot', server='irc.rd.tandberg.com', port=6667):
        
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        
        self.main_channel_name = main_channel_name
        
        ### The three existing commands give two different examples of how to easily send messages
        ### The keys are REGEXES, NOT STRINGS
        ### Can make this a property, with getter and setter!
        self.commandlist = {'help$':self._help,
                            'version$':self._version,
                            'echo (.+)':self._echo,
                            'm-echo (.+)':self._m_echo,
                            'shut up$':self._empty_list,}
    
        self.setup()
        
        #self.compile_helpfile()
        self.compile_commands()
        
        self._message_queue = []
        self._start_messaging_thread()
        self._start_loop_thread()
        
    #def compile_helpfile(self):
    #    self._helpfile = [(msg,False,'') for msg in self.helpfile]
    
    def get_nick(self):
        try:
            n = self.connection.get_nickname()
        except AttributeError as err:
            n = self._bot_name
            self.log('get_nick failed, using {}'.format(n))
        return n
        
    def compile_commands(self):    
        self._commandlist = {re.compile(key):value for key, value in self.commandlist.iteritems()}
        
    def setup(self):
        self.log('set_up not implemented!')
        
    def _start_loop_thread(self):
        t = threading.Timer(1, self.loop_thread)
        t.daemon = True
        t.start()
        
    def loop_thread(self):
        while True:
            self.log('loop_thread not implemented!')
            time.sleep(600)
        
    def on_nicknameinuse(self, connection, event):
        connection.nick(connection.get_nickname() + "_")

    def on_welcome(self, connection, event):
        connection.join(self.main_channel_name)
        self.queue_message(self.welcome_message)
        
    def on_kick(self, connection, event):
        if event.arguments[0] == connection.get_nickname():
            connection.join(self.main_channel_name)
            
    def on_pubmsg(self,connection,event,private=False):
        '''Respond to a message sent - choose from self._command_list'''
        text = unicode(event.arguments[0])
        source = event.source.nick
        channel = event.target
        
        if not text.startswith(self.connection.get_nickname() + ': ') and private:
            text = self.connection.get_nickname() + ': ' + unicode(text) ### Test this!
            
        try:
            #print u'{}: {}'.format(source,text)
            self.log(u'RECV {}{}: {}'.format(source,'(private)' if private else '',text))
        except Exception as err:
            self.log(err)
        
        if self.REQUIRE_PREFIX:
            nick = self.connection.get_nickname()
            command_re = re.compile(u'(?i){}: (.+)'.format(nick))
            command_match = command_re.match(text)
            if command_match is None:
                command = ''
            else:
                command = command_match.groups()[0]
        else:
            command = text
        
        for c in self._commandlist:
            matchobj = c.match(command)
            if matchobj:
                resp_dst = source if private else channel
                self._commandlist[c](source,resp_dst,*matchobj.groups())
    
    def on_privmsg(self,connection,event):
        self.on_pubmsg(connection,event,private=True)
        
    def _start_messaging_thread(self):
        t = threading.Timer(1, self._print_messages)
        t.daemon = True
        t.start()
        
    def _print_messages(self):
        while True:
            if self._message_queue:
                msg = self._message_queue.pop(0)
                self._send_message(msg)
            time.sleep(self._msg_rate)
    
    ### The main way to queue miscellaneous messages
    ### Use something more clever to add batch messages as you don't want them to overlap
    def queue_message(self,text,important=False,channel=''): ###,colour=1):
        self.log(u'SEND {}: {}'.format(channel,text))
        self._message_queue.append((text,important,channel)) ###,colour))
        
    def _send_message(self,msg):
        text = msg[0]
        important = msg[1]
        if msg[2]:
            channel = msg[2]
        else:
            channel = self.main_channel_name
        #colour = msg[3]
        try:
            if important:
                self.connection.privmsg(channel,text)
            else:
                ### Fun things can go here
                #if colour != 1:
                #    bkgcolour = 0
                #    text = u'{:02}{}{}'.format(colour,u',{:02}'.format(bkgcolour),text)
                self.connection.privmsg(channel,text)
        except Exception as err:
            self.log('Warning: {}'.format(err))
            
    def _help(self, source='', resp_dst='', *pargs):
        if source == resp_dst:
            self.queue_message('Listing Help in private message...',False,self.main_channel_name)
        for msg in self.helpfile:
            self.queue_message(msg,False,resp_dst)
            
    def _version(self, source='', resp_dst='', *pargs):
        self.queue_message(self.versionstr,True,resp_dst)
    
    def _echo(self, source='', resp_dst='', *pargs):
        self.queue_message(pargs[0],False,resp_dst)
    
    def _m_echo(self, source='', resp_dst='', *pargs):
        self.queue_message(self._multicolour_string(pargs[0]),False,resp_dst)
    
    def _empty_list(self, source='', resp_dst='', *pargs):
        self._message_queue = []
    
    def _multicolour_string(self,msg):
        string = []
        allowed_col = [2,3,4,6,7,8,9,10,11,12,13]
        count = random.randint(0,len(allowed_col)-1)
        for char in msg:
            if char  == ' ':
                string.append(u' ')
            else:
                string.append(u'{:02}{}'.format(allowed_col[count],char))
                count += 1
                count %= len(allowed_col)
        return unicode(u''.join(string))
            
def main():
    import sys
    if len(sys.argv) <= 1:
        print "Usage: 'python -i lalbot.py <channel> [<nickname> [<server> [<port>]]]'"
        print "bot=self, c=self.connection"
        sys.exit(1)
    bot = LalBot(*sys.argv[1:])
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()
    c = bot.connection