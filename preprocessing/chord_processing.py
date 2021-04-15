'''
chord_processing.py

given a string name representation of the chord, process 
information about it


acknowledge: thanks music theory library music21 for making this module possible

'''
import numpy as np
from music21 import *

notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
enharm = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#", "N": "N"}
# how much the interval corresponds to semitones 
inversion = {"2": 2, "3": 4, "4": 5, "5": 7, "6": 9, "7": 11}

symbols = {"maj":"", "min":"m", "maj7": "7", "min7": "m7", "maj6": "6",
					"min6": "m6", "maj9": "9", "maj(9)": "9", "min(9)": "m9", "maj6(9)": "9add6",
					"hdim7": "dim7", "sus4(b7)": "sus4", "aug(b7)":"+7", "aug":"+",
					"9(13)": "13", "sus4(b7,9)": "9", "maj(2)":"add2", "maj6(7)":"7add6",
					"min(2)": "madd2", "maj9(13)": "9add13", "min7(11)": "m11",
					"maj6(b7)": "7add6", "sus4(9)": "sus4add9", "maj7(2)": "7add2",
					"min(11)": "madd11", "sus2(6)": "sus2add6", "7(4)": "7add4",
					"min7(13)": "m7add3", "7(#9)": "7", "maj13": "7add6"}

def make_symbol(kind):
	if "(" in kind:
		k, a = kind.split("(")
		a = a[:-1]
		if not a.isnumeric():
			return kind
		if k == "min":
			return "madd" + a
		if k == "maj": 
			return "add" + a
		return k + "add" + a
	return kind

'''
the inversion given by the dataset notation is just a number 
above the root, we need to get bass note by the inversion number 
'''
def get_bass(root, inv):
	root = root if root in notes else enharm[root]
	bass_idx = 0
	if len(inv) == 2:
		inv = inv[1]
		bass_idx -= 1
	bass_idx += (notes.index(root) + inversion[inv]) 

	return notes[bass_idx % 12]


'''
parse_chord: given the dataset chord notation, return the music21 
chord object of it.
'''
def parse_chord(d_chord):
	# print(d_chord)
	inversion = None
	if "/" in d_chord:
		d_chord, inversion = d_chord.split("/")
	root, kind = d_chord.split(":")
	bass= root if not inversion else get_bass(root, inversion)
	if len(root) == 2 and root[1] == "b":
		root = root[0] + "-"
	# print("chord construction: {}".format(root + symbols.get(kind, kind)))
	# s = symbols.get(kind, kind)
	# print(make_symbol("sus2"))
	c = harmony.ChordSymbol(root + symbols.get(kind, make_symbol(kind)))

	# if len(c.pitches) == 1:
	# 	print("chord construction failed: {}".format(root + symbols.get(kind, kind)))
	
	c.bass(bass)
	return c


'''
input: chord is music21 chord object, 
			key is music21 key object
based on the functionalityScore given by music21,
we can know whether this chord is in the key or not 
output: a score between 0 and 1
'''
def chord_key_score(chord, key):
	# if type(key) == string:
	# 	key_root, key_kind = key.split(":")
	# 	key = key_root + ("M" if key_kind == "maj" else "m")

	chord.key = key
	return chord.romanNumeral.functionalityScore / 100


'''
match_score: how similar the two chords are 
input: chord_1 and chord_2 are both music21 objects
output: a score between 0 and 1
'''
def match_score(chord_1, chord_2, p=False):
	p_1, p_2 = np.array([c.name for c in chord_1.pitches]), np.array([c.name for c in chord_2.pitches])
	match_score = len(np.intersect1d(p_1, p_2))/float(np.mean([len(p_1), len(p_2)]))

	if p: 
		print(chord_1.pitches)
		print(chord_2.pitches)

	match_score += 0.25 if chord_1.bass() == chord_2.bass() else 0 

	return 1 if match_score >= 1 else match_score






