#!/usr/bin/env python
# -*- coding=utf-8 -*-
from pprint import pprint
import random
import time
import datetime
import threading
from citacards import CitaData
from citacards import CHARACTERS, DISTRICTS, COLOURS, CHAR_NAMES, CHAR_DEFAULTS, CHAR_NUMS, CHAR_SCHEMES

#action stages:
#    0 - take action
#    1 - return card if taken
#    2 - open (i.e. build or use special etc)
#    3 - Warlord building?
#    4 - end-turn (i.e. warlord, alchemist, tax collection)
    
class CitaGame(object):
    DEBUG = 1
    MAX_BUILD = 7 ### Can set a default here
    
    def log(self,msg,level=1):
        if self.DEBUG >= level:
            pprint(msg)
            
    def __init__(self):
        self.CitaData = CitaData()
        self.king_index = 0
        self.game_running = False
        
        self.players = []
        self.char_replacements = []
        self.use_dc_districts = []
        
        self.max_builds = self.MAX_BUILD
        
        self.player_name_list = []
        
        self.characters_match = []
        self.districts = []
        
        self.characters = []
        
        self.init_var()
        
        self.endgame = False
        self.museum_count = 0
        
    def start_game(self):
        self.game_running = True
        self.reset_round()
        
        self.players = [{'name':p,'characters':[],'gold':2,'districts':[],'built':[]} for p in self.player_name_list]
        self.player_name_list = []
        self.districts = self.new_district_deck()
        self.characters_match = self.new_character_deck()
        
        for player in self.players:
            for i in xrange(4):
                player['districts'].append(self.pull_district())
                
        self.king_index = random.randint(0,len(self.players)-1) ################################# Needs some random determination!
        self.action_player = self.king_index
        
    def reset_game(self):
        self.game_running = False
        self.init_var()
       
        self.max_builds = 8
        
        self.players = []
        self.player_name_list = []
        self.characters = []
        self.characters_match = []
        self.districts = []
        
        self.char_replacements = []
        self.use_dc_districts = []
        
        self.endgame = False
        self.museum_count = 0
        
    def reset_round(self):
        self.characters = self.new_character_deck()
        self.init_var()
        
    def init_var(self):
        self.action_player = self.king_index
        self.action_char = 0
        
        for player in self.players:
            player['characters'] = []
            
        self.choose = False
        self.wait_for_discard = False
        self.tax_collect = False
        self.miss_char = None
        self.thief_char = None
        self.init_turn_var()
        
    def init_turn_var(self):
        self.turn_stage = 0
        self.built = False
        self.new_taken_cards = []
        self.used_action = False
            
        self.used_laboratory = False
        self.used_smithy = False
        self.used_observatory = False
        self.used_museum = False
        self.used_hospital = False
        self.allow_lighthouse_select = False
        
    def end_game(self):
        scores = []
        for player in self.players:
            score = 0
            
            ### count costs
            for d in player['built']:
                score += d['cost']
                
            ### count bonuses
            if self.endgame == player:
                score += 4
            elif len(player['built']) >= self.max_builds:
                score += 2
            
            ### count affs
            affs = []
            for d in player['built']: 
                if d['affinity'] != 4 or d['name'] == 'Haunted City':
                    if d['affinity'] not in affs:
                        affs.append(d['affinity'])
            num_aff = len(affs)
            if num_aff >= 4:
                score += 3
            
            ### count specials: University, Dragon Gate, Imperial Treasury, Map Room, Museum, Wishing Well,
            for d in player['built']:
                if d['name'] in ['University','Dragon Gate']:
                    score += 2
                elif d['name'] == 'Imperial Treasury':
                    score += player['gold']
                elif d['name'] == 'Map Room':
                    score += len(player['districts'])
                elif d['name'] == 'Museum':
                    score += self.museum_count
                elif d['name'] == 'Wishing Well':
                    count = len([dn for dn in player['built'] if dn['affinity'] == 4]) - 1
                    score += count
                    
            scores.append((player['name'],score))
        self.reset_game()
        return scores
    
    def start_character_choices(self):
        ### Returns the face-up characters that are not used this round!
        num_players = len(self.players)
        
        self.characters.pop(random.randint(0,len(self.characters)-1))
        
        face_up = []
        
        for i in xrange(CHAR_SCHEMES[num_players]):
            rn = random.randint(0,len(self.characters)-1)
            while self.characters[rn]['number'] == 4:
                self.log('Pulled King/Emperor face-up!',1)
                rn = random.randint(0,len(self.characters)-1)
            char = self.characters.pop(rn)
            self.log('Removed char {}'.format(char['name']))
            face_up.append(char)
            
        self.choose = True
        return face_up
            
    def choose_character(self,player_name,character):
        if self.action_char > 0 or not self.choose:
            return 'Not that stage of the game.'
        player = self.get_action_player()
        if player['name'] != player_name:
            return 'It is not your turn.'
        if self.wait_for_discard:
            return 'Please discard, not choose.'
        if isinstance(character,int):
            check = 'number' ### not using this now - be careful with .lower()s
        elif isinstance(character,str):
            check = 'name'
        elif isinstance(character,unicode):
            check = 'name'
        else:
            print type(character)
            self.log('How did I get here? choose_character {}'.format(character),0)
            return 'Broken in choose_character'
        for char in self.characters:
            if char[check].lower() == character.lower():
                player['characters'].append(char)
                self.characters.remove(char)
                if char['name'] == 'Tax Collector':
                    self.tax_collect = True ### Hax for Assassin/Witch but whatever
                break
        else:
            return '{} is not available.'.format(character)
                
        num_players = len(self.players)
        if num_players == 2 and len(self.characters) != 6:
            self.wait_for_discard = True
        else:
            self.action_player += 1
            self.action_player %= num_players
            
        if len(self.characters) <= 1:
            #if num_players == 7:
            #    pass ### Duuuuude, annoying !!!
            #else:
            ## End choosing
            self.choose = False
            self.wait_for_discard = False
            self.action_char = 1
            while self.get_action_player() is None:
                self.action_char += 1
            self.check_for_new_king()
        return True
                
    def discard_character(self,player_name,character):
        if self.action_char > 0 or not self.choose or not self.wait_for_discard:
            return 'Not that stage of the game.'
        for p in self.players:
            if p['name'] == player_name:
                player = p
                break
        else:
            return 'You are not playing.'
        if isinstance(character,int):
            check = 'number'
        elif isinstance(character,str):
            check = 'name'
        elif isinstance(character,unicode):
            check = 'name'
        else:
            self.log('How did I get here? discard_character {}'.format(character),0)
        for char in self.characters:    
            if char[check].lower() == character.lower():
                self.characters.remove(char)
                break
        else:
            return '{} is not available.'.format(character)
                
        num_players = len(self.players)
        self.wait_for_discard = False
        self.action_player += 1
        self.action_player %= num_players
        return True
    
    def new_character_deck(self):
        deck = self.CitaData.Chars(self.char_replacements)
        return deck
    
    def new_district_deck(self):
        deck = self.CitaData.Dists(self.use_dc_districts)
        return deck
    
    # def pull_character(self):
        # card = self.characters.pop(random.randint(0,len(self.characters)-1))
        # return card
        
    def pull_district(self):
        if self.districts:
            card = self.districts.pop(0)
        else:
            card = random.choice(DISTRICTS[0:17])
        return card
    #
    #def give_player_district(self,player):
    #    dist = self.pull_district()
    #    if dist and player:
    #        player['districts'].append(dist)
    #    else:
    #        self.log('ERROR! DISTRICT DECK EMPTY!',0)
    #    
    def find_new_king(self):
        self.log('find_new_king',2)
        for i,player in enumerate(self.players):
            if 4 in self.char_replacements:
                pass###?!! No.
            else:
                if 4 in player['characters']:
                    return i
    
    def get_action_player(self):
        self.log('get_action_player',2)
        if self.players and self.game_running:
            if self.choose:
                player = self.players[self.action_player]
                return player
            else:
                if self.action_char == 0:
                    return None
                card = self.get_action_card()
                for player in self.players:
                    if card in player['characters']:
                        if card == self.miss_char and self.characters_match[0]['name'] == 'Assassin':
                            self.log('get_action_player matched {} with miss_char and Assassin.'.format(card['name']))
                            return None
                        else:
                            return player
                else:
                    self.log('get_action_player failed to find {}.'.format(card['name']))
                    return None
        else:
            return None
        
    def get_action_player_name(self):
        player = self.get_action_player()
        if player is None:
            return None
        return player['name']
    
    def get_action_card(self):
        card = self.characters_match[self.action_char-1]
        return card

    def get_action_card_name(self):
        card = self.characters_match[self.action_char-1]
        if card:
            return card['name']
        else:
            return None

    def find_char_owner(self,char_name):
        for player in self.players:
            if char_name.lower() in [d['name'].lower() for d in player['characters']]:
                return player
        else:
            return None

    def find_district_owner(self,district_name): ### DON'T USE THIS FUNCTION FOR ANYTHING EXCEPT UNIQUE DISTRICTS
        for player in self.players:
            if district_name.lower() in [d['name'].lower() for d in player['built']]:
                return player
        else:
            return None
        
    def find_player_byname(self,player_name):
        for p in self.players:
            if p['name'] == player_name:
                return p
        else:
            self.log('Looked for missing player {} in find_player_byname'.format(player_name))
            return None
        
    def get_king_player(self):
        self.log('get_king_player',2)
        if self.players and self.game_running:
            player = self.players[self.king_index]
            return player
        else:
            return None
    
    def take_action(self,player_name,act=0):
        if player_name == self.get_action_player_name():
            if not self.choose and self.action_char > 0:
                card = self.get_action_card()
                player = self.get_action_player()
                
                if self.turn_stage == 0:
                    if act == 0:
                        player['gold'] += 2
                        self.post_action()
                        return True
                    
                    elif act == 1:
                        self.new_taken_cards = [self.pull_district(),self.pull_district()]
                        self.turn_stage = 1
                        if 'Observatory' in [d['name'] for d in player['built']]:
                            self.new_taken_cards.append(self.pull_district())
                            self.used_observatory = True
                            if 'Library' in [d['name'] for d in player['built']]:
                                self.used_observatory = False
                        elif 'Library' in [d['name'] for d in player['built']]:
                            self.turn_stage = 2
                        player['districts'].extend(self.new_taken_cards)
                        return True
                    
                elif self.turn_stage > 1 and not self.used_action: ### taking extra gold for districts of their type, or navigator
                    if card['name'] in ['King','Emperor','Bishop','Abbot','Merchant','Warlord','Diplomat'] and act == 0:
                        dist_num = len([d for d in player['built'] if d['affinity'] == card['affinity'] or d['name'] == 'School Of Magic'])
                        player['gold'] += dist_num
                        self.used_action = True
                        return True
                    elif card['name'] == 'Navigator':
                        if act == 0:
                            player['gold'] += 4
                        elif act == 1:
                            self.log('Pulling Navigator cards',2)
                            for i in xrange(4):
                                player['districts'].append(self.pull_district())
                        return True
                else:
                    self.log('Error! Action already taken.')
                    return 'Action already taken.'
            else:
                self.log('Trying to take action out of turn.')
                return 'Trying to take action out of turn.'
        else:
            self.log('Error! Wrong player {}.'.format(player_name))
            return 'Not your turn.'
        
    def return_district(self,player_name,district_name):
        if player_name == self.get_action_player_name():
            if self.turn_stage != 1:
                self.log('Wrong turn stage!')
                return 'Wrong action.'
            else:
                if district_name.lower() in [d['name'].lower() for d in self.new_taken_cards]:
                    for d in self.get_action_player()['districts']:
                        if d['name'].lower() == district_name.lower():
                            district = d
                            break
                    else:
                        self.log('Error! District not found somehow.')
                        return 'Broke something finding district in hand.'
                    
                    self.get_action_player()['districts'].remove(district) ### This needs testing!
                    self.districts.append(district)
                    if self.used_observatory is True:
                        self.used_observatory = False
                    else:
                        self.post_action()
                    return True
                else:
                    return "You didn't pick up that card."
        else:
            self.log('Error! Wrong player {}.'.format(player_name))
            return 'Not your turn.'

    def post_action(self):
        char = self.get_action_card()
        player = self.get_action_player()
        if char == self.miss_char:
            self.log('At do_witch_stuff post_action - moving char before doing post_action.',0)
            player['characters'].remove(char)
            witch_player = self.find_char_owner('Witch')
            witch_player['characters'].append(char)
            char = self.get_action_card()
            player = self.get_action_player()
        if char['name'] == 'Merchant':
            player['gold'] += 1
        if char['name'] == 'Architect':
            player['districts'].append(self.pull_district())
            player['districts'].append(self.pull_district())
        self.turn_stage = 2
    
    def build_district(self,player_name,district_name):
        if player_name == self.get_action_player_name():
            player = self.get_action_player()
            card = self.get_action_card()
            if self.turn_stage != 2:
                return 'Wrong stage of turn. Take your action first.'
            if self.built is True:
                return 'You have already built this turn.'
            if card['name'] in ['Witch','Navigator']:
                return 'The {} cannot build.'.format(card['name'])
            for d in player['districts']:
                if d['name'].lower() == district_name.lower():
                    district = d
                    break
            else:
                district = None
            if district is None:
                return "You don't have the district {}.".format(district_name)
            else:
                ###Check for duplicates, or Wizard, or Quarry
                if card['name'] == 'Wizard':
                    self.log('Allowing duplicate builds for Wizard.')
                elif 'Quarry' in [dn['name'] for dn in player['built']]:
                    count = 0
                    for d in player['built']:
                        if d == district:
                            count += 1
                    if count >= 2:
                        return 'You cannot build more than 1 duplicate with the Quarry.'
                elif district in player['built']:
                    return 'Cannot build duplicate districts.'
                else:
                    self.log('Construction allowed as normal.')
                cost = district['cost']
                if 'Factory' in [dn['name'] for dn in player['built']] and district['affinity'] == 4:
                    cost -= 1
                if player['gold'] < cost: 
                    return "You don't have the gold for this district (requires {}).".format(cost)
                player['built'].append(district) ### Build!
                player['districts'].remove(district)
                player['gold'] -= cost
                if card['name'] == 'Architect': ### Fix here for Architect - can set built = False/1/2/True?
                    self.log('Architect!')
                    if self.built == False: self.built = 1
                    elif self.built == 1: self.built = 2
                    elif self.built == 2: self.built = True
                    self.log('{}'.format(self.built))
                else:
                    self.built = True
                
                ### Special effects on build here
                if district['name'] == 'Lighthouse':
                    self.allow_lighthouse_select = True
                if district['name'] == 'Bell Tower':
                    self.max_builds -= 1
                if len(player['built']) >= self.max_builds and not self.endgame:
                    self.endgame = player
                return True
        else:
            self.log('Error! Wrong player {}.'.format(player_name))
            return 'Not your turn.'

    def end_turn(self):
        # deal with end turn? warlord, alchemist, tax collection
        ### Better way: allow warlord to destroy any time in 2, but force end turn when you do
        char = self.get_action_card()
        player = self.get_action_player()
        if self.turn_stage < 2:
            return 'You must take your action first.'
        
        if self.tax_collect: ### I think we can just hack this for Assassin/Witch...
            if self.built:
                self.log('Should collect Tax...')
                for p in self.players:
                    if 'Tax Collector' in [c['name'] for c in p['characters']]:
                        player2 = p
                        break
                else:
                    self.log('ARGH end_turn tax collection',0)
                    return 'Tax Collector not found?!'
                if player['gold'] >= 1:
                    player['gold'] -= 1
                    player2['gold'] += 1
                    self.log('Player {} collected tax from {}.'.format(player2['name'],player['name']))
                else:   
                    self.log('Player {} not collecting tax from {}: {} gold.'.format(player2['name'],player['name'],player['gold']))
                        
        if self.get_action_card()['name'] == 'Alchemist':
            if self.built:
                cost = self.get_action_player()['districts'][-1]['cost']
                player['gold'] += cost
                
        if 'Poor House' in [dn['name'] for dn in player['built']] and player['gold'] == 0:
            player['gold'] += 1
            self.log('Giving 1 gold to {} for the Poor House'.format(player['name']))
                     
        if 'Park' in [dn['name'] for dn in player['built']] and len(player['districts']) == 0:
            self.log('Giving 2 cards to {} for the Park'.format(player['name'])) ### Problem here is that the deck can run out...
            player['districts'].append(self.pull_district())
            player['districts'].append(self.pull_district())
                     
        self.turn_stage = 4 ### ?
        self.log('Advancing turn.')
        self.advance_char()
        return True
        pass
    
    def advance_char(self):
        if self.action_char >= 8:
            if self.miss_char:
                king_murdered = (self.miss_char['name'] == 'King')
                if king_murdered:
                    crown = self.find_char_owner('King')
                    for i,p in enumerate(self.players):
                        if p == crown:
                            self.king_index = i
                            self.log('New king index {}'.format(self.king_index))
                            break
                    else:
                        self.log('Finding new King broke 8+ - {}'.format(crown))
            if self.endgame:
                self.reset_round()
            else:    
                self.reset_round()
        else:
            self.action_char += 1
            self.init_turn_var()
            if self.get_action_player() is None: ### Check if we are done advancing
                self.advance_char()
            else:
                ### Do start of the next turn stuff
                self.check_for_new_king()
                self.check_thief_steal()
                
    def check_thief_steal(self):
        player = self.get_action_player()
        char = self.get_action_card()
        if char == self.thief_char:
            thief_player = self.find_char_owner('Thief')
            if thief_player is None:
                self.log('Broke finding Thief!',0)
            else:
                thief_player['gold'] += player['gold']
                player['gold'] -= player['gold']
        
    def check_for_new_king(self):
        king = self.find_char_owner('King')
        player = self.get_action_player()
        char = self.get_action_card()
        if king == player:
            if char['name'] == 'King':
                #self.log(king)
                #self.log(player)
                for i,p in enumerate(self.players):
                    if p == king:
                        if self.king_index == i:
                            self.log('King index will not change')
                            return
                        else:
                            self.king_index = i
                            self.log('New king index {}'.format(self.king_index))
                            p2 = self.find_district_owner('Throne Room')
                            if p2:
                                self.log('Giving 1 gold to {} for Throne Room'.format(p2['name']))
                                p2['gold'] += 1
                            return
                else:
                    self.log('Finding new King broke - {}'.format(king))
            else:
                self.log("King player matched but char didn't!")
    
    def use_district(self,dist_name,player_name,my,target):
        dist_name = self.caps(dist_name)
        target = self.caps(target)
        player = self.get_action_player()
        char = self.get_action_card()
        
        if self.turn_stage != 2:
            return 'Take your action first.'
        
        if not dist_name in [d['name'] for d in player['built']]:
            return "You have not built a {}.".format(dist_name)
        
        if dist_name == 'Laboratory':
            if self.used_laboratory:
                return 'You have already used the Laboratory this turn.'
            if player_name:
                return 'Needs a proper target.'
            if target is None:
                return 'You must declare a district card to return.'
            for d in player['districts']:
                if d['name'] == target:
                    dist = d
                    break
            else:
                return "District card {} not found.".format(target)
            if dist:
                player['districts'].remove(dist)
                player['gold'] += 1
                self.used_laboratory = True
                return True
                
        elif dist_name == 'Smithy':
            if self.used_smithy:
                return 'You have already used the Smithy this turn.'
            if my or player_name:
                return 'Smithy doesn\'t need a target.'
            if player['gold'] < 2:
                return "You don't have enough gold (requires 2)."
            player['gold'] -= 2
            for i in xrange(3):
                player['districts'].append(self.pull_district())
            self.used_smithy = True
            return True
        
        elif dist_name == 'Armory':
            if not my and not player_name:
                return 'Needs a proper target.'
            if target is None:
                return 'You must declare a district card to destroy.'
            if my:
                plr = player
            else:
                for p in self.players:
                    if p['name'] == player_name:
                        plr = p
                        break
                else:
                    return '{} is not playing.'.format(player_name)
            for d in plr['built']:
                if d['name'] == target:
                    dist = d
                    break
            else:
                if player_name:
                    return "{} does not have a {}.".format(player_name,target)
                elif my:
                    return "You do not have a {}.".format(target)
                else:
                    return 'How did I get here? use_district Armory, no player/my'
            plr['built'].remove(dist)
            player['built'].remove(DISTRICTS[28])
            if dist['name'] == 'Bell Tower':
                self.log('Bell tower destroyed by Armory, increasing max_builds')
                self.max_builds += 1
            return True
        
        elif dist_name == 'Museum':
            if self.used_museum:
                return 'You have already used the Museum this turn.'
            if player_name:
                return 'Needs a proper target.'
            if target is None:
                return 'You must declare a district card to place.'
            for d in player['districts']:
                if d['name'] == target:
                    dist = d
                    break
            else:
                return "District card {} not found.".format(target)
            if dist:
                player['districts'].remove(dist)
                self.museum_count += 1
                self.used_museum = True
                return True
            
        elif dist_name == 'Lighthouse':
            if not self.allow_lighthouse_select:
                return 'You cannot use the Lighthouse\'s power.'
            if target is None:
                return 'You must declare a district card to take.'
            if player_name or my:
                return 'Needs a proper target.'
            for d in self.districts:
                if d['name'] == target:
                    dist = d
                    break
            else:
                return 'District card {} not found.'.format(target)
            self.districts.remove(dist)
            player['districts'].append(dist)
            random.shuffle(self.districts)
            self.allow_lighthouse_select = False
            return True
            
    def assassin_sp(self,player_name,target):
        char = self.get_action_card()
        player = self.get_action_player_name()
        if char['name'] == 'Assassin' and player_name == player:
            if 1 < self.turn_stage < 4:
                if self.used_action:
                    return 'You have already used your special ability this turn.'
                target = self.caps(target)
                if target == 'Assassin':
                    return 'Cannot murder yourself.'
                if target not in [c['name'] for c in self.characters_match]:
                    return '{} is not used this game.'.format(target)
                self.miss_char = self.characters_match[CHAR_NUMS[target]-1]
                self.used_action = True
                return True
            else:
                return 'Wrong stage of your turn. After action, and before ending.'
        else:
            return 'You are not the Assassin.'
            
    def witch_sp(self,player_name,target):
        char = self.get_action_card()
        player = self.get_action_player_name()
        if char['name'] == 'Witch' and player_name == player:
            if 1 < self.turn_stage < 4:
                target = self.caps(target)
                if target == 'Witch':
                    return 'Cannot bewitch yourself.'
                if target not in [c['name'] for c in self.characters_match]:
                    return '{} is not used this game.'.format(target)
                self.miss_char = self.characters_match[CHAR_NUMS[target]-1]
                self.used_action = True
                return True
            else:
                return 'Wrong stage of your turn. After action, and before ending.'
        else:
            return 'You are not the Witch.'
            
    def thief_sp(self,player_name,target):
        char = self.get_action_card()
        player = self.get_action_player_name()
        if char['name'] == 'Thief' and player_name == player:
            if 1 < self.turn_stage < 4:
                if self.used_action:
                    return 'You have already used your special ability this turn.'
                target = self.caps(target)
                if target in ['Assassin','Witch']:
                    return 'Cannot steal from Assassin/Witch.'
                if target == 'Thief':
                    return 'Cannot steal from yourself.'
                if target not in [c['name'] for c in self.characters_match]:
                    return '{} is not used this game.'.format(target)
                self.thief_char = self.characters_match[CHAR_NUMS[target]-1]
                self.used_action = True
                return True
            else:
                return 'Wrong stage of your turn. After action, and before ending.'
        else:
            return 'You are not the Thief.'
    
    def magician_sp_e(self,player_name,exc_player):
        if exc_player == player_name:
            return 'Cannot exchange with yourself.'
        char = self.get_action_card()
        player = self.get_action_player()
        if char['name'] == 'Magician' and player_name == player['name']:
            if 1 < self.turn_stage < 4:
                if self.used_action:
                    return 'You have already used your special ability this turn.'
                for p in self.players:
                    if p['name'] == exc_player:
                        p2 = p
                        break
                else:
                    return 'Player {} not found?! magician_sp_e'.format(exc_player)
                card_tr = [c for c in p2['districts']]
                self.log('exchanging hands')
                p2['districts'] = [c for c in player['districts']]
                player['districts'] = [c for c in card_tr]
                self.log('finished exchange')
                self.used_action = True
                return True
            else:
                return 'Wrong stage of your turn. After action, and before ending.'
        else:
            return 'You are not the Magician.'
        
    def magician_sp_r(self,player_name,distnames):
        char = self.get_action_card()
        player = self.get_action_player()
        if char['name'] == 'Magician' and player_name == player['name']:
            if 1 < self.turn_stage < 4:
                if self.used_action:
                    return 'You have already used your special ability this turn.'
                for d in distnames:
                    if d.lower() not in [dn['name'].lower() for dn in DISTRICTS]:
                        return 'District "{}" not found.'.format(d)
                    elif d.lower() not in [dn['name'].lower() for dn in player['districts']]:
                        return '''You don't have district "{}".'''.format(d)
                for d in distnames:
                    for dn in player['districts']:
                        if dn['name'].lower() == d.lower():
                            player['districts'].remove(dn)
                            self.districts.append(dn)
                            player['districts'].append(self.pull_district())
                            break
                    else:
                        self.log('Problem! Missed card in hand in magician_sp_r.')
                self.used_action = True
                return True
            else:
                return 'Wrong stage of your turn. After action, and before ending.'
        else:
            return 'You are not the Magician.'
    
    def warlord_sp(self,player_name,player_target,dist_target):
        char = self.get_action_card()
        player = self.get_action_player_name()
        if char['name'] == 'Warlord' and player_name == player:
            if 1 < self.turn_stage < 4:
                dist_target = self.caps(dist_target)
                p = self.find_player_byname(player_target)
                if not p:
                    return '{} is not playing.'.format(player_target)
                if p == self.find_char_owner('Bishop'):
                    return 'Cannot destroy districts belonging to the Bishop.'
                if len(p['built']) >= self.max_builds:
                    return 'Cannot destroy buildings in a completed City ({} or more districts).'.format(self.max_builds)
                if dist_target == 'Keep':
                    return 'Cannot destroy a Keep.'
                for d in p['built']:
                    if d['name'] == dist_target:
                        pl = self.get_action_player()
                        cost = d['cost'] - 1 + (1 if 'Great Wall' in [dn['name'] for dn in p['built']] else 0)
                        if pl['gold'] >= cost:
                            pl['gold'] -= cost
                            p['built'].remove(d)
                            if dist_target == 'Bell Tower':
                                self.log('Bell tower destroyed by Warlord, increasing max_builds')
                                self.max_builds += 1
                            return True
                        else:
                            return "You don't have enough gold (needs {}) to destroy that target.".format(cost)
                else:
                    return "That player doesn't have a {}".format(dist_target)
            else:
                return 'Wrong stage of your turn. Must be after action, and will end your turn.'
        else:
            return 'You are not the Warlord.'
    
        
    def caps(self,a):
        if isinstance(a,str) or isinstance(a,unicode):
            return ' '.join([s.lower().capitalize() for s in a.split(' ')])
    
if __name__ == '__main__':
    game = CitaGame()