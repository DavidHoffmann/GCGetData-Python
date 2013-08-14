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
1'''

# TODO
#exiftool -exif:gpslatitude=52.000000 -exif:gpslatituderef=N -exif:gpslongitude=010.000000 -exif:gpslongituderef=E p10.jpg 

import logging, re, random, time, cgi, json

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

class GCGetData(object):
    def __init__(self, debug):
        import os.path, tempfile

        logFile = os.path.join(tempfile.gettempdir(), 'GCGetData.log')

        if debug:
            logLevel = logging.DEBUG
        else:
            logLevel = logging.INFO

        logging.basicConfig(level = logLevel,
            format = '%(asctime)s %(levelname)-8s %(message)s',
            datefmt = '%a, %d %b %Y %H:%M:%S',
            filename = logFile,
            filemode = 'w')

        self.__logging = logging

        import re, mechanize, cgi

        userAgent = self.__GetRandomUserAgent()

        self.__browser = mechanize.Browser()
        self.__browser.set_handle_equiv(True)
        self.__browser.set_handle_redirect(True)
        self.__browser.set_handle_referer(True)
        self.__browser.set_handle_robots(False)
        self.__browser.addheaders = [('User-Agent', userAgent)]

        if (debug):
            self.__browser.set_debug_http(False)
            self.__browser.set_debug_redirects(False)
            self.__browser.set_debug_responses(False)

    @staticmethod
    def Help():
        """print the commandline parameters."""

        print ("Bitte die folgenden Parameter in der gleichen Reihenfolge anwenden.")
        print (" -u USERNAME -p PASSWORT -c COUNT LAT,LNG")
        print (" -u USERNAME -p PASSWORT -c 10 52.235524,10.542667")


    def GetGPX(self, userLogin, userPassword, lat, lng, amount, isGetMystery, mysteryLat, mysteryLng):
        self.__logging.info("GC Login")

        if (self.__GCLogin(self.__browser, userLogin, userPassword) == False):
            print ("Login failed")
            sys.exit(3)

        self.__logging.info("GC SearchNearest")
        cacheDetailUIDs = self.__SearchNearest(self.__browser, lat, lng, amount, isGetMystery)

        cacheDetails = []
        waypoints = []

        nCount = 1
 
        if (cacheDetailUIDs) and (len(cacheDetailUIDs) > 0):
            for cacheUID in cacheDetailUIDs:

                self.__logging.info("Download GC (" + str(nCount) + "/" + str(amount) + ")")
                nCount = nCount + 1

                cacheDetail = GeoCache()
                cacheDetail.Guid = cacheUID
                try:
                    self.__DownloadCacheDetails(self.__browser, cacheUID, cacheDetail, waypoints)
                    self.__DownloadSendToGPS(self.__browser, cacheUID, cacheDetail)

                    # Change Mystery-Coordinates                                                                                                        
                    if isGetMystery:
                        cacheDetail.Latitude = mysteryLat
                        cacheDetail.Longitude = mysteryLng

                    cacheDetails.append(cacheDetail)
                except Exception as ex:
                    self.__logging.error("GC Download Details - ex: " + str(ex))

        self.__SignOff(self.__browser)
        return  self.__WriteGPXOutput(cacheDetails, waypoints)


    def __RandomWait(self):
        """wait 5-15 seconds."""
        rndTime = random.uniform(5, 15)
    
        self.__logging.debug("RandomWait - Start - %f", rndTime)
        
        time.sleep(rndTime)
    
        self.__logging.debug("RandomWait - Ende")


    def __GetRandomUserAgent(self):
        """return user-agent"""

        # list of browsers
        browsers = [ "Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.41 Safari/534.7", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.91 Chrome/12.0.742.91 Safari/534.30", "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)", "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0" ]
    
        # randomize browsers
        random.shuffle(browsers)

        # get first random browser
        curBrowser = browsers[0]

        self.__logging.debug("Current Browser: " + curBrowser)
    
        return curBrowser


    def __GCLogin(self, browser, userLogin, userPassword):
        """do the login at geocaching.com"""

        self.__logging.debug("GC Login - Start")
    
        try:
            self.__RandomWait()
            
            url = "http://geocaching.com/login/"
            browser.open(url)

            self.__logging.debug(url)
        
            browser.select_form(nr = 0)
            browser["ctl00$ContentBody$tbUsername"] = userLogin
            browser["ctl00$ContentBody$tbPassword"] = userPassword
            self.__RandomWait()
            browser.submit(name='ctl00$ContentBody$btnSignIn')
        
            browserResponse = browser.response().read()
        
            if (re.search("You are signed in as", browserResponse)):
                self.__logging.debug("Login ok")
                return True
            else:
                self.__logging.warn("Login failed")
                self.__logging.debug(browserResponse)
                return False
        except Exception as ex:
            self.__logging.error("GC Login failed - ex: " + str(ex))
            sys.exit(1)        
    
        self.__logging.debug("GC Login - Ende")
        

    def __DownloadSendToGPS(self, browser, cacheUID, cacheDetail):
        self.__logging.debug("GC download sendtogps - Start - " + cacheUID)

        browserResponse = ""
    
        try:
            self.__RandomWait()
            url = "http://www.geocaching.com/seek/sendtogps.aspx?guid=" + cacheUID
            browser.open(url)
        
            self.__logging.debug(url)
        
            browserResponse = browser.response().read()
        
        except Exception as ex:
            self.__logging.error("GC download sendtogps failed - ex: " + str(ex))
        
        if browserResponse and browserResponse != "":
                
            # --- pt.latitude = 52.235556;
            reLat = re.compile("pt.latitude = (\d*?\.\d*?);")
            mLat = reLat.search(browserResponse)
        
            if mLat:
                cacheDetail.Latitude = float(mLat.group(1).strip())
            
                self.__logging.debug("GC latitude: " + str(cacheDetail.Latitude))
            else:
                self.__logging.warn("SendToGPS - latitude not found")
            
            # --- pt.longitude = 10.543611;
            reLng = re.compile("pt.longitude = (\d*?\.\d*?);")
            mLng = reLng.search(browserResponse)
        
            if mLng:
                cacheDetail.Longitude = float(mLng.group(1).strip())
            
                self.__logging.debug("GC longitude: " + str(cacheDetail.Longitude))
            else:
                self.__logging.warn("SendToGPS - longitude not found")
        
            # --- pt.id = 'GC1AJ40';
            reGCCode = re.compile("pt.id = \'(.*?)\';")
            mGCCode = reGCCode.search(browserResponse)
        
            if mGCCode:
                cacheDetail.GCCode = mGCCode.group(1)
            
                self.__logging.debug("GC GCCode: " + cacheDetail.GCCode)
            else:
                self.__logging.warn("SendToGPS - GCCode not found")
        
            # --- pt.label = 'Geschichte der Ari 1';
            reLabel = re.compile("pt.label = \'(.*?)\';")
            mLabel = reLabel.search(browserResponse)
        
            if mLabel:
                cacheDetail.Label = mLabel.group(1)
            
                if cacheDetail.Label and cacheDetail.Label != "":
                    cacheDetail.Label = self.__HTMLEncode(cacheDetail.Label)
                    cacheDetail.Label = cacheDetail.Label.replace("\\'", "'")
            
                self.__logging.debug("GC label: " + cacheDetail.Label)
            else:
                self.__logging.warn("SendToGPS - label not found")
            
            # --- pt.difficulty = 1;
            reDifficulty = re.compile("pt.difficulty = (.*?);")
            mDifficulty = reDifficulty.search(browserResponse)
        
            if mDifficulty:
                cacheDetail.Difficulty = mDifficulty.group(1)
            
                self.__logging.debug("GC difficulty: " + cacheDetail.Difficulty)
            else:
                self.__logging.warn("SendToGPS - difficulty not found")
            
            # --- pt.terrain = 1;
            reTerrain = re.compile("pt.terrain = (.*?);")
            mTerrain = reTerrain.search(browserResponse)
        
            if mTerrain:
                cacheDetail.Terrain = mTerrain.group(1)
            
                self.__logging.debug("GC terrain: " + cacheDetail.Terrain)
            else:
                self.__logging.warn("SendToGPS - terrain not found")
            
            # --- pt.type = 'Traditional Cache';
            reType = re.compile("pt.type = \'(.*?)\';")
            mType = reType.search(browserResponse)
        
            if mType:
                cacheDetail.Type = mType.group(1)
            
                self.__logging.debug("GC type: " + cacheDetail.Type)
            else:
                self.__logging.warn("SendToGPS - type not found")
            
        self.__logging.debug("GC download sendtogps - Ende - " + cacheUID)

    
    def __DownloadCacheDetails(self, browser, cacheUID, cacheDetail, waypoints):
    
        self.__logging.debug("GC Download Cache Details - Start - " + cacheUID)
    
        browserResponse = ""
        try:
            self.__RandomWait()
            url = "http://www.geocaching.com/seek/cache_details.aspx?guid=" + cacheUID + "&log=y&decrypt=y"
            browser.open(url)
        
            self.__logging.debug(url)
        
            browserResponse = browser.response().read()
         
            self.__logging.debug(browserResponse)
        
        except Exception as ex:
            self.__logging.error("GC DownloadCacheDetails failed - ex: " + str(ex))
        
        if browserResponse and browserResponse != "":
        
            # --- cache id - log.aspx?ID=
            reGCID = re.compile("log.aspx\?ID=(.*?)\"", re.S)
            mGCID = reGCID.search(browserResponse)
        
            if mGCID:
                cacheDetail.ID = mGCID.group(1).strip()
            
                self.__logging.debug("GC GCID: " + cacheDetail.ID)
            else:
                self.__logging.warn("Details - GC ID not found")
                
            # --- owner
            reOwnerCreated = re.compile("\) was created by (.*?) on (.*?)\.", re.S)
            mOwnerCreated = reOwnerCreated.search(browserResponse)

            if mOwnerCreated:
                cacheDetail.Owner = mOwnerCreated.group(1)
                cacheDetail.Created = mOwnerCreated.group(2)

                self.__logging.debug("GC Owner: " + cacheDetail.Owner)
                self.__logging.debug("GC Created: " + cacheDetail.Created)
            else:
                self.__logging.warn("Details - GC Owner not found")
                self.__logging.warn("Details - GC Created not found")

            # --- Container

            reContainer = re.compile("It&#39;s a (.*?) size geocache, with difficult", re.S)
            mContainer = reContainer.search(browserResponse)
            
            if mContainer:
                cacheDetail.Container = mContainer.group(1)
                
                self.__logging.debug("GC Container: " + cacheDetail.Container)
            else:
                self.__logging.warn("Details - GC Container not found")

            # --- country, state
            reStateCountry = re.compile("It&#39;s located in (.*?), (.*?)\.", re.S)
            mStateCountry = reStateCountry.search(browserResponse)

            if mStateCountry:
                cacheDetail.State = mStateCountry.group(1)
                cacheDetail.Country = mStateCountry.group(2)

                self.__logging.debug("GC State: " + cacheDetail.State)
                self.__logging.debug("GC Country: " + cacheDetail.Country)
            else:
                self.__logging.warn("Details - State not found")
                self.__logging.warn("Details - Country not found")

            # --- short desc
            reShortDesc = re.compile("\<span id=\"ctl00_ContentBody_ShortDescription\"\>(.*?)\</span\>", re.S)
            mShortDesc = reShortDesc.search(browserResponse)
        
            if mShortDesc:
                shortDesc = mShortDesc.group(1).strip()
                tmpShortDesc = shortDesc.replace('''<br />''', '''\n''')
                tmpShortDesc = shortDesc.replace('''<br>''', '''\n''')
            
                if shortDesc.find("<") > -1:
                    cacheDetail.ShortDescIsHtml = True
                    cacheDetail.ShortDesc = self.__HTMLEncode(shortDesc)
                else:
                    cacheDetail.ShortDesc = tmpShortDesc
            
                self.__logging.debug("GC shortDesc: " + cacheDetail.ShortDesc)
            else:
                self.__logging.warn("Details - shortDesc not found")
        
            # --- long desc
            reLongDesc = re.compile("\<span id=\"ctl00_ContentBody_LongDescription\"\>(.*?)\</span\>\r\n            \r\n        \</div\>", re.S)
            mLongDesc = reLongDesc.search(browserResponse)
        
            if mLongDesc:
                longDesc = mLongDesc.group(1).strip()
                tmpLongDesc = longDesc.replace('''<br />''', '''\n''')
                tmpLongDesc = tmpLongDesc.replace('''<br>''', '''\n''')
            
                if longDesc.find("<") > -1:
                    cacheDetail.LongDescIsHtml = True
                    cacheDetail.LongDesc = self.__HTMLEncode(longDesc)
                else:
                    cacheDetail.LongDesc = tmpLongDesc
            
                self.__logging.debug("GC longDesc: " + cacheDetail.LongDesc)
            else:
                self.__logging.warn("Details - longDesc not found")

            # --- hint
            reHint = re.compile("\<div id=\"div_hint\".*?\>(.*?)\</div\>", re.S)
            mHint = reHint.search(browserResponse)
        
            if mHint:
                cacheDetail.Hint = mHint.group(1).strip()
                cacheDetail.Hint = cacheDetail.Hint.replace('''<br />''', '''\n''')
                cacheDetail.Hint = cacheDetail.Hint.replace('''<br>''', '''\n''')
                cacheDetail.Hint = self.__HTMLEncode(cacheDetail.Hint)
            
                self.__logging.debug("GC hint: " + cacheDetail.Hint)
            else:
                self.__logging.warn("Details - hint not found")
            
            # --- unavailable
            reUnavailable = re.compile("\<strong\>Cache Issues:\<\/strong\>\<\/p\>\<ul class=\"OldWarning\"\>\<li\>This cache is temporarily unavailable.", re.S)
            mUnavailable = reUnavailable.search(browserResponse)
        
            if mUnavailable:
                cacheDetail.Available = False
            
                self.__logging.debug("GC unavailable: " + str(cacheDetail.Available))
            else:
                cacheDetail.Available = True
            
            # --- archived
            reArchived = re.compile("This cache has been archived", re.S)
            mArchived = reArchived.search(browserResponse)
        
            if mArchived:
                cacheDetail.Archived = True
                cacheDetail.Active = False
            
                self.__logging.debug("GC archived: " + str(cacheDetail.Archived))
            else:
                cacheDetail.Archived = False
                cacheDetail.Active = True

            # --- logs - jsonline
            reLogJson = re.compile("initalLogs = \{(.*?)\};", re.S)
            mLogJson = reLogJson.search(browserResponse)
        
            if mLogJson:
                # load json
                jsonLineL = "{" + mLogJson.group(1).strip() + "}"
                cacheDetail = self.__GetJsonLog(cacheDetail, jsonLineL)
                        
                self.__logging.debug("GC log json: " + jsonLineL)
            else:
                self.__logging.warn("Details - Log Json not found")
            
            # Waypoints suchen
            reWaypoints = re.compile('cmapAdditionalWaypoints = \[\{(.+?)\}\];')
            mWaypoints = reWaypoints.search(browserResponse)
        
            if mWaypoints:
                jsonLineW = "[{" + mWaypoints.group(1).strip() + "}]"
                waypoints= self.__GetJsonWaypoints(waypoints, jsonLineW)

                self.__logging.debug("GC waypoints json: " + jsonLineW)
            
        self.__logging.debug("GC Download Cache Details - Ende - " + cacheUID)
        

    def __GetJsonLog(self, cacheDetail, jsonLine):
    
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
                    logDetail.Text = self.__HTMLEncode(logDetail.Text)
            
                logDetail.FinderID = logJItem["AccountID"]
                logDetail.Finder = self.__HTMLEncode(logJItem["UserName"].encode("utf-8"))
            
                logs.append(logDetail)

            if logs:
                cacheDetail.Logs = logs
            
                self.__logging.debug("GC found " + str(nCount) +" logs - (max 50)")
        
        except Exception as ex:
            self.__logging.error("GC GetJsonLog - ex: " + str(ex))
    
        return cacheDetail


    def __GetJsonWaypoints(self, waypoints, jsonLine):
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
            
        except Exception as ex:
            self.__logging.error('GC GetJsonWaypoints - ex: ' + str(ex))
        
        return waypoints


    def __SearchNearest(self, browser, lat, lng, amount, isGetMystery):
        self.__logging.debug("GC SearchStart - Start " + str(lat) + ","+ str(lng) + " count: " + str(amount))
    
        cacheDetailLinks = []
        nIndex = 1
        browserResponse = ""
        foundEnough = False
    
        while nIndex < 100 and foundEnough == False:
            try:
            
                # Beim ersten Mal die Seite direkt aufrufen
                if nIndex == 1:
                    self.__RandomWait()
                    url = "http://www.geocaching.com/seek/nearest.aspx?lat=" + lat + "&lng=" + lng + "&ex=1&cFilter=9a79e6ce-3344-409c-bbe9-496530baf758&children=n"
                    browser.open(url)
                
                    self.__logging.debug(url)
                
                    browserResponse = browser.response().read()
                
                    self.__logging.debug("### SEARCH NEAREST ###\n" + browserResponse)
                
                    # Search total records
                    reTotalRecords = re.compile("Total Records: <b>([0-9]*?)</b>")
                    matchTotalRecords = reTotalRecords.search(browserResponse) 
                
                    if (matchTotalRecords):
                        self.__logging.debug("GC Total Records: " + matchTotalRecords.group(1))
            
                # Link "Next" aufrufen
                else:
                    if browserResponse and browserResponse != "":
                        reNextLink = re.compile("ctl00\$ContentBody\$pgrTop\$ctl08")
                        matchNextLink = reNextLink.search(browserResponse) 

                        if matchNextLink:
                        
                            self.__logging.debug("GC Next Link found")
                            
                            browser.select_form(nr=0)
                            browser.set_all_readonly(False)
                            browser["__EVENTTARGET"] = "ctl00$ContentBody$pgrTop$ctl08"
                        

                            for each in browser.form.controls[:]:
                                if each.name == "ctl00$ContentBody$uxDownloadLoc":
                                    browser.form.controls.remove(each)
    
                            self.__RandomWait()
                            browser.submit()
                        
                            browserResponse = browser.response().read()
                        else:
                            self.__logging.debug("GC Next Link NOT found")
                            self.__logging.debug(browserResponse)
                        
                            # Schleife beenden
                            foundEnough = True
                    
                reCacheDetailLink = re.compile("cache_details\.aspx\?guid=(.*?)\"\ class=\"lnk\"><img.*?(\d{1})\.gif\".*?class=\"SearchResultsWptType\"(.*?)</tr>", re.S)
                matchCacheDetailLinks = re.findall(reCacheDetailLink, browserResponse)
                    
                if matchCacheDetailLinks:
                    for m in matchCacheDetailLinks:
                        if len(cacheDetailLinks) < amount:
                            if m[2].find("Premium Member Only Cache") == -1:
                                if (m[1] != "8" or isGetMystery == True):
                                    self.__logging.debug("GC Cache Detail UID: " + m[0])
                                    cacheDetailLinks.append(m[0])
                                else:
                                    self.__logging.debug("GC Mystery Cache Detail UID: " + m[0] + " wird ausgelassen")
                            else:
                                self.__logging.info(m[0] + " = ist ein Premium Member only cache und wird ausgelassen.")
                        else:
                            foundEnough = True
                            break;
                        
            except Exception as ex:
                self.__logging.error("GC SearchStart failed - ex: " + str(ex))
                sys.exit(1)  
            
            nIndex = nIndex +1  
    
        self.__logging.debug("GC SearchStart - Ende")
        
        return cacheDetailLinks


    def __WriteGPXOutput(self, cacheDetails, waypoints):
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
            except Exception as ex:
                self.__logging.fatal(ex)
            
            if gpxTmpOutput and gpxTmpOutput != '':
                gpxOutput += gpxTmpOutput

        gpxOutput += '''</gpx>'''
    
        return gpxOutput
    

    def __HTMLEncode(self, string):
        '''this method return a string whit html tags encoded'''
    
        s = cgi.escape(string, True)
        s = s.replace('''&quot;''', '''"''')
    
        return s


    def __SignOff(self, browser):
        self.__logging.debug("SignOff")
        self.__RandomWait()

        url = "http://www.geocaching.com/login/default.aspx?RESET=Y"
        browser.open(url)
    
        self.__logging.debug(url)
    
        browser.response().read()


