'''
Given the quantized chords, pick the one that's more right

To consider:
- Modulation
'''

import os
import bisect
import mido
from quantize_and_match import quantize, match
from chord_processing import * 

data_dir = "../POP909/"

'''
given a line of ans and it's prev, next, choose the best among two candidates
rules: 
- doesn't favor inverted chord
- if the prev/next chord is two beat (instead of 4 or 8), favor same chord
- favor the chord that has more repetition with neighbors
- favor the chord in key (check modulation)
'''
def choose(ans, key, prev=None, nex=None):
	op1, op2 = ans[-2], ans[-1]
	if op2 == "N" or op1 == "N":
		return op2 if op2 != "N" else op1

	cand_1, cand_2 = parse_chord(op1), parse_chord(op2)
	score_1, score_2 = 0, 0
	# format the key
	key_root, key_kind = key.split(":")
	key = key_root + ("M" if key_kind == "maj" else "m")

	# check key
	score_1 += chord_key_score(cand_1, key) * 2
	score_2 += chord_key_score(cand_2, key) * 2
	# sometimes the key is the enharmonic equivalence, so that it 
	# can't tell the function of chord in the key accurately. Need to 
	# retry in the equivalence key.
	if score_1 == score_2 == 0:
		e_p = str(pitch.Pitch(key_root).getAllCommonEnharmonics()[0])
		e_key = e_p + ("M" if key_kind == "maj" else "m")
		score_1 += chord_key_score(parse_chord(op1), e_key) * 2
		score_2 += chord_key_score(parse_chord(op2), e_key) * 2

	# unfavor inversion
	score_1 -= 0 if cand_1.inversion() == 0 else 1 
	score_2 -= 0 if cand_2.inversion() == 0 else 1 

	# if there is no neighbor, returned 
	if not prev or not nex:
		return op1 if score_1 >= score_2 else op2		

	neighbors = []
	neighbors.extend(prev[-1:] if len(prev) == 4 else prev[-2:])
	neighbors.extend(nex[-1:] if len(nex) == 4 else nex[-2:])
	neighbors = [parse_chord(n) for n in neighbors if n != "N"]

	# check repetition
	for n in neighbors:
		score_1 += match_score(cand_1, n)
		score_2 += match_score(cand_2, n)

	# duration: weight by length of the previous / next chord
	# chords with smaller duration is more likely to be an embellishment
	if ans[2] <= 2:
		if prev[2] >= 2:
			score_1 += 0 if prev[-1] == "N" else match_score(cand_1, parse_chord(prev[-1])) * prev[2] / 2 
			score_2 += 0 if prev[-1] == "N" else match_score(cand_2, parse_chord(prev[-1])) * prev[2] / 2
		if nex[2] >= 2:
			score_1 += 0 if nex[-1] == "N" else match_score(cand_1, parse_chord(nex[-1])) * nex[2] / 2
			score_2 += 0 if nex[-1] == "N" else match_score(cand_2, parse_chord(nex[-1])) * nex[2] / 2

	return op1 if score_1 >= score_2 else op2


