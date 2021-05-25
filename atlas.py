#!/usr/bin/env python

import json
from pprint import pprint
import requests
import wikilogin
import time
import datetime
import sys

max_castles_per_request = 25

def getCooldownDuration(region_level):
    if region_level == 5:
        return 12*60*60
    if region_level == 4:
        return 9*60*60
    if region_level == 3:
        return 6*60*60
    if region_level == 2:
        return 3*60*60
    return 0

def getShieldAmount(fort_level):
    if fort_level > 0:
        return (50000 + (10000*fort_level))
    return 50000

def send_message(token, msg, img=None):
    """Send a LINE Notify message (with or without an image)."""
    headers = {'Authorization': 'Bearer ' + token}
    payload = {'message': msg}
    files = {'imageFile': open(img, 'rb')} if img else None
    try:
        r = requests.post(LINEURL, headers=headers, params=payload, files=files)
    except:
        print "Caught an error"
        return
    if files:
        files['imageFile'].close()
    print 'status_code = {}, msg remaining {}'.format(r.status_code, r.headers['X-RateLimit-Remaining'])
    return r.headers['X-RateLimit-Remaining']

# Atlas Castles
# /atlas/castles/metadata/macro
# Get high level datails for all castles in kingdom
def apiGetAllCastlesMeta(idx=3,function='web',k_id='1'):
    try:
        resp = requests.get('https://api-dot-pgdragonsong.appspot.com/api/v1/atlas/castles/metadata/macro?realm_name=Celestial_Haven&k_id='+k_id, headers=wikilogin.genHeaders(getKey(idx,function)))
    except:
        print "Caught an error in apiGetAllCastlesMeta requests.get() Status Code:{}".format(resp.status_code)
        raise
    try:
        castles = resp.json()
    except:
        print "No JSON apiGetAllCastlesMeta"
        raise
    for cid in castles['castles']:
        castles['castles'][cid]['coords'] = 'X:{:.1f}'.format(castles['castles'][cid]['coords']['x']/40) + ' Y:{:.1f}'.format(castles['castles'][cid]['coords']['y']/-40)
        castles['castles'][cid]['level'] = castles['castles'][cid]['level'] + 1
    return castles

# Atlas Teams
# /atlas/teams/metadata/macro
# Get high level details for all teams in atlas
def apiGetAllTeamMeta(idx=3,function='web'):
    try:
        resp = requests.get('https://api-dot-pgdragonsong.appspot.com/api/v1/atlas/teams/metadata/macro?k_id=1&realm_name=Celestial_Haven', headers=wikilogin.genHeaders(getKey(idx,function)))
    except:
        print "Caught an error in apiGetAllTeamMeta requests.get() Status Code:{}".format(resp.status_code)
        raise
    try:
        return resp.json()
    except:
        print "No JSON apiGetAllTeamMeta"
        raise

# Atlas Teams
# /atlas/teams/metadata
# Get high level details for specific team in atlas
def apiGetTeamMeta(team, idx=3,function='web'):
    try:
        resp = requests.get('https://api-dot-pgdragonsong.appspot.com/api/v1/atlas/teams/metadata?k_id=1&realm_name=Celestial_Haven&teams='+team, headers=wikilogin.genHeaders(getKey(idx,function)))
    except:
        print "Caught an error in apiGetTeamMeta requests.get() Status Code:{}".format(resp.status_code)
        raise
    try:
        return resp.json()
    except:
        print "No JSON apiGetTeamMeta"
        raise

# Atlas Castles
# /castle_info
# Get information for given group of castles
def apiGetCastleInfo(cont,idx=0,function='web'):
    try:
        resp = requests.get('https://api-dot-pgdragonsong.appspot.com/api/v1/castle_info?cont_ids=['+cont+']', headers=wikilogin.genHeaders(getKey(idx,function)))
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        print "Caught an error in apiGetCastleInfo requests.get() Status Code:{}".format(resp.status_code)
        raise
    try:
        return resp.json()
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        print "No JSON apiGetCastleInfo"
        raise

