# /////////////////////////////////////////
# TAIKO RATE CONVERTER / ? UNTESTED OTHER MODES
# NAKABAMITV (pohmx) - DEVELOPMENT 2022
# https://www.surina.net/soundtouch/README.html#SoundStretch COMMANDS
# SEE ISSUE https://github.com/jiaaro/pydub/issues/645, to fix .ogg conversion crackling
# USING data from https://github.com/l3lackShark/gosumemory
# TO DO: 
# - ADD GUI
# - MOVE FILES
# /////////////////////////////////////////

from urllib.request import urlopen
import json
from pydub import AudioSegment
import shutil
import os
import wave
import subprocess
from decimal import Decimal
import sys
import re

link = "http://localhost:24050/json"
one = True
newRate = 1.7
exportOsu = ""
osuIsLoaded = False

# BEATMAP STRUCTURE
mapLines = []
bpm = 0
mapGeneral = { # osu file format v14
	# [General]
	'AudioFilename:':'',
	'AudioLeadIn:':'',
	'PreviewTime:':'',
	'Countdown:':'',
	'SampleSet:':'',
	'StackLeniency:':'',
	'Mode:':'',
	'LetterboxInBreaks:':'',
	'SpecialStyle:':'',
	'WidescreenStoryboard:':'',
	# [Editor]
	'Bookmarks:':'',
	'DistanceSpacing:':'',
	'BeatDivisor:':'',
	'GridSize:':'',
	'TimelineZoom:':'',
	# [Metadata]
	'Title:':'',
	'TitleUnicode:':'',
	'Artist:':'',
	'ArtistUnicode:':'',
	'Creator:':'',
	'Version:':'',
	'Source:':'',
	'Tags:':'',
	'BeatmapID:':'',
	'BeatmapSetID:':'',
	# [Difficulty]
	'HPDrainRate:':'',
	'CircleSize:':'',
	'OverallDifficulty:':'',
	'ApproachRate:':'',
	'SliderMultiplier:':'',
	'SliderTickRate:':''
}
mapGroups = {
	# [Group]
	'Events':[],
	'TimingPoints':[],
	'Colours':[],
	'HitObjects':[],
	'NewHitObjects':[],
}

def getBpm():
	global bpm
	bpm_list = []
	for t in mapGroups['TimingPoints']:
		if t.split(",",1)[1][0] != '-':
			bpm_list.append(int(round(1/float(t.split(',')[1])*60000))) # round then convert
	if len(bpm_list) == 1:
		bpm = bpm_list[0]
	# IF THERE ARE MORE BPMS DONT CARE
	print("BPM: ",bpm)

def readOsu(osuFile):
	global mapLines
	global mapGroups
	capture = False

	# openfile
	with open(osuFile, 'r', encoding="utf8") as mapFile:
		mapLines = mapFile.readlines()
	
	# Get parameters from beatmap
	for line in mapLines:
		for key in mapGeneral:
			if key in line:
				mapGeneral[key] = line.split(":")[1].rstrip("\n").lstrip()
	
	# Read [Events]
	for line in mapLines:			
		if '[' in line:
			capture = False
		if capture:
			mapGroups['Events'].append(line.rstrip("\n"))
		if '[Events]' in line:
			capture = True
	mapGroups['Events'] = [x for x in mapGroups['Events'] if x]
		
	# Read [Timing Points]
	for line in mapLines:		
		if '[' in line:
			capture = False
		if capture:			
			mapGroups['TimingPoints'].append(line.rstrip("\n"))
		if '[TimingPoints]' in line:
			capture = True
	mapGroups['TimingPoints'] = [x for x in mapGroups['TimingPoints'] if x]

	# Read [Colours]
	for line in mapLines:		
		if '[' in line:
			capture = False
		if capture:			
			mapGroups['Colours'].append(line.rstrip("\n"))
		if '[Colours]' in line:
			capture = True
	mapGroups['Colours'] = [x for x in mapGroups['Colours'] if x]

	# Read [HitObjects]
	for line in mapLines:
		if capture:
			mapGroups['HitObjects'].append(line.rstrip("\n"))
		if '[HitObjects]' in line:
			capture = True
	capture = False
	mapGroups['HitObjects'] = [x for x in mapGroups['HitObjects'] if x]

