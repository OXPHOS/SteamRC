# Game list in json format can be retrived from https://api.steampowered.com/ISteamApps/GetAppList/v2/
# Detailed information of each game can be retrieved at http://store.steampowered.com/api/appdetails?appids=10

import json
import requests
import re


HEADER = {
    'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.361',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate, sdch, br',
    'Accept-Language':'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
}

gameListUrl = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
gameListResp = requests.get(gameListUrl, HEADER) #html
gameListJson = gameListResp.json()

appidList = []
for apps in gameListJson['applist']['apps']:
    appidList.append(apps['appid'])
    


for _ in appidList[0:10]:
    gameListUrl = "http://store.steampowered.com/api/appdetails?appids=%s"%_
    gameListResp = requests.get(gameListUrl, HEADER) #html
    gameListJson = gameListResp.json()
    
    with open('./rawdata/app_detail.txt', 'a') as f:
        json.dump(gameListJson, f)
