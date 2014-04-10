import random

AFFINITY = ['Noble',
            'Religious',
            'Trade',
            'Military',
            'Special',]

COLOURS = {'yellow':'Noble',
           'blue':'Religious',
           'green':'Trade',
           'red':'Military',
           'purple':'Special',}

CHARACTERS = [{'name':'Assassin',
               'number':1,
               'affinity':None,
               'text':['''Announce the title of another character that you wish to murder. ("murder [name]")''',
                       '''The player who has the murdered character must say nothing, and must remain silent when the murdered character is called upon to take his turn.''',
                       '''The murdered character misses his entire turn.''']},
              {'name':'Witch',
               'number':1,
               'affinity':None,
               'text':['''After you take an action, you must announce the title of another character that you wish to bewitch ("bewitch [name]"),''',
                       '''then immediately end your turn. When the bewitched character is called upon,''',
                       '''its player must show his character card, take an action, and then immediately end his turn.''',
                       '''You now resume this player's turn as if you were playing the bewitched character, using''',
                       '''all that character's powers (including the gold bonus of the Merchant or the''',
                       '''two card bonus of the Architect) in your city.''',
                       '''If the King is bewitched, the King player still receives the Crown counter.''',
                       '''If the bewitched character is not in play, you do not resume your turn.''',
                       '''The Thief cannot steal from the Witch or the bewitched character.''']},
              {'name':'Thief',
               'number':2,
               'affinity':None,
               'text':['''Announce the title of a character from whom you wish to steal. ("steal from [name]")''',
                        '''When the player who has that character is called upon to take his turn,''',
                        '''you first take all of his gold. You may not steal from the Assassin or the Assassin's target.''']},
              {'name':'Tax Collector',
               'number':2,
               'affinity':None,
               'text':['''After another player has built one or more districts in his city, that player must,''',
                       '''at the end of his turn, give you one gold (if he has any gold left).''',
                       '''If the Assassin has already built a district card,''',
                       '''their players must pay you one gold as you reveal that you have the Tax Collector.''']},
              {'name':'Magician',
               'number':3,
               'affinity':None,
               'text':['''At any time during your turn, you may do one of the following two things:''',
                       '''- "exchange with [name]": Exchange your entire hand of cards (not the cards in your city) with the hand of another player.''',
                       '''  This applies even if you have no cards in your hand, in which case you simply take the other player's cards).''',
                       '''- "replace [name], [name], ...": Place any number of cards from your hand facedown at the bottom of the District Deck,''',
                       '''  then draw an equal number of cards from the top of the District Deck.''',
                       '''  Use private messages for this.''']},
              {'name':'Wizard',
               'number':3,
               'affinity':None,
               'text':['''You may look at another player's hand of cards and take one card.''',
                       '''You may then either put this card into your hand, or pay to build it in your city.''',
                       '''If you build it in your city, it does not count towards the one district building limit,''',
                       '''which means you can build another district as well.''',
                       '''During this turn, you may build district cards identical to another district already in your city.''']},
              {'name':'King',
               'number':4,
               'affinity':0,
               'text':['''You receive one gold for each noble (yellow) district in your city.''',
                       '''When the King is called, you immediately receive the Crown.''',
                       '''You will be the first player to choose your character during the next round.''',
                       '''If there is no King during the next round, you keep the Crown.''',
                       '''If you are murdered, you skip your turn like any other character.''',
                       '''Nevertheless, after the last player has played his turn, when it becomes known''',
                       '''that you had the murdered King's character card, you take the Crown (as the king's heir).''']},
              {'name':'Emperor',
               'number':4,
               'affinity':0,
               'text':['''You receive one gold for each noble (yellow) district in your city.''',
                       '''When the Emperor is called, you must take the Crown from''',
                       '''the player who has it and give it to a different player (but not yourself).''',
                       '''The player who receives the Crown  must give you either one gold or one district card from his hand.''',
                       '''If the player has neither a gold nor a card, he does not have to give you anything.''',
                       '''(Note that, like the King, the Emperor may not be in the faceup discarded character cards.)''']},
              {'name':'Bishop',
               'number':5,
               'affinity':1,
               'text':['''You receive one gold for each religious (blue) district in your city.''',
                       '''Your districts may not be destroyed by the Warlord.''']},
              {'name':'Abbot',
               'number':5,
               'affinity':1,
               'text':['''You receive one gold for each religious (blue) district in your city.''',
                       '''The player who has the most gold must give you one gold.''',
                       '''If there is a tie for the player with the most gold, or if you have the most gold, then you do not receive the gold.''']},
              {'name':'Merchant',
               'number':6,
               'affinity':2,
               'text':['''You receive one gold for each trade (green) district in your city.''',
                       '''After you take an action, you receive one additional gold.''']},
              {'name':'Alchemist',
               'number':6,
               'affinity':None,
               'text':['''At the end of your turn, you receive back all the gold you spent to build district''',
                       '''cards this turn, but not the gold you spent for other reasons (paying the Tax Collector, for example).''',
                       '''You cannot spend more gold than you have during your turn.''']},
              {'name':'Architect',
               'number':7,
               'affinity':None,
               'text':['''After you take an action, you draw two additional district cards and put both in your hand.''',
                       '''You may build up to three districts during your turn.''']},
              {'name':'Navigator',
               'number':7,
               'affinity':None,
               'text':['''After taking your action, you may either receive an additional four gold or draw an additional four cards.''',
                       '''You may not build any district cards.''']},
              {'name':'Warlord',
               'number':8,
               'affinity':3,
               'text':['''You receive one gold for each military (red) district in your city.''',
                       '''At the end of your turn, you may destroy one district of your choice by paying''',
                       '''a number of gold equal to one less than the cost of the district.''',
                       '''Thus, you may destroy a cost 1 district for free, a cost 2 district for 1 gold,''',
                       '''or a cost 5 district for 4 gold, etc. You may destroy one of your own districts.''',
                       '''You may not, however, destroy a district in a city that is already completed by having eight districts.''']},
              {'name':'Diplomat',
               'number':8,
               'affinity':3,
               'text':['''You receive one gold for each military (red) district in your city.''',
                       '''At the end of your turn, you may take a district from another player's city in exchange''',
                       '''for a district in your city.''',
                       '''If the district you take has a higher cost than the district you give, you must pay the''',
                       '''difference in gold to the player with whom you make the exchange.''',
                       '''The Great Wall affects this cost. You may not take the Keep district, or any districts in the Bishop's city.''',]},
              {'name':'Artist',
               'number':9,
               'affinity':None,
               'text':['']},
              {'name':'Queen',
               'number':9,
               'affinity':None,
               'text':['']},
              ]

