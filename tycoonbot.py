#!/usr/bin/env python
# -*- coding=utf-8 -*-
from lalbot import LalBot
from pprint import pprint
from copy import deepcopy
import time
import datetime
import threading
import re

class TyBot(LalBot):
    
    versionstr = 'v0.1'
    
    helpfile = [u'''Tycoon {}'''.format(versionstr),
                ]
    
    REQUIRE_PREFIX = False
    
    _property_types = {'brown':{'house':50,
                               'num':2,
                               'names':{}},
                      'light blue':{'house':50,
                               'num':3,
                               'names':{}},
                      'pink':{'house':100,
                               'num':3,
                               'names':{}},
                      'orange':{'house':100,
                               'num':3,
                               'names':{}},
                      'red':{'house':150,
                               'num':3,
                               'names':{}},
                      'yellow':{'house':150,
                               'num':3,
                               'names':{}},
                      'green':{'house':200,
                               'num':3,
                               'names':{}},
                      'dark blue':{'house':200,
                               'num':2,
                               'names':{}},
                      'stations':{'house':50,
                               'num':4,
                               'names':{}},
                      'schools':{'house':50, ### Srsly...
                               'num':4,
                               'names':{}},
                      'utilities':{'house':20,
                               'num':2,
                               'names':{}},
                      'shopping centres':{'house':20, ### Srsly...
                               'num':2,
                               'names':{}},
                        }

    currency = u'\\xa3'
    botname = u'tycoonb'
    
    def disable(self):
        self.commandlist = {'help':self._help,
                            'version':self._version,
                            'echo (.+)':self._echo,}
        self.compile_commands()
        
    def setup(self):
        self.game_running = False
        self.num_plr = 1
        self.trade_re_string = ''
        
        self.saw_new_game = False
        
        self.set_var()
        
        plr_string = '[a-zA-Z_]+'
        prop_name_string = '[A-Z][a-zA-Z \']+'
        group_string = '[a-z ]+'
        
        new_commands = {u'{}: help'.format(self.botname):self._help,
                        u'{}: version'.format(self.botname):self._version,
                        u'{}: echo (.+)'.format(self.botname):self._echo,
                        u'{}: m-echo (.+)'.format(self.botname):self._m_echo,
                        u'{}: shut up'.format(self.botname):self._empty_list,
                        
                        u'{}: play monopoly'.format(self.botname):self.new_game,
                        u'{}: leave'.format(self.botname):self.leave_game,
                        
                        u'setting up game':self.saw_newgame,
                        u'monopoly: join':self.join_plr,
                        u'monopoly: leave':self.leave_plr,
                        
                        #u'It is [a-zA-Z_]+\'s turn: waiting for roll':self.request_plr,
                        
                        u'It is ([a-zA-Z_]+)\'s turn: waiting for roll':self.game_run,
                        u'[a-zA-Z_]+: Balances: (.+)':self.update_plr,
                        u'([a-zA-Z_]+) wins!':self.game_end,
                        
                        #u'{}(.+)':self._echo,
                        u'.+(?:,|:) ([A-Z][a-zA-Z \']+) \(([a-z ]+)\)()':self.catch_type,
                        u'.+like to buy ([A-Z][a-zA-Z \']+) \(part of the \"([a-z ]+)\" set\)?.+{}(\d+)'.format(self.currency):self.catch_type,
                        u'[a-zA-Z_]+: ([A-Z][a-zA-Z \']+) is now mortgaged':self.catch_mortgage,
                        u'([A-Z][a-zA-Z \']+) \(mortgaged\) \(([a-z ]+)\)':self.catch_mortgage,
                        u'[a-zA-Z_]+: ([A-Z][a-zA-Z \']+) is now unmortgaged':self.catch_unmortgage, ### !!! NEEDS CHECKING
                        
                        #tycoon: Whitehall is now mortgaged
                        u'{}: Balance is now {}(\d+)'.format(self.botname,self.currency):self.set_money,
                        
                        u'{}: Property bought.'.format(self.botname):self.win_auction,
                        u'[a-zA-Z_]+: Property bought.'.format(self.botname):self.lose_auction,
                        
                        u'{}: You own (.+)'.format(self.botname):self.update_property,
                        u'{} owns (.+)'.format(self.botname):self.update_property,
                        u'{0}: {0} owns (.+)'.format(self.botname):self.update_property,
                        
                        u'[a-zA-Z_]+: ([A-Z][a-zA-Z \']+) now has (\d houses|a hotel)':self.update_houses_simple,
                        u'[a-zA-Z_]+: ([A-Z][a-zA-Z \']+) has (\d houses|a hotel); ([A-Z][a-zA-Z \']+) has (\d houses|a hotel)(?:; ([A-Z][a-zA-Z \']+) has (\d houses|a hotel)) \(([a-z ]+) set\)':self.update_houses,
                        
                        u'{}: Would you like to buy ([A-Z][a-zA-Z \']+) \(part of the \"(.+)\" set\)?.+{}(\d+)'.format(self.botname,self.currency):self.buy_property,
                        
                        u'Face value for (.+) is {}(\d+)'.format(self.currency):self.start_auction,
                        u'([a-zA-Z_]+) bids {}(\d+)'.format(self.currency):self.bid_in_auction,
                        u'(Opening) the bidding at {}(\d+)'.format(self.currency):self.bid_in_auction,
                        
                        u'{}: .+not autorolling wh'.format(self.botname):self.roll_jail,
                        
                        u'[a-zA-Z_]+: error: {}: You don\'t have enough money to pay {}(\d+)'.format(self.botname,self.currency):self.pay_debt,
                        u'([a-zA-Z_]+) is offering (.+) in return for ({}) giving (.+)'.format(self.botname):self.respond_trade,
                        
                        u'''.+ to take the Chance''':self.fine_chance,
                        u'{}: You might want to buy houses. Say "monopoly: done" to end your go.'.format(self.botname):self.done_turn,
                        }
        
        self.commandlist = new_commands
        
    def set_var(self):
        self.property = {}
        ### {'orange':['Vine Street']}
        #self.houses = {}
        #### {'orange':{'Vine Street':1},'red':{}}
        self.property_types = deepcopy(self._property_types)
        self.money = 1500
        self.auction_property = None
    
    ### -------------------------------------------------------------------
    ### Joining, leaving
    ### -------------------------------------------------------------------
    
    def saw_newgame(self,source='',resp_dst='',*pargs):
        if source == 'monopoly':
            self.saw_new_game = True ### Can try not doing this?
            pass
            
    def new_game(self,source='',resp_dst='',*pargs):
        if not self.game_running:
            self.set_var()
            self.queue_message(u'monopoly: join',True)
        else:
            self.queue_message(u'Thanks, {}.'.format(source))
    
    def leave_game(self,source='',resp_dst='',*pargs):
        if not self.game_running:
            self.queue_message(u'monopoly: leave',True)
        else:
            self.queue_message(u'No!')
    
    def join_plr(self,source='',resp_dst='',*pargs):
        if not self.game_running:
            self.num_plr += 1
            self.log('num_plr {}'.format(self.num_plr))
            
    def leave_plr(self,source='',resp_dst='',*pargs):
        if not self.game_running:
            self.num_plr -= 1
            self.log('num_plr {}'.format(self.num_plr))
    
    def update_plr(self,source='',resp_dst='',*pargs):
        plr_list = pargs[0].split(', ')
        self.num_plr = len(plr_list)
        self.saw_new_game = True
        self.log('saw Balances {}'.format(plr_list))
        self.log('updated num_plr {}'.format(self.num_plr))
        
    def game_run(self,source='',resp_dst='',*pargs):
        if source == 'monopoly':
            self.game_running = True
            if self.saw_new_game == False:
                self.queue_message('monopoly: balances',True,'monopoly')
            if pargs[0] == self.botname:
                self.queue_message('monopoly: roll')
    
    def game_end(self,source='',resp_dst='',*pargs):
        if source == 'monopoly':
            self.game_running = False
    
    def fine_chance(self,source='',resp_dst='',*pargs):
        self.queue_message('monopoly: take chance')
        
    def done_turn(self,source='',resp_dst='',*pargs):
        self.queue_message('monopoly: done')
        self.queue_message('monopoly: roll')
        
    ### -------------------------------------------------------------------
    ### Acquiring game state
    ### -------------------------------------------------------------------
    
    def find_property_group(self,name):
        for group,data in self.property_types.iteritems():
            if name in data['names']:
                return group
        else:
            self.log('Not found name in property_types! {}'.format(name))
            return None
        
    def set_money(self,source='',resp_dst='',*pargs):
        if self.game_running and source == 'monopoly':
            self.money = int(pargs[0])
            self.log('Set money {}'.format(self.money))
            
    ### Pick up property names as we see them
    def catch_type(self,source='',resp_dst='',*pargs):
        name = pargs[0]
        group = pargs[1]
        cost = pargs[2]
        if not cost:
            cost = 990
        else:
            cost = int(cost)
        self.log('Seen name {} with group {}, cost {}'.format(name,group,cost))
        if group not in self.property_types:
            return
        if name not in self.property_types[group]['names']:
            self.log('New: name {} with group {}, cost {}'.format(name,group,cost))
            self.property_types[group]['names'].update({name:{'group':group,
                                                              'cost':cost,
                                                              'houses':0,
                                                              'mortgaged':False}})
        
        ### catch cost when we can, set a default known bogus value and boot it when we catch the right one
        elif self.property_types[group]['names'][name]['cost'] == 990 and cost != 990:
            self.log('Upd: name {} with group {}, cost {}'.format(name,group,cost))
            self.property_types[group]['names'][name]['cost'] = cost
    
    def catch_mortgage(self,source='',resp_dst='',*pargs):
        self.log('seen mortgaged {}'.format(pargs))
        name = pargs[0]
        group = self.find_property_group(name)
        self.property_types[group]['names'][name]['mortgaged'] = True
    
    def catch_unmortgage(self,source='',resp_dst='',*pargs):
        self.log('seen unmortgaged {}'.format(pargs))
        name = pargs[0]
        group = self.find_property_group(name)
        self.property_types[group]['names'][name]['mortgaged'] = False
    
    def request_property(self,source='',resp_dst='',*pargs):
        if self.game_running:
            self.queue_message(u'monopoly: what do i own?',True,'monopoly')
    
    def request_all_property(self,source='',resp_dst='',*pargs):
        if self.game_running:
            self.queue_message(u'monopoly: who owns what?',True,'monopoly')
    
    def update_property(self,source='',resp_dst='',*pargs):
        if self.game_running:
            property_to_examine = pargs[0]
            property_split = property_to_examine.split(', ')
            property_re = re.compile('([A-Z][a-zA-Z \']+) \(([a-z ]+)\)')
            for prop in property_split:
                result = property_re.match(prop)
                if result:
                    name,group = result.groups()
                    self.update_property_simple(source,resp_dst,name,group,None)
    
    def update_property_simple(self,source='',resp_dst='',*pargs):
        name,group,cost = pargs
        if cost:
            cost = int(cost)
        else:
            cost = 990
        if group not in self.property_types:
            return
        if group in self.property:
            if name not in self.property[group]:
                self.property[group].append(name)
        else:
            self.property.update({group:[name]})
    
    def win_auction(self,source='',resp_dst='',*pargs):
        if source == 'monopoly':
            if self.auction_property:
                name,group,cost = self.auction_property
                self.update_property_simple(source,resp_dst,name,group,cost)
                self.auction_property = None
    
    def lose_auction(self,source='',resp_dst='',*pargs):
        if source == 'monopoly':
            self.auction_property = None
    
    def request_houses(self,source='',resp_dst='',*pargs):
        if self.game_running:
            self.queue_message(u'monopoly: houses',True,'monopoly')
    
    def enum_house(self,num):
        if num.endswith('houses') or num.endswith('house'):
            num = int(num[0])
        elif num == 'a hotel':
            num = 5
        else:
            self.log('Can\'t count houses - assuming 0 - {} {}'.format(name,num))
            num = 0
        return num
            
    def update_houses_simple(self,source='',resp_dst='',*pargs):
        if self.game_running:
            name = pargs[0]
            num = self.enum_house(pargs[1]) ### Needs to catch correctly...
            group = self.find_property_group(name)
            if group:
                self.property_types[group]['names'][name]['houses'] = num
    
    def update_houses(self,source='',resp_dst='',*pargs):
        if self.game_running:
            self.log('Attempting multiple houses update...')
            self.log(pargs)
            n1,m1,n2,m2,n3,m3,group = pargs
            for t in [(n1,m1),(n2,m2),(n3,m3)]:
                if t[0] and t[1]:
                    self.update_houses_simple(source,resp_dst,*t)
    
    ### -------------------------------------------------------------------
    ### Values and decisions
    ### -------------------------------------------------------------------
    
    def value_property(self,name,group=None,cost=0):
        try:
            return int(float(name))
        except ValueError as err:
            pass
            #self.log(err)
            
        value = 1.0
        add = 0
        
        if not group:
            group = self.find_property_group(name)
        if not cost:
            cost = self.property_types[group]['names'][name]['cost']
            
        ###min value of a property is always cost/2
        
        house = self.property_types[group]['house']
        q = self.property_types[group]['num']
        if group in self.property:
            if name in self.property[group]:
                haveq = len(self.property[group]) - 1
            else:
                haveq = len(self.property[group])
        else:
            haveq = 0
            
        spend = max(0,self.money - house*q*3)
        
        self.log('haveq is {} valuing {}'.format(haveq,name))
        
        if group in ['stations','schools']:
            if haveq == 4:
                pay = 1400
            elif haveq == 3:
                pay = 600
            elif haveq == 2:
                pay = 440
            elif haveq == 1:
                pay = 280
            else: pay = 200
            
        elif group in ['utilities','shopping centres']:
            if haveq == 2:
                pay = 300
            elif haveq == 1:
                pay = 220
            else: pay = 100
            
        elif group in ['brown','dark blue']:
            if haveq == 2:
                pay = cost*5 + house*6
            elif haveq == 1:
                pay = cost*2 + house*4 + spend/2
            else: pay = cost
            
        elif group in self.property_types:
            if haveq == 3:
                pay = cost*5 + house*6
            elif haveq == 2:
                pay = cost*2 + house*3 + spend/2
            elif haveq == 1:
                pay = cost*1.5 + spend/4
            else: pay = cost
            
        else:
            pay = 100000000
        
        pay *= (2+self.num_plr*0.5)/2.49
            
        self.log('Valuing {} at {}.'.format(name,max(pay+1,cost/2)))
        return int(max(pay+1,cost/2))
    
    def recommend_houses(self):
        ### Make groups have 3 houses first, then all 3 houses, then hotels
        recommendations = []
        complete_groups = []
        cost = 0
        
        for group,props in self.property.iteritems():
            if len(props) == self.property_types[group]['num'] and group not in ['stations','schools','utilities','shopping centres']:
                complete_groups.append(group)
        
        self.log('complete groups:')
        self.log(complete_groups)
        
        ###Even out existing groups
        for group in complete_groups:
            house_cost = self.property_types[group]['house']
            housing_group = sorted([(name,v['houses']) for name,v in self.property_types[group]['names'].iteritems()],key=lambda v: -v[1])
            if all([i == housing_group[0] for i in housing_group]):
                self.log('Seeing same number of houses on all in group {}'.format(group))
            else:
                for name,num in housing_group:
                    if num < housing_group[-1][1]:
                        if cost + house_cost <= self.money:
                            self.log('Recommending house on {} at cost {} with bank {}.'.format(name,house_cost,self.money))
                            recommendations.append((name,housing_group[-1][1]-num)) ### Should only ever come to 1 or 0 new houses
                            cost += house_cost * housing_group[-1][1]-num
                            self.log('Total cost increases to {}.'.format(cost))
                        else: return recommendations
        
        for max_houses in (3,5):
            for group in complete_groups:
                house_per_cost = self.property_types[group]['num'] * self.property_types[group]['house']
                house_on_group = max([p['houses'] for k,p in self.property_types[group]['names'].iteritems()])
                more = max_houses - house_on_group
                if more > 0:
                    for i in xrange(more):
                        if cost + house_per_cost <= self.money:
                            recommendations.append((group,1))
                            cost += house_per_cost
                        else: return recommendations
        
        return recommendations
    
    def decide_trade(self):
        for group,props in self.property.iteritems():
            if len(props) == self.property_types[group]['num'] - 1:
                ### We have one left of a group to get
                self.log('One prop left in group {}'.format(group))
                names = self.property_types[group]['names'].iteritems
                for name,v in names():
                    if name not in props:
                        self.log('Decided we want property {}'.format(name))
                        return name
    
    def decide_price(self,trade_target):
        trade_factor = 0.8
        req = self.value_property(trade_target)*trade_factor
        no_touch_group = self.find_property_group(trade_target)
        price = []
        value = 0
        valued_properties = sorted([(p,self.value_property(p)) for group,proplist in self.property.iteritems() for p in proplist if group != no_touch_group],key=lambda v: v[1])
        
        self.log('Deciding price for {} - trades:'.format(trade_target))
        self.log(valued_properties)
        for p in valued_properties:
            price.append(p[0])
            value += p[1]
            if value >= req:
                return price
        if req-value > self.money:
            return []
        else:
            price.append(u'{}'.format(int(req-value)))
            return price
        
    ### -------------------------------------------------------------------
    ### Responding and creating desired game state
    ### -------------------------------------------------------------------
    
    def buy_property(self,source='',resp_dst='',*pargs):
        if self.game_running: ## and source == 'monopoly':
            ####pargs[0] is name, [1] is group, [2] is cost
            name = pargs[0]
            group = pargs[1]
            cost = int(pargs[2])
            if self.value_property(name,group,cost) >= cost:
                if self.money >= cost:
                    self.queue_message('monopoly: buy',True)
                    #self.update_property_simple(source,resp_dst,name,group,cost)
                else:
                    self.mortgage_spares()
                    self.queue_message('monopoly: buy',True)
                    self.queue_message('monopoly: auction',True)
            else:
                self.queue_message('monopoly: auction',True)
    
    def start_auction(self,source='',resp_dst='',*pargs):
        if self.game_running and source == 'monopoly':
            self.log('Action property {}'.format(pargs))
            name = pargs[0]
            group = self.find_property_group(name)
            cost = int(pargs[1])
            self.auction_property = (name,group,cost) ###Name, group, cost
        
    def bid_in_auction(self,source='',resp_dst='',*pargs):
        if self.game_running:
            if pargs[0] == self.botname: ### don't outbid yourself?
                return
            if pargs[0] == 'Opening':
                self.queue_message('monopoly: bid 10',True)
                return
            max_bid = self.value_property(*self.auction_property)
            current_bid = int(pargs[1])
            if max_bid - 20 >= current_bid:
                self.queue_message('monopoly: bid {}'.format(current_bid+20),True)
            else:
                self.queue_message('monopoly: rule me out')
        
    def buy_houses(self,source='',resp_dst='',*pargs):
        if self.game_running:
            self.log('Checking for house purchasing')
            ### If you have a complete group, mortgage all non-complete property sets (except stations) and build 3 houses on each set - if not, do nothing
            rec = self.recommend_houses()
            self.log('recommendations:')
            self.log(rec)
            for prop,number in rec:
                if prop in self.property_types:
                    self.unmortgage_group(prop)
                else:
                    self.unmortgage_property(prop)
                self.queue_message('monopoly: buy {} houses on {}'.format(number,prop),True,'monopoly')
    
    def roll_jail(self,source='',resp_dst='',*pargs):
        if self.game_running:
            ### If you have a complete group with 3+ houses, stay in jail, else keep moving
            for group,props in self.property.iteritems():
                if group not in ['utilities','shopping centres'] and len(props) == self.property_types[group]['num']: ### roll if we have a complete set
                    self.queue_message('monopoly: roll')
                    break
            else:
                self.queue_message('monopoly: pay to get out of jail')
                self.queue_message('monopoly: roll')
        
    def pay_debt(self,source='',resp_dst='',*pargs):
        if self.game_running:
            amount = int(pargs[0])
            self.mortgage_spares()
            self.queue_message('monopoly: pay debt')
        
    def respond_trade(self,source='',resp_dst='',*pargs):
        if self.game_running:
            self.log('Responding to trade: {}'.format(pargs))
            time.sleep(2)
            p1,theirs,p2,mine = pargs ### don't currently care about how valuable it is to our opponents?
            if p2 != 'tycoon': return
            mine = [m if not m.startswith('{}'.format(self.currency)) else int(m.strip('{}'.format(self.currency))) for m in mine.split(', ')]
            theirs = [m if not m.startswith('{}'.format(self.currency)) else int(m.strip('{}'.format(self.currency))) for m in theirs.split(', ')]
            
            mine_value = sum([self.value_property(m) for m in mine])
            theirs_value = sum([self.value_property(m) for m in theirs])
            
            if mine_value >= theirs_value:
                self.queue_message('monopoly: reject')
            else:
                self.queue_message('monopoly: confirm')
                ### Needs to update properties!!!
                
    def start_trade(self,source='',resp_dst='',*pargs):
        trade_player = pargs[0]
        trade_target = pargs[1]
        price = self.decide_price(trade_target)
        if price:
            self.queue_message('monopoly: trade {} with {} for {}'.format(', '.join(price),trade_player,trade_target))
        else:
            self.log('Cannot afford wanted property {}'.format(trade_target))
        
    def initiate_trade(self,trade_target):
        self.commandlist.pop(self.trade_re_string,'')
        
        self.trade_re_string = '{}: ([a-zA-Z_]+) owns.+({})'.format(self.botname,trade_target)

        ### Create new command that finds who owns the target property
        self.commandlist.update({self.trade_re_string:self.start_trade})
        self.compile_commands()
        
        self.request_all_property() ### re will match and call start_trade
    
    def mortgage_spares(self):
        if self.money < 500:
            for group,proplist in self.property.iteritems():
                if group not in ['stations','schools'] and len(proplist) < self.property_types[group]['num']:
                    for name in proplist:
                        if not self.property_types[group]['names'][name]['mortgaged']:
                            self.queue_message('monopoly: mortgage {}'.format(name),True,'monopoly')
                            self.property_types[group]['names'][name]['mortgaged'] = True
    
    def unmortgage_group(self,group):
        self.log('Unmortgaging group {}'.format(group))
        for name in self.property[group]:
            self.unmortgage_property(name)
    
    def unmortgage_property(self,name):
        group = self.find_property_group(name)
        if self.property_types[group]['names'][name]['mortgaged']:
            self.log('Unmortgaging {}'.format(name))
            self.queue_message('monopoly: unmortgage {}'.format(name),True,'monopoly')
        else:
            self.log('{} is not mortgaged, doing nothing.'.format(name))
    
    ### -------------------------------------------------------------------
    ### Monitor thread
    ### -------------------------------------------------------------------
    
    def loop_thread(self):
        while True:
            if self.game_running:
                self.mortgage_spares()
                time.sleep(10)
                self.buy_houses()
                time.sleep(10)
                trade_target = self.decide_trade()
                if trade_target:
                    self.initiate_trade(trade_target)
                time.sleep(40)
            else:
                time.sleep(1)


