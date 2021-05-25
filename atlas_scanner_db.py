#!/usr/bin/env python
import sys
import json
import requests
import wikilogin
import time
import datetime
import atlas
from concurrent.futures import ThreadPoolExecutor, as_completed
import mysql.connector as mysql

db = mysql.connect(
        host = "localhost",
        user = "root",
        passwd = "IVxhCVQVHnv6",
        database = "atlas1")

cursor = db.cursor()

# Create the table
fields = ""
fields += "cid VARCHAR(16) PRIMARY KEY,"
fields += "level INT,"
fields += "owner TINYTEXT,"
fields += "coords TINYTEXT,"
fields += "customname TINYTEXT,"
fields += "guards INT,"
fields += "troops INT,"
fields += "shieldtroops INT,"
fields += "shieldactive TINYTEXT,"
fields += "bubbleleft INT,"
fields += "cooldownleft INT,"
fields += "marshall TINYTEXT,"
fields += "ownedsince INT,"
fields += "powerrank INT,"
fields += "depth INT"

create_table_command = "CREATE TABLE IF NOT EXISTS scanner(" + fields + ")"
cursor.execute(create_table_command)

function = 'scanner'
token = wikilogin.token_den
#token = wikilogin.token_me
first = 0
k_id='1'
mute = []
mydata = {}

print "getting team meta"
teammeta = atlas.apiGetAllTeamMeta(0,function)

cont_list = []

mydata_depth = {}
with open('mydata_depth.json') as json_file:
    mydata_depth = json.load(json_file)

# create cont list
vpcids = []
for cid in mydata_depth:
    vpcids.append(cid)
cont_list = atlas.createContList(vpcids)


num_pool = 3
#num_pool = 15
pool = ThreadPoolExecutor(num_pool)

cont_list_len = len(cont_list)
last_len = cont_list_len % num_pool
print "num_pool={}, cont_list_len={}, remainder={}".format(num_pool, cont_list_len,last_len)

cont_list2 = []

replace_query = "REPLACE INTO scanner (cid, level, owner, coords, customname, guards, troops, shieldtroops, shieldactive, bubbleleft, cooldownleft, marshall, ownedsince, powerrank, depth) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"

while(True):
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

        #print json.dumps(castlejson, sort_keys=True, indent=4)
        data = []
        values = []
        for cid in castlejson:
            mydata[cid] = {}

            now = time.time()
            timeleft = castlejson[cid]['infra']['fort']['shield_time_ts'] - now
            timeleftcd = now - castlejson[cid]['infra']['fort']['shield_time_ts']
            #print timeleftcd

            troopsleft = atlas.getShieldAmount(castlejson[cid]['infra']['fort']['level']) - round(castlejson[cid]['infra']['fort']['shield_ships_lost'])

            team_troop_total = 0
            for prim in castlejson[cid]['fleets']:
                if castlejson[cid]['fleets'][prim]['dtype'] == 'garrison':
                    mydata[cid]['guards'] = castlejson[cid]['fleets'][prim]['total_troops']
                elif castlejson[cid]['fleets'][prim]['team_name'] == castlejson[cid]['owner_team']:
                    team_troop_total += castlejson[cid]['fleets'][prim]['total_troops']
            if 'guards' not in mydata[cid]:
                mydata[cid]['guards'] = 0
            mydata[cid]['troops'] = team_troop_total

            mydata[cid]['shieldtroops'] = troopsleft

            if castlejson[cid]['infra']['fort']['shield_turned_on']:
                mydata[cid]['shieldactive'] = 'Enabled'
            else:
                mydata[cid]['shieldactive'] = 'Disabled'
            if timeleft < 0:
                mydata[cid]['bubbleleft'] = 0
            else:
                mydata[cid]['bubbleleft'] = round(timeleft)
            cdduration = atlas.getCooldownDuration(castlejson[cid]['level']+1)
            if timeleftcd > cdduration or timeleft > 0:
                mydata[cid]['cooldownleft'] = 0
            else:
                mydata[cid]['cooldownleft'] = round(cdduration-timeleftcd)

            if castlejson[cid]['owned_since_epoch'] == None:
                mydata[cid]['ownedsince'] = 0
            else:
                mydata[cid]['ownedsince'] = round(now-castlejson[cid]['owned_since_epoch'])

            if 'name' in castlejson[cid]['infra']['fort']['executor']:
                mydata[cid]['marshall'] = castlejson[cid]['infra']['fort']['executor']['name']
            else:
                mydata[cid]['marshall'] = ''

            mydata[cid]['level'] = castlejson[cid]['level']+1
            mydata[cid]['owner'] = castlejson[cid]['owner_team']
            mydata[cid]['customname'] = castlejson[cid]['custom_name']
            mydata[cid]['coords'] = mydata_depth[cid]['coords']
            try:
                mydata[cid]['powerrank'] = teammeta['teams'][mydata[cid]['owner']]['power_rank']
            except:
                mydata[cid]['powerrank'] = 0
            mydata[cid]['depth'] = mydata_depth[cid]['depth']

            values.append( (
                            cid,
                            mydata[cid]['level'],
                            mydata[cid]['owner'],
                            mydata[cid]['coords'],
                            mydata[cid]['customname'],
                            mydata[cid]['guards'],
                            mydata[cid]['troops'],
                            mydata[cid]['shieldtroops'],
                            mydata[cid]['shieldactive'],
                            mydata[cid]['bubbleleft'],
                            mydata[cid]['cooldownleft'],
                            mydata[cid]['marshall'],
                            mydata[cid]['ownedsince'],
                            mydata[cid]['powerrank'],
                            mydata[cid]['depth']
                           )
                        )
            if mydata[cid]['guards'] < 80000:
                if cid not in mute:
                    mute.append(cid)
                    message = '[T{} {}BD] {} {}'.format(mydata[cid]['level'], mydata[cid]['depth'], mydata[cid]['owner'], mydata[cid]['coords'])
                    status_code = atlas.send_message(token, message, None)

        cursor.executemany(replace_query, values)
        db.commit()
        print first,i,datetime.datetime.now().strftime('%H:%M:%S')
        time.sleep(5)
    print first, datetime.datetime.now().strftime('%H:%M:%S')
    first = first + 1


