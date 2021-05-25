#!/usr/bin/env python
import sys
import json
import requests
import wikilogin
import time
import datetime
import atlas
import pickle
import copy
import mysql.connector as mysql

def getCidList():
    db = mysql.connect(
            host = "localhost",
            user = "root",
            passwd = "IVxhCVQVHnv6",
            database = "atlas1")

    cursor = db.cursor()

    search_query = "SELECT * FROM scanner WHERE bubbleleft > 0"
    vpcids = {}

    cursor.execute(search_query)
    result = cursor.fetchall()

    for r in result:
        vpcids.update({r[0]:r[4]})

    cursor.close()

    return vpcids

def checkStateChange():
    for cid in current_state:
        if previous_state[cid]['exposed']==0 and current_state[cid]['exposed']==1 and cid not in vpcids:
            if mydata_depth[cid]['depth'] > 0:
                if 'power_rank' not in teammeta['teams'][mydata_depth[cid]['owner']]:
                    message = '[T{} {}BD ****] '.format(mydata_depth[cid]['level'],mydata_depth[cid]['depth'])
                    message += mydata_depth[cid]['owner'] + ' ' + mydata_depth[cid]['coords']
                elif teammeta['teams'][mydata_depth[cid]['owner']]['power_rank'] < 230:
                    message = '[T{} {}BD #{}] '.format(mydata_depth[cid]['level'],mydata_depth[cid]['depth'],teammeta['teams'][mydata_depth[cid]['owner']]['power_rank'])
                    message += mydata_depth[cid]['owner'] + ' [' + mydata_depth[cid]['coords'] + ']'
                    print message
                    if mydata_depth[cid]['owner'] not in atlas.ally_list:
                        status_code = atlas.send_message(token, message, None)

def setExposure(depth):
    for cid in current_state:
        if current_state[cid]['depth'] == depth:
            #print cid
            for entry_cid in current_state[cid]['entry']:
                if entry_cid in vpcids and current_state[entry_cid]['exposed'] == 1:
                    current_state[cid]['exposed'] = 1

def setBlockade(depth):
    for cid in current_state:
        if current_state[cid]['depth'] == depth:
            for entry_cid in current_state[cid]['entry']:
                if current_state[entry_cid]['exposed'] == 1:
                    current_state[cid]['blockade'] = 1


#token = wikilogin.token_me
token = wikilogin.token_glory
function = 'web'
first = 1
error = 0
current_state = {}
next_state = {}
previous_state = {}
mydata_depth = {}

with open('mydata_depth.json') as json_file:
    mydata_depth = json.load(json_file)

# Add exposed key, and set all access castles to exposed
for depth_cid in mydata_depth:
    mydata_depth[depth_cid]['blockade'] = 0

    if mydata_depth[depth_cid]['depth'] == 0:
        mydata_depth[depth_cid]['exposed'] = 1
    else:
        mydata_depth[depth_cid]['exposed'] = 0

print 'getting castle meta'
castlemeta = atlas.apiGetAllCastlesMeta(0,function)
if 'error' in castlemeta:
    print castlemeta['error']
    sys.exit(0)

for depth_cid in mydata_depth:
    mydata_depth[depth_cid]['owner'] = castlemeta['castles'][depth_cid[2:]]['owner_team']

# Save the current list as last_updated_castle
with open('mydata_depth_new.json', 'w') as outfile:
    json.dump(mydata_depth, outfile, indent=4, sort_keys=True)

print 'getting team meta'
teammeta = atlas.apiGetAllTeamMeta(0,function)
if 'error' in teammeta:
    print teammeta['error']
    sys.exit(0)

# initial condition
current_state = copy.deepcopy(mydata_depth)
#print json.dumps(current_state, indent=4, sort_keys=True)
previous_state = copy.deepcopy(mydata_depth)


first = 0
vpcids = {}
while (True):
    # get bubbled castles from spreadsheet
    vpcids = getCidList()
    if len(vpcids) == 0:
        print "Bubble list is empty"
        time.sleep(30)
        continue
    #else:
    #    print json.dumps(vpcids,indent=4)

    # set exposed flags and recurse for multi-path
    for depth_idx in range (1,14):
        setExposure(depth_idx)
    for depth_idx in range (1,14):
        setExposure(depth_idx)
    for depth_idx in range (1,14):
        setExposure(depth_idx)

    # set blockade flag
    for depth_idx in range (1,14):
        setBlockade(depth_idx)

    # check for state change
    checkStateChange()

    # save state for next iteration
    # ONE HOUR if first%280 == 279:
    if first%150 == 149:
        previous_state = copy.deepcopy(mydata_depth)
        status_code = atlas.send_message(token,"  *SUMMARY*  " , None)
    else:
        previous_state = copy.deepcopy(current_state)
    current_state = copy.deepcopy(mydata_depth)

    print first,datetime.datetime.now().strftime('%H:%M:%S')
    first += 1
    time.sleep(20)