def changeTiming():

	# TIMING POINTS

	newTiming = []

	for timingPoint in mapGroups['TimingPoints']:
		if timingPoint.split(",",1)[1][0] != '-': # negative symbol
			newBpm = str(round(float(timingPoint.split(",",1)[1].split(",",1)[0]) / newRate, 11))
			newOffset = str(int(float(timingPoint.split(",",1)[0].split(",",1)[0]) / newRate))			
			fullTiming = newOffset + "," + newBpm + "," + timingPoint.split(",",1)[1].split(",",1)[1]
			newTiming.append(fullTiming)
		else:
			newOffset = str(int(float(timingPoint.split(",",1)[0].split(",",1)[0]) / newRate))
			fullTiming = newOffset + "," + timingPoint.split(",",1)[1]
			newTiming.append(fullTiming)

	mapGroups['TimingPoints'] = []

	for override in newTiming:
		mapGroups['TimingPoints'].append(override)

	# HITOBJECTS

	for hitObject in mapGroups['HitObjects']:
		if hitObject.split(",",4)[3] == '5' or hitObject.split(",",4)[3] == '1':
			# x,y,time,type,hitSound,garbage (272,223,37748,1,8,0:0:0:0:) // HIT CIRCLE, TAIKO
			newObject = hitObject.split(",",3)[0] + "," + hitObject.split(",",3)[1] + "," + str(round(int(hitObject.split(",",3)[2])/newRate)) + "," + hitObject.split(",",3)[3]
		elif hitObject.split(",",4)[3] == '12':
			# x,y,time,type,hitSound,endTime,garbage (256,192,37850,12,0,38462,0:0:0:0:) // SPINNER, TAIKO
			newObject = hitObject.split(",",6)[0] + "," + hitObject.split(",",6)[1] + "," + str(round(int(hitObject.split(",",6)[2])/newRate)) + "," + hitObject.split(",",6)[3] + "," + hitObject.split(",",6)[4] + "," + str(round(int(hitObject.split(",",6)[5])/newRate)) + "," + hitObject.split(",",6)[6] 
		elif hitObject.split(",",4)[3] == '128':
			# x,y,time,type,hitSound,endTime:garbage (36,192,926,128,2,3464:0:0:0:0:) // HOLD NOTE, MANIA
			newObject = hitObject.split(",",5)[0] + "," + hitObject.split(",",5)[1] + "," + str(round(int(hitObject.split(",",5)[2])/newRate)) + "," + hitObject.split(",",5)[3] + "," + hitObject.split(",",5)[4] + "," + str(round(int(hitObject.split(",",5)[5].split(":",1)[0])/newRate)) + ":" + hitObject.split(",",5)[5].split(":",1)[1]
		elif hitObject.split(",",4)[3] == '2':
			# x,y,time,type,hitSound,SLIDERDATA,repeat,osuPixelsLength(endtime)**DONT APPLY RATE HERE** 200,284,72968,2,0,L|124:273,1,70
			newObject = hitObject.split(",",7)[0] + "," + hitObject.split(",",7)[1] + "," + str(round(int(hitObject.split(",",7)[2])/newRate)) + "," + hitObject.split(",",7)[3] + "," + hitObject.split(",",7)[4] + "," + hitObject.split(",",7)[5] + "," + hitObject.split(",",7)[6] + "," + hitObject.split(",",7)[7]
		elif hitObject.split(",",4)[3] == '6':
			newObject = hitObject.split(",",7)[0] + "," + hitObject.split(",",7)[1] + "," + str(round(int(hitObject.split(",",7)[2])/newRate)) + "," + hitObject.split(",",7)[3] + "," + hitObject.split(",",7)[4] + "," + hitObject.split(",",7)[5] + "," + hitObject.split(",",7)[6] + "," + hitObject.split(",",7)[7]
			print(hitObject, newObject)
		mapGroups['NewHitObjects'].append(newObject)

	# BOOKMARKS

	bookmarksNew = []

	if mapGeneral['Bookmarks:'].split(",") != ['']:
		for bookmark in mapGeneral['Bookmarks:'].split(","):
			bookmarksNew.append(str(int(int(bookmark) / newRate)))
		mapGeneral['Bookmarks:'] = ",". join(bookmarksNew)