# Atlas Alliances
# /atlas/alliance/teams
# Get All Atlas Alliances and their members
def apiGetAlliance(idx=0, function='web'):
    try:
        resp = requests.get('https://api-dot-pgdragonsong.appspot.com/api/v1/atlas/alliance/teams', headers=wikilogin.genHeaders(getKey(idx,function)))
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        print "Caught an error in apiGetAlliance requests.get() Status Code:{}".format(resp.status_code)
        raise
    try:
        return resp.json()
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        print "No JSON apiGetAlliance"
        raise

def getKey(idx, function):
    avatar = [0,1,2,3,4]
    protect = [5,6,7,8,9]
    scanner = [10,11,12]
    #scanner = [0,1,2,3,4,5,6,7,8,9,10,11,12,13]
    web = [13]
    if function == 'avatar':
        apiKey = avatar[(idx % len(avatar))]
        #print 'using key {} {}'.format(apiKey, function)
    if function == 'scanner':
        apiKey = scanner[(idx % len(scanner))]
        #print 'using key {} {}'.format(apiKey, function)
    if function == 'protect':
        apiKey = protect[(idx % len(protect))]
    if function == 'web':
        apiKey = web[(idx % len(web))]
        #print 'using key {} {}'.format(apiKey, function)
    return apiKey

def createContList(vpcids):
    cont_list = []
    # Create the castle query string
    cont = ''
    for idx,vpcid in enumerate(vpcids):
        # assemble cont_idx string
        cont += '"{}",'.format(vpcid)
        if idx % max_castles_per_request == (max_castles_per_request-1):
            cont = cont[:-1]
            cont_list.append(cont)
            cont = ''
    if len(cont) > 0:
        if cont[-1] == ',':
            cont = cont[:-1]
        cont_list.append(cont)
    return cont_list

def createContListMinus1(vpcids):
    cont_list = []
    # Create the castle query string
    cont = ''
    for idx,vpcid in enumerate(vpcids):
        # assemble cont_idx string
        cont += '"{}",'.format(vpcid)
        if idx % (max_castles_per_request-1) == (max_castles_per_request-2):
            cont = cont[:-1]
            cont_list.append(cont)
            cont = ''
    if len(cont) > 0:
        if cont[-1] == ',':
            cont = cont[:-1]
        cont_list.append(cont)
    return cont_list

def parseCastleJson(castlemeta,castlejson):
    current_state = {}
    for cid in castlejson:
        mydata = {}

        now = time.time()
        timeleft = castlejson[cid]['infra']['fort']['shield_time_ts'] - now
        timeleftcd = now - castlejson[cid]['infra']['fort']['shield_time_ts']

        troopsleft = getShieldAmount(castlejson[cid]['infra']['fort']['level']) - round(castlejson[cid]['infra']['fort']['shield_ships_lost'])

        team_troop_total = 0
        team_troop_counts = []
        for prim in castlejson[cid]['fleets']:
            if castlejson[cid]['fleets'][prim]['dtype'] == 'garrison':
                mydata['guards'] = '{:,}'.format(castlejson[cid]['fleets'][prim]['total_troops'])
            elif castlejson[cid]['fleets'][prim]['team_name'] == castlejson[cid]['owner_team']:
                team_troop_total += castlejson[cid]['fleets'][prim]['total_troops']
                team_troop_counts.append(castlejson[cid]['fleets'][prim]['total_troops'])
        if 'guards' not in mydata:
            mydata['guards'] = '0'
        mydata['troops'] = '{:,}'.format(int(team_troop_total))
        guard_defense = 0
        for idx,cnt in enumerate(sorted(team_troop_counts, reverse=True)):
            if idx < 3:
                guard_defense += cnt
        if guard_defense > 1000:
            mydata['troops_rounded'] = '{:,}K'.format(int(guard_defense/1000))
        else:
            mydata['troops_rounded'] = '{:,}'.format(int(guard_defense))

        mydata['shieldtroops'] = '{:,}'.format(int(troopsleft))

        if castlejson[cid]['infra']['fort']['shield_turned_on']:
            mydata['shieldactive'] = 'Enabled'
        else:
            mydata['shieldactive'] = 'Disabled'
        if timeleft < 0:
            mydata['bubbleleft'] = '0'
        else:
            mydata['bubbleleft'] = '{:}'.format(datetime.timedelta(seconds=round(timeleft)))
        cdduration = getCooldownDuration(castlejson[cid]['level']+1)
        if timeleftcd > cdduration or timeleft > 0:
            mydata['cooldownleft'] = '0'
        else:
            mydata['cooldownleft'] = '{:}'.format(datetime.timedelta(seconds=round(cdduration-timeleftcd)))

        mydata['level'] = castlejson[cid]['level']+1
        mydata['owner'] = castlejson[cid]['owner_team']
        mydata['customname'] = castlejson[cid]['custom_name']
        mydata['coords'] = castlemeta['castles'][cid[2:]]['coords']
        mydata['fleets'] = castlejson[cid]['fleets']
        current_state.update({cid:mydata})
        #print current_state
    return current_state

