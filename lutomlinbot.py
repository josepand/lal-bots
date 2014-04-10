from LalBot.lalbot import LalBot
import random
import time
import threading

class LutomlinBot(LalBot):
    
    versionstr = u'v0.1'
    
    helpfile = []
    
    welcome_message = ''
        
    _msg_rate = 3
    
    REQUIRE_PREFIX = False
    
    _bot_name = 'lutomlin'
    
    def delay(self):
        time.sleep(random.randint(2,5))
        
    def setup(self):
        new_commands = {'':self.shup_rwge,
                        'mario: (\d) more':self.mario_yes,
                        'lutomlin: .+\?$':self.magic_8ball,
                        'News: Mario Kart result in! .+beat.+Arvinda':self.arvinda,
                        'guppy: smack lutomlin':self.no_smack,
                        }
        
        self.commandlist = new_commands
    
    def shup_rwge(self,source='',resp_dst='',*pargs):
        if source == 'rwge' and not random.randint(0,49):
            self.delay()
            self.queue_message('shup rwge')
    
    def mario_yes(self,source='',resp_dst='',*pargs):
        self.delay()
        if pargs[0] in ('1','2','3'):
            yes = random.choice(['yes','y','why not','-.-- . ...'])
            self.queue_message('mario: {}'.format(yes))
            self.queue_message('{} more'.format(pargs[0]))
        else:
            self.queue_message('wtf')
    
    def magic_8ball(self,source='',resp_dst='',*pargs):
        random_8ball_responses = ['yes',
                                  'no',
                                  'in your dreams',
                                  'i think so, ask rwge',
                                  'maybe...',
                                  'seems reasonable',
                                  'probably, it would make sense',
                                  'figure it out yourself',
                                  'nobody knows!',
                                  'obviously',
                                  'why not',
                                  'i doubt it',
                                  'tjw probably knows',
                                  'don\'t count on it',
                                  'that\'s a stupid question',
                                  'i like your style',
                                  'guppy: smack {}'.format(source),
                                  'haha yes',
                                  ]
        
        self.delay()
        self.queue_message(random.choice(random_8ball_responses))
        
    def arvinda(self,source='',resp_dst='',*pargs):
        if source == 'mario':
            notes = ['aa: :(',
                     'you need to win more aa',
                     'oh dear',
                     ]
            self.delay()
            self.queue_message(random.choice(notes))
    
    def no_smack(self,source='',resp_dst='',*pargs):
        self.delay()
        self.queue_message('oi')

    def loop_thread(self):
        while True:
            time.sleep(1)
            if not random.randint(0,7199):
                if self.get_nick() != 'lutomlin':
                    self.connection.nick('lutomlin')
                self.log('Sending message...')
                self.choose_timer_message()
                
    def choose_timer_message(self):
        possible_message_fns = [self.mario,
                                self.poker,
                                self.rajini,
                                self.cita,
                                self.endpoint_hate,
                                self.guppy,
                                self.hubot,
                                ]
        self.delay()
        random.choice(possible_message_fns)()
        
    def mario(self):
        self.queue_message('mario: 3 more')
        
    def poker(self):
        self.queue_message('poker: join')
        time.sleep(7)
        self.queue_message('poker: leave')
        
    def rajini(self):
        self.queue_message('hubot: rajini {}'.format(random.choice(('uu','aa','ob','ianp','rwge','your mother','littlerob','jobrandh'))))

    def cita(self):
        self.queue_message('citadels anyone?')
        
    def endpoint_hate(self):
        notes = ['i hate polycom',
                 'lifesizes are terrible',
                 'the OTX is broken again',
                 'who messed with the LSD lab']
        self.queue_message(random.choice(notes))
        
    def guppy(self):
        private = random.choice((True,False))
        target = random.choice(('uu','aa','ob','ianp','rwge','your mother','littlerob','jobrandh'))
        self.queue_message('guppy: smack {}'.format(target),False,'guppy' if private else '')
        
    def hubot(self):
        self.queue_message('hubot compliment poker: echo hubot rajini ship it waterpug sigh to stallman')
        
def main():
    import sys
    if len(sys.argv) <= 1:
        print "Usage: 'python -i lutomlinbot.py <channel> [<nickname> [<server> [<port>]]]'"
        print "bot=self, c=self.connection"
        sys.exit(1)
    bot = LutomlinBot(*sys.argv[1:])
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()