DISTRICTS = [{'affinity': 0, 'cost': 3, 'name': 'Manor', 'text':'', 'quantity':5},
             {'affinity': 0, 'cost': 4, 'name': 'Castle', 'text': '', 'quantity':4},
             {'affinity': 0, 'cost': 5, 'name': 'Palace', 'text': '', 'quantity':3},
             {'affinity': 1, 'cost': 1, 'name': 'Temple', 'text': '', 'quantity':3},
             {'affinity': 1, 'cost': 2, 'name': 'Church', 'text': '', 'quantity':3},
             {'affinity': 1, 'cost': 3, 'name': 'Monastery', 'text': '', 'quantity':3},
             {'affinity': 1, 'cost': 5, 'name': 'Cathedral', 'text': '', 'quantity':2},
             {'affinity': 2, 'cost': 1, 'name': 'Tavern', 'text': '', 'quantity':5},
             {'affinity': 2, 'cost': 2, 'name': 'Market', 'text': '', 'quantity':4},
             {'affinity': 2, 'cost': 2, 'name': 'Trading Post', 'text': '', 'quantity':3},
             {'affinity': 2, 'cost': 3, 'name': 'Docks', 'text': '', 'quantity':3},
             {'affinity': 2, 'cost': 4, 'name': 'Harbor', 'text': '', 'quantity':3},
             {'affinity': 2, 'cost': 5, 'name': 'Town Hall', 'text': '', 'quantity':2},
             {'affinity': 3, 'cost': 1, 'name': 'Watchtower', 'text': '', 'quantity':3},
             {'affinity': 3, 'cost': 2, 'name': 'Prison', 'text': '', 'quantity':3},
             {'affinity': 3, 'cost': 3, 'name': 'Battlefield', 'text': '', 'quantity':3},
             {'affinity': 3, 'cost': 5, 'name': 'Fortress', 'text': '', 'quantity':2}, ## 16
             
             ### Specials
             ### HC 17
             {"affinity": 4, "cost": 2, "name": "Haunted City", "text": ["For the purposes of victory points, the Haunted City is conisdered to be of the type of your choice."], "quantity":1},
             {"affinity": 4, "cost": 3, "name": "Keep", "text": ["The Keep cannot be destroyed by the Warlord."], "quantity":2},
             {"affinity": 4, "cost": 5, "name": "Laboratory", "text": ["Once during your turn, you may discard a district card from your hand and receive one gold from the bank."], "quantity":1},
             {"affinity": 4, "cost": 5, "name": "Smithy", "text": ["Once during your turn, you may pay two gold to draw 3 district cards."], "quantity":1},
             {"affinity": 4, "cost": 5, "name": "Observatory", "text": ["If you choose to draw cards when you take an action, you draw 3 cards, keep one of your choice, and put the other 2 on the bottom of the deck."], "quantity":1},
             {"affinity": 4, "cost": 6, "name": "Dragon Gate", "text": ["This district costs 6 gold to build, but is worth 8 points at the end of the game."], "quantity":1},
             {"affinity": 4, "cost": 6, "name": "University", "text": ["This district costs 6 gold to build, but is worth 8 points at the end of the game."], "quantity":1},
             {"affinity": 4, "cost": 6, "name": "Library", "text": ["If you choose to draw cards when you take an action, you keep both of the cards you have drawn."], "quantity":1},
             {"affinity": 4, "cost": 6, "name": "Great Wall", "text": ["The cost for the Warlord to destroy any of your other districts is increased by one gold."], "quantity":1},
             {"affinity": 4, "cost": 6, "name": "School Of Magic", "text": ["For the purposes of income, the School Of Magic is considered to be the type of your choice.",
                                                                            "If you are the King this round, for example, the School is considered to be a Noble district."], "quantity":1},
             ### SoM 26
             
             ### Expansion
             ### LH 27
             {"affinity": 4, "cost": 3, "name": "Lighthouse", "text": ["When you place the Lighthouse in your city, you may look through the District Deck, choose one card and add it to your hand.",
                                                                       "Shuffle the deck afterwards."], "quantity":1},
             {"affinity": 4, "cost": 3, "name": "Armory", "text": ["During your turn, you may destroy the Armory in order to destroy any other district card of your choice in another player's city."], "quantity":1},
             {"affinity": 4, "cost": 4, "name": "Museum", "text": ["On your turn, you may place one district card from your hand face down under the Museum.",
                                                                   "At the end of the game, you score one extra point for every card under the Museum."], "quantity":1},
             {"affinity": 4, "cost": 4, "name": "Imperial Treasury", "text": ["At the end of the game, you score one point for each gold in your possession.",
                                                                              "Gold placed on your district cards do not count towards this total."], "quantity":1},
             {"affinity": 4, "cost": 5, "name": "Map Room", "text": ["At the end of the game, you score one point for each card in your hand."], "quantity":1},
             {"affinity": 4, "cost": 5, "name": "Wishing Well", "text": ["At the end of the game, you score one point for every OTHER purple district in your city."], "quantity":1},
             {"affinity": 4, "cost": 5, "name": "Quarry", "text": ["When building, you may play a district already found in your city.",
                                                                   "You may only have one such duplicate district in your city at any one time."], "quantity":1},
             {"affinity": 4, "cost": 5, "name": "Poor House", "text": ["If you have no gold at the end of your turn, receive one gold from the bank.",
                                                                       "Gold placed on your district cards does not count as your gold for this purpose."], "quantity":1},
             {"affinity": 4, "cost": 5, "name": "Bell Tower", "text": ["When you place the Bell Tower in your city, a city will be complete one district earlier.",
                                                                       "This will happen even if the Bell Tower is your last district.  If the Bell Tower is later destroyed, the game end conditions return to normal."], "quantity":1},
             {"affinity": 4, "cost": 6, "name": "Factory", "text": ["Your cost for building OTHER purple district cards is reduced by one.",
                                                                    "This does not affect the Warlord's cost for destroying the card."], "quantity":1},
             {"affinity": 4, "cost": 6, "name": "Park", "text": ["If you have no cards in your hand at the end of your turn, you may draw 2 cards from the District Deck."], "quantity":1},
             {"affinity": 4, "cost": 6, "name": "Hospital", "text": ["Even if you are assassinated, you may take an action during your turn (but you may not build a district card or use your character's power)."], "quantity":1},
             {"affinity": 4, "cost": 6, "name": "Throne Room", "text": ["Every time the Crown switches players, you receive one gold from the bank."], "quantity":1},
             ### TR 39
             
             ### Unused
             {"affinity": 4, "cost": 5, "name": "Graveyard", "text": ["When the Warlord destroys a district, you may pay one gold to take the destroyed district into your hand.",
                                                                      "You may not do this if you are the Warlord."], "quantity":1},
             {"affinity": 4, "cost": 6, "name": "Ball Room", "text": ["When you have the Crown, all other players must say \"Thanks, your Excellency\" after you have called his character.",
                                                                      "If a player forgets to address you in this way, he loses the turn."], "quantity":1},
            ]

