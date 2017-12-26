#!/usr/bin/env python3

import sys
import json
import requests
import re

#User preferences
crawltimeout = 10 #When
crawldepth = 10 #How deep the search should be. 0 means recurse infinitely
linkperpage = crawldepth #How many unique links from a page should be followed. 
                         #0 means follow all of the links from a page


def getpagetext(session, url, timeout=crawltimeout):
    r = session.get(url,timeout=timeout)
    return r.text

def findmatch(regexp, cache):
    matchlist = regexp.findall(cache)
    matchset = frozenset(matchlist)
    return matchset

def crawlsite(session,rooturl,maxdepth=crawldepth,linkread=linkperpage):
    #Generic regex for emails. Kinda dumb.
    mailreg = re.compile('( \
                            (?:[A-Z0-9_\-\.]+) \
                            @ \
                            (?:[A-Z0-9_\-\.]+) \
                            (?: \
                              \.(?:[A-Z]{2,5}) \
                            ){1,5} \
                          )', flags=re.I|re.X)
    #Regex for links on html page.
    linkreg = re.compile('href=" \
                          ( \
                            (?:'+ rooturl + ')? \
                            /[^/\s>] \
                            [^\s>]*? \
                          )"', flags=re.I|re.X)
    ignorelist = [
        # images
        'mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif',
        'tiff', 'ai', 'drw', 'dxf', 'eps', 'ps', 'svg', 'ico',
        # audio
        'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',
        # video
        '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
        'm4a',
        # other
        'css', 'js', 'pdf', 'doc', 'docx', 'exe', 'bin', 'rss', 'zip', 'rar', 
        'ppt', 'pptx', 'djvu', 'rtf'
    ]

    #Simplifying the links we got for easier handling. Most of this stuff should increase performance of script
    #by skipping pages that we shouldn't go to. Is probably beneficial computationally.
    def reconstructlinks(linkset):
        newlinkset = set()
        for i in linkset:
            cont = False
            #Ignoring some commonly known binary file formats, or types of text that shouldn't contain anything interesting
            for j in ignorelist:
                if re.search(j+r'(\?[A-Z0-9\-\_\.=]*)?$',i,re.I):
                    cont = True
                    break
            if cont == True:
                continue
            #If a link is relative adding root of the site to beginning for requests API and for easier exclusion of already followed links
            if re.match(rooturl,i,re.I) == None:
                newi = rooturl + i
            else:
                newi = i
            #Deleting anchors at the end of file if there are some
            if re.search(r'#[^/]*$',newi,re.I) == None:
                newi = newi
            else:
                newi = newi.rpartition('#')[0];
            newlinkset.add(newi)
        return newlinkset

    def crawliter(url=rooturl,depth=0):
        cache = getpagetext(session,url)
        mailset = findmatch(mailreg,cache)
        linkset = findmatch(linkreg,cache)
        newlinkset = reconstructlinks(linkset)
        newlinkset = newlinkset-crawliter.usedlink #No need to visit links already visited
        crawliter.usedlink = crawliter.usedlink|newlinkset #Writing down used links
        if maxdepth == 0 or depth < maxdepth: #If not too deep, crawl further
            counter = 0
            for i in newlinkset:
                if linkread == 0 or counter>=linkread: #If followed too many links on this page, skip the rest
                    break
                mailset=mailset|crawliter(i,depth+1) #Adding emails to set
                counter=counter+1
        return mailset

    crawliter.usedlink = set() #List of links already visited, used to avoid duplication of effort
    return crawliter


def main(argv):
    #mailset = set()
    s = requests.Session()
    rooturl = "http://www.csd.tsu.ru"
    mailset = crawlsite(s,rooturl)()
    s.close()
    print(json.dumps({rooturl: list(mailset)}))

    s = requests.Session()
    rooturl = "https://mosigra.ru"
    mailset = crawlsite(s,rooturl)()
    s.close()
    print(json.dumps({rooturl: list(mailset)}))

    return

if __name__ == "__main__":
    main(sys.argv)
