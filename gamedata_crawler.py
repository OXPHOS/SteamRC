# Game list in json format can be retrived from https://api.steampowered.com/ISteamApps/GetAppList/v2/
# Detailed information of each game can be retrieved at (eg.) http://store.steampowered.com/api/appdetails?appids=10

import json
import os
import requests
import ast
import time
import random

HEADER = {
    'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.361',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate, sdch, br',
    'Accept-Language':'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
}


app_list = './rawdata/appid_list.txt'
apps_detail = './rawdata/apps_detail.json'
appidList = []

if not os.path.isfile(app_list):
    file = open(app_list, 'w')
    gameListUrl = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    gameListResp = requests.get(gameListUrl, HEADER, timeout=10) #html
    gameListJson = gameListResp.json()

    for apps in gameListJson['applist']['apps']:
        appidList.append(apps['appid']) #print len(appidList) #42026
        file.write("%s\n" %apps)
    file.close()
    
else:
   with open(app_list, 'r') as file:
       appidListLoad = file.readlines()
   for _ in appidListLoad:
        appidList.append(ast.literal_eval(_)['appid'])

#try:
#    os.remove('./rawdata/apps_detail.txt')
#except OSError:
#    pass

file = open(apps_detail, 'w')
for _ in appidList:

    gameUrl = "http://store.steampowered.com/api/appdetails?appids=%s"%_
    gameResp = requests.get(gameUrl, HEADER) #html
    gameJson = gameResp.json()
    
    if ((gameJson is None) or ((gameJson[str(_)]).get('success') == False)):
        continue
    else:
        key = gameJson.keys()[0]
        # print key
        gameJsonReparse = {'appid':key, 'data':gameJson[key]['data']}
        
        # The best way for generating multiple line JSON file
        # which can be read by sparkSession smoothly
        file.write(json.dumps(gameJsonReparse)+'\n')
        
    time.sleep(random.randint(0, 60))
    
file.close()
