#!/usr/bin/env python
import sys
import json
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
whitelist = [
    'BouHblCBETA','Caradhras','COZVEzzzDIE','Dragonforce101',
    'EquiIibrium','FIresClan','HARLEM420','HotTubParty','LordsOfEvil',
    'MythicForce','R3b3lDragons','RoyalRoad','SkyGladiators',
    'VaIarMorghuIis','WarEnforcers','TheAnkou','TheFrozenCove',
    ]
vpcids = []
alliance_name = 'xSNAFUx'
first = 0
last = 0
k_id = '1'
annoyance_list = ['FireDemonMaxus']
remove_list = []

token = wikilogin.token_avatar_bot
#token = wikilogin.token_5ta
#token = wikilogin.token_me
mute = {}
default_mute_duration = 240
mute_duration = default_mute_duration
function = 'avatar'

# Get all vpcid for entire 5TA
print "Getting VPCIDs from VP holdings"
for team in teams:
    searchurl = 'https://506-dot-pgdragonsong.appspot.com/ext/dragonsong/world/season/get_vp_holdings_for_team?team='+team
    searchresp = requests.get(searchurl)
    searchjson = {}
    searchjson = searchresp.json()
    print "{} has {} castles".format(team, len(searchjson['holdings']))
    for castle in searchjson['holdings']:
        vpcids.append(castle['cid'])
print "Getting allCastleMeta"
allCastleMeta = atlas.apiGetAllCastlesMeta(k_id=k_id)
#for castle in allCastleMeta['castles']:
#    if allCastleMeta['castles'][castle]['owner_team'] in teams:
#        vpcid = k_id+'-'+castle
#        vpcids.append(vpcid)
#if len(vpcids) < 1:
#    print allCastleMeta['error']
#    sys.exit()
if 'error' in allCastleMeta:
    print allCastleMeta['error']
    sys.exit()


print 'Adding {} castles to avatar'.format(len(vpcids))

for cid in remove_list:
    if cid in vpcids:
        print 'found'
        vpcids.remove(cid)

print 'Adding {} castles to avatar'.format(len(vpcids))

cont_list = atlas.createContList(vpcids)
print "Number of API keys needed: {}".format(len(cont_list))

passage = []

pool = ThreadPoolExecutor(len(cont_list))

#futures = [pool.submit(atlas.apiGetCastleInfo, cont, idx) for idx,cont in enumerate(cont_list)]
#castlejson = {}
#for r in as_completed(futures):
#    castlejson.update(r.result())
#results = [r.result() for r in as_completed(futures)]
#print json.dumps(results, indent=4)
#sys.exit(0)

while True:
    # This is for no castle limit
    #castlejson = {}
    #try:
    #    castlejson = atlas.apiGetCastleInfo(cont)
    #except KeyboardInterrupt:
    #    sys.exit(0)
    #except:
    #    print "********** castlejson. continue **********"
    #    time.sleep(2)
    #    continue

    # This is for ThreadPool
    castlejson = {}
    futures = [pool.submit(atlas.apiGetCastleInfo, cont, idx, function) for idx,cont in enumerate(cont_list)]
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

    # Request passage list every 15 iterations
    if first % 15 == 0:
        teamjson = {}
        try:
            teamjson = atlas.apiGetTeamMeta('["CatNapping","XxBOHICAxX","DarkWinds","KOMBATKILLERZ","ColdBrewCrew"]',0,function)
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            print "passage. continue"
            time.sleep(2)
            continue
        if 'error' in teamjson:
            print json.dumps(teamjson['error'], indent=4)
            continue
        passage = []
        for team in teamjson:
            passage.extend(teamjson[team]['free_passages'])
        #print 'passage: ', passage

    #print json.dumps(castlejson, indent=4)

    for vpcid in vpcids:
        for prims in castlejson[vpcid]['fleets']:
            prim = castlejson[vpcid]['fleets'][prims]
            #print json.dumps(prim, sort_keys=True, indent=4)
            if prim['alliance_name'] != alliance_name and prim['team_name'] not in whitelist:
                if prim['team_name'] == None:
                    enemy_team = 'None'
                    print '[skipping] No team', prims
                    continue
                if prims[:-2] in annoyance_list:
                    print '[skipping] Annoyance', prims
                    continue
                if castlejson[vpcid]['infra']['fort']['shield_time_ts'] - time.time() > 0:
                    print '[skipping] Castle bubbled', prims
                    continue
                if prims in mute:
                    if time.time()-mute[prims] > mute_duration:
                        print 'unmute', prims
                        try:
                            del mute[prims]
                        except:
                            print 'error deleting {}'.format(prims)
                    else:
                        print '[skipping] Muted', prims
                        continue
                if prim['team_name'] in passage:
                    print '[skipping] passage granted', prims
                    continue
                if prim['team_name'] in teams:
                    continue

                if first-last > 100:
                    print 'clearing dictionary'
                    mute.clear()
                last = first
                mute.update({prims:time.time()})
                enemy_team = prim['team_name']
                try:
                    ts = teamsshort[castlejson[vpcid]['owner_team']]
                except:
                    ts = castlejson[vpcid]['owner_team']
                message = '[' + ts + ' T' + str(castlejson[vpcid]['level']+1) + ' ' + castlejson[vpcid]['custom_name'] + '] ' + u'\u2694'
                message +=' [' + enemy_team + ' ' + prims + ' ' + '{:,} troops'.format(prim['total_troops']) + '] [{:}]'.format(allCastleMeta['castles'][vpcid[2:]]['coords'])
                print message
                try:
                    status_code = atlas.send_message(token, message, None)
                except KeyboardInterrupt:
                    sys.exit(0)
                except:
                    continue
                try:
                    a = int(status_code)
                except:
                    status_code = 999
                if int(status_code) <  300:
                    mute_duration = default_mute_duration*4
                elif int(status_code) < 500:
                    mute_duration = default_mute_duration*3
                elif int(status_code) < 850:
                    mute_duration = default_mute_duration*2
                else:
                    mute_duration = default_mute_duration
                print "mute_duration={}".format(mute_duration)

        #print '....', castlejson[vpcid]['owner_team'], castlejson[vpcid]['custom_name'], vpcid
    print first,datetime.datetime.now().strftime('%H:%M:%S')
    first += 1
    time.sleep(2)
    #time.sleep(3.8)
