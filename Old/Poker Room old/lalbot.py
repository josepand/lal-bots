
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
    
    _versionstr = 'v0.1'
    
    helpfile = ['''LalBot %s''' % _versionstr,
                      '''This is a basic bot that does basically nothing.''']
        
    _msg_rate = 0.7
    
    def __init__(self, main_channel_name='#ladttest', nickname='lalbot', server='irc.rd.tandberg.com', port=6667):
        
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        
        self.main_channel_name = main_channel_name
        
        ### The two existing commands give two different examples of how to easily send messages
        ### The keys are REGEXES, NOT STRINGS
        ### Can make this a property, with getter and setter!
        self.commandlist = {'help':self._help,
                            'version':self._version,
                            'echo (.+)':self._echo,}
    
        self.setup()
        
        self.compile_helpfile()
        self.compile_commands()
        
        self._message_queue = []
        self._start_messaging_thread()
        self._start_loop_thread()
        
    def compile_helpfile(self):
        self._helpfile = [(msg,False,'') for msg in self.helpfile]
    
    def compile_commands(self):    
        self._commandlist = {re.compile(key):value for key, value in self.commandlist.iteritems()}
        
    def setup(self):
        print 'set_up not implemented!'
        
    def _start_loop_thread(self):
        t = threading.Timer(1, self.loop_thread)
        t.daemon = True
        t.start()
        
    def loop_thread(self):
        while True:
            print 'loop_thread not implemented!'
            time.sleep(600)
        
    def on_nicknameinuse(self, connection, event):
        connection.nick(connection.get_nickname() + "_")

    def on_welcome(self, connection, event):
        connection.join(self.main_channel_name)
        
    def on_kick(self, connection, event):
        if event.arguments[0] == connection.get_nickname():
            connection.join(self.main_channel_name)
            
    def on_pubmsg(self,connection,event):
        '''Respond to a message sent - choose from self._command_list'''
        text = event.arguments[0]
        source = event.source.nick
        
        print '{}: {}'.format(source,text)
        
        nick = self.connection.get_nickname()
        command_re = re.compile('{}: (.+)'.format(nick))
        command_match = command_re.match(text)
        if command_match is None:
            command = ''
        else:
            command = command_match.groups()[0]
        
        for c in self._commandlist:
            matchobj = c.match(command)
            if matchobj:
                self._commandlist[c](source,*matchobj.groups())
    
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
            else:
                time.sleep(self._msg_rate)
    
    ### The main way to queue miscellaneous messages
    ### Use something more clever to add batch messages as you don't want them to overlap
    def queue_message(self,text,important=False,channel=''):
        self._message_queue.append((text,important,channel))
        
    def _send_message(self,msg):
        text = msg[0]
        important = msg[1]
        if msg[2]:
            channel = msg[2]
        else:
            channel = self.main_channel_name
        try:
            if important:
                self.connection.privmsg(channel,text)
            else:
                ### Fun things can go here
                self.connection.privmsg(channel,text)
        except irc.client.ServerNotConnectedError as err:
            print 'Warning: {}'.format(err)
            
    def _help(self, source, *pargs):
        self._message_queue.extend(self._helpfile)
    
    def _version(self, source, *pargs):
        self.queue_message(self._versionstr)
    
    def _echo(self, source, *pargs):
        self.queue_message(pargs[0],False,'')
        
        
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