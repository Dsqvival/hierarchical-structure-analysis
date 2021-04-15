import os 
import mido
import numpy as np
import math
import sys

data_dir = "../POP909/"

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

def quantize(piece, print_detail=False, save=False, save_summary = True):
	piece_dir = data_dir + piece + "/"
	midiFile = mido.MidiFile(piece_dir + piece + '.mid', clip=True)

	tpb = midiFile.ticks_per_beat
	# each beat is a quarter note, so sixteens is each 120 ticks 

	# tempo in meta message 
	tempo = midiFile.tracks[0][0].tempo

	beat_length = mido.tick2second(120, tpb, tempo) * 2.0

	# format of reads: [[start, end, value], [start, end, value], ...]
	with open(piece_dir + "chord_audio.txt", "r") as f:
		audio_chords = [l.split() for l in f.readlines()]
		audio_chords = [[float(s), float(e), c] for s, e, c in audio_chords]
	f.close()

	with open(piece_dir + "chord_midi.txt", "r") as f:
		midi_chords = [l.split() for l in f.readlines()]
		midi_chords = [[float(s), float(e), c] for s, e, c in midi_chords]
	f.close()

	with open(piece_dir + "timestamps.txt", "r") as f:
		timestamps = [l.split() for l in f.readlines()]
		timestamps = [[float(s), float(e)] for s, e in timestamps]
	f.close()

	# notice there might be multiple keys due to modulation
	with open(piece_dir + "key_audio.txt", "r") as kf:
		key = [l.split() for l in kf.readlines()]
	kf.close()


	# old begin time, not useful 
	begin_time = 0.0
	while midi_chords[0][2] == "N":
	 	begin_time = float((midi_chords.pop(0))[1])	
	while float(audio_chords[0][1]) < begin_time:
	 	audio_chords.pop(0)

	audio_chords = convert_time(timestamps, audio_chords)
	midi_chords = convert_time(timestamps, midi_chords)


	# quantization

	# for i in range(len(midi_chords)):
	# 	midi_chords[i][0] = int(round((float(midi_chords[i][0]) - begin_time) / beat_length))
	# 	midi_chords[i][1] = int(round((float(midi_chords[i][1]) - begin_time) / beat_length))
	# 	# if midi_chords[i][0] == midi_chords[i][1] and midi_chords[i][2] != "N":
	# 	# 	print("{}: MIDI delete ({}, {}) - {}".format(piece, a, b, midi_chords[i][2]))

	# for i in range(len(audio_chords)):
	# 	audio_chords[i][0] = int(round((float(audio_chords[i][0]) - begin_time) / beat_length))
	# 	audio_chords[i][1] = int(round((float(audio_chords[i][1]) - begin_time) / beat_length))
	# 	# if audio_chords[i][0] == audio_chords[i][1] and audio_chords[i][2] != "N":
	# 	# 	print("{}: Audio delete ({}, {}) - {}".format(piece, a, b, audio_chords[i][2]))

	# print("midi_chords is: ")
	# for c in midi_chords:
	# 	print(c)

	n = audio_chords[-1][1]
	# if midi_chords[-1][1] < n:
	# 	n = midi_chords[-1][1]

	# this is wrong, every measurement using beat_sec is now invalid 
	beat_sec = beat_length * np.array(range(n + 1))

    # fill the audio and midi chords into sixteenth segments
	audio_samples = ["N" for i in range(n)]
	for c in audio_chords:
		j = c[0]
		while j < c[1] and j < n:
			audio_samples[j] = c[2]
			j = j + 1
	midi_samples = ["N" for i in range(n)]
	for c in midi_chords:
		j = c[0]
		while j < c[1] and j < n:
			midi_samples[j] = c[2]
			j = j + 1

	# print("audio_samples | midi_samples is: ")
	# for idx, c in enumerate(audio_samples):
	# 	print("{} {}".format(c, midi_samples[idx]))

	percentage = sum([match(audio_samples[i], midi_samples[i]) for i in range(n)]) / n
	# print(percentage)

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

	# optional arguments 
	if print_detail:
		for x in range(n):
			print("({} , {}) : {} {}".format(round(beat_sec[x], 2), round(beat_sec[x + 1], 2), audio_samples[x], midi_samples[x]))
			# print(match(audio_samples[x], midi_samples[x]))

		for x in range(n):
			print("({}.{} , {}.{}) : {} {}".format(x // 4, x % 4, (x + 1) // 4, (x + 1) % 4, audio_samples[x], midi_samples[x]))

	if save:
		with open(piece_dir + "quantized_midi_chord.txt", "w") as f:
			for x in range(n):
				f.write("{}\t{}\n".format(round(sixteens[x], 4), midi_samples[x]) )
		f.close()
		with open(piece_dir + "quantized_audio_chord.txt", "w") as g:
			for x in range(n):
				g.write("{}\t{}\n".format(round(sixteens[x], 4), audio_samples[x]) )
		g.close()

	# save_summary will be done in finalize_chord, and the choice will be printed
	# if save_summary:
	# 	with open(piece_dir + "chords_summary.txt", "w") as f:
	# 		# f.write("{}\n".format(key[0][2]))
	# 		for x in ans:		
	# 			if len(x) == 5:
	# 				f.write("Start Beat {}.{} for {}: {},  {}\n".format(x[0], x[1], x[2], x[3], x[4]))	
	# 			else:
	# 				f.write("Start Beat {}.{} for {}: {}\n".format(x[0], x[1], x[2], x[3]))							
	# 		f.write("Match rate: {}\n".format(round(percentage, 4)))	
	# 		# f.write("Match rate (delete misalignment): {}\n".format(round(final_percentage, 4)))
	# 		f.close()						

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