def createMap(audio, rate):

	global exportOsu

	if bpm != 0:
		mapGeneral['Version:'] = mapGeneral['Version:'] + ' ' + str(float(rate)) + 'x (' + str(bpm) + 'bpm)'
	else:
		mapGeneral['Version:'] = mapGeneral['Version:'] + ' ' + str(float(rate)) + 'x'

	mapGeneral['AudioFilename:'] = audio
	if mapGeneral['PreviewTime:'] != '-1': #?
		mapGeneral['PreviewTime:'] = str(int(int(mapGeneral['PreviewTime:']) / newRate))

	mapGeneral['Tags:'] += ' nimi-trainer'
	newMap = ['osu file format v14','','[General]']
	general = [
		'AudioFilename:',
		'AudioLeadIn:',
		'PreviewTime:',
		'Countdown:',
		'SampleSet:',
		'StackLeniency:',
		'Mode:',
		'LetterboxInBreaks:',
		'SpecialStyle:',
		'WidescreenStoryboard:'
		]
	editor = [
		'Bookmarks:',
		'DistanceSpacing:',
		'BeatDivisor:',
		'GridSize:',
		'TimelineZoom:'
	]
	metadata = [
		'Title:',
		'TitleUnicode:',
		'Artist:',
		'ArtistUnicode:',
		'Creator:',
		'Version:',
		'Source:',
		'Tags:',
		'BeatmapID:',
		'BeatmapSetID:'
	]
	difficulty = [
		'HPDrainRate:',
		'CircleSize:',
		'OverallDifficulty:',
		'ApproachRate:',
		'SliderMultiplier:',
		'SliderTickRate:'
	]
	
	# REMOVE EMPTY DATA

	if len(mapGeneral['SpecialStyle:']) == 0:
		general.remove('SpecialStyle:') 

	if len(mapGeneral['TimelineZoom:']) == 0:
		editor.remove('TimelineZoom:') 

	if len(mapGeneral['Bookmarks:']) == 0:
		editor.remove('Bookmarks:') # remove from above list, not from raw data dictionary

	for v in general:
		newMap.append(str(v+' '+mapGeneral[v]))
	newMap.append('')

	newMap.append('[Editor]')
	for v in editor:
		newMap.append(str(v+' '+mapGeneral[v]))
	newMap.append('')

	newMap.append('[Metadata]')
	for v in metadata:
		newMap.append(str(v+mapGeneral[v]))
	newMap.append('')

	newMap.append('[Difficulty]')
	for v in difficulty:
		newMap.append(str(v+mapGeneral[v]))
	newMap.append('')

	newMap.append('[Events]')
	for v in mapGroups['Events']:
		newMap.append(v)
	newMap.append('')

	newMap.append('[TimingPoints]')
	for v in mapGroups['TimingPoints']:
		newMap.append(v)
	newMap.append('')

	# REMOVE EMPTY HEADERS
	if len(mapGroups['Colours']) != 0:
		newMap.append('[Colours]')
		for v in mapGroups['Colours']:
			newMap.append(v)
		newMap.append('')

	newMap.append('[HitObjects]')
	for v in mapGroups['NewHitObjects']:
		newMap.append(v)
	newMap.append('')

	filename = mapGeneral['Artist:'] + ' - ' + mapGeneral['Title:'] + ' (' + mapGeneral['Creator:'] + ') ' + '[' + mapGeneral['Version:'] +  '].osu'
	exportOsu = filename.replace('"','')

	with open(exportOsu,'w', encoding="utf8") as f:
		for line in newMap:
			f.write(line+'\n')
	
