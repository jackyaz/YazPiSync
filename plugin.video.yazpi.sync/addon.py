import subprocess, xbmcaddon, xbmc

yazpisyncaddonpath = xbmcaddon.Addon().getAddonInfo("path")
iconpath = yazpisyncaddonpath + "/icon.png"
erroriconpath = yazpisyncaddonpath + "/resources/media/erroricon.png"

xbmc.executebuiltin("Notification(YazPi Sync,Addon starting,2000," + iconpath + ")")
xbmc.sleep( 2000 )

pathtosh =  yazpisyncaddonpath + "/resources/lib/PiSync.sh"
subprocess.call(["chmod","+x",pathtosh])

if xbmcaddon.Addon().getSetting("boolfolder1") == "true" and xbmcaddon.Addon().getSetting("boolfolder2") == "true":
	subprocess.call(["sudo",pathtosh,yazpisyncaddonpath,xbmcaddon.Addon().getSetting("export1"),xbmcaddon.Addon().getSetting("folder1"),xbmcaddon.Addon().getSetting("export2"),xbmcaddon.Addon().getSetting("folder2")])
elif xbmcaddon.Addon().getSetting("boolfolder1") == "true" and xbmcaddon.Addon().getSetting("boolfolder2") == "false":
	subprocess.call(["sudo",pathtosh,yazpisyncaddonpath,xbmcaddon.Addon().getSetting("export1"),xbmcaddon.Addon().getSetting("folder1")])
elif xbmcaddon.Addon().getSetting("boolfolder1") == "false" and xbmcaddon.Addon().getSetting("boolfolder2") == "true":
	subprocess.call(["sudo",pathtosh,yazpisyncaddonpath,xbmcaddon.Addon().getSetting("export2"),xbmcaddon.Addon().getSetting("folder2")])
else:
	xbmc.executebuiltin("Notification(YazPi Sync,Check settings - no folders enabled!,2000," + erroriconpath + ")")