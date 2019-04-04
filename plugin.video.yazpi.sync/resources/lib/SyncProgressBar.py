import xbmc, xbmcaddon, xbmcgui, shutil, sys, subprocess, time, os

def formattime(timeinseconds):
	timeinseconds = float(timeinseconds)
	if timeinseconds < 60:
		timeremaining = str(int(timeinseconds)) + "s"
	elif timeinseconds >= 60 and timeinseconds < 3600:
		timeremaining = str(int(timeinseconds/60)) + "m " + str(int(timeinseconds - (int(timeinseconds/60) * 60))) + "s"
	else:
		timeremaining = "Go make dinner or something"
	
	return timeremaining

def formatfilesize(filesize):
	filesize = float(filesize)
	if filesize < 1024:
		filesize = str(filesize) + "B"
	elif filesize >= 1024 and filesize < 1048576:
		filesize = '%.2f' % (filesize/1024) + "KB"
	elif filesize >= 1048576 and filesize < 1073741824:
		filesize = '%.2f' % ((filesize/1024)/1024) + "MB"
	elif filesize >= 1073741824 and filesize < 1099511627776:
		filesize = '%.2f' % (((filesize/1024)/1024)/1024) + "GB"
	else:
		filesize = '%.2f' % ((((filesize/1024)/1024)/1024)/1024) + "TB"
		
	return filesize

def copywithprogress(src, dst, filenumber, filesize, startprogress, filecount, filesizeremaining, buffersize=16*1024*1024):
	filename = src.rsplit("/",1)[1]
	buffersize = min(buffersize,filesize)
	if(buffersize == 0):
		buffersize = 16*1024
	with open(src, 'rb') as fsrc:
		with open(dst, 'wb') as fdst:
			copied = 0
			ctime = time.time()
			while True:
				buf = fsrc.read(buffersize)
				if not buf:
					break
				fdst.write(buf)
				copied += len(buf)
				percent = startprogress + float ( ( ( copied / float(filesize) ) * 100) / float(filecount))
				
				diftime = time.time() - ctime
				speed = buffersize / diftime
				
				global totalspeeds
				totalspeeds += speed
				
				global numberofspeeds
				numberofspeeds += 1
				
				avgspeed = totalspeeds/numberofspeeds
				
				heading = "Syncing file " + str(filenumber) + "/" + str(filecount) + " - " + formatfilesize(filesizeremaining - copied) + " left - " + formatfilesize(avgspeed) + "/s" + " - ETA: " + formattime((filesizeremaining - copied) / avgspeed)
				message = filename + " - " + formatfilesize(filesize - copied) + " - "  + formatfilesize(speed) + "/s" + " - ETA: " + formattime((filesize - copied)/speed)
				
				progress.update( int(percent), heading, message )
				
				ctime = time.time()
	shutil.copystat(src,dst)

script, filecount, totalfilesize, filenames, strsourcelist, strdestlist = sys.argv

progress = xbmcgui.DialogProgressBG()

if int(filecount) > 0:
	filenamesfile = open(filenames, "r")
	strfilenames = filenamesfile.read()
	filenamesfile.close()
	os.remove(filenames)
	arrfilelist = strfilenames.split(":")
	arrsourcefilenames = arrfilelist[0].split("|")
	arrdestfilenames = arrfilelist[1].split("|")
	arrfilesizes = arrfilelist[2].split("|")

if len(strsourcelist) > 0:
	arrsourcelist = strsourcelist.split("|")
	arrdestlist = strdestlist.split("|")

	progress.create("YazPi Sync", "Cleaning up missing files")
	xbmc.sleep( 500 )

	i = 0
	while i < len(arrsourcelist):
		
		subprocess.call(["rsync","-a","--delete","--existing","--ignore-existing","--no-inc-recursive","--exclude='*.db'",str(arrsourcelist[i]).replace("???",","),str(arrdestlist[i]).replace("???",",")])
		
		i = i + 1

	progress.update( 100,"YazPi Sync", "Cleanup complete" )
	xbmc.sleep( 500 )
	progress.close()

if int(filecount) > 0:

	progress = xbmcgui.DialogProgressBG()
	progress.create("YazPi Sync", "Syncing " + filecount + " files - Total size to sync: " + formatfilesize(totalfilesize))
	xbmc.sleep( 1500 )

	filesizeremaining=totalfilesize
	numberofspeeds = 0
	totalspeeds = 0

	i = 1
	while i <= int(filecount):
		
		filename = arrsourcefilenames[i - 1].rsplit("/",1)[1].replace("???",",")
		filesize = arrfilesizes[i - 1]
		
		percent = int(((i-1) / float(filecount)) * 100)
		
		if i == 1:
			heading = "Syncing file " + str(i) + "/" + filecount + " - " + formatfilesize(filesizeremaining) + " left - ETA: calculating..."
		else:
			avgspeed = totalspeeds/numberofspeeds
			heading = "Syncing file " + str(i) + "/" + filecount + " - " + formatfilesize(filesizeremaining) + " left - " + formatfilesize(avgspeed) + "/s" + " - ETA: " + formattime(filesizeremaining/avgspeed)
		
		message = filename + " - " + formatfilesize(filesize)
		
		progress.update( percent, heading, message )
		
		subprocess.call(["mkdir","-p", str(arrdestfilenames[i - 1].rsplit("/",1)[0]).replace("???",",")])
		copywithprogress(str(arrsourcefilenames[i - 1]).replace("???",","), str(arrdestfilenames[i - 1]).replace("???",","), i, int(filesize), int(percent), int(filecount), int(filesizeremaining))
		
		filesizeremaining = int(filesizeremaining) - int(filesize)
		
		if progress.isFinished():
			break
		i = i + 1
	
	progress.update( 100,"YazPi Sync", "Syncing files completed" )
	xbmc.sleep( 1500 )
	progress.close()

if len(strsourcelist) > 0:
	arrsourcelist = strsourcelist.split("|")
	i = 0
	while i < len(arrsourcelist):
		
		subprocess.call(["sudo","umount",str(arrsourcelist[i])])
		
		i = i + 1

progress.create("YazPi Sync", "Finishing changes to disk(s)")
progress.update( 100,"YazPi Sync", "Finishing changes to disk(s)" )
xbmc.sleep( 1000 )
subprocess.call(["sync"])
progress.close()

iconpath = xbmcaddon.Addon("plugin.video.yazpi.sync").getAddonInfo("path") + "/icon.png"

xbmc.executebuiltin("Notification(YazPi Sync,Sync from server completed,2000," + iconpath + ")")
xbmc.sleep( 2000 )
xbmc.executebuiltin("UpdateLibrary(video)")