#!/usr/bin/env python
import hashlib
import time

#
# WIKI BOT Login
# --- Special Pages -> Bot Passwords
lgname = ""
lgpassword = ""

#
# LINE Notify Tokens
#
#1-on-1
token_me = ""
token_team = ""
token_officers = ""
token_5ta = ""
token_avatar = ""
token_avatar_bot = ""
token_nightswatch = ""
token_sauron = ""
token_den = ""
token_glory = ""
token_blockade = ""

#
# Wardragons API
# --- 
CLIENT_ID = ['app-',
            ]
CLIENT_SECRET = ['secret-',
                ]

api_key = ['apikey-',
          ]

def genHeaders(idx=0):
    #print 'this is my idx: {:}'.format(idx)
    now = time.time()
    msg = ':'.join([CLIENT_SECRET[idx], api_key[idx], str(int(now))]).encode('utf-8')
    generated_signature = hashlib.sha256(msg).hexdigest()
    return {'X-WarDragons-APIKey':api_key[idx], 'X-WarDragons-Request-Timestamp': str(int(now)), 'X-WarDragons-Signature':str(generated_signature)}


