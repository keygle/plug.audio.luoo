# -*- coding: utf-8 -*-
import sys,urllib2,re,json,xbmcplugin, xbmcgui,gzip,StringIO,urllib,xbmcaddon
import xml.dom.minidom

plugin_url = sys.argv[0]
handle = int(sys.argv[1])
userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36'


__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo("name")

def log(txt):
    message = "%s: %s" % (__addonname__, unicode(txt).encode('utf-8'))
    print(message)
#解析xml
def getDom(url):
    return xml.dom.minidom.parse(urllib2.urlopen(url))

def getParams():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

def getHttpData(url,host="www.luoo.net",referer="http://www.luoo.net"):
    req = urllib2.Request(url)
    req.add_header("User-Agent", userAgent)
    req.add_header("Host",host)
    req.add_header("Referer",referer)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    if response.headers.get('content-encoding', None) == 'gzip':
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
    response.close()
    match = re.compile('<meta http-equiv="[Cc]ontent-[Tt]ype" content="text/html; charset=(.+?)"').findall(httpdata)
    if len(match)<=0:
        match = re.compile('meta charset="(.+?)"').findall(httpdata)
    if len(match)>0:
        charset = match[0].lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = unicode(httpdata, charset).encode('utf8')# 根据编码 解析数据
    return httpdata

#显示 落网FM 的相应的专辑
def index():
    url = "http://www.luoo.net"
    reqHtml = getHttpData(url)
    pattern = '<li><a href="([^"]+)" rel="bookmark" class="title">([^<]+)</a></li>'
    matchs = re.compile(pattern).findall(reqHtml)
    for i in matchs:
        li = xbmcgui.ListItem(unicode(i[1],'utf-8').encode('utf-8')) 
        li.setInfo(type="Music",infoLabels={'Title':unicode(i[1],'utf-8').encode('utf-8')})   
        url = plugin_url+"?act=list&listUrl="+urllib.quote_plus(i[0])
        xbmcplugin.addDirectoryItem(handle, url, li, True)
    xbmcplugin.endOfDirectory(handle)

#获得 专辑播放页里的mp3列表
def getPlayList(musicUrl):
    musicHtml = getHttpData(musicUrl)
    imgPattern = '<p style="text-align: center;"><img src="([^"]+)"'
    imgMatchs = re.compile(imgPattern).findall(musicHtml)
    playPattern = '<iframe .* src="([^"]+)"' 
    playUrl = re.compile(playPattern).findall(musicHtml)
    playXmlUrl = playUrl[0].replace('mp3player.html', 'mp3.xml') #替换相应的地址  xml里有mp3地址
    try:
        req = urllib2.urlopen(playXmlUrl)
        req.close()
    except:
        playXmlUrl = playUrl[0].replace('mp3player.html', 'mp3player.xml') #替换相应的地址  xml里有mp3地址
    
    xmlDom = getDom(playXmlUrl)
    listitemAll = xbmcgui.ListItem('播放当前专辑所有歌曲')
    listitemAll.setInfo(type="Music",infoLabels={ "Title": '播放当前专辑所有歌曲'})
    listUrl = plugin_url+"?act=playList&playXmlUrl="+urllib.quote_plus(playXmlUrl)
    xbmcplugin.addDirectoryItem(handle, listUrl, listitemAll, False)
    for node in xmlDom.getElementsByTagName('song'):
        listitem=xbmcgui.ListItem(node.getAttribute('id')+' '+node.getAttribute('title'))
        listitem.setInfo(type="Music",infoLabels={ "Title": node.getAttribute('id')+' '+node.getAttribute('title')})
        url = plugin_url+"?act=play&title="+node.getAttribute('title')+"&playUrl="+urllib.quote_plus(node.getAttribute('path'))
        xbmcplugin.addDirectoryItem(handle, url, listitem, False)
    xbmcplugin.endOfDirectory(handle)
#播放单曲音乐
def play(mp3path,title):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)  #xbmc.PLAYLIST_MUSIC 表示 audio   也可直接用 0 
    playlist.clear() #中止播放列表
    listitem=xbmcgui.ListItem(title)
    listitem.setInfo(type="Music",infoLabels={ "Title": title})
    xbmc.Player().play(mp3path,listitem)
    #playlist.add(mp3path, listitem)    
    #xbmc.Player().play(playlist)

#播放当前专辑列表里的歌曲
def playList(playXmlUrl):
    xmlDom = getDom(playXmlUrl)
    playlist = xbmc.PlayList(0)
    playlist.clear()
    for node in xmlDom.getElementsByTagName('song'):
        title = node.getAttribute('id')+' '+node.getAttribute('title')
        listitem=xbmcgui.ListItem(title)
        listitem.setInfo(type="Music",infoLabels={ "Title": title})
        playlist.add(node.getAttribute('path'), listitem)    
    xbmc.Player().play(playlist)




params = getParams()
try:
    act = params['act']
except :
    act = 'index'
try:
    listUrl = urllib.unquote_plus(params["listUrl"])
except :
    pass
try:
    playUrl = urllib.unquote_plus(params["playUrl"])
except :
    pass
try:
    title = urllib.unquote_plus(params["title"])
except :
    pass
try:
    playXmlUrl = urllib.unquote_plus(params["playXmlUrl"])
except:
    pass

if act == 'index':
    index()
if act == 'list':
    getPlayList(listUrl)
if act == 'play':
    play(playUrl,title)
if act == 'playList':
    playList(playXmlUrl)