'''
piece - a number index that shows which piece of the 909

save file format:
[Cmaj, 1][Dmin, 1][Gmaj, 2]
'''
def finalize(piece, save_file=False, print_details=False, save_summary=False):
	'''
	quantize return: [(measure, beat, duration, start, end, audio_chord, (midi_chord))]
	duration - in quavers 
	'''
	piece_dir = data_dir + piece + "/"

	ans, percentage = quantize(piece, save_summary=False)

	# if percentage > 0.7:
	# 	print("skipped")
	# 	return 

	res = []

	# if the midi and audio has large discrepancy, then they are 
	# propably not on the same key and it's better to stick with one of them for consistency. 
	if percentage < 0.7:
		with open(piece_dir + "chords_summary.txt", "w") as f:
			for a in ans:
				# merge the continuous label
				if len(res) != 0 and res[-1][0] == a[-1]:
					res[-1][1] += a[2]
				else:
					res.append([a[-1], a[2]])
				if len(a) == 5:
					if print_details:
						print("Start Beat {}.{} for {}: {}, {}, choosed {}".format(a[0], a[1], a[2], a[3], a[4], a[-1]))
					if save_summary:
						f.write("Start Beat {}.{} for {}: {}, {}, choosed {}\n".format(a[0], a[1], a[2], a[3], a[4], a[-1]))
				else:
					if print_details:
						print("Start Beat {}.{} for {}: {}".format(a[0], a[1], a[2], a[3]))
					if save_summary:
						f.write("Start Beat {}.{} for {}: {}\n".format(a[0], a[1], a[2], a[3]))				
			f.write("Match rate: {}\n".format(round(percentage, 4)))	
		f.close()
	else:
		with open(piece_dir + "key_audio.txt", "r") as f:
			keys = [l.split() for l in f.readlines()]
		f.close()
		with open(piece_dir + "chords_summary.txt", "w") as f:
			for idx, a in enumerate(ans):
				# get the right key based on the staring time 
				# key_idx = bisect.bisect([float(k[0]) for k in keys], a[3]) - 1
				key = keys[0][2]

				if len(a) == 5:
					if idx == 0 or idx == len(ans)-1:
						c = choose(a, key)
					else:
						c = choose(a, key, prev=ans[idx-1], nex=ans[idx+1])

					# merge the continuous label
					if len(res) != 0 and res[-1][0] == c:
						res[-1][1] += a[2]
					else:
						res.append([c, a[2]])
					if print_details:
						print("Start Beat {}.{} for {}: {}, {}, choosed {}".format(a[0], a[1], a[2], a[3], a[4], c))	
					if save_summary:
						f.write("Start Beat {}.{} for {}: {}, {}, choosed {}\n".format(a[0], a[1], a[2], a[3], a[4], c))
				else:
					if len(res) != 0 and res[-1][0] == a[-1]:
						res[-1][1] += a[2]
					else:
						res.append([a[-1], a[2]])
					if print_details:
						print("Start Beat {}.{} for {}: {}".format(a[0], a[1], a[2], a[3]))
					if save_summary:
						f.write("Start Beat {}.{} for {}: {}\n".format(a[0], a[1], a[2], a[3]))
			f.write("Match rate: {}\n".format(round(percentage, 4)))	
		f.close()
	
	if save_file:
		with open(piece_dir + "finalized_chord.txt", "w") as f:
			for c in res:
				f.write("{} {}\n".format(c[0], c[1]))
		f.close()
		# after save file, need to change format
		finalized_change_format(piece)
	return res
'''
piece is three digit index
output each line into format:
[symbol, array of chord note, bass, duration]
if the chord is N, then the chord note is [] and bass is ""
'''
def finalized_change_format(piece):
	piece_dir = data_dir + piece + "/"

	with open(piece_dir + "finalized_chord.txt") as f:
		chords = [l.split() for l in f.readlines()]
	f.close()

	formatted_chords = []
	for c in chords:
		symbol, duration = c[0], c[1]

		if symbol == "N":
			formatted_chords.append([symbol, [], "", duration])
			continue

		parsed_c = parse_chord(symbol)
		notes = sorted([p.pitchClass for p in parsed_c.pitches])
		bass = parsed_c.bass().pitchClass
		formatted_chords.append([symbol, notes, bass, duration])

	# get rid of the empty beats at beginning and then document it
	# so that melody truncate the same part
	begin_beats = 0
	if formatted_chords[0][0] == "N":
		begin_beats = formatted_chords[0][3]
		formatted_chords = formatted_chords[1:]

	with open(piece_dir + "finalized_chord.txt", "w") as f:
		for c in formatted_chords:
			f.write("{} {} {} {} \n".format(*c))
	f.close()
	with open(piece_dir + "begin_time.txt", "w") as f:
		f.write(str(begin_beats))
	f.close()



def run_all():
	for filename in os.listdir(data_dir):
		if len(filename) != 3:
			continue
		finalize(filename, save_file=True, save_summary=True)
		print(filename + " done")

# finalize("797", save_file=True, save_summary=True)

# finalize("019", save_summary=True)
# finalized_change_format("025")
run_all()

def check_all():
	for filename in os.listdir(data_dir):
		if len(filename) != 3:
			continue
		ans, percentage = quantize(filename)
		if percentage > 0.7 and percentage < 0.85:
			print(filename)

# check_all()





