#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import common
import random
import threading

pluginhandle = common.pluginhandle
xbmc = common.xbmc
xbmcplugin = common.xbmcplugin
urllib = common.urllib
urllib2 = common.urllib2
sys = common.sys
xbmcgui = common.xbmcgui
re = common.re
json = common.json
addon = common.addon
os = common.os
hashlib = common.hashlib
Dialog = xbmcgui.Dialog()
platform = 0
if xbmc.getCondVisibility('system.platform.windows'): platform = 1
if xbmc.getCondVisibility('system.platform.linux'): platform = 2
if xbmc.getCondVisibility('system.platform.osx'): platform = 3
if xbmc.getCondVisibility('system.platform.android'): platform = 4
playMethod = int(addon.getSetting("playmethod"))
amazonUrl = common.BASE_URL + "/dp/" + common.args.asin
browser = int(addon.getSetting("browser"))
 
def PLAYVIDEO():
    if not platform:
        Dialog.notification(common.__plugin__, 'Betriebssytem wird von diesem Addon nicht unterstützt', xbmcgui.NOTIFICATION_ERROR)
        return
    waitsec = int(addon.getSetting("clickwait")) * 1000
    pin = addon.getSetting("pin")
    waitpin = int(addon.getSetting("waitpin")) * 1000
    waitprepin = int(addon.getSetting("waitprepin")) * 1000
    trailer = common.args.trailer
    isAdult = int(common.args.adult)
    pininput = fullscr = False
    if addon.getSetting("pininput") == 'true': pininput = True
    if addon.getSetting("fullscreen") == 'true': fullscr = True
    xbmc.Player().stop()
    
    if trailer == '1':
        videoUrl = amazonUrl + "/?autoplaytrailer=1"
    else:
        videoUrl = amazonUrl + "/?autoplay=1"

    if playMethod == 2 or platform == 4:
        AndroidPlayback(common.args.asin, trailer)
        return
    else:
        if addon.getSetting('logging') == 'true': videoUrl += '&playerDebug=true'
        url = getCmdLine(videoUrl)
        if not url:
            Dialog.notification(common.__plugin__, common.getString(30198), xbmcgui.NOTIFICATION_ERROR)
            addon.openSettings()
            return
        common.Log('Executing: %s' % url)
        if platform == 1:
            process = subprocess.Popen(url, startupinfo=getStartupInfo())
        else:
            process = subprocess.Popen(url, shell=True)
        
    if isAdult == 1 and pininput:
        if fullscr: waitsec = waitsec*0.75
        else: waitsec = waitprepin
        xbmc.sleep(int(waitsec))
        Input(keys=pin)
        waitsec = 0
        if fullscr: xbmc.sleep(waitpin)
    
    if fullscr:
        xbmc.sleep(int(waitsec))
        if isAdult == 0: pininput = True
        if pininput:
            if browser != 0:
                Input(keys='f')
            else:
                Input(mousex=-1,mousey=350,click=2)
                xbmc.sleep(500)
                Input(mousex=9999,mousey=350)
            
    Input(mousex=9999,mousey=-1)
    myWindow = window()
    myWindow.modal(process)

def AndroidPlayback(asin, trailer):
    manu = ''
    if os.access('/system/bin/getprop', os.X_OK):
        manu = subprocess.Popen(['getprop', 'ro.product.manufacturer'], stdout=subprocess.PIPE).communicate()[0].strip()
    common.Log('Manufacturer: %s' % manu)
    #Start Activity Intent { act=android.intent.action.VIEW cat=[android.intent.category.DEFAULT,android.intent.category.BROWSABLE] dat=B00UXZ61HI cmp=com.amazon.avod/.playbackclient.EdPlaybackActivity }
    #am start -a android.intent.action.VIEW -d B00UXZ61HI -c android.intent.category.DEFAULT -c android.intent.category.BROWSABLE -n com.amazon.avod/.playbackclient.EdPlaybackActivity
    if manu == 'Amazon':
        cmp = 'com.amazon.avod/com.amazon.avod.playbackclient.EdPlaybackActivity'
        pkg = 'com.fivecent.amazonvideowrapper'
        act = ''
        url = asin
    else:
        cmp = 'com.amazon.avod.thirdpartyclient/com.amazon.avod.thirdpartyclient.ThirdPartyPlaybackActivity'
        pkg = 'com.amazon.avod.thirdpartyclient'
        act = 'android.intent.action.VIEW'
        url = common.BASE_URL + '/piv-apk-play?asin=' + asin
        if trailer == '1': url += '&playTrailer=T'

    subprocess.Popen(['log', '-p', 'v', '-t', 'Kodi-Amazon', 'Manufacturer: '+manu])
    subprocess.Popen(['log', '-p', 'v', '-t', 'Kodi-Amazon', 'Starting App: %s Video: %s' % (pkg, url)])
    common.Log('Playing: %s' % url)
    xbmc.executebuiltin('StartAndroidActivity("%s", "%s", "", "%s")' % (pkg, act, url))

