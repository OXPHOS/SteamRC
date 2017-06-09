# Downloader class: retrieve available proxies
# Downlaod html via SOCKS proxy

# pip install pysocks
import os
import requests
import re
import logging
import random

class Downloader(object):
    """
    Get the data from url bypass proxy; and maintain proxy list
    This should be a singleton object, like logging.
    """
    proxy_path = './proxy'
    proxy_file = 'proxy.txt'
    
    header = {
        'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.361',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, sdch, br',
        'Accept-Language':'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
        }

    def __init__(self):
        """
        Try to get the saved proxy file. If not exist, create one for writing,
        and write to it a long list of available proxies.
        Or read in entries from proxy.txt.
        """

        if not os.path.isdir(self.proxy_path):
            os.mkdir(self.proxy_path)

        self.proxyfile = os.path.join(self.proxy_path, self.proxy_file)
        
        if os.path.isfile(self.proxyfile):
            self._v_proxies = self.getProxyListFromFile()
            # if none in proxy file, it will not use proxy
            if not len(self._v_proxies):
                self._v_proxies = self._crawl_for_proxy()
                self.updateProxyFile(self._v_proxies)
         #if file exists, read from it
        else:
            # get lastest proxy list from network
            self._v_proxies = self._crawl_for_proxy()
            self.updateProxyFile(self._v_proxies)

    def _crawl_for_proxy(self):
        v_url = []
        # http://www.idcloak.com/proxylist/free-proxy-servers-list.html
        # http://www.idcloak.com/proxylist/proxy-list.html
        try:
            r = requests.get('http://www.idcloak.com/proxylist/proxy-list.html')
        except requests.exceptions.RequestException as e:
            logging.error("Request exception (proxy crawl 1): %s", e.message)

        if r.text != '':
            html = r.text
            pattern = '<div\s*?style="vertical-align:bottom; width:[^<>]*?" title="(\d+?)%"\s*?></div></div></td><td>([^<>]*?)</td><td>([^<>]*?)</td><td>(\d+?)</td><td>([^<>]*?)</td>'
            regxObj = re.compile(pattern, re.IGNORECASE | re.UNICODE | re.DOTALL)
            matches = regxObj.findall(html)
            count = len(matches)
            if count > 0:
                for i in range(0, count):
                    if int(matches[i][0]) > 50 and matches[i][1] == 'High':
                        url = matches[i][2] + "://" + matches[i][4] + ":" + matches[i][3]
                        v_url.append(url)

        # http://www.gatherproxy.com/
        try:
            r = requests.get('http://www.gatherproxy.com/')
        except requests.exceptions.RequestException as e:
            logging.error("Request exception (proxy crawl 2): %s", e.message)

        if r.text != '':
            html = r.text
            pattern = '"PROXY_IP":"(.+?)",.*?"PROXY_PORT":"(.+?)".*?"PROXY_TIME":"(\d+?)","PROXY_TYPE":"(.+?)"'
            regxObj = re.compile(pattern, re.IGNORECASE | re.UNICODE | re.DOTALL)
            matches = regxObj.findall(html)
            count = len(matches)
            if count > 0:
                for i in range(0, count):
                    if int(matches[i][2]) < 250 and matches[i][3] == 'Elite':
                        url = "http://" + matches[i][0] + ":" + str(int(matches[i][2],16))
                        v_url.append(url)

        # http://free-proxy-list.net      no speed information
        try:
            r = requests.get('https://free-proxy-list.net')
        except requests.exceptions.RequestException as e:
            logging.error("Request exception (proxy crawl 3): %s", e.message)

        if r.text != '':
            html = r.text
            pattern = '<tr><td>([^<>]+?)</td><td>([^<>]+?)</td><td>[^<>]+?</td><td>[^<>]+?</td><td>([^<>]+?)</td><td>[^<>]+?</td><td>([^<>]+?)</td>.*?</tr>'
            regxObj = re.compile(pattern, re.IGNORECASE | re.UNICODE | re.DOTALL)
            matches = regxObj.findall(html)
            count = len(matches)
            if count > 0:
                for i in range(0, count):
                    if matches[i][2] == 'elite proxy':
                        url = 'http://' if matches[i][2] == 'no' else 'https://' + matches[i][0] + ":" + matches[i][1]
                        v_url.append(url)

        # returns a list of url strings without '\n'
        print v_url
        return v_url

    def getProxyListFromFile(self):
        return open(self.proxyfile, 'r').read().splitlines()

    def updateProxyFile(self, proxylist):
        open(self.proxyfile, 'w').write('\n'.join(proxylist))

    def get(self, url):
        """
        Simply wrap requests to get the html by url
        """
        patient = 10
        step = 0
        #debug
        #d100 = 0
        while patient:
            patient -= 1
            try:
                
                proxy = random.choice(self._v_proxies)

                r = requests.get(url, headers=self.header, timeout=10, 
                                 proxies={proxy.split(':')[0]:proxy})

                if r.text == '':
                    raise requests.exceptions.HTTPError("No HTTP body returned")

                if r.text.find("too many requests") != -1:
                    raise requests.exceptions.HTTPError("Too many requests")
                print "SUCCESS!"
                return r.text

            # ProxyError is a derived class of ConnectionError
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.Timeout) as e:
                logging.error("Proxy exception: %s", e.message)
                continue

            except requests.exceptions.RequestException as e:
                logging.error("Request exception (get url): %s", e.message)

        # TODO
        # do more work for all failed case later
        logging.critical("Get Response failed from url %s after 10 tries" % url)
        raise Exception('Downloader exception, failed too many times')
        
if __name__ == '__main__':
    dr = Downloader()
    dr.get('http://steamcommunity.com/profiles/76561197960265738')