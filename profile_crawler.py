# Extract and process user profile from steam
# V1.0 generate user list from seed user and his/her friends list
# V1.1 crawl with proxy (to do)
# V1.2 add logger and exception (to do)
# V1.3 singleton (to do)

import os, sys
import json
import re
import requests
from proxy_crawler import Downloader

HEADER = {
    'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.361',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate, sdch, br',
    'Accept-Language':'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
}


PATTERNS = {
    'profile': {
              'steamID': '"steamid":"(\d*)"',
              'userName':'"personaname":"(.+?)","',
              'realName':'class="header_real_name ellipsis".+?\n.+?<bdi>(.+?)</bdi>',
              'level':'class="persona_name persona_level".+?"friendPlayerLevelNum">(\d*)',
              'since':'Member since (.+?)\.',
              'location':'class="profile_flag".+?\n.+?(\S.+?)</div>',
              'gamesURL':'.*"(http://steamcommunity\.com/.+?/games/\?tab=all)"',
              'friendsURL':'.*"(http://steamcommunity\.com/.+?/friends/)"',
              'customURL':'"(http://steamcommunity\.com/id/.+?)/friends'
              },
    'gamesList':'var rgGames = \[(.+?)\];',
    'games':{
             'name':'"name":"(.+?)","',
             'appID':'"appid":(\d*),',
             'totalTime':'"hours_forever":"(\d*)",',
             'lastPlayed':'"last_played":(\d*)'
             },
    'friends': '"friendBlockLinkOverlay".+(http:\/\/steamcommunity.com\/.+?)"><\/a>'
}

VALIDATION = {
    "This profile is private": 'PRIVATE',
    "The specified profile could not be found": 'UNAVAILABLE',
    "Failed loading profile data": 'UNAVAILABLE',
    "This user has not yet set up their Steam Community profile": 'NOPROFILE'
}

class steamUserInfo():
    def __init__(self, userID):
        self.userID = userID
        self.profileURL = "http://steamcommunity.com/profiles/%s"%self.userID
        self.profileContent = requests.get(self.profileURL, HEADER).text
        self.level = self.check_level()
        self.gamesURL = ''
        self.friendsURL = ''
    
    def check_level(self):
        for key, val in VALIDATION.items():
            if key in self.profileContent:
                return val
        return 'AVAILABLE'
    
    # Parse html text file with regular expression
    def info_extractor(self, pattern, page):
        regxObj = re.compile(pattern, re.IGNORECASE | re.UNICODE)
        match = regxObj.search(page)
        try:
            extract = match.group(1)
        except AttributeError:
            extract = ""
        return extract
        
    def retrieve_profile(self, write_to_file=False):
        if self.level == 'AVAILABLE':
            profile = {}
            for key, val in PATTERNS['profile'].items():
                profile[key] = self.info_extractor(val, self.profileContent)
                
            self.gamesURL = profile['gamesURL']
            self.friendsURL = profile['friendsURL']
            
            if write_to_file:
                self._write_to_file(userDetail, json.dumps({self.userID:profile}))
            else:
                pass
                # print profile
                
            return True
        else:
            return False
            
    def retrieve_games(self, write_to_file=False):
        if self.level == 'AVAILABLE':
            if self.gamesURL == '':
                self.gamesURL = self.info_extractor(PATTERNS['profile']['gameURL'])
   
            gamesContent = requests.get(self.gamesURL, HEADER).text
            gamesList = self.info_extractor(PATTERNS['gamesList'], gamesContent)[1:-1]
            games = []
            
            for gameInfo in gamesList.split('},{'):
                gamesTmp = {}             
                for key, val in PATTERNS['games'].items():
                    gamesTmp[key] = self.info_extractor(val, gameInfo)
                    
                if gamesTmp['lastPlayed'] != '':
                    games.append({gamesTmp['appID']:gamesTmp})
                
            if write_to_file:
                self._write_to_file(ratingDetail, json.dumps({self.userID:games}))
            else:
                pass
                # print games[0:3]
                       
            return True
        else:
            return False
        
    def retrieve_friends(self):
        if self.level == 'AVAILABLE':
            if self.friendsURL == '':
                self.friendsURL = self.info_extractor(PATTERNS['profile']['friendsURL'])

            friendsContent = requests.get(self.friendsURL, HEADER).text
            regxObj = re.compile(PATTERNS['friends'])
            friendsIter = re.finditer(regxObj, friendsContent)
    
            for it in friendsIter:
                addr = str(it.group(1))
                
                if addr.startswith('http://steamcommunity.com/id'):
                    friendsID = self.info_extractor(
                                PATTERNS['profile']['steamID'],
                                requests.get(addr, HEADER).text)
                    yield friendsID
                    
                else:
                    friendsID = re.search('.+?profiles/(\d*)', addr).group(1)
                    yield friendsID
                
    def _write_to_file(self, file, content):
        with open(file, 'a+') as f:
            f.write(content+'\n')
            
def remove_files(path):
    try:
        os.remove(path)
    except OSError:
        pass
    
if __name__ == '__main__':
    starter = 76561197960265738
    
    # a user list to go through
    idList = [starter]
    idDict = {starter:1}
    counter = 0
 
    # data file path
    userDetail = './rawdata/users_detail.json'
    ratingDetail = './rawdata/ratings_detail.json'
    friendsDetail = './rawdata/friends_detail.json'

    remove_files(userDetail)
    remove_files(ratingDetail)
    remove_files(friendsDetail)
    
    dr = Downloader()

    while counter < 10: #for test purpose
        try: #skip the entry if fails
             #loop through users
            userID = idList.pop()
            
            steam = steamUserInfo(userID)
            steam.retrieve_profile(True)
            steam.retrieve_games(True)
            
            # update queue
            #ctr = 0
            for key in steam.retrieve_friends():
                # ctr += 1
                key = int(key)
                if key not in idDict:
                    idList.append(key)
                    idDict[key] = 1
            #print ctr
            #print counter
            counter += 1
            time.sleep(random.randint(0, 60))
        except:
            continue
        
    
    
    