def getCmdLine(videoUrl):
    scr_path = addon.getSetting("scr_path")
    br_path = addon.getSetting("br_path").strip()
    scr_param = addon.getSetting("scr_param").strip()
    kiosk = addon.getSetting("kiosk")
    appdata = addon.getSetting("ownappdata")
    cust_br = addon.getSetting("cust_path")
    
    if playMethod == 1:
        if not os.path.exists(scr_path): return ''
        return scr_path + ' ' + scr_param.replace('{f}', getPlaybackInfo(amazonUrl)).replace('{u}', videoUrl)

    os_paths = [('C:\\Program Files\\', 'C:\\Program Files (x86)\\'), ('/usr/bin/', '/usr/local/bin/'), 'open -a ']
    # path(win,lin,osx), kiosk, profile, args
    br_config = [[('Internet Explorer\\iexplore.exe', '', ''), '-k ', '', ''], 
                 [('Google\\Chrome\\Application\\chrome.exe', 'google-chrome', '"Google Chrome"'), '--kiosk ', '--user-data-dir=', '--start-maximized --disable-translate --disable-new-tab-first-run --no-default-browser-check --no-first-run '],
                 [('Mozilla Firefox\\firefox.exe', 'firefox', 'firefox'), '', '-profile ', ''],
                 [('Safari\\Safari.exe', '', 'safari'), '', '', '']]
    
    if platform != 3 and cust_br == 'false':
        for path in os_paths[platform-1]:
            path += br_config[browser][0][platform-1]
            if os.path.exists(path): 
                br_path = path
                break
    if not os.path.exists(br_path): return ''
    if platform == 3 and cust_br == 'false': br_path = os_paths[2] + br_config[browser][0][2]
    
    br_path += ' ' + br_config[browser][3]
    if kiosk == 'true': br_path += br_config[browser][1]
    if appdata == 'true' and br_config[browser][2]: 
        br_path += br_config[browser][2] + '"' + os.path.join(common.pldatapath,str(browser)) + '" '
    br_path += '"' + videoUrl + '"'
    return br_path
    
def Input(mousex=0,mousey=0,click=0,keys=False,delay='200'):
    screenWidth = int(xbmc.getInfoLabel('System.ScreenWidth'))
    screenHeight = int(xbmc.getInfoLabel('System.ScreenHeight'))
    keys_only = sc_only = keybd = ''
    if mousex == -1: mousex = screenWidth/2
    if mousey == -1: mousey = screenHeight/2

    spec_keys = {'{EX}': ('!{F4}', 'control+shift+q', 'kd:cmd t:q ku:cmd'),
                 '{SPC}': ('{SPACE}', 'space', 't:p'),
                 '{LFT}': ('{LEFT}', 'Left', 'kp:arrow-left'),
                 '{RGT}': ('{RIGHT}', 'Right', 'kp:arrow-right'),
                 '{U}': ('{UP}', 'Up', 'kp:arrow-up'),
                 '{DWN}': ('{DOWN}', 'Down', 'kp:arrow-down'),
                 '{BACK}': ('{BS}', 'BackSpace', 'kp:delete'),
                 '{RET}': ('{ENTER}', 'Return', 'kp:return')}
                 
    if keys:
        keys_only = keys
        for sc in spec_keys:
            while sc in keys:
                keys = keys.replace(sc, spec_keys[sc][platform-1]).strip()
                keys_only = keys_only.replace(sc, '').strip()
        sc_only = keys.replace(keys_only, '').strip()

    if platform == 1:
        app = os.path.join(common.pluginpath, 'tools', 'userinput.exe' )
        mouse = ' mouse %s %s' % (mousex,mousey)
        mclk = ' ' + str(click)
        keybd = ' key %s %s' % (keys,delay)
    elif platform == 2:
        app = 'xdotool'
        mouse = ' mousemove %s %s' % (mousex,mousey)
        mclk = ' click --repeat %s 1' % click
        if keys_only: keybd = ' type --delay %s %s' % (delay, keys_only)
        if sc_only: 
            if keybd: keybd += ' && ' + app
            keybd += ' key ' + sc_only
    elif platform == 3:
        app = 'cliclick'
        mouse = ' m:'
        if click == 1: mouse = ' c:'
        elif click == 2: mouse = ' dc:'
        mouse += '%s,%s' % (mousex,mousey)
        mclk = ''
        keybd = ' -w %s' % delay
        if keys_only: keybd += ' t:%s' % keys_only
        if keys <> keys_only: keybd += ' ' + sc_only

    if keys:
        cmd = app + keybd
    else:
        cmd = app + mouse
        if click: cmd += mclk
    common.Log('Run command: %s' % cmd)
    subprocess.call(cmd, shell=True)

