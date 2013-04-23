#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
 * This file is part of GCGetData
 * Copyright (C) 2011 David Hoffmann
 *
 * GCGetData is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation, version 2.
 *
 * AndNaviki is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with AndNaviki; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

# TODO
#exiftool -exif:gpslatitude=52.000000 -exif:gpslatituderef=N -exif:gpslongitude=010.000000 -exif:gpslongituderef=E p10.jpg 

class GeoCache(object):
    def __init__(self):
        self.Latitude = ''
        self.Longitude = ''
        self.Created = ''
        self.ShortDesc = ''
        self.ShortDescIsHtml = False
        self.LongDesc = ''
        self.LongDescIsHtml = False
        self.Hint = ''
        self.ID = ''
        self.GCCode = ''
        self.Label = ''
        self.Owner = ''
        self.Difficulty = ''
        self.Terrain = ''
        self.Type = ''
        self.Container = ''
        self.Country = ''
        self.State = ''
        self.Guid = ''
        self.Archived = False
        self.Available = True
        self.Logs = []
        
class LogDetail(object):
    def __init__(self):
        self.Date = ''
        self.Type = ''
        self.FinderID = ''
        self.Finder = ''
        self.LogID = ''
        self.Text = ''

class WayPoint(object):
    def __init__(self):
        self.Latitude = None
        self.Longitude = None
        self.Created = None
        self.Name = None
        self.Comment = None
        self.Description = None
        self.Url = None
        self.UrlName = None
        self.Sym = None
        self.Type = None        

import sys, getopt, time, logging, random, json, tempfile, os.path

def help():
    print """Bitte die folgenden Parameter in der gleichen Reihenfolge anwenden.
    -u USERNAME -p PASSWORT -c COUNT LAT,LNG
    -u USERNAME -p PASSWORT -c 10 52.235524,10.542667
    """
    
def RandomWait():
    rndTime = random.uniform(5, 15)
    
    if (DEBUG):
        logging.debug("RandomWait - Start - %f", rndTime)
        
    time.sleep(rndTime)
    
    if (DEBUG):
        logging.debug("RandomWait - Ende")

