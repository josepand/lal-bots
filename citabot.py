#!/usr/bin/env python
# -*- coding=utf-8 -*-
#
#import sys
#sys.path.append('C:\\Users\\lutomlin\\Dropbox\\Personal\\LalBot')
#from lalbot_fake import LalBot
from LalBot.lalbot import LalBot
from pprint import pprint
import time
import datetime
import threading
import random
#from citacards import CitaData
from Citadels.citagame import CitaGame
from Citadels.citacards import CHARACTERS, DISTRICTS, COLOURS, CHAR_NAMES, CHAR_DEFAULTS, CHAR_NUMS, AFFINITY

from whitelist import WHITELIST

FIRST = ['zero',
         'first',
         'second',
         'third',
         'fourth',
         'fifth',
         'sixth',
         'seventh']

#CitaData.char_names
#CitaData.char_numbers
#CitaData.Chars()
#CitaData.Dists()

class CitaBot(LalBot):
    
    versionstr = u'v1.2.2'
    
    _whitelisted = False
    
    player_whitelist = WHITELIST
    
    _bot_name = 'citadels'# 'cds' # it's only the default fallback if we can't find a name
    
    def setup(self):
        self.allow_newgame = True
        
        new_commands = {'rules':self.print_rules,
                        'scores':self.print_scores,
                        'join':self.add_player,
                        'leave':self.remove_player,
                        'players':self.tell_players,
                        #'switch char ([a-zA-Z, ]+)':self.replace_char,
                        'extra dist ?([a-zA-Z, ]+)?':self.use_dc,
                        'max build ?(\d)?$':self.set_max_build,
                        'start':self.start_game,
                        'cancel game':self.cancel_game,
                        
                        'status':self.status,
                        
                        'list characters':self.list_characters,
                        'char ([a-zA-Z ]+)':self.read_character,
                        'dist ([a-zA-Z ]+)':self.read_district,
                        'cards':self.tell_player_cards,
                        'read my districts':self.read_my_districts,
                        'districts':self.show_districts,
                        'built':self.tell_player_built,
                        'crown':self.crown,
                        'gold':self.show_gold,
                        
                        'options':self.options,
                        
                        'choose ([a-zA-Z ]+)':self.choose_character,
                        'discard ([a-zA-Z ]+)':self.discard_character,
                        
                        '(take gold|take cards)':self.take_action,
                        'return ([a-zA-Z ]+)':self.return_dist_card,
                        'build ([a-zA-Z ]+)':self.build_district,
                        'use ([a-zA-Z]+)(?: with (?:([a-zA-Z_]+)\'s|(my))? ?([a-zA-Z ]+))?':self.use_district,
                        'end':self.end_turn,
                        
                        'murder ([a-zA-Z ]+)':self.assassin_sp,
                        'bewitch ([a-zA-Z ]+)':self.witch_sp,
                        'steal from ([a-zA-Z ]+)':self.thief_sp,
                        'exchange with ([a-zA-Z_]+)':self.magician_sp_e,
                        'replace ([a-zA-Z, ]+)':self.magician_sp_r,
                        'destroy ([a-zA-Z_]+)\'s ([a-zA-Z ]+)':self.warlord_sp,
                        }
        
        self.commandlist.update(new_commands)
        
        self.game = CitaGame()
    @property
    def welcome_message(self):
        n = self.get_nick()
        welcome_message = u'Internet Relay Citadels {}. Type "help" in a private message for more information.'.format(self.versionstr,n)
        return welcome_message
    
    @property
    def helpfile(self):
        n = self.get_nick()
        helpfile = [u'''CitaBot {}'''.format(self.versionstr),
                    u'''CitaBot accepts any command in both private and public message, and it will generally try to respond in the same place you talk.''',
                    u'''CitaBot does not need the "{}: " prefix in a private message.'''.format(n),
                    u'''Of course some commands will always need to respond either privately or publically.'''.format(n),
                    u'''Type "{}: rules" for a basic explanation of the rules, and a link to the full rules.'''.format(n),
                    u'''Type "{}: scores" to show how scores are calculated.'''.format(n),
                    u'''Type "{}: join" to join a game in setup.'''.format(n),
                    u'''Type "{}: leave" to leave a game in setup.'''.format(n),
                    u'''Type "{}: players" to see who is playing.'''.format(n),
                    #u'''Type "{}: switch char [name], [name],..." to use special characters.'''.format(n), ### EXTRA CHARACTERS ARE NOT IMPLEMENTED YET
                    u'''Type "{}: extra dist [name], [name],..." to use more special districts.'''.format(n),
                    u'''Type "{}: max build [x]" to set the number of districts required to complete a city. 2-8, {} is default for a new game.'''.format(n,self.game.MAX_BUILD),
                    u'''Typing "extra dist" or "max build" with no arguments will show what ones are currently selected.''',
                    u'''Type "{}: start" to start a game when players are ready.'''.format(n),
                    u'''Type "{}: status" to see whose turn it is.'''.format(n),
                    u'''Type "{}: list characters" for a list of the characters being used this game.'''.format(n),
                    u'''Type "{}: char [name]" to read a character card.'''.format(n),
                    u'''Type "{}: dist [name]" to read a district card.'''.format(n),
                    u'''Type "{}: districts" to see a list of constructed districts.'''.format(n),
                    u'''Type "{}: cards" to list the district cards you are holding.'''.format(n),
                    u'''Type "{}: read my districts" to read all your district cards.'''.format(n),
                    u'''Type "{}: built" to list the districts in your city.'''.format(n),
                    u'''Type "{}: crown" to see who has the Crown.'''.format(n),
                    u'''Type "{}: gold" to list gold balances.'''.format(n),
                    u'''Type "{}: options" to list your available options at any point.'''.format(n),
                    ]
        return helpfile
                
    @property
    def rulesfile(self):
        n = self.get_nick()
        rulesfile = [u'''Citadels Rulebook: http://desktopgames.com.ua/games/3/citadelsrules.pdf''',
                     u'''(Only the basic characters are available so far.)''',
                     u'''The objective is to score the most points by the end of the game.''',
                     u'''Points are scored by the amount of gold you have spend building districts.''',
                     u'''All scoring rules are available with "{}: scores".'''.format(n),
                     u'''Each round consists of two parts - character selection, and character turns.''',
                     u'''Characters are selected secretly, one at a time from the available choices.''',
                     u'''The player with the Crown is the first to choose their character card(s) - check the full rulebook for exact selection rules.''',
                     u'''Player turns are then taken in order of the character numbers, not by seating.''',
                     u'''Turns are:''',
                     u'''1) Take action (either taking gold or new district cards),''',
                     u'''2) Build a district and/or use Special Abilities.''',
                     u'''The game ends when any player completes their city (this means building {} districts).'''.format(self.game.MAX_BUILD),
                     u'''Default special districts are: Haunted City, Keep x2, Laboratory, Smithy, Observatory,''',
                     u'''Dragon Gate, University, Library, Great Wall, School Of Magic.''',
                     u'''House Rule: Observatory and Library combined mean you draw 3 cards and keep 2.''',
                     
                     
                     #u'''House Rule: The Bell Tower's effect is mandatory because I can't be bothered to figure out how to code it.''',
                     #u'''House Rule: The Graveyard is not being used because I can't be bothered to figure out how to code it.''',
                     #u'''House Rule: The Ball Room's effect is stupid so I can't be bothered to figure out how to code it.''',
                     ]
        return rulesfile
    
    @property
    def scoresfile(self):
        n = self.get_nick()
        scoresfile = [u'''Scoring:''',
                      u'''The goal is to score the most points. Points are scored at the end of the game.''',
                      u'''You get one point for each gold a district in your city cost to build.''',
                      u'''If you were first to complete your city, you earn 4 bonus points.''',
                      u'''Other players who have a complete city when the game ends earn 2 bonus points.''',
                      u'''If you have one of each of the 4 district types, you score 3 bonus points.''',
                      u'''There are also some special districts that affect your final score.''',
                      ]
        return scoresfile
    
    def print_rules(self,source='',resp_dst='',*pargs):
        if source == resp_dst:
            self.queue_message('Listing Rules in private message...',False,self.main_channel_name)
        for message in self.rulesfile:
            self.queue_message(message,False,resp_dst)
    
    def print_scores(self,source='',resp_dst='',*pargs):
        if source == resp_dst:
            self.queue_message('Listing Scoring in private message...',False,self.main_channel_name)
        for message in self.scoresfile:
            self.queue_message(message,False,resp_dst)
    
    def add_player(self,source='',resp_dst='',*pargs):
        if not self._whitelisted or source in self.player_whitelist:
            if not self.game.game_running:
                if source not in self.game.player_name_list:
                    self.game.player_name_list.append(source)
                    self.queue_message(u'Player {} joined the game.'.format(source))
                    if source == resp_dst:
                        self.queue_message(u'Joined.',False,resp_dst)
                else:
                    self.queue_message(u'You are already in, {}.'.format(source),False,resp_dst)
            else:
                self.queue_message(u'Game is in progress already!')
        else:
            self.queue_message(u'Go away, {}.'.format(source),False,resp_dst)
    
    def remove_player(self,source='',resp_dst='',*pargs):
        if not self.game.game_running:
            if source in self.game.player_name_list:
                self.game.player_name_list.remove(source)
                self.queue_message(u'Player {} left the game.'.format(source))
                if source == resp_dst:
                    self.queue_message(u'Left.',False,resp_dst)
            else:
                self.queue_message(u'Thanks, {}.'.format(source),False,resp_dst)
        else:
            self.queue_message(u'Game is in progress already!')
    
    def tell_players(self,source='',resp_dst='',*pargs):
        if not self.game.game_running:
            self.queue_message(u'Players ready to start: {}'.format(', '.join(self.game.player_name_list)),False,resp_dst)
        else:
            self.queue_message(u'Players playing: {}'.format(', '.join([p['name'] for p in self.game.players])),False,resp_dst)
    
    def replace_char(self,source='',resp_dst='',*pargs):
        if self.game.game_running:
            self.queue_message(u'Not available during a running game.',False,resp_dst)
        else:
            #self.queue_message(u'Bonus characters not available yet.',False,resp_dst)
            charnames = pargs[0].split(',')
            charnames = [c.strip(', ') for c in charnames if c.strip(', ')]
            self.game.char_replacements = []
            self.queue_message('New setup:')
            for c in charnames:
                if c.lower() in [cn.lower() for cn in CHAR_NAMES]:
                    if c.lower() not in [cn.lower() for cn in CHAR_DEFAULTS]:
                        self.game.char_replacements.append(CHAR_NUMS[self.caps(c.lower())])
                        self.queue_message('Using {} as {}.'.format(self.caps(c.lower()),CHAR_NUMS[self.caps(c.lower())])) ### Dammit, capitals
                    else:
                        if CHAR_NUMS[self.caps(c.lower())] in self.game.char_replacements:
                            self.game.char_replacements.remove(CHAR_NUMS[self.caps(c.lower())])
                        self.queue_message('{} is a default character, using as {}.'.format(self.caps(c.lower()),CHAR_NUMS[self.caps(c.lower())]))
                else:
                    self.queue_message('No such character: {}'.format(source,c),False,resp_dst)
    
    def use_dc(self,source,resp_dst='',*pargs): ### !!! SHOULDN'T BE ON/OFF, SHOULD BE CHOICE
        if self.game.game_running:
            self.queue_message(u'Not available during a running game.',False,resp_dst)
        else:
            if not pargs[0]:
                dist_names_valid = []
                for dist_num in self.game.use_dc_districts:
                    dist_names_valid.append(DISTRICTS[dist_num]['name'])
                self.queue_message('Using extra districts: {}'.format(', '.join(dist_names_valid) if dist_names_valid else 'no extra districts.'),False,resp_dst)
            else:
                distnames = pargs[0].split(',')
                distnames = [self.caps(d.strip(', ')) for d in distnames if d.strip(', ')]
                pprint(distnames)
                self.game.use_dc_districts = []
                for d in distnames:
                    if d == 'None':
                        pass
                    elif d in [dn['name'] for dn in DISTRICTS]:
                        dists = [(i,dn) for i,dn in enumerate(DISTRICTS[27:40])]
                        for i,dn in dists:
                            if dn['name'] == d:
                                district = dn
                                num_dist = i + 27
                                if num_dist not in self.game.use_dc_districts:
                                    self.game.use_dc_districts.append(num_dist)
                                else:
                                    self.queue_message('Trying to use a district twice...',False,resp_dst)
                                break
                        else:
                            self.queue_message('{} is a either a default district or not usable.'.format(self.caps(d)),False,resp_dst)
                    else:
                        self.queue_message('No such district: {}'.format(d),False,resp_dst)
                        
                dist_names_valid = []
                for dist_num in self.game.use_dc_districts:
                    dist_names_valid.append(DISTRICTS[dist_num]['name'])
                self.queue_message('New setup: Using {}'.format(', '.join(dist_names_valid if dist_names_valid else ['no extra districts.'])))

    def set_max_build(self,source='',resp_dst='',*pargs):
        if pargs[0]:
            if self.game.game_running:
                self.queue_message(u'Not available during a running game.',False,resp_dst)
            else:
                max_build = int(pargs[0])
                if not 1 < max_build  < 9:
                    self.queue_message(u'Required districts should be between 2 and 8.',False,resp_dst)
                else:
                    self.game.max_builds = max_build
                    self.queue_message(u'New setup: {} districts will be required for a completed city.'.format(self.game.max_builds))
        else:
                self.queue_message(u'{} districts will be required for a completed city.'.format(self.game.max_builds))
                
            
    def start_game(self,source='',resp_dst='',*pargs):
        if self.game.game_running:
            self.queue_message(u'Game already running.',False,resp_dst)
        else:
            if not 2 <= len(self.game.player_name_list) < 7: ### Should be <= 7 but 7 is hard
                self.queue_message(u'This game is implemented for 2-6 players.',False,resp_dst)
            elif source not in self.game.player_name_list:
                pass
            else:
                self.game.start_game()
                self.queue_message(u'Game starting!')
                self.queue_message(u'All players begin with 2 Gold.')
                self.tell_all_player_cards()
                self.ki = self.game.king_index
                self.start_round(source,resp_dst,*pargs)
    
    def cancel_game(self,source='',resp_dst='',*pargs):
        if self.game.game_running and source == 'lutomlin':
            self.score_and_end()
        else:
            self.queue_message('Go away.')
        
    def start_round(self,source='',resp_dst='',*pargs):
        self.queue_message('New round!')
        self.crown()
        face_up = self.game.start_character_choices()
        if face_up:
            self.queue_message(u'Face up card(s) (not used this round): {}'.format(', '.join('{}: {}'.format(c['number'],c['name']) for c in face_up)))
        p = self.game.get_action_player_name()
        self.queue_message(u'{}: Please take your first choice of card. Use private messages ("choose [name]").'.format(p))
        player = self.game.get_action_player_name()
        self.list_char_deck(player,player,*pargs)
    
    def choose_character(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player_name()
        if player == source:
            if resp_dst != source:
                self.queue_message(u'Please use private messaging for choices!',False,resp_dst)
            success = self.game.choose_character(source,pargs[0])
            if success is True:
                self.queue_message(u'{} has chosen.'.format(source))
                self.queue_message(u'You chose {}.'.format(self.caps(pargs[0].lower())),False,source)
                p = self.game.get_action_player_name()
                if self.game.choose:
                    if self.game.wait_for_discard:
                        self.queue_message(u'{}: now place one card face down ("discard [name]").'.format(p))
                        self.list_char_deck(p,resp_dst,*pargs)
                    else:
                        self.queue_message(u'{}: Your turn to choose ("choose [name]").'.format(p))
                        self.list_char_deck(p,resp_dst,*pargs)
                else:
                    self.queue_message(u'Characters have been chosen!'.format(p))
                    self.call_character()
            else:
                self.queue_message(u'Not valid: {}'.format(success),False,resp_dst)
     
    def discard_character(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player_name()
        if player == source:
            if resp_dst != source:
                self.queue_message(u'Please use private messaging for choices!',False,resp_dst)
            success = self.game.discard_character(source,pargs[0])
            if success is True:
                self.queue_message(u'{} has discarded.'.format(source))
                self.queue_message(u'You discarded {}.'.format(self.caps(pargs[0].lower())),False,source)
                p = self.game.get_action_player_name()
                if self.game.choose:
                    if not self.game.wait_for_discard:
                        self.queue_message(u'{}: Your turn to choose ("choose [name]").'.format(p))
                        self.list_char_deck(p,resp_dst,*pargs)
                    else:
                        self.queue_message(u'{}: WHAT?!.'.format(p))
                else:
                    self.queue_message(u'Characters have been chosen!'.format(p))
                    self.call_character()
            else:
                self.queue_message(u'Not valid: {}'.format(success),False,resp_dst)
    
    def list_char_deck(self,source='',resp_dst='',*pargs):
        self.queue_message(u'Characters available: {}'.format(', '.join(c['name'] for c in self.game.characters)),False,source)
        
    def list_dist_deck(self,source='',resp_dst='',*pargs):
        num_one_msg = 5
        self.queue_message('Listing district deck for Lighthouse selection:',False,source)
        dists = [u'{}: Cost {}, Type {}'.format(dist['name'],dist['cost'],AFFINITY[dist['affinity']]) for dist in self.game.districts]
        num_dists = len(dists)
        for i in xrange((len(dists)/num_one_msg) + 1):
            start = i*num_one_msg
            end = (i+1)*num_one_msg
            if end > num_dists: end = -1
            self.queue_message(' | '.join(dists[start:end]),False,source)
            
    # def choose_character_int(self,source='',resp_dst='',*pargs):
        # num = int(pargs[0])
        # self.choose_character(source,resp_dst,num)
    
    # def discard_character_int(self,source='',resp_dst='',*pargs):
        # num = int(pargs[0])
        # self.discard_character(source,resp_dst,num)
        
    def list_characters(self,source='',resp_dst='',*pargs):
        if self.game.game_running:
            for char in self.game.characters_match:
                self.queue_message('{}: {}'.format(char['number'],char['name']),False,resp_dst)
        else:
            self.queue_message(u'Not currently available outside a game (this function needs to be finished).',False,resp_dst)
        
    def read_character(self,source='',resp_dst='',*pargs):
        for char in CHARACTERS:
            if char['name'].lower() == pargs[0].lower():
                self.queue_message('{}: {}'.format(char['number'],char['name']),False,resp_dst)
                for l in char['text']:
                    self.queue_message(l,False,resp_dst)
                break
        else:
            self.queue_message(u'Char not found: {}'.format(pargs[0]),False,resp_dst)
    
    def read_district(self,source='',resp_dst='',*pargs):
        for dist in DISTRICTS:
            if dist['name'].lower() == pargs[0].lower():
                self.queue_message(u'{}: Cost {}, Type {}'.format(dist['name'],dist['cost'],AFFINITY[dist['affinity']]),False,resp_dst)
                for l in dist['text']:
                    self.queue_message(l,False,resp_dst)
                break
        else:
            self.queue_message(u'District not found: {}'.format(pargs[0]),False,resp_dst)
                    
    def read_my_districts(self,source='',resp_dst='',*pargs):
        for p in self.game.players:
            if p['name'] == source:
                player = p
                break
        else:
            return
        if source == resp_dst:
            self.queue_message('Reading districts in private message...',False,self.main_channel_name)
        if player['districts']:
            self.queue_message(u'Cards in hand:',False,source)
            for district in player['districts']:
                self.read_district(source,source,district['name'])
        if player['built']:
            self.queue_message(u'Districts built:',False,source)
            for district in player['built']:
                self.read_district(source,source,district['name'])
        
    def show_districts(self,source='',resp_dst='',*pargs):
        for player in self.game.players:
            n = len(player['built'])
            self.queue_message(u'{} has built {} district{}.'.format(player['name'], n if n > 0 else 'no','' if n == 1 else 's'),False,resp_dst)
            if player['built']:
                self.queue_message(u'{} has: {}'.format(player['name'],', '.join(['{} (cost {}, {})'.format(d['name'],d['cost'],AFFINITY[d['affinity']]) for d in player['built']])),False,resp_dst)
    
    def crown(self,source='',resp_dst='',*pargs):
        if self.game.game_running:
            self.queue_message(u'{} has the Crown.'.format(self.game.players[self.game.king_index]['name']),False,resp_dst)
        
    def tell_player_cards(self,source='',resp_dst='',*pargs):
        for p in self.game.players:
            if p['name'] == source:
                player = p
                self.queue_message(u'You hold: {}'.format(', '.join('{} (cost {}, {})'.format(d['name'],d['cost'],AFFINITY[d['affinity']]) for d in player['districts'])),False,source)
                break
    
    def tell_player_built(self,source='',resp_dst='',*pargs):
        for p in self.game.players:
            if p['name'] == source:
                player = p
                self.queue_message(u'Your City contains: {}'.format(', '.join('{} (cost {}, {})'.format(d['name'],d['cost'],AFFINITY[d['affinity']]) for d in player['built'])),False,resp_dst)
                break
    
    def tell_player_gold(self,source='',resp_dst='',*pargs):
        for p in self.game.players:
            if p['name'] == source:
                player = p
                self.queue_message(u'You have {} gold'.format(player['gold']),False,source)
                break
    
    def show_gold(self,source='',resp_dst='',*pargs):
        if self.game.game_running:
            self.queue_message(u'Gold: {}'.format(', '.join(['{}: {}'.format(p['name'],p['gold']) for p in self.game.players])),False,resp_dst)
        
    def tell_all_player_cards(self,source='',resp_dst='',*pargs):
        for player in self.game.players:
            self.tell_player_cards(player['name'],player['name'])
            
    def tell_player_new_cards(self,source='',resp_dst='',*pargs):
        if self.game.new_taken_cards:
            self.queue_message(u'You drew: {}'.format(', '.join('{} (cost {}, {})'.format(d['name'],d['cost'],AFFINITY[d['affinity']]) for d in self.game.new_taken_cards)),False,source)
        else:
            self.queue_message(u'How are we here? tell_player_new_cards')
            
    def call_character(self,source='',resp_dst='',*pargs):
        char = self.game.get_action_card()
        player = self.game.get_action_player()
        if player and char:
            self.queue_message(u"It is {}'s turn as the {} ({})!".format(player['name'],char['name'],char['number']))
            if char['name'] == 'King':
                if self.ki != self.game.king_index:
                    self.queue_message(u'{} takes the Crown!'.format(self.game.players[self.game.king_index]['name']))
                    p2 = self.game.find_district_owner('Throne Room')
                    if p2:
                        self.queue_message(u'{} receives 1 gold for the Throne Room.'.format(p2['name']))
                        self.tell_player_gold(p2['name'])
                else:
                    self.queue_message(u'{} already has the Crown.'.format(player['name']))
            if self.game.thief_char == char:
                self.queue_message(u"{} steals all of {}'s gold!".format(self.game.find_char_owner('Thief')['name'],player['name']))
                self.tell_player_gold(self.game.find_char_owner('Thief')['name'])
                self.tell_player_gold(player['name'])
            self.queue_message(u'{}: Take your action ("take gold" or "take cards").'.format(player['name']))
        else:
            if self.game.endgame:
                self.score_and_end()
            else:
            ### This could really really really not work - turns out it does
                self.start_round()
    
    def score_and_end(self,source='',resp_dst='',*pargs):
        self.queue_message(u'Game Over!')
        self.show_districts()
        scores = self.game.end_game()
        self.log(scores)
        x = 999
        for i,p in enumerate(sorted(scores,key = lambda v: -v[1])):
            if i == 0:
                x = p[1]
            else:
                if x != p[1]:
                    self.queue_message(u'{} is {} with {} points.'.format(p[0],FIRST[i+1],p[1]))
                    x = p[1]
                else:
                    self.queue_message(u'{} also has {} points.'.format(p[0],p[1]))
        
    def status(self,source='',resp_dst='',*pargs):
        if self.game.game_running:
            p = self.game.get_action_player_name()
            if self.game.choose:
                self.queue_message(u'Waiting on {} to choose their character.'.format(p),False,resp_dst)
            else:
                if self.game.turn_stage == 0:
                    self.queue_message(u'Waiting on {} to take an action using "take gold" or "take cards".'.format(p),False,resp_dst)
                if self.game.turn_stage == 1:
                    self.queue_message(u'Waiting on {} to discard a character using "discard [name]'.format(p),False,resp_dst)
                if self.game.turn_stage == 2:
                    self.queue_message(u'Waiting on {} to build or use special abilities.'.format(p),False,resp_dst)
                if self.game.turn_stage == 3:
                    self.queue_message(u'Waiting on {} to end their turn.'.format(p),False,resp_dst)
        else:
            self.queue_message(u'Game has not started yet.',False,resp_dst)
                
    def options(self,source='',resp_dst='',*pargs):
        if self.game.game_running:
            player = self.game.get_action_player_name()
            charname = self.game.get_action_card_name()
            if player == source:
                self.queue_message(u'Options available:',False,resp_dst)
                if self.game.choose:
                    if self.game.wait_for_discard:
                        self.queue_message(u'"discard [name] to discard a character (privately).',False,resp_dst)
                    else:
                        self.queue_message(u'"choose [name] to choose your character (privately).',False,resp_dst)
                else:
                    if self.game.turn_stage == 0:
                        #self.queue_message("You must take your turn action.")
                        self.queue_message(u'"take gold" to take 2 gold.',False,resp_dst)
                        self.queue_message(u'"take cards" to take 2 district cards, one of which must be returned privately with "return [name]".',False,resp_dst)
                    elif self.game.turn_stage == 1:
                        #self.queue_message('You must return one of your new district cards to the bottom of the deck.')
                        self.queue_message(u'"return [name]" to return one of the drawn cards (privately).',False,resp_dst)
                    elif self.game.turn_stage == 2:
                        if charname == 'Witch':
                            self.queue_message(u'"bewitch [name]" to bewitch a character and take their turn.',False,resp_dst)
                            return ### This should be the only possible action for Witch - not even "end".
                        if self.game.built is not True and charname != 'Navigator':
                            self.queue_message(u'"build [name]" to build one of your district cards into your city (requires gold).',False,resp_dst)
                        if not self.game.used_action:
                            if charname == 'Assassin':
                                self.queue_message(u'"murder [name]" to assassinate one character, as your special ability.',False,resp_dst)
                            elif charname == 'Thief':
                                self.queue_message(u'"steal from [name]" to steal all the gold of one character, as your special ability.',False,resp_dst)
                            elif charname == 'Magician':
                                self.queue_message(u'"exchange with [name]" to exchange your district cards with another player.',False,resp_dst)
                                self.queue_message(u'"replace [name], [name],..." to return district cards to the bottom of the deck and draw the same number.',False,resp_dst)
                            elif charname == 'King':
                                self.queue_message(u'"take gold" to take a number of gold equal to the number of Noble districts you have constructed.',False,resp_dst)
                                self.queue_message(u'Hint: do this after building a Noble district to earn 1 more gold.',False,resp_dst)
                            elif charname == 'Bishop':
                                self.queue_message(u'"take gold" to take a number of gold equal to the number of Religious districts you have constructed.',False,resp_dst)
                                self.queue_message(u'Hint: do this after building a Religious district to earn 1 more gold.',False,resp_dst)
                            elif charname == 'Merchant':
                                self.queue_message(u'"take gold" to take a number of gold equal to the number of Trade districts you have constructed.',False,resp_dst)
                                self.queue_message(u'Hint: do this after building a Trade district to earn 1 more gold.',False,resp_dst)
                            elif charname == 'Navigator':
                                self.queue_message(u'"take gold" to take 4 gold, as your special ability.',False,resp_dst)
                                self.queue_message(u'"take cards" to take 4 district cards, as your special ability.',False,resp_dst)
                            elif charname == 'Architect' and self.game.built is not True:
                                self.queue_message(u'You can build up to 3 times this turn.',False,resp_dst)
                            elif charname == 'Warlord':
                                self.queue_message(u'"take gold" to take a number of gold equal to the number of Military districts you have constructed.',False,resp_dst)
                                self.queue_message(u'Hint: do this after building a Military district to earn 1 more gold.',False,resp_dst)
                        if charname == 'Warlord':
                            self.queue_message(u'''"destroy [player]'s [district]" to destroy a constructed district.''',False,resp_dst)
                            self.queue_message(u'''This must be done as the end of your turn, and costs you one less gold than required to construct it.''',False,resp_dst)
                            self.queue_message(u'''If the target player owns a Great Wall, you must pay 1 extra gold.''',False,resp_dst)
                        p = self.game.get_action_player()
                        if 'Laboratory' in [d['name'] for d in p['built']] and not self.game.used_laboratory:
                            self.queue_message(u'''"use Laboratory with [name]" to use the Laboratory's ability.''',False,resp_dst)
                        if 'Smithy' in [d['name'] for d in p['built']] and not self.game.used_smithy:
                            self.queue_message(u'''"use Smithy" to use the Smithy's ability.''',False,resp_dst)
                        if 'Armory' in [d['name'] for d in p['built']]:
                            self.queue_message(u'''"use Armory with ([name]'s|my) [name]" to use the Armory's ability.''',False,resp_dst)
                        if 'Museum' in [d['name'] for d in p['built']] and not self.game.used_museum:
                            self.queue_message(u'''"use Museum with [name]" to use the Museum's ability.''',False,resp_dst)
                        if 'Lighthouse' in [d['name'] for d in p['built']] and self.game.allow_lighthouse_select:
                            self.queue_message(u'''"use Lighthouse with [name]" to use the Lighthouse's ability.''',False,resp_dst)
                        ### Add all new usable districts here.
                        self.queue_message(u'"end" to end your turn.',False,resp_dst)
        else:
            n = self.get_nick()
            self.queue_message(u'''Type "{}: join" to join a game in setup.'''.format(n),False,resp_dst)
            self.queue_message(u'''Type "{}: leave" to leave a game in setup.'''.format(n),False,resp_dst)
            #self.queue_message(u'''Type "{}: switch char [name], [name],..." to use special characters.'''.format(n),False,resp_dst)
            self.queue_message(u'''Type "{}: extra dist [name], [name],..." to use more special districts.'''.format(n),False,resp_dst)
            self.queue_message(u'''Type "{}: max build [x]" to set the number of districts required to complete a city. 2-8, {} is default for a new game.'''.format(n,self.game.MAX_BUILD),False,resp_dst)
            self.queue_message(u'''Type "{}: start" to start a game when players are ready.'''.format(n),False,resp_dst)
    
    def take_action(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player_name()
        if player == source:
            act = (0 if pargs[0] == 'take gold' else 1 if pargs[0] == 'take cards' else None)
            stage = self.game.turn_stage
            player = self.game.get_action_player()
            card = self.game.get_action_card()
            should_tell = False
            success = self.game.take_action(source,act)
            if success is True:
                if act == 0:
                    if stage == 0:
                        self.queue_message(u'{} takes 2 gold.'.format(source))
                        self.post_action(source,resp_dst)
                    elif stage > 1:
                        if card['name'] in ['King','Emperor','Bishop','Abbot','Merchant','Warlord','Diplomat']:
                            dist_num = len([d for d in player['built'] if d['affinity'] == card['affinity'] or d['name'] == 'School Of Magic'])
                            self.queue_message(u'{} takes {} gold for {} {} district{}.'.format(source,dist_num,dist_num,AFFINITY[card['affinity']],'' if dist_num == 1 else 's'))
                            self.tell_player_gold(source)
                        elif card['name'] == 'Navigator':
                            self.queue_message('{} takes 4 gold as the Navigator.'.format(source))
                            self.tell_player_gold(source)
                        else:
                            self.queue_message(u'ARGH! How did we get here? take_action gold success with stage > 0 and not special')
                elif act == 1:
                    if stage == 0:
                        if 'Observatory' in [d['name'] for d in player['built']]:
                            if 'Library' in [d['name'] for d in player['built']]:
                                self.queue_message(u'{} takes 3 cards - you must return 1 (use "return [card name]" in a private message).'.format(source))
                            else:
                                self.queue_message(u'{} takes 3 cards - you must return 2 (use "return [card name]" in a private message).'.format(source))
                        else:
                            self.queue_message(u'{} takes 2 cards - you must return 1 (use "return [card name]" in a private message).'.format(source))
                    elif stage > 1:
                        if card['name'] == 'Navigator':
                            self.queue_message('{} takes 4 district cards as the Navigator.'.format(source))
                        else:
                            self.queue_message(u'ARGH! How did we get here? take_action cards success with stage > 0 and not special')
                    self.tell_player_new_cards(source)
                if should_tell:
                    self.tell_player_gold(source)
            else:
                self.queue_message(u'Not valid - {}'.format(success),False,resp_dst)
                
    def return_dist_card(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player_name()
        if player == source:
            card = self.game.get_action_card()
            if resp_dst != source:
                self.queue_message(u"Warning: Please don't reveal the returned card to the channel.")
            success = self.game.return_district(source,pargs[0])
            if success is True:
                self.queue_message(u'{} returned a card to the bottom of the deck.'.format(source))
                self.queue_message(u'Returned {} to the deck.'.format(self.caps(pargs[0])),False,resp_dst) ### Fuck .capitalize
                if self.game.turn_stage == 2:
                    self.post_action(source,resp_dst)
                elif self.game.turn_stage == 1:
                    self.queue_message(u'You must return 1 more card.',False,source)
                else:
                    self.queue_message(u'Not quite sure what happened! Observatory code broke?')
            else:
                self.queue_message(u'Not valid - {}'.format(success),False,resp_dst)
    
    def post_action(self,source='',resp_dst='',act=0):
        player = self.game.get_action_player_name()
        card = self.game.get_action_card()
        should_tell_g = act == 0
        should_tell_c = act == 1
        if player != source:
            self.queue_message(u'Witch takes over {}\'s turn - {} may take the rest of the turn.'.format(source,player))
        if card['name'] == 'Architect':
            should_tell_c = True
            self.queue_message(u'{} receives 2 additional cards as the Architect.'.format(player))
        elif card['name'] == 'Merchant':
            should_tell_g = True
            self.queue_message(u'{} receives 1 additional gold as the Merchant.'.format(player))
        if should_tell_g:
            self.tell_player_gold(source)
        if should_tell_c:
            self.tell_player_cards(source)
    
    def build_district(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player_name()
        if player == source:
            endgame = self.game.endgame
            success = self.game.build_district(source,pargs[0])
            if success is True:
                dn = self.caps(pargs[0].lower()) ### Fuck .capitalize
                self.queue_message(u'{} built by {}.'.format(dn,source))
                
                if self.game.allow_lighthouse_select and dn == 'Lighthouse':
                    self.queue_message(u'You have built a Lighthouse! You may select one card from the district deck with "use Lighthouse with [name]".')
                    self.list_dist_deck(source)
                if dn == 'Bell Tower':
                    self.queue_message(u'The Bell Tower tolls! A completed city has shrunk to {} districts.'.format(self.game.max_builds))
                self.tell_player_gold(source)
                self.tell_player_cards(source)
                self.tell_player_built(source,resp_dst)
                if endgame is False and self.game.endgame:
                    self.queue_message(u'{} has built {} districts! Game will end this round.'.format(player,self.game.max_builds))
            else:
                self.queue_message(u'Not valid - {}'.format(success),False,resp_dst)
    
    def use_district(self,source='',resp_dst='',*pargs): ### Lab, Smi,
        player = self.game.get_action_player_name()
        if player == source:
            dist_name = pargs[0]
            player_name = pargs[1]
            my = pargs[2]
            target = pargs[3]
            success = self.game.use_district(dist_name,player_name,my,target)
            if success is True:
                if self.caps(dist_name) == 'Laboratory':
                    self.queue_message(u'{} used the Laboratory to discard a card and receive one gold.'.format(source))
                    self.tell_player_gold(source)
                elif self.caps(dist_name) == 'Smithy':
                    self.queue_message(u'{} used the Smithy to buy 3 district cards for 2 gold.'.format(source))
                    self.tell_player_cards(source)
                    self.tell_player_gold(source)
                elif self.caps(dist_name) == 'Armory':
                    if player_name:
                        self.queue_message(u"{} used the Armory to destroy {}'s {}.".format(source,player_name,self.caps(target)))
                    elif my:
                        self.queue_message(u"{} used the Armory to destroy their own {}.".format(source,self.caps(target)))
                    else:
                        self.queue_message(u'Something weird happened in use_district, no player/my')
                    if self.caps(target) == 'Bell Tower':
                        self.queue_message(u'The Bell Tower was destroyed! A completed city is back to {} districts.'.format(self.game.max_builds))
                elif self.caps(dist_name) == 'Museum':
                    self.queue_message(u'{} placed a {} card under the Museum. Current total {} card{}.'.format(source,self.caps(target),self.game.museum_count,'' if self.game.museum_count == 1 else 's'))
                elif self.caps(dist_name) == 'Lighthouse':
                    self.queue_message(u'{} used the Lighthouse to select a card from the district deck.'.format(source))
                    self.tell_player_cards(source)
            else:
                self.queue_message(u'Not valid - {}'.format(success),False,resp_dst)
    
    def end_turn(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player()
        self.ki = self.game.king_index
        if player['name'] == source:
            char = self.game.get_action_card()
            if char['name'] == 'Witch' and not self.game.used_action:
                self.queue_message(u'Witch must bewitch someone.',False,resp_dst)
                return ### Need game.end_turn to be usable, so we can call that elsewhere...
            tax = self.game.tax_collect
            built = self.game.built
            gold = player['gold']
            dists = len(player['districts'])
            should_tell = False
            success = self.game.end_turn()
            if success is True:
                self.queue_message(u'{} ends their turn.'.format(source))
                if tax and built and gold > 0 and source != self.game.find_char_owner('Tax Collector')['name']: ### Don't collect from yourself...
                    ### This could be problematic if we introduce other things that affect gold...
                    self.queue_message(u'{} takes tax of 1 gold from {}'.format(self.game.find_char_owner('Tax Collector')['name'],source))
                    self.tell_player_gold(self.game.find_char_owner('Tax Collector')['name'])
                    gold -= 1 ### so track the gold through to see if we need to do Poor House
                    should_tell = True
                if char['name'] == 'Alchemist' and built:
                    self.queue_message(u'Alchemist gets a gold refund.')
                    gold += 1
                    should_tell = True
                if 'Poor House' in [d['name'] for d in player['built']] and gold == 0:
                    self.queue_message('{} gets 1 gold for the Poor House.'.format(source))
                    should_tell = True
                if 'Park' in [dn['name'] for dn in player['built']] and dists == 0:
                    self.queue_message('{} picks up 2 cards for the Park.'.format(source))
                    self.tell_player_cards(source)
                if should_tell:
                    self.tell_player_gold(source)
                self.call_character(source,resp_dst,*pargs)
            else:
                self.queue_message(u'Not valid - {}'.format(success),False,resp_dst)
        
    def assassin_sp(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player_name()
        if player == source:
            success = self.game.assassin_sp(source,pargs[0])
            if success is True:
                self.queue_message(u'Assassin has murdered the {}!'.format(self.game.miss_char['name']))
            else:
                self.queue_message(u'Not valid - {}'.format(success),False,resp_dst)
        
    def witch_sp(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player_name()
        if player == source:
            success = self.game.witch_sp(source,pargs[0])
            if success is True:
                self.queue_message(u'Witch has bewitched the {}! Turn must end immediately...'.format(self.game.miss_char['name']))
                self.end_turn(source,resp_dst) ### Force end turn...
            else:
                self.queue_message(u'Not valid - {}'.format(success),False,resp_dst)
        
    def thief_sp(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player_name()
        if player == source:
            success = self.game.thief_sp(source,pargs[0])
            if success is True:
                self.queue_message(u'Thief has stolen from {}!'.format(self.game.thief_char['name']))
            else:
                self.queue_message(u'Not valid - {}'.format(success),False,resp_dst)
        
    def magician_sp_e(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player_name()
        if player == source:
            success = self.game.magician_sp_e(source,pargs[0])
            if success is True:
                self.queue_message(u'Magician exchanges cards with {}.'.format(pargs[0]))
                self.tell_player_cards(source)
                self.tell_player_cards(pargs[0])
            else:
                self.queue_message(u'Not valid - {}'.format(success),False,resp_dst)
        
    def magician_sp_r(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player_name()
        if player == source:
            distnames = [d.strip(', ') for d in pargs[0].split(',') if d.strip(', ')] ###if d.strip(', ').lower() in [ds['name'].lower() for ds in DISTRICTS]] ### If we want name validation?
            success = self.game.magician_sp_r(source,distnames)
            if success is True:
                self.queue_message(u'Magician returned {} cards.'.format(len(distnames)))
                self.queue_message(u'Returned {}'.format(', '.join([self.caps(d) for d in distnames])),False,source)
                self.tell_player_cards(source)
            else:
                self.queue_message(u'Not valid - {}'.format(success),False,resp_dst)
                
    def warlord_sp(self,source='',resp_dst='',*pargs):
        player = self.game.get_action_player_name()
        if player == source:
            success = self.game.warlord_sp(source,pargs[0],pargs[1])
            if success is True:
                self.queue_message(u"Warlord destroys {}'s {}.".format(pargs[0],self.caps(pargs[1])))
                if self.caps(pargs[1]) == 'Bell Tower':
                    self.queue_message(u'The Bell Tower was destroyed! A completed city is back to {} districts.'.format(self.game.max_builds))
                self.end_turn(source,resp_dst,*pargs) ### Must end warlord's turn - doing here, not in citagame
            else:
                self.queue_message(u'Not valid - {}'.format(success),False,resp_dst)
        
    def loop_thread(self):
        while True:
            if self.allow_newgame:
                time.sleep(1)
            else:
                time.sleep(1)
    
    def prevent_newgame(self):
        self.queue_message(u'Closing at the end of this game for a reboot...')
        self.allow_newgame = False
        
    def caps(self,a):
        if isinstance(a,str) or isinstance(a,unicode):
            return ' '.join([s.lower().capitalize() for s in a.split(' ')])
    
                            #
                        #### Must end their turn now - this should be the last thing to happen in this function.
                        #elif card['name'] == 'Witch':
                        #    self.tell_player_gold(source)
                        #    self.queue_message(u'{} has taken their action as the Witch - turn ends immediately.'.format(source))
                        #    self.end_turn(source,resp_dst)
                        #    return
                        #
                        
                        
                    #
                    #### Must end their turn now - this should be the last thing to happen in this function.
                    #if card['name'] == 'Witch':
                    #    self.queue_message(u'{} has taken their action as the Witch - turn ends immediately.'.format(source))
                    #    self.end_turn(source,resp_dst)
                    #    return
                    #
                    
    def ut1(self):
        self.add_player('a')
        self.add_player('b')
        self.add_player('c')
        self.add_player('d')
        self.on_privmsg('a','switch char witch, tax collector')
        self.game.use_dc_districts = [27,28,29,30,31,32,33,34,35,36,37,38,39]
        self.game.max_builds = 12
        self.on_privmsg('a','start')
        self.on_privmsg('a','choose witch')
        self.on_privmsg('a','choose thief')
        self.on_privmsg('a','choose magician')
        self.on_privmsg('b','choose tax collector')
        self.on_privmsg('b','choose king')
        self.on_privmsg('b','choose bishop')
        self.on_privmsg('c','choose king')
        self.on_privmsg('c','choose merchant')
        self.on_privmsg('c','choose architect')
        self.on_privmsg('d','choose architect')
        self.on_privmsg('d','choose warlord')
        #self.game.players[0]['built'].extend(DISTRICTS[33:37])
        for p in self.game.players:
            p['gold'] = 1000
            for i in xrange(5):
                p['built'].append(self.game.pull_district())
                
    def sel_chr(self):
        self.on_privmsg('a','choose {}'.format(random.choice(self.game.characters)['name']))
        self.on_privmsg('b','choose {}'.format(random.choice(self.game.characters)['name']))
        self.on_privmsg('c','choose {}'.format(random.choice(self.game.characters)['name']))
        self.on_privmsg('d','choose {}'.format(random.choice(self.game.characters)['name']))
        self.on_privmsg('a','choose {}'.format(random.choice(self.game.characters)['name']))
        self.on_privmsg('b','choose {}'.format(random.choice(self.game.characters)['name']))
        self.on_privmsg('c','choose {}'.format(random.choice(self.game.characters)['name']))
    
    def act(self):
        self.on_privmsg(self.game.get_action_player_name(),'take gold')
        
    def test_all_dist(self):
        self.add_player('a')
        self.add_player('b')
        self.add_player('c')
        self.add_player('d')

        self.game.max_builds = 12
        self.game.use_dc_districts = [27,28,29,30,31,32,33,34,35,36,37,38,39]
        self.on_privmsg('a','start')
        
        dists = [DISTRICTS[i] for i in xrange(17,40)]
        pc = 0
        while dists:
            dist = dists.pop(0)
            self.game.players[pc]['built'].append(dist)
            pc += 1
            pc %= len(self.game.players)
        self.sel_chr()
        for p in self.game.players:
            p['gold'] = 1000
        self.on_privmsg('a','districts')
        
        
        
    def ut2(self):
        self.add_player('a')
        self.add_player('b')
        self.on_privmsg('a','start')
        self.on_privmsg('a','choose assassin')
        self.on_privmsg('a','choose thief')
        self.on_privmsg('a','choose magician')
        self.on_privmsg('b','choose magician')
        self.on_privmsg('b','choose king')
        self.on_privmsg('b','choose bishop')
        for p in self.game.players:
            for i in xrange(7):
                p['built'].append(self.game.pull_district())
        
    def ut3(self):
        ###Obs/Lib
        self.add_player('a')
        self.add_player('b')
        self.add_player('c')
        self.add_player('d')
        self.on_privmsg('a','start')
        self.on_privmsg('a','choose assassin')
        self.on_privmsg('a','choose thief')
        self.on_privmsg('a','choose magician')
        self.on_privmsg('b','choose magician')
        self.on_privmsg('b','choose king')
        self.on_privmsg('b','choose bishop')
        self.on_privmsg('c','choose bishop')
        self.on_privmsg('c','choose merchant')
        self.on_privmsg('c','choose architect')
        self.on_privmsg('d','choose architect')
        self.on_privmsg('d','choose warlord')
        p = self.game.players[0]
        p['built'].extend(DISTRICTS[17:-2])
        self.on_privmsg('a','take gold')
        #self.on_privmsg('a','end')
        #self.on_privmsg('b','take gold')
        #self.on_privmsg('b','end')
        #self.on_privmsg('c','take gold')
        #self.on_privmsg('c','end')
        #self.on_privmsg('d','take gold')
        
    def ut4(self):
        self.add_player('a')
        self.add_player('b')
        self.add_player('c')
        self.on_privmsg('a','start')
        self.on_privmsg('a','choose assassin')
        self.on_privmsg('a','choose thief')
        self.on_privmsg('a','choose magician')
        self.on_privmsg('b','choose magician')
        self.on_privmsg('b','choose king')
        self.on_privmsg('b','choose bishop')
        self.on_privmsg('c','choose bishop')
        self.on_privmsg('c','choose merchant')
        self.on_privmsg('c','choose architect')
        for p in self.game.players:
            for i in xrange(7):
                p['built'].append(self.game.pull_district())
                
    def ut5(self):
        ### magician exch
        self.add_player('lutomlin')
        self.add_player('ob')
        self.on_privmsg('lutomlin','start')
        self.on_privmsg('lutomlin','choose {}'.format(self.game.characters[0]['name']))
        self.on_privmsg('lutomlin','discard {}'.format(self.game.characters[0]['name']))
        self.on_privmsg('ob','choose {}'.format(self.game.characters[0]['name']))
        self.on_privmsg('ob','discard {}'.format(self.game.characters[0]['name']))
        self.on_privmsg('lutomlin','choose {}'.format(self.game.characters[0]['name']))
        self.on_privmsg('lutomlin','discard {}'.format(self.game.characters[0]['name']))
        self.on_privmsg('ob','choose {}'.format(self.game.characters[0]['name']))
        self.on_privmsg('ob','discard {}'.format(self.game.characters[0]['name']))
        self.on_privmsg('lutomlin','choose {}'.format(self.game.characters[0]['name']))
        self.on_privmsg('lutomlin','discard {}'.format(self.game.characters[0]['name']))
    
    def ut6(self):
        self.on_privmsg('a','extra dist armory, castle, keep, keep ,armory, lighthouse, \
                        armory, qwer, asdf , ,,,  q, ,q q  ,,q , , ,  , university, ball room, factory')
        
def main():
    import sys
    if len(sys.argv) <= 1:
        print "Usage: 'python -i citabot.py <channel> [<nickname> [<server> [<port>]]]'"
        print "bot=self, c=self.connection"
        sys.exit(1)
    bot = CitaBot(*sys.argv[1:])
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()