def getStartupInfo():
    si = subprocess.STARTUPINFO()
    si.dwFlags = subprocess.STARTF_USESHOWWINDOW
    return si
    
def getStreams(suc, data):
    if not suc:
        return ''
        
    for cdn in data['audioVideoUrls']['avCdnUrlSets']:
        for urlset in cdn['avUrlInfoList']:
            data = common.getURL(urlset['url'])
            fps_string = re.compile('frameRate="([^"]*)').findall(data)[0]
            fr = round(eval(fps_string + '.0'), 3)
            return str(fr).replace('.0','')
    return ''
    
def getPlaybackInfo(url):
    if addon.getSetting("framerate") == 'false': return ''
    Dialog.notification(xbmc.getLocalizedString(20186), '', xbmcgui.NOTIFICATION_INFO, 60000, False)
    values = getFlashVars(url)
    if not values: return ''
    fr = getStreams(*getUrldata('catalog/GetPlaybackResources', values, extra=True))
    Dialog.notification(xbmc.getLocalizedString(20186), '', xbmcgui.NOTIFICATION_INFO, 10, False)
    return fr

def getFlashVars(url):
    cookie = common.mechanizeLogin()
    showpage = common.getURL(url, useCookie=cookie)
    #common.WriteLog(showpage, 'flashvars', 'w')
    if not showpage:
        Dialog.notification(common.__plugin__, Error('CDP.InvalidRequest'), xbmcgui.NOTIFICATION_ERROR)
        return False
    values = {}
    search = {'asin'       : '"pageAsin":"(.*?)"',
              'sessionID'  : "ue_sid='(.*?)'",
              'marketplace': "ue_mid='(.*?)'",
              'customer'   : '"customerID":"(.*?)"'}
    if 'var config' in showpage:
        flashVars = re.compile('var config = (.*?);',re.DOTALL).findall(showpage)
        flashVars = json.loads(unicode(flashVars[0], errors='ignore'))
        values = flashVars['player']['fl_config']['initParams']
    else:
        for key, pattern in search.items():
            result = re.compile(pattern, re.DOTALL).findall(showpage)
            if result: values[key] = result[0]
    
    for key in values.keys():
        if not values.has_key(key):
            Dialog.notification(common.getString(30200), common.getString(30210), xbmcgui.NOTIFICATION_ERROR)
            return False

    values['deviceTypeID']  = 'AOAGZA014O5RE'
    values['userAgent']     = common.UserAgent
    values['deviceID']      = common.hmac.new(common.UserAgent, common.gen_id(), hashlib.sha224).hexdigest()
    rand = 'onWebToken_' + str(random.randint(0,484))
    pltoken = common.getURL(common.BASE_URL + "/gp/video/streaming/player-token.json?callback=" + rand, useCookie=cookie)
    try:
        values['token']  = re.compile('"([^"]*).*"([^"]*)"').findall(pltoken)[0][1]
    except:
        Dialog.notification(common.getString(30200), common.getString(30201), xbmcgui.NOTIFICATION_ERROR)
        return False
    return values
    
def getUrldata(mode, values, format='json', devicetypeid=False, version=1, firmware='1', opt='', extra=False, useCookie=False):
    if not devicetypeid:
        devicetypeid = values['deviceTypeID']
    url  = common.ATV_URL + '/cdp/' + mode
    url += '?asin=' + values['asin']
    url += '&deviceTypeID=' + devicetypeid
    url += '&firmware=' + firmware
    url += '&customerID=' + values['customer']
    url += '&deviceID=' + values['deviceID']
    url += '&marketplaceID=' + values['marketplace']
    url += '&token=' + values['token']
    url += '&format=' + format
    url += '&version=' + str(version)
    url += opt
    if extra:
        url += '&resourceUsage=ImmediateConsumption&videoMaterialType=Feature&consumptionType=Streaming&desiredResources=AudioVideoUrls&deviceDrmOverride=CENC&deviceStreamingTechnologyOverride=DASH&deviceProtocolOverride=Http&deviceBitrateAdaptationsOverride=CVBR%2CCBR&audioTrackId=all'
    data = common.getURL(url, common.ATV_URL.split('//')[1], useCookie=useCookie)
    if data:
        jsondata = json.loads(data)
        del data
        if jsondata.has_key('error'):
            return False, Error(jsondata['error'])
        return True, jsondata
    return False, 'HTTP Fehler'
    
