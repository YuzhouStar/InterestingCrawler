# coding:utf-8
from selenium import webdriver
import requests
import time
from urllib import parse
import re
import redis
import json


class Spider(object):

    def __init__(self):
        self.web = webdriver.Chrome()
        self.web.get('https://user.qzone.qq.com')
        self.__username = '1272082503'
        self.__password = ''
        self.headers = {
            'host': 'h5.qzone.qq.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.8',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'connection': 'keep-alive'
        }
        self.headers2 = {
            'host': 'h5.qzone.qq.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.8',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'connection': 'keep-alive'
        }
        self.req = requests.Session()
        self.cookies = {}
        self.qzonetoken = ""
        self.re = connect_redis()
        self.content = []
        self.unikeys = []
        self.like_list_names = []

    def login(self):
        self.web.switch_to_frame('login_frame')
        log = self.web.find_element_by_id("switcher_plogin")
        log.click()
        time.sleep(1)
        username = self.web.find_element_by_id('u')
        username.send_keys(self.__username)
        ps = self.web.find_element_by_id('p')
        ps.send_keys(self.__password)
        btn = self.web.find_element_by_id('login_button')
        time.sleep(1)
        btn.click()
        time.sleep(2)
        self.web.get('https://user.qzone.qq.com/{}'.format(self.__username))
        cookie = ''
        for elem in self.web.get_cookies():
            cookie += elem["name"] + "=" + elem["value"] + ";"
        self.cookies = cookie
        self.get_g_tk()
        self.headers['Cookie'] = self.cookies
        self.web.quit()

    def get_aggree_url(self):
        url = "https://h5.qzone.qq.com/proxy/domain/users.qzone.qq.com/cgi-bin/likes/get_like_list_app?"
        params = {
            "unikey": "",
            "begin_uin":0,
            "query_count":60,
            "if_first_page=1":1,
            "g_tk": self.g_tk
        }
        url = url + parse.urlencode(params)
        return url

    def get_mood_url(self):
        url = 'https://h5.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6?'
        params = {
            "sort": 0,
            "start": 0,
            "num": 20,
            "cgi_host": "http://taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6",
            "replynum": 100,
            "callback": "_preloadCallback",
            "code_version": 1,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "notice": 0,
            "format": "jsonp",
            "need_private_comment": 1,
            "g_tk": self.g_tk
        }
        url = url + parse.urlencode(params)
        return url

    def get_aggree_url(self):
        url = 'https://user.qzone.qq.com/proxy/domain/users.qzone.qq.com/cgi-bin/likes/get_like_list_app?'
        params = {
            "uin": "1272082503",
            "unikey": self.unikey,
            "begin_uin": 0,
            "query_count": 60,
            "if_first_page": 1,
            "g_tk": self.g_tk,
        }
        url = url + parse.urlencode(params)
        return url

    def get_json(self, str1):
        arr = re.findall(r'[^()]+', str1)
        json = ""
        for i in range(1, len(arr) - 1):
            json += arr[i]
        return json

    def get_mood_detail(self):
        urlMood = self.get_mood_url()
        url_Mood = urlMood + '&uin=' + str(1272082503)
        self.re = connect_redis()
        pos = 0
        while pos < 1700:
            url__ = url_Mood + '&pos=' + str(pos)
            mood_detail = self.req.get(url=url__, headers=self.headers)
            jsonContent = self.get_json(str(mood_detail.content.decode('utf-8')))
            self.content.append(jsonContent)
            # print(jsonContent)
            self.unikeys = self.get_unilikeKey(jsonContent)
            for unikey in self.unikeys:
                # print('unikey' + unikey)
                self.unikey = unikey
                like_detail = self.get_like_list()

                self.like_list_names.append(like_detail)
            # print('1272082503', jsonContent)
            # 存储到json文件
            with open('data' + str(pos) + '.json', 'w', encoding='utf-8') as w:
                w.write(jsonContent)
            pos += 20
            print(pos)
        # time.sleep(2)

        # print(self.content)
        with open('agree' + '.json', 'w', encoding='utf-8') as w2:
            json.dump(self.like_list_names, w2, ensure_ascii=False)

        print(self.content)
        print(json.dumps(self.content))
        print("=====================")
        print(json.dumps(self.like_list_names, ensure_ascii=False))
        self.re.set("QQ", json.dumps(self.content, ensure_ascii=False))
        self.re.set("QQ_like_list_all", json.dumps(self.like_list_names, ensure_ascii=False))
        print("finish")

    def get_like_list(self):
        url = self.get_aggree_url()
        # print(url)
        like_list = self.req.get(url=url, headers=self.headers)
        like_list_detail = self.get_json(like_list.content.decode('utf-8'))
        like_list_detail = like_list_detail.replace('\\n', '')
        # print("success to get like list")
        return like_list_detail


    def get_g_tk(self):
        p_skey = self.cookies[self.cookies.find('p_skey=') + 7: self.cookies.find(';', self.cookies.find('p_skey='))]
        h = 5381
        for i in p_skey:
            h += (h << 5) + ord(i)
        print('g_tk', h & 2147483647)
        self.g_tk = h & 2147483647

    def get_unilikeKey(self, mood_detail):
        allunikey = []
        jsonData = json.loads(mood_detail)
        for item in jsonData['msglist']:
            # print(item.keys())
            if 'pic' in item:
                itemKey = item['pic']
                if 'curlikekey' in itemKey[0]:
                    unikey = itemKey[0]['curlikekey'].split('^||^')
                    print('unikey:' + unikey[0])
                    allunikey.append(unikey[0])
        return allunikey