#(1:26:57 PM) monopoly: Balances: tjw: £938, lutomlin: £0, ob: £1442
#(1:11:46 PM) lutomlin: monopoly: what do i own?
#(1:11:47 PM) monopoly: lutomlin: You own Chalvey Road W (light blue), Lower Britwell Road (light blue), Trelawney Avenue (light blue), Cippenham Lane (orange), Farnham Road (orange), Uxbridge Road (orange), Windsor Road (red), Upton Court Road (dark blue)
    
#(1:17:17 PM) lutomlin: monopoly: who owns what?
#(1:17:17 PM) monopoly: lutomlin: tjw owns St Mary's Road (green), Castleview Road (green), Lascelles Road (green)
#(1:17:18 PM) monopoly: lutomlin: lutomlin owns Chalvey Road W (light blue), Lower Britwell Road (light blue), Trelawney Avenue (light blue), Cippenham Lane (orange), Farnham Road (orange), Uxbridge Road (orange), Windsor Road (mortgaged) (red), Upton Court Road (dark blue)
#(1:17:19 PM) monopoly: lutomlin: littlerob owns Tobermory Close (brown), Crown Meadow (brown), Upton Court Grammar (schools), Queensmere (shopping centres), Herschel Grammar (schools), Langley Academy (schools), Observatory (shopping centres), East Berkshire College (schools)
#(1:17:20 PM) monopoly: lutomlin: ob owns Parlaunt Road (pink), Common Road (pink), Meadfield Road (pink), Stoke Poges Lane (red), Herschel Street (red), Waterside Drive (yellow), High Street (yellow), Bath Road (yellow), Langley Road (dark blue)
#(1:17:21 PM) monopoly: lutomlin: The bank owns nothing
#
#
#
#tycoonb is offering Bow Street, Marlborough Street, Strand, Euston Road, Leicester Square in return for tycoon giving Old Kent Road
#u'RECV monopoly: lutomlin: tycoonb owns Electric Company (utilities), Marylebone
# Station (stations), Bow Street (mortgaged) (orange), Trafalgar Square (red), Wa
#ter Works (utilities), Liverpool Street Station (stations)'