renameCrest = {
        'icon_team_crest_001' : 'icon_COA_book',
        'icon_team_crest_002' : 'icon_COA_bow',
        'icon_team_crest_003' : 'icon_COA_carrot',
        'icon_team_crest_004' : 'icon_COA_castle',
        'icon_team_crest_005' : 'icon_COA_chevron',
        'icon_team_crest_006' : 'icon_COA_chickenLeg',
        'icon_team_crest_007' : 'icon_COA_crescent',
        'icon_team_crest_008' : 'icon_COA_crossingSwords',
        'icon_team_crest_009' : 'icon_COA_crown',
        'icon_team_crest_010' : 'icon_COA_deadTree',
        'icon_team_crest_011' : 'icon_COA_dragon',
        'icon_team_crest_012' : 'icon_COA_fire',
        'icon_team_crest_013' : 'icon_COA_fleurDeLys',
        'icon_team_crest_014' : 'icon_COA_flower',
        'icon_team_crest_015' : 'icon_COA_fourLeafClover2',
        'icon_team_crest_016' : 'icon_COA_fourLeafClover'
    }


LINEURL = 'https://notify-api.line.me/api/notify'

# Libertas and Allys rank 1 to 250
ally_list = ['ColdBrewCrew','XxBOHICAxX','DarkWinds','KOMBATKILLERZ','CatNapping',
    #Libertas List
    'BouHblCBETA','Caradhras','COZVEzzzDIE','Dragonforce101',
    'EquiIibrium','FIresClan','Forb1dden','HARLEM420','HotTubParty','LordsOfEvil',
    'MythicForce','R3b3lDragons','RoyalRoad','SkyGladiators',
    'VaIarMorghuIis','WarEnforcers','TheAnkou','TheFrozenCove',
    #Popularis
    '7WingsOfFire','AncientElites','ArchDevilz','ChudoYudo2015','CreatorsWrath',
    'Deathxwillxwin','DragonBarons','DRAKOS457ARMY','Empire0fFire','EvilConduct',
    'halfbloodprnc','InvidiasWraith','KiwiLollipop','LaViaDraconis','LexxTalionis',
    'NoMercyOrder','Norulesteam','RisingElites','SKYOVERDREAM','TheRedEclipse',
    'WARriorxDragns','xDRAGONLORDZx','xHELLFIREx','XxCANLARxX',
    #Arachnid
    '1WingedFury1','Arcana','Bilzabob','BlueReapers','Burntwoods',
    'DiamondCrest','DoomCakes',
    'Gryphonsclaw','GSpotHeroes','HockeyRules','HydraRising','ImmortalCrew','IrishDragons',
    'KnightsOfHell','LittleXSavages','MysticDragunz','NaturesHavoc',
    'NutzAndGutz','PaddyDragon','Phyxius','ProjectGhost','PyroEmpire',
    'RegulatorsX','RevengeandWar','Risingangels','RizingDragonz','Rulesky',
    'Shadowriders','SolsticexxWar','TeamPilipinas','TheDeathRow','TheElderNine',
    'ValiantLegends','ValkyrieShadow','Vikingdrags','WhoGiveaDragon','xIndoFighterx','XJUDGEMENTDAYX ',
    'XxCieloxX',

    'LoyalBlood','ZensCastle','1sTR',
    'LesVolturis','ServesYouRight','TheDestroyers1','4Vengeance','OdinsWaechter',
    'FunFlyingdrags','MobxBrutality','Invalesco',
    'HERExBExDRAGON','Apwal','5oArrows','SudnDreams',
    'ButWeAreBetter','DigitalChaos','Strikers','Thedevourers','PaleHorseRider',
    'TheReforged','Dustlar','GhostLeaders','Niohoggrs','abner9527',
    'Brotherinarms','TaiwanWINNER','TantricAlchemy','BENDTHEKNEE1',
    'SudnDreams','AffIiction','TheEternalones','GermanHunters',
    'Scientists','Rwolves','SINNENN','SUKZ2BEU','BrothersAsylum',
    'DisneyShocking','Ward0gs','DarkentheEarth','momotaiwan','AJISAIFLORECER',
    'Storadia','SevenEleven7','TheDogHouse','50xWarriors','ShadowsOrder',
    'Gryfindor','awakedragons','DILL1GAF','HERExBExDRAGON',
    'FrenchPapys','FriendsnFamily','PhoenixRisen','DragonEmpireRU','INMORTALES',
    'Flamesphere','xFLAWLESSx','Corsarios','0DragonGods0','AnimusLegion',
    'KsArmy','XxWalhallaxX','DracoGenus','xSuaSpontex',
    'primalknights','DemonDragons','DragonHelpers1','BRASILOFICIAL','Apwal','0dyssee',
    'LegendOfThai','VeGiSeNtai','KnightsReign',
    '00Smaug00','SkyGodz','Hivequeen',
    'BridgeKillers','Eragonland','XxRoyalsxX','ChaoticDrive',
    'Ref0rged','BloodLegions','Darkshades','MUFUFUxJPN','FujinxXxRaijin',
    'xBEASTxMODEx','Phantomvoid','GdragonsNight','KingDragon73',
    'CarnalForge','Teng4JAPAN',
    ]