CHAR_NAMES = [c['name'] for c in CHARACTERS]
CHAR_DEFAULTS = [c['name'] for c in [CHARACTERS[i*2] for i in xrange(8)]]
CHAR_NUMS = {c['name']:c['number'] for c in CHARACTERS}

CHAR_SCHEMES = [None,None,0,0,2,1,0,0,]

class CitaData(object):
    def Chars(self,replace_chars):
        cards = [CHARACTERS[i*2] for i in xrange(8)]
        for c in replace_chars:
            if c not in [card['name'] for card in cards]:
                new_char = self.find_char(c)
                cards.pop(new_char['number']-1)
                cards.insert(new_char['number']-1,new_char) ### Test this
        print 'chars: {}'.format([c['name'] for c in cards])
        return cards
    
    def Dists(self,use_dc,shuffle=True):
        cards = []
        for dist in DISTRICTS[:27]:
            for i in xrange(dist['quantity']):
                cards.append(dist)
        for dist_num in use_dc:
            dist = DISTRICTS[dist_num]
            for i in xrange(dist['quantity']):
                cards.append(dist)
        if shuffle: random.shuffle(cards)
        return cards
        
    def find_char(self,char_num):
        for c in CHARACTERS:
            if c['number'] == char_num and c['name'] not in CHAR_DEFAULTS:
                return c
            
    char_names = []
    
    