#            
#            
                        #
                        #'[a-zA-Z_]+: (.+) now has (\d) houses':self.update_houses,
#                        
#                        
#            
#        (1:34:29 PM) ob: monopoly: houses
#(1:34:29 PM) monopoly: Parlaunt Road has a hotel; Common Road has a hotel; Meadfield Road has a hotel (pink set)
#(1:34:30 PM) monopoly: Tobermory Close has a hotel; Crown Meadow has a hotel (brown set)
#(1:34:31 PM) monopoly: Langley Road has 2 house(s); Upton Court Road has 2 house(s) (dark blue set)
#(1:34:32 PM) monopoly: Waterside Drive has a hotel; High Street has a hotel; Bath Road has a hotel (yellow set)
#(1:34:33 PM) monopoly: St Mary's Road has 4 house(s); Castleview Road has 4 house(s); Lascelles Road has 4 house(s) (green set)
#(1:34:34 PM) monopoly: Chalvey Road W has a hotel; Lower Britwell Road has a hotel; Trelawney Avenue has a hotel (light blue set)
    
def main():
    import sys
    if len(sys.argv) <= 1:
        print "Usage: 'python -i tybot.py <channel> [<nickname> [<server> [<port>]]]'"
        print "bot=self, c=self.connection"
        sys.exit(1)
    bot = TyBot(*sys.argv[1:])
    thread = threading.Thread(target=bot.start)
    thread.daemon = True
    thread.start()
    return bot

if __name__ == "__main__":
    bot = main()