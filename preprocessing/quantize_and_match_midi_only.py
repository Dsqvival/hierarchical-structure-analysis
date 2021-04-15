import os 
import mido
import numpy as np
import math
import sys

# data_dir = "../POP909/"

# data_dir = "../../lmd_melody_track/"
data_dir = ""

notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
enharm = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#", "N": "N"}
# how much the interval corresponds to semitones 
inversion = {"2": 2, "3": 4, "4": 5, "5": 7, "6": 9, "7": 11}



# determine wether two chords are the same
def match(chord_1, chord_2):
	root_1 = chord_1.split(":")[0]
	root_2 = chord_2.split(":")[0]

	# for inverted chords, calcuate their bass and compare 
	bass = []
	for c in [chord_1, chord_2]:
		b = c.split(":")[0]
		if "/" in c and c[-1].isnumeric():
			bb = b if b in notes else enharm[b]
			b_idx = (notes.index(bb) + inversion[c[-1]]) 
			if c[-2] == "b":
				b_idx -= 1
			bass.append(notes[b_idx % 12])
		else:
			bb = b if b in notes else enharm[b]
			bass.append(bb)

	if bass[0] == bass[1] or (chord_1 in chord_2) or (chord_2 in chord_1):
		return True

	# if length == 1:
	# 	return True	

	return False


'''
timestamp is a correspondace of seconds - beats
for the time in seconds in the chord list, convert them
to the nearest timestamp into beats
return the converted chords in the same format
chords format: [(start, end, chord), (start, end, chord...)]
'''
def convert_time(timestamps, chords):

	for c in chords:
		min_diff_0 = float("inf")
		min_diff_1 = float("inf")
		for t in timestamps:
			if abs(t[0] - c[0]) < min_diff_0:
				beat_0 = t[1]
				min_diff_0 = abs(t[0] - c[0])
			if abs(t[0] - c[1]) < min_diff_1:
				beat_1 = t[1]
				min_diff_1 = abs(t[0] - c[1])
			if t[0] > c[1]:
				break
		# start and end
		c[0] = round(beat_0)
		c[1] = round(beat_1)

	return chords


"""
quantize: 
translate the chord analysis into quantized form 
input: piece - a number index that shows which piece of the 909
	   it will look for midi_chord.txt and audio_chord.txt inside folder
	   print_detail: print each timestamp and whether they matched 
	   save: save to file in each folder 
output: percentage of the match in the two 
"""

def quantize(file_name, print_detail=False, save=False, save_summary = True):
	file_path = "/".join(file_name.split("/")[:-1])
	midiFile = mido.MidiFile(file_name)

	tpb = midiFile.ticks_per_beat
	# each beat is a quarter note, so sixteens is each 120 ticks 

	# tempo in meta message 
	# tempo = midiFile.tracks[0][0].tempo
	events = [e.tempo for e in midiFile.tracks[0] if e.type == "set_tempo"]
	beat_length = mido.tick2second(120, tpb, events[0]) * 2.0

	# beat_length = mido.tick2second(120, tpb, tempo) * 2.0

	with open(file_path + "/chord_midi.txt", "r") as f:
		midi_chords = [l.split() for l in f.readlines()]
		midi_chords = [[float(s), float(e), c] for s, e, c in midi_chords]
	f.close()

	with open(file_path + "/timestamps.txt", "r") as f:
		timestamps = [l.split() for l in f.readlines()]
		timestamps = [[float(s), float(e)] for s, e in timestamps]
	f.close()

	midi_chords = convert_time(timestamps, midi_chords)


	
	n = midi_chords[-1][1]

	# this is wrong, every measurement using beat_sec is now invalid 
	beat_sec = beat_length * np.array(range(n + 1))

    # fill the audio and midi chords into sixteenth segments
	midi_samples = ["N" for i in range(n)]
	for c in midi_chords:
		j = c[0]
		while j < c[1] and j < n:
			midi_samples[j] = c[2]
			j = j + 1
	audio_samples = midi_samples		

	# print("audio_samples | midi_samples is: ")
	# for idx, c in enumerate(audio_samples):
	# 	print("{} {}".format(c, midi_samples[idx]))

	percentage = 0.1

	# merge the same continuous label 
	ans = []
	i = 0
	while i < n:
		start = i
		i = i + 1
		while i < n and match(midi_samples[i], 
			midi_samples[start]) and match(audio_samples[i], audio_samples[start]):
			i = i + 1
		if match(midi_samples[start], audio_samples[start]) == False:
			ans.append([start // 4, start % 4, i - start, 
				# beat_sec[start] + begin_time, beat_sec[i] + begin_time, 
				audio_samples[start], midi_samples[start]])
		else:
			ans.append([start // 4, start % 4, i - start, 
				# beat_sec[start] + begin_time, beat_sec[i] + begin_time, 
				midi_samples[start]])		
	return ans, percentage


def output_to_file():
	for filename in os.listdir(data_dir):
		if len(filename) != 3:
			continue
		quantize(filename, save=True)

# output_to_file()

def run_one(x):
	percentages = []
	for i in range(x, x+1):	
		percentages.append(quantize(("0" * (3-len(str(x)))) + str(i), print_detail=False))
	print(percentages)	


def run_all():
	percentages = []
	for filename in os.listdir(data_dir):
		if len(filename) != 3:
			continue
		# percentages.append(quantize(filename, save_summary = True))
		quantize(filename)

	# # the percentage that matches more than 90% and 80%
	# up_90 = sum([percentages[i] >= 0.9 for i in range(909)]) / 909
	# up_80 = sum([percentages[i] >= 0.8 for i in range(909)]) / 909

	# print(up_90)	
	# print(up_80)	

# filename = "001"
# quantize("018") 

# run_one(348)
# run_all()
