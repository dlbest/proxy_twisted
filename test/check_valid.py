#!/usr/bin/env python


"""
@PROJECT: proxy_twisted
@AUTHOR: momen
@TIME: 12/8/19 11:16 PM
"""

from twisted.internet import reactor
from twisted.web.client import ProxyAgent
import pymysql
import requests


conn = pymysql.connect(host='192.168.1.55', user='root', passwd='931121', db='ipools', charset='utf8')
cursor = conn.cursor()
cursor.execute('select protocol, ip, port from xici')
ips = cursor.fetchall()
proxies = []
for ip in ips:
    proxies.append('{}://{}:{}'.format(ip[0].lower(), ip[1], ip[2]))


invalid = []
print(len(proxies))
for ip in ips:
    try:
        resp = requests.get(url='https://www.baidu.com', proxies={'https': '{}://{}:{}'.format(ip[0].lower(), ip[1], ip[2])}, headers={'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0'}, timeout=3)
        print(resp, '+++')
        if resp.status_code > 300:
            raise Exception('failure')
    except Exception as e:
        invalid.append(ip[1])

for ip in invalid:
    cursor.execute('delete from xici where ip = %s', (ip,))
    conn.commit()