def Error(data):
    code = data['errorCode']
    common.Log('%s (%s) ' %(data['message'], code), xbmc.LOGERROR)
    if 'CDP.InvalidRequest' in code:
        return common.getString(30204)
    elif 'CDP.Playback.NoAvailableStreams' in code:
        return common.getString(30205)
    elif 'CDP.Playback.NotOwned' in code:
        return common.getString(30206)
    elif 'CDP.Authorization.InvalidGeoIP' in code:
        return common.getString(30207)
    elif 'CDP.Playback.TemporarilyUnavailable' in code:
        return common.getString(30208)
    else:
        return '%s (%s) ' %(data['message'], code)
        
class window(xbmcgui.WindowDialog):
    def __init__(self):
        xbmcgui.WindowDialog.__init__(self)
        self._stopEvent = threading.Event()
        self._wakeUpThread = threading.Thread(target=self._wakeUpThreadProc)
        self._wakeUpThread.start()
        self._parentprocess = None
        self._rc = addon.getSetting("remotectrl")
        
    def _wakeUpThreadProc(self):
        while not self._stopEvent.is_set():
            xbmc.executebuiltin("playercontrol(wakeup)")
            # bit of a hack above: wakeup is actually not a valid playercontrol argument,
            # but there's no error printed if the argument isn't found and any playercontrol
            # causes the DPMS/idle timeout to reset itself
            self._stopEvent.wait(60)

    def stopWakeupThread(self):
        self._stopEvent.set()
        self._wakeUpThread.join()

    def modal(self, process):
        self._parentprocess = process
        self.doModal()
    
    def close(self):
        self.stopWakeupThread()
        xbmcgui.WindowDialog.close(self)

    def onAction(self, action):
        ACTION_SELECT_ITEM = 7
        ACTION_PARENT_DIR = 9
        ACTION_PREVIOUS_MENU = 10
        ACTION_PAUSE = 12
        ACTION_STOP = 13
        ACTION_SHOW_INFO = 11
        ACTION_SHOW_GUI = 18
        ACTION_MOVE_LEFT = 1
        ACTION_MOVE_RIGHT = 2
        ACTION_MOVE_UP = 3
        ACTION_MOVE_DOWN = 4
        ACTION_PLAYER_PLAY = 79
        ACTION_VOLUME_UP = 88
        ACTION_VOLUME_DOWN = 89
        ACTION_MUTE = 91
        ACTION_NAV_BACK = 92
        ACTION_BUILT_IN_FUNCTION = 122
        KEY_BUTTON_BACK = 275
        
        exit = False
        if self._parentprocess:
            self._parentprocess.poll()
            if self._parentprocess.returncode != None: exit = True

        if self._rc == 'false' and not exit: return
        
        actionId = action.getId()
        if action in [ACTION_SHOW_GUI, ACTION_STOP, ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK, KEY_BUTTON_BACK]:
            if exit:
                if action in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK, KEY_BUTTON_BACK]: Input(keys='{BACK}')
            else: Input(keys='{EX}')
            self.close()
        elif action in [ACTION_SELECT_ITEM, ACTION_PLAYER_PLAY, ACTION_PAUSE]:
            Input(keys='{SPC}')
        elif action==ACTION_MOVE_LEFT:
            Input(keys='{LFT}')
        elif action==ACTION_MOVE_RIGHT:
            Input(keys='{RGT}')
        elif action==ACTION_MOVE_UP:
            Input(keys='{U}')
        elif action==ACTION_MOVE_DOWN:
            Input(keys='{DWN}')
        elif action==ACTION_SHOW_INFO:
            Input(9999,0)
            xbmc.sleep(800)
            Input(9999,-1)
        # numkeys for pin input
        elif actionId > 57 and actionId < 68:
            strKey = str(actionId-58)
            Input(keys=strKey)

        if exit: self.close()