def connect_redis():
    pool = redis.ConnectionPool(host="127.0.0.1", port=6379)
    re = redis.Redis(connection_pool=pool)
    return re

def doAnalysis(fileName, commentNumber, commentList):
    # re = connect_redis()
    # data = re.get("QQ")
    # data = data.decode('utf-8').replace('\\', '')
    # print(data)
    f = open(fileName, encoding='utf-8')
    data = json.load(f)
    agreeDict = []
    for item in data['msglist']:
        print(item['content'])
        # print(item.keys())
        time_local = time.localtime(item['created_time'])
        # 转换成新的时间格式(2016-05-05 20:28:54)
        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        print(dt)
        # print(item['pic'])

        if 'pic' in item:
            itemKey = item['pic']
            if 'curlikekey' in itemKey[0]:
                unikey = itemKey[0]['curlikekey'].split('^||^')
                # print(unikey)
        if 'commentlist' in item:
            commentNumber.append(len(item['commentlist']))
            for item2 in item['commentlist']:
                if item2['name'] in commentList:
                    commentList[item2['name']] +=1
                else:
                    commentList[item2['name']] = 1
                # print(item2['name'])
        else:
            commentNumber.append(0)


    f.close()

def getFileName():
    commentList = {}
    commentNumber = []
    pos = 0
    while pos < 1700:
        fileName = 'data' + str(pos) + '.json'
        doAnalysis(fileName, commentNumber, commentList)
        pos += 20
    f = open('agree.json', encoding='utf-8')
    data = json.load(f)
    totalAgree = 0
    agreeNick = {}
    agreeNumberList = []
    for item in data:
        item = json.loads(item)
        uin_data = item['data']
        totalAgree += int(uin_data['total_number'])
        agreeNumberList.append(uin_data['total_number'])
        # print(str(agreeNumberList))
        for item_uin in uin_data['like_uin_info']:
            if item_uin['nick'] in agreeNick:
                agreeNick[item_uin['nick']] += 1
            else:
                agreeNick[item_uin['nick']] = 1
    agreeNumberList.sort(reverse=True)
    commentNumber.sort(reverse=True)
    print("累计点赞数：" + str(totalAgree))
    print("平均点赞数" + str(totalAgree / 1700))
    print("点赞次数" + str(agreeNumberList))
    print("点赞的人：" + str(sorted(agreeNick.items(), key= lambda item2: item2[1], reverse=True)))
    # print("评论数:" + str(commentNumber))
    print("给我评论的人：" + str(sorted(commentList.items(), key=lambda nameItem: nameItem[1], reverse=True)))
    print("finish")
    f.close()

if __name__ == '__main__':
    # sp = Spider()
    # sp.login()
    # print("Login success")
    # sp.get_mood_detail()
    getFileName()