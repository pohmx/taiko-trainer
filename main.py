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
from soundstretch import SoundStretch # SoundStretch 2.1.1 for Windows 
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
newRate = 1.5

'''
# UNUSED
# https://github.com/Manarabdelaty/Audio-Stretching
def stretch_funny(fname, factor): #audio.wav, 0.5
	infile=wave.open( fname, 'rb')
	rate= infile.getframerate()
	channels=infile.getnchannels()
	swidth=infile.getsampwidth()
	nframes= infile.getnframes()
	audio_signal= infile.readframes(nframes)
	outfile = wave.open('stretched.wav', 'wb')
	outfile.setnchannels(channels)
	outfile.setsampwidth(swidth)
	outfile.setframerate(rate/factor)
	outfile.writeframes(audio_signal)
	outfile.close()
	return
'''

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
	'HitObjects':[],
	'NewHitObjects':[],
}

def getBpm():
	global bpm
	bpm_list = []
	for t in mapGroups['TimingPoints']:
		if t.split(",",1)[1][0] != '-':
			bpm_list.append(int(1/float(t.split(',')[1])*60000))
	if len(bpm_list) == 1:
		bpm = bpm_list[0]
	# IF THERE ARE MORE BPMS DONT CARE
	print(bpm)

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
		if '[TimingPoints]' in line:
			capture = False
		if capture:
			mapGroups['Events'].append(line.rstrip("\n"))
		if '[Events]' in line:
			capture = True
	mapGroups['Events'] = [x for x in mapGroups['Events'] if x]
		
	# Read [Timing Points]
	for line in mapLines:		
		if '[HitObjects]' in line:
			capture = False
		if capture:			
			mapGroups['TimingPoints'].append(line.rstrip("\n"))
		if '[TimingPoints]' in line:
			capture = True
	mapGroups['TimingPoints'] = [x for x in mapGroups['TimingPoints'] if x]

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
		newObject = hitObject.split(",",3)[0] + "," + hitObject.split(",",3)[1] + "," + str(round(int(hitObject.split(",",3)[2])/newRate)) + "," + hitObject.split(",",3)[3] #X,Y,TIMING,DATA
		mapGroups['NewHitObjects'].append(newObject)

	# BOOKMARKS

	bookmarksNew = []

	if mapGeneral['Bookmarks:'].split(",") != ['']:
		for bookmark in mapGeneral['Bookmarks:'].split(","):
			bookmarksNew.append(str(int(bookmark) / newRate))
		mapGeneral['Bookmarks:'] = ",". join(bookmarksNew)
	
	'''
	# FIGURE OUT IF MAP IN 0.5X MATCHES EXPECTED TIMING POINTS

	take first point, add difference * 0.75 (rate)

		newTiming_stretch.append(point)
	else:
		difference = str(abs(int(timingPoint.split(",",1)[0])-int(newTiming_stretch[count-1].split(",",1)[0])))
		print(difference)
		newTiming_stretch.append(difference + ',' + (timingPoint.split(",",1)[1]))
		pass
	print(newTiming_stretch)
	
	if count < len(newTiming) - 1:
		number1 = int(timingPoint.split(",",1)[0])
		number2 = int(newTiming_stretch[count-1].split(",",1)[0])
		difference = abs(number1-number2)
		print(difference)
	if count == len(newTiming) - 1:
		number1 = int(timingPoint[count-1].split(",",1)[0])
		number2 = int(newTiming_stretch[-1].split(",",1)[0])
		difference = abs(number1-number2)
		print(difference)
	'''

def createMap(audio, rate):
	if bpm != 0:
		mapGeneral['Version:'] = mapGeneral['Version:'] + ' ' + str(float(rate)) + 'x (' + str(bpm) + 'bpm)'
	else:
		mapGeneral['Version:'] = mapGeneral['Version:'] + ' ' + str(float(rate)) + 'x'
	mapGeneral['AudioFilename:'] = audio
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

	newMap.append('[HitObjects]')
	for v in mapGroups['NewHitObjects']:
		newMap.append(v)
	newMap.append('')

	filename = mapGeneral['Artist:'] + ' - ' + mapGeneral['Title:'] + ' (' + mapGeneral['Creator:'] + ') ' + '[' + mapGeneral['Version:'] +  '].osu'

	# print(filename)

	with open(filename,'w', encoding="utf8") as f:
		for line in newMap:
			f.write(line+'\n')
	
while True:

	# RAW
	json_data = str(urlopen(link).read())[2:-1].replace('\\x', '\\\\x').replace('\\\\u0026', '&')
	json_converted = json.loads(json_data)

	# PATHS
	song_folder = json_converted['settings']['folders']['songs'].replace('\\\\', '\\')	
	path_folder = json_converted['menu']['bm']['path']['folder']
	path_beatmap = json_converted['menu']['bm']['path']['file']
	path_audio = json_converted['menu']['bm']['path']['audio']
	full_beatmap_path = song_folder + "\\" + path_folder + "\\" + path_beatmap
	full_beatmap_path_audio = song_folder + "\\" + path_folder + "\\" + path_audio
	# METADATA
	metadata = json_converted['menu']['bm']['metadata']

	#print(full_beatmap_path)

	if one is True:
		one = False

		# AUDIO FILE CREATION
		shutil.copyfile(full_beatmap_path_audio, path_audio)
		path_wav = os.path.splitext(path_audio)[0] + ".wav"

		if os.path.splitext(path_audio)[1] == '.mp3':			
			sound = AudioSegment.from_mp3(path_audio)			
			sound.export(path_wav, format="wav")
			os.remove(path_audio)	# clean up
		elif os.path.splitext(path_audio)[1] == '.ogg':			
			sound = AudioSegment.from_ogg(path_audio)
			sound.export(path_wav, format="wav")
			os.remove(path_audio)	# clean up

		'''
		normalized_rate = Decimal(1.5) * Decimal(newRate)
		bpm_effectiveMultiplier = normalized_rate / Decimal(1.5) 
		bpm_multiplier = (bpm_effectiveMultiplier - 1) * 100
		'''

		bpm_multiplier = (newRate - 1) * 100
		newAudio = os.path.splitext(path_audio)[0] + '-' +  str(float(newRate)) + 'x.wav' 

		# OPTIONS
		switches_quick = True
		switches_no_anti_alias = True
		switches_string = ''
		if switches_quick: switches_string += ' -quick'			
		if switches_no_anti_alias: switches_string += ' -naa'

		switches = 'soundstretch.exe "' + sys.path[0] + '\\' + path_wav + '" "' + sys.path[0] + '\\' + newAudio + '"' + switches_string + ' -tempo=' + str(bpm_multiplier)
		subprocess.run(switches, shell=True) # MAYBE CHECK RETURN
		#stretch_funny(path_wav, 0.75) FUNNY STRETCH OPTION
		os.remove(path_wav)

		mp3 = AudioSegment.from_file(newAudio)
		mp3.export(os.path.splitext(newAudio)[0]+'.mp3', format="mp3", bitrate="320k")
		os.remove(newAudio)
		newAudio = os.path.splitext(newAudio)[0]+'.mp3'

		# BEATMAP CREATION
		readOsu(full_beatmap_path)
		changeTiming()
		getBpm()
		createMap(newAudio, newRate)

		# COPY TO ORIGINAL FOLDER