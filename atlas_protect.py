#!/usr/bin/env python
import sys
import json
from pprint import pprint
import requests
import wikilogin
import time
import datetime
import atlas
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed

teams = ['ColdBrewCrew','XxBOHICAxX','KOMBATKILLERZ','CatNapping']
teamsshort = {'ColdBrewCrew':'CBC',
              'XxBOHICAxX':'BOH',
              'KOMBATKILLERZ':'KK',
              'CatNapping':'CAT'}

alliance_name = 'xSNAFUx'

print "apiGetAllCastlesMeta()"
allCastleMeta = atlas.apiGetAllCastlesMeta()

print 'getting team meta'
teammeta = atlas.apiGetAllTeamMeta(0,'web')
if 'error' in teammeta:
    print teammeta['error']
    sys.exit(0)


ta_holdings = {}
ta_vpcids = []
# Get all vpcid for entire 5TA
for team in teams:
    searchurl = 'https://506-dot-pgdragonsong.appspot.com/ext/dragonsong/world/season/get_vp_holdings_for_team?team='+team
    searchresp = requests.get(searchurl)
    searchjson = {}
    searchjson = searchresp.json()
    for castle in searchjson['holdings']:
        ta_holdings.update({castle['cid']:{'customname':castle['name'],'owner':team}})
        ta_vpcids.append(castle['cid'])

ta_cont_list = atlas.createContList(ta_vpcids)
print "Number of API keys needed for TA check: {}".format(len(ta_cont_list))

mydata_depth = {}

with open('mydata_depth.json') as json_file:
    mydata_depth = json.load(json_file)

#------------------------------------------------------------------------
# RULES
#------------------------------------------------------------------------

rules = [
    #{
    #    "name": "Inlandsurfer",
    #    "type": "player",
    #    "match": "Inlandsurfer",
    #    "cid" : "",
    #},
    #{
    #    "name": "RheagarTargryn",
    #    "type": "player",
    #    "match": "RheagarTargryn",
    #    "cid" : "",
    #},
    #{
    #    "name": "BoomerxxSooner",
    #    "type": "player",
    #    "match": "BoomerxxSooner",
    #    "cid" : "",
    #},
    #{
    #    "name": "Bat5hit",
    #    "type": "player",
    #    "match": "Bat5hit",
    #    "cid" : "",
    #},
    {
        "name": "Blockade",
        "type": "Blockade",
        "cid" : "",
    },
]

mute = {}
mute_duration = 600
sz_mute_duration = 120

current_state = {}
previous_state = {}
token = wikilogin.token_nightswatch
#token = wikilogin.token_me
token_sauron = wikilogin.token_sauron
#token_sauron = wikilogin.token_me
token_blockade = wikilogin.token_blockade

first = 1
error = 0
function = 'protect'
num_pool = 5
pool = ThreadPoolExecutor(num_pool)

vpcids = []
protect_lookup = {}

for cid in ta_holdings:
    # only castles with depth greater than 0 will have an entry field
    if 'entry' in mydata_depth[cid]:
        for entry_cid in mydata_depth[cid]['entry']:
            # add entry to vpcids list
            if entry_cid not in vpcids:
                vpcids.append(entry_cid)
            # add to protect lookup
            if entry_cid in protect_lookup:
                protect_lookup[entry_cid].append(cid)
            else:
                protect_lookup.update({entry_cid:[cid]})

#print json.dumps(protect_lookup, indent=4)

#protect_lookup.update({"1-A749-1":["1-A1687-2"]})  # house of pain
#protect_lookup.update({"1-A573-2":["1-A1651-0"]}) # BashSaidOops
priority_list = ["1-A749-1","1-A573-2"]

cont_list = atlas.createContListMinus1(vpcids)
for idx,cont in enumerate(cont_list):
    cont_list[idx]+=',"{}"'.format(priority_list[idx%len(priority_list)])
    #print idx, cont_list[idx]

cont_list_len = len(cont_list)
last_len = cont_list_len % num_pool
print "num_pool={}, cont_list_len={}, remainder={}".format(num_pool, cont_list_len,last_len)

