# -*- coding: utf-8 -*-

import json
import re
import sys
import traceback
import bs4
import requests
import os
import subprocess
import base64


env_dist = os.environ # environ是在os.py中定义的一个dict environ = {}

if(env_dist.__contains__('NOLOG') and env_dist['NOLOG'] == '1'):
    sys.stdout = open(os.devnull, 'w')

def loadCookie(sess):    
    if(env_dist.__contains__('COOKIEKEY')):
        logger.info("KEYExist");
    else:
        logger.info("NOKEY")
        exit(1)
    cookies = env_dist['COOKIEKEY']
    cookies = cookies.replace("\n", "")
    cookies = json.loads(cookies)
    sess.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
    for cookie in cookies:
        sess.cookies[cookie["name"]] = cookie["value"]


def getTbs(sess):
    success = False
    while not success:
        try:
            res = sess.get("http://tieba.baidu.com/dc/common/tbs", timeout=5)
            success = True
        except Exception:
            traceback.print_exc()
            pass
    tbs = res.json()["tbs"]
    return tbs


def getThreadList(sess, startPageNumber, endPageNumber):
    threadList = list()
    tidExp = re.compile(r"/([0-9]{1,})")
    pidExp = re.compile(r"pid=([0-9]{1,})")

    for number in range(startPageNumber, endPageNumber + 1):
        logger.info("Now in thread page", number)
        url = "http://tieba.baidu.com/i/i/my_tie?pn=" + str(number)
        res = sess.get(url)

        if res.url == "http://static.tieba.baidu.com/tb/error.html?ErrType=1":
            logger.info("Cookie has been expried, Please update it")
            return
        

        # fo = open("S___" + str(number) + ".html" , "w")
        # logger.info("文件名为: ", fo.name)
        # fo.write( res.text );

        # fo.close();
        

        html = bs4.BeautifulSoup(res.text, "lxml")
        


        elements = html.find_all(name="a", attrs={"class": "thread_title"})
        for element in elements:
            logger.info(element)
            thread = element.get("href")
            threadDict = dict()
            threadDict["tid"] = tidExp.findall(thread)[0]
            threadDict["pid"] = pidExp.findall(thread)[0]
            threadList.append(threadDict)
    return threadList


def getReplyList(sess, startPageNumber, endPageNumber):
    replyList = list()
    tidExp = re.compile(r"/([0-9]{1,})")
    pidExp = re.compile(r"pid=([0-9]{1,})")  # 主题贴和回复都为 pid
    cidExp = re.compile(r"cid=([0-9]{1,})")  # 楼中楼为 cid

    for number in range(startPageNumber, endPageNumber + 1):
        logger.info("Now in reply page", number)
        url = "http://tieba.baidu.com/i/i/my_reply?pn=" + str(number)
        res = sess.get(url)

        if res.url == "http://static.tieba.baidu.com/tb/error.html?ErrType=1":
            logger.info("Cookie has been expried, Please update it")
            return

        html = bs4.BeautifulSoup(res.text, "lxml")
        elements = html.find_all(name="a", attrs={"class": "b_reply"})
        for element in elements:
            reply = element.get("href")
            if reply.find("pid") != -1:
                tid = tidExp.findall(reply)
                pid = pidExp.findall(reply)
                cid = cidExp.findall(reply)
                replyDict = dict()
                replyDict["tid"] = tid[0]

                if cid and cid[0] != "0":  # 如果 cid != 0, 这个回复是楼中楼, 否则是一整楼的回复
                    replyDict["pid"] = cid[0]
                else:
                    replyDict["pid"] = pid[0]
                replyList.append(replyDict)
    return replyList


def getFollowedBaList(sess, startPageNumber, endPageNumber):
    baList = list()
    for number in range(startPageNumber, endPageNumber + 1):
        logger.info("Now in followed Ba page", number)
        url = "http://tieba.baidu.com/f/like/mylike?pn=" + str(number)
        res = sess.get(url)

        if res.url == "http://static.tieba.baidu.com/tb/error.html?ErrType=1":
            logger.info("Cookie has been expried, Please update it")
            return

        html = bs4.BeautifulSoup(res.text, "lxml")
        elements = html.find_all(name="span")
        for element in elements:
            baDict = dict()
            baDict["fid"] = element.get("balvid")
            baDict["tbs"] = element.get("tbs")
            baDict["fname"] = element.get("balvname")
            baList.append(baDict)
    return baList


def getConcerns(sess, startPageNumber, endPageNumber):
    concernList = list()
    for number in range(startPageNumber, endPageNumber + 1):
        logger.info("Now in concern page", number)
        url = "http://tieba.baidu.com/i/i/concern?pn=" + str(number)
        res = sess.get(url)

        if res.url == "http://static.tieba.baidu.com/tb/error.html?ErrType=1":
            logger.info("Cookie has been expried, Please update it")
            return

        html = bs4.BeautifulSoup(res.text, "lxml")
        elements = html.find_all(name="input", attrs={"class": "btn_unfollow"})
        for element in elements:
            concernDict = dict()
            concernDict["cmd"] = "unfollow"
            concernDict["tbs"] = element.get("tbs")
            concernDict["id"] = element.get("portrait")
            concernList.append(concernDict)
    return concernList


