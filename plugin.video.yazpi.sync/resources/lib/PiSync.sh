#!/bin/bash
#Script to sync files from NFS share to local destination
#Argument structure: [NFS server IP] [NFS share path] [Destination path for sync]

function getfilelistnfs(){
	#variable assignment
	MNTFLDR=$1
	NFSIP=$2
	NFSSHARE=$3
	DESTSYNCDIR=$4
	
	#check if directory for mount points already exists
	if [ ! -d "$MNTFLDR" ]; then
		mkdir -p "$MNTFLDR"
		#echo "$(date +"%Y-%m-%d %H:%M"): Mount point directory created, continuing"
	fi
	
	#echo "$(date +"%Y-%m-%d %H:%M"): Begin NFS mount check"
	sleep 2
	
	#retrieve existing NFS mounts
	NFSMOUNTED=$(mount | grep nfs | grep YazPiSync | grep "$NFSSHARE")
	
	#check if any existing NFS mounts were found. If no mount found, mount it
	if [ ${#NFSMOUNTED} -eq 0 ]; then
		if [ ! -d "$MNTFLDR/$NFSSHARE" ]; then
			mkdir -p "$MNTFLDR/$NFSSHARE"
		fi
		
		showmount -e "$NFSIP"
		
		#check if NFS mount was successful, if not, exit script
		if [ ! $? -eq 0 ]; then
			#could not mount NFS share, exit
			#echo "$(date +"%Y-%m-%d %H:%M"): NFS server $MNTFLDR/$NFSSHARE unavailable" && 
			kodi-send -a "Notification(YazPi Sync,$NFSIP/$NFSSHARE unavailable,2000,$addonpath/resources/media/erroricon.png)" > /dev/null
			sleep 2
			return
		else
			#mount the NFS share
			mount -o ro,hard,intr,retry=0 "$NFSIP:/$NFSSHARE" "$MNTFLDR/$NFSSHARE"
			
			#NFS server mounted successfully
			#echo "$(date +"%Y-%m-%d %H:%M"): NFS server $MNTFLDR/$NFSSHARE mounted"
			
			#end of NFS mounting success check
		fi
	#end of NFS mount existence checking
	fi
	
	#NFS share either existed or was successfully mounted, so we can continue
	if [ ! -d "$DESTSYNCDIR" ]; then
		#echo "$(date +"%Y-%m-%d %H:%M"): Destination path does not exist" &&
		kodi-send -a "Notification(YazPi Sync,$DESTSYNCDIR unavailable,2000,$addonpath/resources/media/erroricon.png)" > /dev/null
		sleep 2
		umount "$MNTFLDR/$NFSSHARE"
		return
	else
		rsynclog=$(rsync -ani --no-inc-recursive --exclude="*.db" "$MNTFLDR/$NFSSHARE/" "$DESTSYNCDIR")
		newFiles=$(echo "$rsynclog" | grep '>f+++++++++' | cut -d' ' -f2-)
		changedFiles=$(echo "$rsynclog" | grep -E ">f[.](.*)" | cut -d' ' -f2-)
		totalFiles="$newFiles"$'\n'"$changedFiles"
		
		filecount=0
		filesizetotal=0
		filesourcelist=""
		filedestlist=""
		filesizelist=""
		
		IFS=$'\n' 
		for file in $totalFiles; do
			rsyncitem=""
			pathlength=$(echo "$file" | tr '/' '\n' | wc -l)
			
			if [ $pathlength -gt 1 ]; then
				rsyncitem=$(rsync -anvR --stats "$MNTFLDR/$NFSSHARE/$file" "$DESTSYNCDIR/"'$file')
			else
				rsyncitem=$(rsync -anv --stats "$MNTFLDR/$NFSSHARE/$file" "$DESTSYNCDIR/"'$file')
			fi
			
			filesize=$(echo "$rsyncitem" | grep "Total transferred file size: " | cut -d':' -f2- | cut -d' ' -f2 | tr -d ',')
			
			file="${file//,/???}"
			
			if [ $filecount -eq 0 ]; then
				filesourcelist="$filesourcelist$MNTFLDR/$NFSSHARE/$file"
				filedestlist="$filedestlist$DESTSYNCDIR/$file"
				filesizelist="$filesizelist$filesize"
			else
				filesourcelist="$filesourcelist"'|'"$MNTFLDR/$NFSSHARE/$file"
				filedestlist="$filedestlist"'|'"$DESTSYNCDIR/$file"
				filesizelist="$filesizelist"'|'"$filesize"
			fi
			
			filecount=$((filecount + 1))
			filesizetotal=$((filesizetotal + $filesize))
		done
		unset IFS
		
		rowcount=0
		
		if [ ${#nfsfilelist} -ne 0 ]; then
			IFS=$':' 
			for row in $nfsfilelist; do
				if [ $rowcount -eq 0 ]; then
					filesourcelist="$row"'|'"$filesourcelist"
				elif [ $rowcount -eq 1 ]; then
					filedestlist="$row"'|'"$filedestlist"
				elif [ $rowcount -eq 2 ]; then
					filesizelist="$row"'|'"$filesizelist"
				fi
				rowcount=$((rowcount + 1))
			done
			unset IFS
		fi
		
		if [ ${#filesourcelist} -ne 0 ]; then
			nfsfilelist="$filesourcelist:$filedestlist:$filesizelist"
		fi
		
		totalfilesize=$((totalfilesize + $filesizetotal))
		totalfilecount=$((totalfilecount + $filecount))
		
		if [ ${#sourcelist} -eq 0 ]; then
			sourcelist="$MNTFLDR/$NFSSHARE/"
			destlist="$DESTSYNCDIR"
		else
			sourcelist="$sourcelist"'|'"$MNTFLDR/$NFSSHARE/"
			destlist="$destlist"'|'"$DESTSYNCDIR"
		fi
		
		echo "$(date +"%Y-%m-%d %H:%M"): NFS server $MNTFLDR/$NFSSHARE file list built"
		
		return
	fi
}

nfsfilelist=""
sourcelist=""
destlist=""
totalfilecount=0
totalfilesize=0

mntdir="/home/osmc/mnt/YazPiSync"

if [ $# -lt 1 ]; then
	echo "No arguments provided!"
	exit 1
fi

addonpath=$1
exportpath1=${2%/}
exportpath2=${4%/}
targetpath1=${3%/}
targetpath2=${5%/}

kodi-send -a "Notification(YazPi Sync,This will take a long time for a large number of files,5000,$addonpath/icon.png)" > /dev/null
sleep 5

if [ ! -z $exportpath1 ] && [ ! -z $targetpath1 ]; then
	nfsserverip1=$(echo "${exportpath1/nfs:\/\//}" | cut -f1 -d"/")
	nfsshare1=$(echo "$exportpath1" | rev | cut -f1 -d"/" | rev)
	getfilelistnfs "$mntdir" "$nfsserverip1" "$nfsshare1" "$targetpath1"
fi

if [ ! -z $exportpath2 ] && [ ! -z $targetpath2 ]; then
	nfsserverip2=$(echo "${exportpath2/nfs:\/\//}" | cut -f1 -d"/")
	nfsshare2=$(echo "$exportpath2" | rev | cut -f1 -d"/" | rev)
	getfilelistnfs "$mntdir" "$nfsserverip2" "$nfsshare2" "$targetpath2"
fi

echo $nfsfilelist > $mntdir/filelist.txt
kodi-send -a "RunScript($addonpath/resources/lib/SyncProgressBar.py,$totalfilecount,$totalfilesize,$mntdir/filelist.txt,$sourcelist,$destlist)" > /dev/null