while True:
	# CHECK CONNECTION (IF DATA EXISTS.)
	try:
		json_data = str(urlopen(link).read().decode('utf-8'))
		json_converted = json.loads(json_data, strict=False)
		try:				
			# PATHS
			song_folder = json_converted['settings']['folders']['songs']
			path_folder = json_converted['menu']['bm']['path']['folder']
			path_beatmap = json_converted['menu']['bm']['path']['file']	
			path_audio = json_converted['menu']['bm']['path']['audio']	
			full_beatmap_path = song_folder + "\\" + path_folder + "\\" + path_beatmap
			full_folder_path = song_folder + "\\" + path_folder
			full_beatmap_path_audio = song_folder + "\\" + path_folder + "\\" + path_audio
			# METADATA
			metadata = json_converted['menu']['bm']['metadata']
			# SWITCH
			osuIsLoaded = True
		except:
			print('gosumemory-error: ', json_converted['error'])
	except:
		print("taiko-trainer-error: can't stablish connection to gosumemory.")

	if one is True and osuIsLoaded is True:
		one = False

		# AUDIO FILE CREATION
		# COPY TO ROOT, CONVERT .MP3 & .OGG TO .WAV
		# CALCULATION, NAMING OF FILE

		shutil.copyfile(full_beatmap_path_audio, path_audio)
		path_wav = os.path.splitext(path_audio)[0] + ".wav"

		if os.path.splitext(path_audio)[1] == '.mp3':
			try:
				sound = AudioSegment.from_file(path_audio, 'mp3') # NORMAL READ			
				sound.export(path_wav, format="wav")
			except:
				sound = AudioSegment.from_file(path_audio) # EXCEPTED READ // CAN'T FIND CONTAINER
				sound.export(path_wav, format="wav")

		elif os.path.splitext(path_audio)[1] == '.ogg':			
			sound = AudioSegment.from_ogg(path_audio)
			sound.export(path_wav, format="wav")
		
		bpm_multiplier = (newRate - 1) * 100
		newAudio = os.path.splitext(path_audio)[0] + '-' +  str(float(newRate)) + 'x.wav' 

		# SETS SOUNDSTRETCHER OPTIONS
		# CREATES FILE, REMOVES OLD .WAV

		switches_quick = True
		switches_no_anti_alias = True
		switches_string = ''
		if switches_quick: switches_string += ' -quick'			
		if switches_no_anti_alias: switches_string += ' -naa'

		switches = 'soundstretch.exe "' + sys.path[0] + '\\' + path_wav + '" "' + sys.path[0] + '\\' + newAudio + '"' + switches_string + ' -tempo=' + str(bpm_multiplier)
		subprocess.run(switches, shell=True) # MAYBE CHECK RETURN
		os.remove(path_wav)

		mp3 = AudioSegment.from_wav(newAudio)
		mp3.export(os.path.splitext(newAudio)[0]+'.mp3', format="mp3", bitrate="320k")
		newAudio_mp3 = os.path.splitext(newAudio)[0]+'.mp3'		

		# BEATMAP CREATION
		readOsu(full_beatmap_path)
		changeTiming()
		getBpm()
		createMap(newAudio_mp3, newRate)

		# COPY TO ORIGINAL FOLDER
		shutil.copyfile(newAudio, full_folder_path + '\\' + newAudio_mp3)
		shutil.copyfile(exportOsu, full_folder_path + '\\' + exportOsu)
		os.remove(path_audio)
		os.remove(newAudio)
		os.remove(newAudio_mp3)
		os.remove(exportOsu)

		print('taiko-trainer-info: created file', exportOsu, newAudio_mp3)