def getFans(sess, startPageNumber, endPageNumber):
    fansList = list()
    tbsExp = re.compile(r"tbs : '([0-9a-zA-Z]{16})'")  # 居然还有一个短版 tbs.... 绝了
    
    for number in range(startPageNumber, endPageNumber + 1):
        logger.info("Now in fans page", number)
        url = "http://tieba.baidu.com/i/i/fans?pn=" + str(number)
        res = sess.get(url)

        if res.url == "http://static.tieba.baidu.com/tb/error.html?ErrType=1":
            logger.info("Cookie has been expried, Please update it")
            return

        tbs = tbsExp.findall(res.text)[0]
        html = bs4.BeautifulSoup(res.text, "lxml")
        elements = html.find_all(name="input", attrs={"class": "btn_follow"})
        for element in elements:
            fanDict = dict()
            fanDict["cmd"] = "add_black_list"
            fanDict["tbs"] = tbs
            fanDict["portrait"] = element.get("portrait")
            fansList.append(fanDict)
    return fansList


def deleteThread(sess, threadList):
    url = "https://tieba.baidu.com/f/commit/post/delete"
    count = 0

    for threadDict in threadList:
        logger.info("Now deleting", threadDict)
        postData = dict()
        postData["tbs"] = getTbs(sess)
        for idName in threadDict:
            postData[idName] = threadDict[idName]
        res = sess.post(url, data=postData)

        # logger.info(res.text)
        logger.info(res.text.encode('latin-1').decode('unicode_escape'))


        if res.json()["err_code"] == 220034:  #达到上限
            logger.info("Limit exceeded, exiting.")
            return count
        else:
            count += 1

    return count


def deleteFollowedBa(sess, baList):
    url = "https://tieba.baidu.com/f/like/commit/delete"

    for ba in baList:
        logger.info("Now unfollowing", ba)
        res = sess.post(url, data=ba)
        logger.info(res.text)


def deleteConcern(sess, concernList):
    url = "https://tieba.baidu.com/home/post/unfollow"

    for concern in concernList:
        logger.info("Now unfollowing", concern)
        res = sess.post(url, data=concern)
        logger.info(res.text)


def deleteFans(sess, fansList):
    url = "https://tieba.baidu.com/i/commit"

    for fans in fansList:
        logger.info("Now blocking fans", fans)
        res = sess.post(url, data=fans)
        logger.info(res.text)


def check(obj):
    if obj is None:
        exit(0)


def main():
    config = open("/".join([sys.path[0], "config.json"])).read().replace("\n", "")
    config = json.loads(config)
    sess = requests.session()
    loadCookie(sess)

    if config["thread"]["enable"]:
        threadList = getThreadList(sess, config["thread"]["start"], config["thread"]["end"])
        check(threadList)
        logger.info("Collected", len(threadList), "threads", end="\n\n")
        count = deleteThread(sess, threadList)
        logger.info(count, "threads has been deleted", end="")
        if len(threadList) != count:
            logger.info(", left", len(threadList) - count, "threads due to limit exceeded.", end="\n\n")
        else:
            logger.info(".", end="\n\n")
        
    if config["reply"]["enable"]:
        replyList = getReplyList(sess, config["reply"]["start"], config["reply"]["end"])
        check(replyList)
        logger.info("Collected", len(replyList), "replys", end="\n\n")
        count = deleteThread(sess, replyList)
        logger.info(count, "replys has been deleted", end="")
        if len(replyList) != count:
            logger.info(", left", len(replyList) - count, "replys due to limit exceeded.", end="\n\n")
        else:
            logger.info(".", end="\n\n")

    if config["followedBa"]["enable"]:
        baList = getFollowedBaList(sess, config["followedBa"]["start"], config["followedBa"]["end"])
        check(baList)
        logger.info("Collected", len(baList), "followed Ba", end="\n\n")
        deleteFollowedBa(sess, baList)
        logger.info(len(baList), "followed Ba has been deleted.", end="\n\n")

    if config["concern"]["enable"]:
        concernList = getConcerns(sess, config["concern"]["start"], config["concern"]["end"])
        check(concernList)
        logger.info("Collected", len(concernList), "concerns", end="\n\n")
        deleteConcern(sess, concernList)
        logger.info(len(concernList), "concerns has been deleted.", end="\n\n")

    if config["fans"]["enable"]:
        fansList = getFans(sess, config["fans"]["start"], config["fans"]["end"])
        check(fansList)
        logger.info("Collected", len(fansList), "fans", end="\n\n")
        deleteFans(sess, fansList)
        logger.info(len(fansList), "fans has been deleted.", end="\n\n")


if __name__ == "__main__":
    main()