if __name__ == "__main__":
    #print json.dumps(apiGetTeamMeta('["CatNapping","XxBOHICAxX","DarkWinds","KOMBATKILLERZ","ColdBrewCrew"]',0,'web'), sort_keys=True, indent=4)
    #print json.dumps(apiGetTeamMeta('["DarkWinds"]',0,'web'), sort_keys=True, indent=4)

    #teams = apiGetAllTeamMeta(1,'web')
    #print json.dumps(teams, sort_keys=True, indent=4)
    #print len(teams['teams'])
    #print json.dumps(apiGetAllCastlesMeta(k_id='1'), sort_keys=True, indent=4)

    #castles = apiGetAllCastlesMeta(0,'web')
    #print json.dumps(castles, indent=4, sort_keys=True)
    #print len(castles['castles'])
    #with open('newapi.json', 'w') as outfile:
    #    json.dump(castles, outfile, indent=4, sort_keys=True)

    #print json.dumps(apiGetCastleInfo('{"cont_idx":"0","k_id":"1","region_id":"A1243"}'),sort_keys=True, indent=4)
    #print json.dumps(apiGetCastleInfo('{"cont_idx":"2","k_id":"1","region_id":"A1655"}'),sort_keys=True, indent=4)
    #print json.dumps(apiGetCastleInfo('"6-A3430-0"'), sort_keys=True, indent=4)
    #print json.dumps(apiGetCastleInfo('"1-A749-1","1-A3120-0"',2,'web'), sort_keys=True, indent=4)

    alliances = apiGetAlliance(0,'web')
    print json.dumps(alliances, sort_keys=True, indent=4)

    #left = send_message(wikilogin.token_me, 'test')
    #print json.dumps(left, sort_keys=True, indent=4)