if __name__ == '__main__':
    """main for console """

    import sys, getopt

    """get args"""
    try:
        args = sys.argv[1:]
        opts, args = getopt.gnu_getopt(args, "u:p:c:d:m:", ["help"])
    except getopt.GetoptError:
        # print help information and exit:
        GCGetData.Help()
        sys.exit(2)
        
    debug = False
    
    userlogin = ''
    userPassword = ''
    amount = 10
    
    isGetMystery = False
    mysteryLat = None
    mysteryLng = None

    maxDistance = "999"
    
    for o, a in opts:
        if o == "-u":
            userLogin = a
        if o == "-p":
            userPassword = a
        if o == "--help" or o == "-h":
            GCGetData.Help()
            sys.exit()
        if o == "-d":
            debug = True
        if o == "-c":
            amount = int(a)
            
        if o == "-m":
            isGetMystery = True
            mysteryLat, mysteryLng = a.split(",")
    
    if len(args) < 1:
        GCGetData.Help()
        sys.exit()

    lat, lng = args[0].split(",")
    
    if len(args) >= 3:
        maxDistance = args[2]
        
    if isGetMystery:
        amount = 1
        
    gcGetData = GCGetData(debug)

    # load data
    gpxOutput = gcGetData.GetGPX(userLogin, userPassword, lat, lng, amount, isGetMystery, mysteryLat, mysteryLng)
    print(gpxOutput)
    
