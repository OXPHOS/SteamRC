# Extract and process user profile from steam
# V0.1 process single user data
# V0.2 generate user list from seed user and his/her friends list

import os, sys
import json
import requests
import re

HEADER = {
    'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.361',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate, sdch, br',
    'Accept-Language':'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
}

# Parse html text file with regular expression
def infoExtractor(regxObj, pageText):
    match = regxObj.search(pageText)
    try:
        extract = match.group(1)
    except AttributeError:
        extract = ""
    return extract

# For each user, extract the information of his/her profile, games and friends    
class SteamUserInfoCrawler:
    def __init__(self, userID):
        self.userID = userID
        print userID
        self.userProfile = {}
        self.ratingList = []
        self.friendsList = []
        
        self.userInfoProcessor()
        if len(self.userProfile['gamesURL'])!=0:
            self.ratingInfoProcessor()
        if len(self.userProfile['friendsURL'])!=0:
            self.friendsProcessor()
    
    # extract user profile
    def userInfoProcessor(self):
        self.userProfile = {}
        profileUrl = "http://steamcommunity.com/profiles/%s"%self.userID
        profileResp = requests.get(profileUrl, HEADER) #html
        profileRespHtml = profileResp.text
        self.userProfile.update({"steamID": infoExtractor(
            re.compile('"steamid":"(\d*)"', re.UNICODE), profileRespHtml)})
        self.userProfile.update({"name": infoExtractor(
            re.compile('"personaname":"(.+?)","', re.IGNORECASE | re.UNICODE), profileRespHtml)})
        self.userProfile.update({"gamesURL": infoExtractor(
            re.compile('.*"(http://steamcommunity\.com/.+?/games/\?tab=all)"', re.UNICODE), profileRespHtml)})
        self.userProfile.update({"level": infoExtractor(
            re.compile('class="persona_name persona_level".+?"friendPlayerLevelNum">(\d*)'), profileRespHtml)})
        self.userProfile.update({"friendsURL": infoExtractor(
            re.compile('.*"(http://steamcommunity\.com/.+?/friends/)"', re.UNICODE), profileRespHtml)})
        self.userProfile.update({"since": infoExtractor(
            re.compile('Member since (.+?)\.', re.UNICODE), profileRespHtml)})
        self.userProfile.update({"customURL": infoExtractor(
            re.compile('"(http://steamcommunity\.com/id/.+?)/friends', re.UNICODE), profileRespHtml)})
        self.userProfile.update({"realName": infoExtractor(
            re.compile('class="header_real_name ellipsis".+?\n.+?<bdi>(.+?)</bdi>', re.UNICODE), profileRespHtml)})
        self.userProfile.update({"location": (infoExtractor(
            re.compile('class="profile_flag".+?\n.+?(\S.+?)</div>', re.UNICODE), profileRespHtml)).strip()})
        
    # extract game information of the user 
    def ratingInfoProcessor(self):        
        gamesUrl = self.userProfile['gamesURL']
        gamesResp = requests.get(gamesUrl, HEADER) #html
        gamesRespHtml = gamesResp.text
        gamesListFull = infoExtractor(re.compile('var rgGames = \[(.+?)\];'), gamesRespHtml)[1:-1]
        for gameInfo in gamesListFull.split('},{'):
            gameRatingList = {}
            gameRatingList.update({"name": infoExtractor(
                re.compile('"name":(.+?),"', re.UNICODE), gameInfo)})
            gameRatingList.update({"appID": infoExtractor(
                re.compile('"appid":(\d*),', re.UNICODE), gameInfo)})
            gameRatingList.update({"forever": infoExtractor(
                re.compile('"hours_forever":(\d*),', re.UNICODE), gameInfo)})
            gameRatingList.update({"last_played": infoExtractor(
                re.compile('"last_played":(\d*),', re.UNICODE), gameInfo)})

            self.ratingList.append(gameRatingList)
        
    # extract friend information of the user        
    def friendsProcessor(self):        
        friendsUrl = self.userProfile['friendsURL']
        friendsResp = requests.get(friendsUrl, HEADER) #html
        friendsRespHtml = friendsResp.text

        regxObj = re.compile('"friendBlockLinkOverlay".+?(http://steamcommunity.com/.+?)"></a>')
        friendsIter = re.finditer(regxObj, friendsRespHtml)
    
        for it in friendsIter:
            addr = str(it.group(1))
            if addr.startswith('http://steamcommunity.com/id'):
                friendsID = infoExtractor(re.compile('"steamid":"(\d*)"', re.UNICODE),
                                          requests.get(addr, HEADER).text)
            else:
                friendsID = re.search('.+?profiles/(\d*)', addr).group(1)
            self.friendsList.append(friendsID)
    
    # save method    
    def saveToJson(self, filename, content):
        with open(filename, 'a') as f:
            json.dump(content, f)

if __name__ == "__main__":
    # test ID
    userID = 76561197960265738
    
    # a user list to go through
    idList = [userID]
    idDict = {userID:1}
    counter = 0
 
    # data file path
    userDetail = './rawdata/user_detail.json'
    ratingDetail = './rawdata/rating_detail.json'
    friendsDetail = './rawdata/friend_detail.json'
    
    os.remove(userDetail)
    os.remove(ratingDetail)
    os.remove(friendsDetail)
    
    while counter < 10: #for test purpose
        try: #skip the entry if fails (usually caused by non-UNICODE information)
            # loop through users
            userID = idList.pop()
            steam = SteamUserInfoCrawler(userID)
            
            # update information of each user
            userIDStr = '"' + str(userID) + '"'
            steam.saveToJson(userDetail, steam.userProfile)
            steam.saveToJson(ratingDetail, {userIDStr:steam.ratingList})
            steam.saveToJson(friendsDetail, {userIDStr:steam.friendsList})
            
            # update queue
            for _ in steam.friendsList:
                key = _.strip('"')
                if key not in idDict:
                    idList.append(key)
                    idDict[key] = 1
            counter += 1
        except:
            continue