idx = 0
cont_list2 = []
while True:
    #
    # This request is for the TA castles
    #
    castlejson = {}
    futures = [pool.submit(atlas.apiGetCastleInfo, cont, idx, function) for idx,cont in enumerate(ta_cont_list)]
    try:
        for r in as_completed(futures):
            castlejson.update(r.result())
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        print "********** as_complete. continue **********"
        continue

    # If error detected (most likely server or rate limit), then skip to next loop
    if 'error' in castlejson:
        print 'thread pool'
        print json.dumps(castlejson['error'], indent=4)
        time.sleep(5)
        continue
    else:
        print 'Got TA castles'
    ta_state = atlas.parseCastleJson(allCastleMeta,castlejson)
    time.sleep(5)

    #
    # This loop is for the entries
    #
    for i in xrange(0,cont_list_len,num_pool):
        cont_list2 = []
        if i+num_pool > cont_list_len:
            # remainder
            for j in range(0,last_len):
                cont_list2.append(cont_list[i+j])
        else:
            for j in range(0,num_pool):
                cont_list2.append(cont_list[i+j])

        castlejson = {}
        futures = [pool.submit(atlas.apiGetCastleInfo, cont, idx, function) for idx,cont in enumerate(cont_list2)]
        try:
            for r in as_completed(futures):
                castlejson.update(r.result())
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print "********** as_complete. continue **********"
            continue

        # If error detected (most likely server or rate limit), then skip to next loop
        if 'error' in castlejson:
            print i, json.dumps(castlejson['error'], indent=4)
            time.sleep(5)
            continue

        previous_state.update(copy.deepcopy(current_state))
        current_state = atlas.parseCastleJson(allCastleMeta,castlejson)
        now = time.time()

        # don't send message for startup condition
        if first == 1:
            previous_state.update(copy.deepcopy(current_state))

        for cid in current_state:
            if current_state[cid]['bubbleleft'] != '0':
                current_bubble = 'Bubbled'
            else:
                current_bubble = 'Normal'
            if previous_state[cid]['bubbleleft'] != '0':
                previous_bubble = 'Bubbled'
            else:
                previous_bubble = 'Normal'
            #print cid, current_bubble, previous_bubble

            if current_bubble == 'Bubbled' and previous_bubble == 'Normal':
                for protect_cid in protect_lookup[cid]:
                    protect_name = ta_holdings[protect_cid]['customname']
                    protect_team = ta_holdings[protect_cid]['owner']
                    message = '[' + teamsshort[protect_team] + ' T' + str(allCastleMeta['castles'][protect_cid[2:]]['level']) + ' ' + protect_name + '] is exposed' + ' [' + allCastleMeta['castles'][protect_cid[2:]]['coords'] + ']'
                    status_code = atlas.send_message(token, message, None)
                    #print('status_code = {}'.format(status_code))

            for ridx in range(len(rules)):
                #if rules[ridx]['type'] == "player":
                #    # Determine if rule matched
                #    match = 0
                #    for prim in current_state[cid]['fleets']:
                #        if rules[ridx]['match'] in prim:
                #            match = 1
                #    if match == 1:
                #        # Check for mute duration
                #        if rules[ridx]['name'] in mute:
                #            if now-mute[rules[ridx]['name']] < mute_duration:
                #                skip = 1
                #                print '[skipping] Muted', rules[ridx]['name']
                #            else:
                #                skip = 0
                #        else:
                #            skip = 0
                #        # Send message only if not muted
                #        if skip == 0:
                #            protect_cid = protect_lookup[cid]
                #            protect_name = ta_holdings[protect_cid]['customname']
                #            protect_team = ta_holdings[protect_cid]['owner']
                #            message = '[' + teamsshort[protect_team] + ' T' + str(allCastleMeta['castles'][protect_cid[2:]]['level']) + ' ' + protect_name
                #            message += '] enemy alert rule violated: ' + rules[ridx]['name'] + '] [' + allCastleMeta['castles'][protect_cid[2:]]['coords'] + ']'
                #            status_code = atlas.send_message(token_sauron, message, None)
                #            #print('status_code = {}'.format(status_code))
                #            mute.update({rules[ridx]['name']:now})
                if rules[ridx]['type'] == "newarrival" and rules[ridx]['cid'] == cid:
                    #print "rule matched"
                    for prim in current_state[cid]['fleets']:
                        if prim not in previous_state[cid]['fleets']:
                            if current_state[cid]['fleets'][prim]['alliance_name'] != alliance_name and current_state[cid]['fleets'][prim]['team_name'] not in atlas.ally_list:
                                if current_state[cid]['fleets'][prim]['team_name'] == None:
                                    enemy_team = 'None'
                                else:
                                    enemy_team = current_state[cid]['fleets'][prim]['team_name']
                                if enemy_team in teammeta['teams']:
                                    rank = teammeta['teams'][enemy_team]['power_rank']
                                else:
                                    rank = 0

                                protect_cid = protect_lookup[cid][0]
                                protect_name = ta_holdings[protect_cid]['customname']
                                protect_team = ta_holdings[protect_cid]['owner']
                                message = '[' + teamsshort[protect_team] + ' T' + str(allCastleMeta['castles'][protect_cid[2:]]['level']) + ' ' + protect_name + ']['
                                message += rules[ridx]['name'] + ' ' + enemy_team + ' ' + prim + '] [' + allCastleMeta['castles'][protect_cid[2:]]['coords'] + ']'
                                if rank < 230:
                                    if prim[:-2] == 'Zmeij':
                                        print message
                                    elif prim in mute:
                                        if now-mute[prim] < sz_mute_duration:
                                            print message
                                        else:
                                            status_code = atlas.send_message(token_sauron, message, None)
                                            mute.update({prim:now})
                                    else:
                                        status_code = atlas.send_message(token_sauron, message, None)
                                        mute.update({prim:now})
                                else:
                                    print message
                elif rules[ridx]['type'] == "Blockade":
                    # Determine if rule matched
                    for prim in current_state[cid]['fleets']:
                        if prim not in previous_state[cid]['fleets']:
                            if current_state[cid]['fleets'][prim]['alliance_name'] != alliance_name and current_state[cid]['fleets'][prim]['team_name'] not in atlas.ally_list:
                                if current_state[cid]['fleets'][prim]['blockade_until_epoch'] - now > 0:
                                    if current_state[cid]['fleets'][prim]['team_name'] == None:
                                        enemy_team = 'None'
                                    else:
                                        enemy_team = current_state[cid]['fleets'][prim]['team_name']
                                    if enemy_team in teammeta['teams']:
                                        rank = teammeta['teams'][enemy_team]['power_rank']
                                    else:
                                        rank = 0
                                    for protect_cid in protect_lookup[cid]:
                                        protect_name = ta_holdings[protect_cid]['customname']
                                        protect_team = ta_holdings[protect_cid]['owner']
                                        message = '[' + teamsshort[protect_team] + ' T' + str(allCastleMeta['castles'][protect_cid[2:]]['level']) + ' ' + protect_name + ' {:}]['.format(ta_state[protect_cid]['troops_rounded'])
                                        message += enemy_team + ' ' + prim + '  {:,} troops] ['.format(current_state[cid]['fleets'][prim]['total_troops']) + allCastleMeta['castles'][protect_cid[2:]]['coords'] + ']'
                                        if rank < 230:
                                            status_code = atlas.send_message(token_blockade, message, None)
                                        else:
                                            print message
                                        if current_state[cid]['fleets'][prim]['total_troops'] > ta_state[protect_cid]['troops']:
                                            message = '[' + teamsshort[protect_team] + ' T' + str(allCastleMeta['castles'][protect_cid[2:]]['level']) + ' ' + protect_name + '] *REINFORCE- CASTLE GUARDS EXPOSED* ['
                                            message += enemy_team + ' ' + prim + '  {:,} troops] ['.format(current_state[cid]['fleets'][prim]['total_troops']) + allCastleMeta['castles'][protect_cid[2:]]['coords'] + ']'
                                            status_code = atlas.send_message(token_sauron, message, None)

        print first,i,datetime.datetime.now().strftime('%H:%M:%S')
        time.sleep(5)

    print first, datetime.datetime.now().strftime('%H:%M:%S')
    first += 1