def GetRandomUserAgent():
    # list of browsers
    browsers = [ "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.41 Safari/534.7", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.91 Chrome/12.0.742.91 Safari/534.30" ]
    
    # randomize browsers
    random.shuffle(browsers)

    # get first random browser
    curBrowser = browsers[0]

    if (DEBUG):
        logging.debug("Current Browser: " + curBrowser)
    
    return curBrowser

def GCLogin(browser, userLogin, userPassword):
    if (DEBUG):
        logging.debug("GC Login - Start")
    
    try:
        RandomWait()
        url = "http://geocaching.com/login/"
        browser.open(url)
        logging.debug(url)
        
        browser.select_form(nr = 0)
        browser["ctl00$ContentBody$tbUsername"] = userLogin
        browser["ctl00$ContentBody$tbPassword"] = userPassword
        RandomWait()
        browser.submit(name='ctl00$ContentBody$btnSignIn')
        
        browserResponse = browser.response().read()
        
        if (re.search("You are signed in as", browserResponse)):
            logging.debug("Login ok")
            return True
        else:
            logging.warn("Login failed")
            logging.debug(browserResponse)
            return False
    except Exception, ex:
        logging.error("GC Login failed - ex: " + str(ex))
        sys.exit(1)        
    
    if (DEBUG):
        logging.debug("GC Login - Ende")
        
def DownloadSendToGPS(browser, cacheUID, cacheDetail):
    if (DEBUG):
        logging.debug("GC download sendtogps - Start - " + cacheUID)

    browserResponse = ""
    
    try:
        RandomWait()
        url = "http://www.geocaching.com/seek/sendtogps.aspx?guid=" + cacheUID
        browser.open(url)
        
        logging.debug(url)
        
        browserResponse = browser.response().read()
        
    except Exception, ex:
        logging.error("GC download sendtogps failed - ex: " + str(ex))
        
    if browserResponse and browserResponse != "":
                
        # --- pt.latitude = 52.235556;
        reLat = re.compile("pt.latitude = (\d*?\.\d*?);")
        mLat = reLat.search(browserResponse)
        
        if mLat:
            cacheDetail.Latitude = float(mLat.group(1).strip())
            
            if DEBUG:
                logging.debug("GC latitude: " + str(cacheDetail.Latitude))
        else:
            logging.warn("SendToGPS - latitude not found")
            
        # --- pt.longitude = 10.543611;
        reLng = re.compile("pt.longitude = (\d*?\.\d*?);")
        mLng = reLng.search(browserResponse)
        
        if mLng:
            cacheDetail.Longitude = float(mLng.group(1).strip())
            
            if DEBUG:
                logging.debug("GC longitude: " + str(cacheDetail.Longitude))
        else:
            logging.warn("SendToGPS - longitude not found")
        
        # --- pt.created     = '2008-03-25T00:00:00';
        reDate = re.compile("pt.created     = \'(.*?)\';")
        mDate = reDate.search(browserResponse)
        
        if mDate:
            cacheDetail.Created = mDate.group(1)
            
            if DEBUG:
                logging.debug("GC date: " + cacheDetail.Created)
        else:
            logging.warn("SendToGPS - created not found")
        
        # --- pt.id = 'GC1AJ40';
        reGCCode = re.compile("pt.id = \'(.*?)\';")
        mGCCode = reGCCode.search(browserResponse)
        
        if mGCCode:
            cacheDetail.GCCode = mGCCode.group(1)
            
            if DEBUG:
                logging.debug("GC GCCode: " + cacheDetail.GCCode)
        else:
            logging.warn("SendToGPS - GCCode not found")
        
        # --- pt.label = 'Geschichte der Ari 1';
        reLabel = re.compile("pt.label = \'(.*?)\';")
        mLabel = reLabel.search(browserResponse)
        
        if mLabel:
            cacheDetail.Label = mLabel.group(1)
            
            if cacheDetail.Label and cacheDetail.Label != "":
                cacheDetail.Label = HTMLEncode(cacheDetail.Label)
                cacheDetail.Label = cacheDetail.Label.replace("\\'", "'")
            
            if DEBUG:
                logging.debug("GC label: " + cacheDetail.Label)
        else:
            logging.warn("SendToGPS - label not found")
            
        # --- pt.owner       = 'kiowan';
        reOwner = re.compile("pt.owner       = \'(.*?)\';")
        mOwner = reOwner.search(browserResponse)
        
        if mOwner:
            cacheDetail.Owner = mOwner.group(1)
            
            if DEBUG:
                logging.debug("GC owner: " + cacheDetail.Owner)
        else:
            logging.warn("SendToGPS - owner not found")
                    
        # --- pt.difficulty = 1;
        reDifficulty = re.compile("pt.difficulty = (.*?);")
        mDifficulty = reDifficulty.search(browserResponse)
        
        if mDifficulty:
            cacheDetail.Difficulty = mDifficulty.group(1)
            
            if DEBUG:
                logging.debug("GC difficulty: " + cacheDetail.Difficulty)
        else:
            logging.warn("SendToGPS - difficulty not found")
            
        # --- pt.terrain = 1;
        reTerrain = re.compile("pt.terrain = (.*?);")
        mTerrain = reTerrain.search(browserResponse)
        
        if mTerrain:
            cacheDetail.Terrain = mTerrain.group(1)
            
            if DEBUG:
                logging.debug("GC terrain: " + cacheDetail.Terrain)
        else:
            logging.warn("SendToGPS - terrain not found")
            
        # --- pt.type = 'Traditional Cache';
        reType = re.compile("pt.type = \'(.*?)\';")
        mType = reType.search(browserResponse)
        
        if mType:
            cacheDetail.Type = mType.group(1)
            
            if DEBUG:
                logging.debug("GC type: " + cacheDetail.Type)
        else:
            logging.warn("SendToGPS - type not found")
            
        # --- pt.container   = 'Micro';
        reContainer = re.compile("pt.container   = \'(.*?)\';")
        mContainer = reContainer.search(browserResponse)
        
        if mContainer:
            cacheDetail.Container = mContainer.group(1)
            
            if DEBUG:
                logging.debug("GC container: " + cacheDetail.Container)
        else:
            logging.warn("SendToGPS - Container not found")
        
        # --- pt.country     = 'Germany';
        reCountry = re.compile("pt.country     = \'(.*?)\';")
        mCountry = reCountry.search(browserResponse)
        
        if mCountry:
            cacheDetail.Country = mCountry.group(1)
            
            if DEBUG:
                logging.debug("GC country: " + cacheDetail.Country)
        else:
            logging.warn("SendToGPS - country not found")
            
        # --- pt.state       = 'Niedersachsen';
        reState = re.compile("pt.state       = \'(.*?)\';")
        mState = reState.search(browserResponse)
        
        if mState:
            cacheDetail.State = mState.group(1)
            
            if DEBUG:
                logging.debug("GC state: " + cacheDetail.State)
        else:
            logging.warn("SendToGPS - state not found")
        
    if (DEBUG):
        logging.debug("GC download sendtogps - Ende - " + cacheUID)
    
        
        
def DownloadCacheDetails(browser, cacheUID, cacheDetail, waypoints):
    
    if (DEBUG):
        logging.debug("GC Download Cache Details - Start - " + cacheUID)
    
    browserResponse = ""
    try:
        RandomWait()
        url = "http://www.geocaching.com/seek/cache_details.aspx?guid=" + cacheUID + "&log=y&decrypt=y"
        browser.open(url)
        
        logging.debug(url)
        
        browserResponse = browser.response().read()
        
        logging.fatal(browserResponse)
        
    except Exception, ex:
        logging.error("GC DownloadCacheDetails failed - ex: " + str(ex))
        
    if browserResponse and browserResponse != "":
        
        # --- cache id - log.aspx?ID=
        reGCID = re.compile("log.aspx\?ID=(.*?)\"", re.S)
        mGCID = reGCID.search(browserResponse)
        
        if mGCID:
            cacheDetail.ID = mGCID.group(1).strip()
            
            if DEBUG:
                logging.debug("GC GCID: " + cacheDetail.ID)
        else:
            logging.warn("Details - GC ID not found")
                
        # --- short desc
        reShortDesc = re.compile("\<span id=\"ctl00_ContentBody_ShortDescription\"\>(.*?)\</span\>", re.S)
        mShortDesc = reShortDesc.search(browserResponse)
        
        if mShortDesc:
            shortDesc = mShortDesc.group(1).strip()
            tmpShortDesc = shortDesc.replace('''<br />''', '''\n''')
            tmpShortDesc = shortDesc.replace('''<br>''', '''\n''')
            
            if shortDesc.find("<") > -1:
                cacheDetail.ShortDescIsHtml = True
                cacheDetail.ShortDesc = HTMLEncode(shortDesc)
            else:
                cacheDetail.ShortDesc = tmpShortDesc
            
            if DEBUG:
                logging.debug("GC shortDesc: " + cacheDetail.ShortDesc)
        else:
            logging.warn("Details - shortDesc not found")
        
        # --- long desc
        reLongDesc = re.compile("\<span id=\"ctl00_ContentBody_LongDescription\"\>(.*?)\</span\>\r\n            \r\n        \</div\>", re.S)
        mLongDesc = reLongDesc.search(browserResponse)
        
        if mLongDesc:
            longDesc = mLongDesc.group(1).strip()
            tmpLongDesc = longDesc.replace('''<br />''', '''\n''')
            tmpLongDesc = tmpLongDesc.replace('''<br>''', '''\n''')
            
            if longDesc.find("<") > -1:
                cacheDetail.LongDescIsHtml = True
                cacheDetail.LongDesc = HTMLEncode(longDesc)
            else:
                cacheDetail.LongDesc = tmpLongDesc
            
            if DEBUG:
                logging.debug("GC longDesc: " + cacheDetail.LongDesc)
        else:
            logging.warn("Details - longDesc not found")

        # --- hint
        reHint = re.compile("\<div id=\"div_hint\".*?\>(.*?)\</div\>", re.S)
        mHint = reHint.search(browserResponse)
        
        if mHint:
            cacheDetail.Hint = mHint.group(1).strip()
            cacheDetail.Hint = cacheDetail.Hint.replace('''<br />''', '''\n''')
            cacheDetail.Hint = cacheDetail.Hint.replace('''<br>''', '''\n''')
            cacheDetail.Hint = HTMLEncode(cacheDetail.Hint)
            
            if DEBUG:
                logging.debug("GC hint: " + cacheDetail.Hint)
        else:
            logging.warn("Details - hint not found")
            
        # --- unavailable
        reUnavailable = re.compile("\<strong\>Cache Issues:\<\/strong\>\<\/p\>\<ul class=\"OldWarning\"\>\<li\>This cache is temporarily unavailable.", re.S)
        mUnavailable = reUnavailable.search(browserResponse)
        
        if mUnavailable:
            cacheDetail.Available = False
            
            if DEBUG:
                logging.debug("GC unavailable: " + str(cacheDetail.Available))
        else:
            cacheDetail.Available = True
            
        # --- archived
        reArchived = re.compile("This cache has been archived", re.S)
        mArchived = reArchived.search(browserResponse)
        
        if mArchived:
            cacheDetail.Archived = True
            cacheDetail.Active = False
            
            if DEBUG:
                logging.debug("GC archived: " + str(cacheDetail.Archived))
        else:
            cacheDetail.Archived = False
            cacheDetail.Active = True

        # --- logs - jsonline
        reLogJson = re.compile("initalLogs = \{(.*?)\};", re.S)
        mLogJson = reLogJson.search(browserResponse)
        
        if mLogJson:
            # load json
            jsonLineL = "{" + mLogJson.group(1).strip() + "}"
            cacheDetail = GetJsonLog(cacheDetail, jsonLineL)
                        
            if DEBUG:
                logging.debug("GC log json: " + jsonLineL)
        else:
            logging.warn("Details - Log Json not found")
            
        # Waypoints suchen
        reWaypoints = re.compile('cmapAdditionalWaypoints = \[\{(.+?)\}\];')
        mWaypoints = reWaypoints.search(browserResponse)
        
        if mWaypoints:
            jsonLineW = "[{" + mWaypoints.group(1).strip() + "}]"
            waypoints= GetJsonWaypoints(waypoints, jsonLineW)

            logging.debug("GC waypoints json: " + jsonLineW)
            
    if (DEBUG):
        logging.debug("GC Download Cache Details - Ende - " + cacheUID)
        
    return cacheDetails            
        

def GetJsonLog(cacheDetail, jsonLine):
    
    try:
        j = json.loads(jsonLine)
        
        nCount = 0
        logs = []
        
        for logJItem in (j["data"]):
            
            # 25 Log Einträge müssen reichen.
            if nCount >= 25:
                break
            
            nCount += 1
            logDetail = LogDetail()
            
            logDetail.LogID = logJItem["LogID"]
            logDetail.Type = logJItem["LogType"].encode("utf-8")
            logDetail.Date = logJItem["Visited"][6:10] + "-" + logJItem["Visited"][3:5] + "-" + logJItem["Visited"][0:2]
            logDetail.Date = logDetail.Date.encode("utf-8")
            
            logDetail.Text = logJItem["LogText"].encode("utf-8")
            if logDetail.Text and logDetail.Text != "":
                logDetail.Text = logDetail.Text.replace("<br />", "\n")
                logDetail.Text = logDetail.Text.replace("<br>", "\n")
                logDetail.Text = HTMLEncode(logDetail.Text)
            
            logDetail.FinderID = logJItem["AccountID"]
            logDetail.Finder = HTMLEncode(logJItem["UserName"].encode("utf-8"))
            
            logs.append(logDetail)

        if logs:
            cacheDetail.Logs = logs
            
            if DEBUG:
                logging.debug("GC found " + str(nCount) +" logs - (max 50)")
        
    except Exception, ex:
        logging.error("GC GetJsonLog - ex: " + str(ex))
    
    return cacheDetail

def GetJsonWaypoints(waypoints, jsonLine):
    try:
        if jsonLine and len(jsonLine) > 0:
            j = json.loads(jsonLine)
        
        for wJItem in (j):
            wp = WayPoint()
            wp.Latitude = float(wJItem['lat'])
            wp.Longitude = float(wJItem['lng'])
            
            if wJItem['name']:
                reName = re.compile('(.*?) \( (.*?) \)')
                mName = reName.search(wJItem['name'])
                
                if mName:
                    wp.Comment = mName.group(1).strip()
                    wp.Type = mName.group(2).strip()
            
            waypoints.append(wp)
            
    except Exception, ex:
        logging.error('GC GetJsonWaypoints - ex: ' + str(ex))
        
    return waypoints

def SearchNearest(browser, lat, lng, amount, isGetMystery):
    if (DEBUG):
        logging.debug("GC SearchStart - Start " + str(lat) + ","+ str(lng) + " count: " + str(amount))
    
    cacheDetailLinks = []
    nIndex = 1
    browserResponse = ""
    foundEnough = False
    
    while nIndex < 100 and foundEnough == False:
        try:
            
            # Beim ersten Mal die Seite direkt aufrufen
            if nIndex == 1:
                RandomWait()
                url = "http://www.geocaching.com/seek/nearest.aspx?lat=" + lat + "&lng=" + lng + "&ex=1&cFilter=9a79e6ce-3344-409c-bbe9-496530baf758&children=n"
                browser.open(url)
                
                logging.debug(url)
                
                browserResponse = browser.response().read()
                
                logging.debug("### SEARCH NEAREST ###\n" + browserResponse)
                
                # Search total records
                reTotalRecords = re.compile("Total Records: <b>([0-9]*?)</b>")
                matchTotalRecords = reTotalRecords.search(browserResponse) 
                
                if (matchTotalRecords):
                    if (DEBUG):
                        logging.debug("GC Total Records: " + matchTotalRecords.group(1))
            
            # Link "Next" aufrufen
            else:
                if browserResponse and browserResponse <> "":
                    reNextLink = re.compile("ctl00\$ContentBody\$pgrTop\$ctl08")
                    matchNextLink = reNextLink.search(browserResponse) 

                    if matchNextLink:
                        
                        if DEBUG:
                            logging.debug("GC Next Link found")
                            
                        browser.select_form(nr=0)
                        browser.set_all_readonly(False)
                        browser["__EVENTTARGET"] = "ctl00$ContentBody$pgrTop$ctl08"
                        

                        for each in browser.form.controls[:]:
                            if each.name == "ctl00$ContentBody$uxDownloadLoc":
                                browser.form.controls.remove(each)
    
                        RandomWait()
                        browser.submit()
                        
                        browserResponse = browser.response().read()
                    else:
                        logging.debug("GC Next Link NOT found")
                        logging.debug(browserResponse)
                        
                        # Schleife beenden
                        foundEnough = True
                    
            reCacheDetailLink = re.compile("cache_details\.aspx\?guid=(.*?)\"\ class=\"lnk\"><img.*?(\d{1})\.gif\".*?class=\"SearchResultsWptType\"(.*?)</tr>", re.S)
            matchCacheDetailLinks = re.findall(reCacheDetailLink, browserResponse)
                    
            if matchCacheDetailLinks:
                for m in matchCacheDetailLinks:
                    if len(cacheDetailLinks) < amount:
                        if m[2].find("Premium Member Only Cache") == -1:
                            if (m[1] != "8" or isGetMystery == True):
                                logging.debug("GC Cache Detail UID: " + m[0])
                                cacheDetailLinks.append(m[0])
                            else:
                                logging.debug("GC Mystery Cache Detail UID: " + m[0] + " wird ausgelassen")
                        else:
                            logging.info(m[0] + " = ist ein Premium Member only cache und wird ausgelassen.")
                    else:
                        foundEnough = True
                        break;
                        
        except Exception, ex:
            logging.error("GC SearchStart failed - ex: " + str(ex))
            sys.exit(1)  
            
        nIndex = nIndex +1  
    
    if (DEBUG):
        logging.debug("GC SearchStart - Ende")
        
    return cacheDetailLinks

def WriteGPXOutput(cacheDetails, waypoints):
    
    minLat = None
    maxLat = None
    minLng = None
    maxLng = None
    
    for cache in (cacheDetails):
        if (minLat is None) or (minLat > cache.Latitude):
            minLat = cache.Latitude

        if (maxLat is None) or (maxLat < cache.Latitude):
            maxLat = cache.Latitude
    
        if (minLng is None) or (minLng > cache.Longitude):
            minLng = cache.Longitude

        if (maxLng is None) or (maxLng < cache.Longitude):
            maxLng = cache.Longitude

    for wp in (waypoints):
        if (minLat is None) or (minLat > wp.Latitude):
            minLat = wp.Latitude

        if (maxLat is None) or (maxLat < wp.Latitude):
            maxLat = wp.Latitude
    
        if (minLng is None) or (minLng > wp.Longitude):
            minLng = wp.Longitude

        if (maxLng is None) or (maxLng < wp.Longitude):
            maxLng = wp.Longitude
    
    gpxOutput = '''<?xml version="1.0" encoding="utf-8"?>
<gpx xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0" creator="Groundspeak, Inc. All  Rights Reserved. http://www.groundspeak.com" xsi:schemaLocation="http://www.topografix.com/GPX/1/0  http://www.topografix.com/GPX/1/0/gpx.xsd http://www.groundspeak.com/cache/1/0  http://www.groundspeak.com/cache/1/0/cache.xsd" xmlns="http://www.topografix.com/GPX/1/0">
    <name>Braunschweig</name>
    <desc>Geocache file generated by GCGetData</desc>
    <author>Groundspeak</author>
    <email>contact@groundspeak.com</email>
    <url>http://www.geocaching.com</url>
    <urlname>Geocaching - High Tech Treasure Hunting</urlname>
    <time></time>
    <keywords>cache, geocache, groundspeak</keywords>
    <bounds minlat="''' + str(minLat) + '''" minlon="''' + str(minLng) + '''" maxlat="''' + str(maxLat) + '''" maxlon="''' + str(maxLng) + '''" />
'''
    
    for cache in (cacheDetails):
        gpxOutput += '''    <wpt lat="''' + str(cache.Latitude) + '''" lon="''' + str(cache.Longitude) + '''">
        <time>''' + cache.Created + '''Z</time>
        <name>''' + cache.GCCode + '''</name>
        <desc>''' + cache.Label + ''' by ''' + cache.Owner + ''', ''' + cache.Type + '''(''' + cache.Difficulty + '''/''' + cache.Terrain + ''')</desc>
        <url>http://www.geocaching.com/seek/cache_details.aspx?guid=''' + cache.Guid + '''</url>
        <urlname>''' + cache.Label + '''</urlname>
        <sym>Geocache</sym>
        <type>Geocache|''' + cache.Type + '''</type>
        <groundspeak:cache id="''' + cache.ID + '''" available="''' + str(cache.Available) + '''" archived="''' + str(cache.Archived) + '''" xmlns:groundspeak="http://www.groundspeak.com/cache/1/0">
            <groundspeak:name>''' + cache.Label + '''</groundspeak:name>
            <groundspeak:placed_by>''' + cache.Owner + '''</groundspeak:placed_by>
            <groundspeak:owner id="">''' + cache.Owner + '''</groundspeak:owner>
            <groundspeak:type>''' + cache.Type + '''</groundspeak:type>
            <groundspeak:container>''' + cache.Container + '''</groundspeak:container>
            <groundspeak:difficulty>''' + cache.Difficulty + '''</groundspeak:difficulty>
            <groundspeak:terrain>''' + cache.Terrain + '''</groundspeak:terrain>
            <groundspeak:country>''' + cache.Country + '''</groundspeak:country>
            <groundspeak:state>''' + cache.State + '''</groundspeak:state>
            <groundspeak:short_description html="''' + str(cache.ShortDescIsHtml) + '''">''' + cache.ShortDesc + '''</groundspeak:short_description>
            <groundspeak:long_description html="''' + str(cache.LongDescIsHtml) + '''">''' + cache.LongDesc + '''</groundspeak:long_description>
            <groundspeak:encoded_hints>''' + cache.Hint + '''</groundspeak:encoded_hints>
            <groundspeak:logs>
'''
        
        for log in (cache.Logs):
            gpxOutput += '''                <groundspeak:log id="''' + str(log.LogID) + '''">
                    <groundspeak:date>''' + log.Date + '''T00:00:00Z</groundspeak:date>
                    <groundspeak:type>''' + log.Type + '''</groundspeak:type>
                    <groundspeak:finder id="''' + str(log.FinderID) + '''">''' + str(log.Finder) + '''</groundspeak:finder>
                    <groundspeak:text encoded="False">''' + log.Text + '''</groundspeak:text>
                </groundspeak:log>
'''
        gpxOutput += '''            </groundspeak:logs>
        </groundspeak:cache>
    </wpt>
'''
    for w in (waypoints):
        gpxTmpOutput = ''
        try:
            gpxTmpOutput = '''    <wpt lat="''' + str(w.Latitude) + '''" lon="''' + str(w.Longitude) + '''">
        <name>''' + w.Comment + '''</name>
        <cmt>''' + w.Comment + '''</cmt>
        <sym>''' + w.Type + '''</sym>
        <type>Waypoint|''' + w.Type + '''</type>
    </wpt>
'''
            gpxTmpOutput = gpxTmpOutput.encode('utf-8')
        except Exception, ex:
            logging.fatal(ex)
            
        if gpxTmpOutput and gpxTmpOutput != '':
            gpxOutput += gpxTmpOutput

    gpxOutput += '''</gpx>'''
    
    return gpxOutput
    
def HTMLEncode(string):
    '''this method return a string whit html tags encoded'''
    
    s = cgi.escape(string, True)
    s = s.replace('''&quot;''', '''"''')
    
    return s

def SignOff(browser):
    logging.debug("SignOff")
    RandomWait()

    url = "http://www.geocaching.com/login/default.aspx?RESET=Y"
    browser.open(url)
    
    logging.debug(url)
    
    browser.response().read()

if __name__ == '__main__':
    
    try:
        args = sys.argv[1:]
        opts, args = getopt.gnu_getopt(args, "u:p:c:d:m:", ["help"])
    except getopt.GetoptError:
        # print help information and exit:
        help()
        sys.exit(2)
        
    DEBUG = False
    
    UserLogin = ''
    UserPassword = ''
    Amount = 10
    
    IsGetMystery = False
    MysteryLat = None
    MysteryLng = None
    
    for o, a in opts:
        if o == "-u":
            UserLogin = a
        if o == "-p":
            UserPassword = a
        if o == "--help" or o == "-h":
            help()
            sys.exit()
        if o == "-d":
            DEBUG = True
        if o == "-c":
            Amount = int(a)
            
        if o == "-m":
            IsGetMystery = True
            MysteryLat, MysteryLng = a.split(",")
    
    if len(args) < 1:
        help()
        sys.exit()

    logFile = os.path.join(tempfile.gettempdir(), 'gcGetData.log')
    logLevel = logging.INFO
    
    if DEBUG:
        logLevel = logging.DEBUG

    logging.basicConfig(level=logLevel,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename= logFile,
                        filemode='w')
        
    lat, lng = args[0].split(",")
    
    if len(args) >= 3:
        MaxDistance = args[2]
    else:
        MaxDistance = "999"
        
    if IsGetMystery:
        Amount = 1
        
    if (DEBUG):
        logging.debug("Programm Start")
    
    import re, mechanize, cgi
    
    userAgent = GetRandomUserAgent()
    
    browser = mechanize.Browser()
    browser.set_handle_equiv(True)
    browser.set_handle_redirect(True)
    browser.set_handle_referer(True)
    browser.set_handle_robots(False)
    browser.addheaders = [('User-Agent', userAgent)]
    
    if (DEBUG):
        browser.set_debug_http(False)
        browser.set_debug_redirects(False)
        browser.set_debug_responses(False)
    
    logging.info("GC Login")
    
    if (GCLogin(browser, UserLogin, UserPassword) == False):
        sys.exit(3)
    
    logging.info("GC SearchNearest")    
    cacheDetailUIDs = SearchNearest(browser, lat, lng, Amount, IsGetMystery)
       
    cacheDetails = []
    waypoints = []
    
    nCount = 1
    
    if (cacheDetailUIDs) and (len(cacheDetailUIDs) > 0):
        for cacheUID in cacheDetailUIDs:
            
            logging.info("Download GC (" + str(nCount) + "/" + str(Amount) + ")")
            nCount = nCount + 1
            
            cacheDetail = GeoCache()
            cacheDetail.Guid = cacheUID
            try:
                DownloadCacheDetails(browser, cacheUID, cacheDetail, waypoints)
                DownloadSendToGPS(browser, cacheUID, cacheDetail)
                
                # Change Mystery-Coordinates
                if IsGetMystery:
                    cacheDetail.Latitude = MysteryLat
                    cacheDetail.Longitude = MysteryLng
                
                cacheDetails.append(cacheDetail)
            except Exception, ex:
                logging.error("GC Download Details - ex: " + str(ex))

    SignOff(browser)    
    gpxOutput = WriteGPXOutput(cacheDetails, waypoints)
    
    print gpxOutput
    
    logging.info("Programm Ende")
