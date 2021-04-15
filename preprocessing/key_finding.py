'''
key_finding.py
Kristin

given a list of chord, parse the best key sequene from the chord

reference:
Krumhansl-Schmuckler key-finding algorithm
http://rnhart.net/articles/key-finding/ 

'''

import sys, os
import numpy as np
from music21 import * 
from mido import *
import mido

# data_dir = "../POP909/"
data_dir = "../../lmd_melody_track/"

# from Krumhansl-Schmuckler key profile
mj_c = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
mi_c = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
# mj_c = [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1]
# mj_cs = [1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0]
# mi_c = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1]

knames = ["C:maj", "Db:maj", "D:maj", "Eb:maj", "E:maj", "F:maj", 
          "Gb:maj", "G:maj", "Ab:maj", "A:maj", "Bb:maj", "B:maj",
          "C:min", "Db:min", "D:min", "Eb:min", "E:min", "F:min", 
          "Gb:min", "G:min", "Ab:min", "A:min", "Bb:min", "B:min"]

pfifth = {"C:maj" : "G:maj", "Db:maj" : "Ab:maj", "D:maj" : "A:maj", "Eb:maj" : "Bb:maj", "E:maj" : "B:maj", "F:maj" : "C:maj", 
          "Gb:maj" : "Db:maj", "G:maj" : "D:maj", "Ab:maj" : "Eb:maj", "A:maj" : "E:maj", "Bb:maj" : "F:maj", "B:maj" : "Gb:maj",
          "C:min" : "G:min", "Db:min" : "Ab:min", "D:min" : "A:min", "Eb:min" : "Bb:min", "E:min" : "B:min", "F:min" : "C:min", 
          "Gb:min" : "Db:min", "G:min" : "D:min", "Ab:min" : "Eb:min", "A:min" : "E:min", "Bb:min" : "F:min", "B:min" : "Gb:min"}   

equal_symbol = {"C" : "B#", "C#" : "Db", "D#" : "Eb", "E" : "Fb", "E#" : "F", "F#" : "Gb", "G#" : "Ab", "A#" : "Bb", "B" : "Cb",
                "B#" : "C", "Db" : "C#", "Eb" : "D#", "Fb" : "E", "F" : "E#", "Gb" : "F#", "Ab" : "G#", "Bb" : "A#", "Cb" : "B",
                "D" : "D", "G" : "G", "A": "A"}     

MIDI_symbol = {60: "C", 61: "C#", 62: "D", 63: "D#", 64: "E", 65: "F", 66: "F#", 67: "G", 68: "G#", 69: "A", 70: "A#", 71: "B"} 

scale_pitch = { "C:maj" : ["C", "D", "E", "F", "G", "A", "B"], 
                "Db:maj" : ["C#", "D#", "E#", "F#", "G#", "A#", "B#"], 
                "D:maj" : ["C#", "D", "E", "F#", "G", "A", "B"], 
                "Eb:maj" : ["C", "D", "Eb", "F", "G", "Ab", "Bb"], 
                "E:maj" : ["C#", "D#", "E", "F#", "G#", "A", "B"], 
                "F:maj" : ["C", "D", "E", "F", "G", "A", "Bb"], 
                "Gb:maj" : ["Cb", "Db", "Eb", "F", "Gb", "Ab", "Bb"], 
                "G:maj" : ["C", "D", "E", "F#", "G", "A", "B"], 
                "Ab:maj" : ["C", "Db", "Eb", "F", "G", "Ab", "Bb"], 
                "A:maj" : ["C#", "D", "E", "F#", "G#", "A", "B"], 
                "Bb:maj" : ["C", "D", "Eb", "F", "G", "A", "Bb"], 
                "B:maj" : ["C#", "D#", "E", "F#", "G#", "A#", "B"],
                "C:min" : ["C", "D", "Eb", "F", "G", "Ab", "Bb", "B", "A"], 
                "Db:min" : ["C#", "D#", "E", "F#", "G#", "A", "B", "C", "Bb"], 
                "D:min" : ["C", "D", "E", "F", "G", "A", "Bb", "C#", "B"], 
                "Eb:min": ["Cb", "Db", "Eb", "F", "Gb", "Ab", "Bb", "D", "C"], 
                "E:min" : ["C", "D", "E", "F#", "G", "A", "B", "Eb", "C#"], 
                "F:min" : ["C", "Db", "Eb", "F", "G", "Ab", "Bb", "E", "D"], 
                "Gb:min" : ["C#", "D", "E", "F#", "G#", "A", "B", "F", "D#"], 
                "G:min" : ["C", "D", "Eb", "F", "G", "A", "Bb", "F#", "E"], 
                "Ab:min" : ["C#", "D#", "E", "F#", "G#", "A#", "B", "G", "F"], 
                "A:min" : ["C", "D", "E", "F", "G", "A", "B", "G#", "F#"], 
                "Bb:min" : ["C#", "D#", "E#", "F#", "G#", "A#", "B#", "A", "G"], 
                "B:min" : ["C#", "D", "E", "F#", "G", "A", "B", "A#", "G#"]}                      

majors, minors = [], []

for i in range(12):
    tmp = mj_c[-i:] + mj_c[:-i]
    majors.append(tmp)
    tmp = mi_c[-i:] + mi_c[:-i]
    minors.append(tmp)

keys = majors + minors

global count
'''
return the correlation coefficient to tell how close the stats is to the key
'''
def score(stats, key):
    return np.corrcoef(stats, key)[1, 0]

'''
given the a chord sequence[start: end], compare the statistics
to each kind of the scale, return the most likely key (in string)
and a confidence score
'''
def match_scales(start, end, chords):
    start = min(start, end)
    end = max(start, end)

    chords = chords[start: end]
    stats = np.sum(np.array(chords), axis=0)
    #print(stats)

    scores = [score(stats, k) for k in keys]
    confidence = max(scores)
    key = scores.index(confidence)

    #print(scores)
    #print(keys[key])

    return knames[key], confidence

def match_scales_acc_chord(scale, start, end, chords):
    start = min(start, end)
    end = max(start, end)

    chords = chords[start: end]
    stats = np.sum(np.array(chords), axis=0)

    return score(stats, keys[knames.index(scale)])

# change the pitch class representation of chord into binary representation
def to_binary(chord):
    ans = [0] * 12
    for n in chord:
        ans[n] += 1
    return ans


'''
given the name of the piece, read the finalized chord from saving
output of the chords are of their pitch class, i.e:
[[2, 7, 10], [0, 4, 9]]

'''
def get_chord_seq(file_name):
    file_path = "/".join(file_name.split("/")[:-1])
    with open("{}/finalized_chord.txt".format(file_path), "r") as f:
        chords = f.readlines()
    f.close()
    notes = [(c.split("[")[1]).split("]")[0].split(", ") for c in chords]
    notes = [[] if '' in n else n for n in notes]
    durs = [int(c.split()[-1]) for c in chords]
    chords = [to_binary(list(map(int, c))) for c in notes]
    chords = [np.array(chords[i]) * durs[i] for i in range(len(chords))]
    return chords

def get_first_last_chord(file_name):
    file_path = "/".join(file_name.split("/")[:-1])
    with open("{}/finalized_chord.txt".format(file_path), "r") as f:
        chords = f.readlines()
    f.close()
    c1 = chords[0].split(":")[0]
    c2 = chords[-1].split(":")[0]
    return c1, c2

def get_pitch_seq(file_name):
    file_path = "/".join(file_name.split("/")[:-1])
    with open("{}/melody.txt".format(file_path), "r") as f:
        pitches = f.readlines()
    f.close()
    pvector = [int(p.split(" ")[0]) for p in pitches]
    durs = [int(p.split(" ")[1]) for p in pitches]

    pfinal = []
    for i in range(len(pvector)):
        if pvector[i] > 0:
            p1 = pvector[i]
            while p1 < 60:
                p1 = p1 + 12
            while p1 > 71: 
                p1 = p1 - 12
            for j in range(durs[i]):    
                pfinal.append(MIDI_symbol[p1])      
    return pfinal

def match_scales_acc_pitch(scale, pitches):
    candidates = scale_pitch[scale]
    # print(scale, pitches, candidates)
    pcount = 0
    for p in pitches:
        if (p in candidates) or (equal_symbol[p] in candidates):
            pcount = pcount + 1
    return float(pcount) / float(len(pitches))    

def match_scales_melody(pitches):
    scores = [match_scales_acc_pitch(k, pitches) for k in knames]
    confidence = max(scores)
    key = scores.index(confidence)
    return knames[key], confidence   



# run_all()
# get_chord_seq("569")

# def write_correct_key():
#   with open("key_label.txt") as f:
#       tmp_keys = f.readlines()
#   f.close()
#   keys = [[line.split(" ")[0], (line.split(" ")[1]).split('\n')[0]]for line in tmp_keys]
#   for k in keys:
#       with open(data_dir + k[0] + "/analyzed_key.txt", "w") as f:
#           f.write("{}\n".format(k[1]))
#       f.close()

# write_correct_key()   

def calculate_time_sig(file_name):
    file_path = "/".join(file_name.split("/")[:-1])
    mf = mido.MidiFile(file_name)
    result = []
    for i, track in enumerate(mf.tracks):
        # print('Track {}: {}'.format(i, track.name))
        for msg in track:
            if msg.is_meta and msg.type == 'time_signature':
                # print(file_name, ":", msg.numerator, msg.denominator, "done")
                result.append([msg.numerator, msg.denominator])
    
    with open("{}/time_signature.txt".format(file_path), "w") as f:
        for x in result:
            f.write("{} {}\n".format(x[0], x[1]))
    f.close()

def calculate_key_sig(file_name):
    file_path = "/".join(file_name.split("/")[:-1])
    chords = get_chord_seq(file_name)
    c1, c2 = get_first_last_chord(file_name)
    pitches = get_pitch_seq(file_name)
    n = len(chords)

    if len(pitches) == 0:
        print(file_name, ": NO melody!")
        return

    if len(chords) == 0:
        print(file_name, ": No chord!")
        return

    key_chord, confidence_chord = match_scales(0, n, chords)
    key_melody, confidence_melody = match_scales_melody(pitches)

    if key_chord == key_melody:
        key = key_chord
    else:
        chord_pitch_acc = match_scales_acc_pitch(key_chord, pitches)
        candidates = []
        best = []
        for tmp_k in knames:
            if match_scales_acc_pitch(tmp_k, pitches) > chord_pitch_acc and match_scales_acc_chord(tmp_k, 0, n, chords) + 0.1 > confidence_chord:
                candidates.append([tmp_k, match_scales_acc_chord(tmp_k, 0, n, chords), match_scales_acc_pitch(tmp_k, pitches)])
        best = [key_chord, confidence_chord, chord_pitch_acc]    
        for x in candidates:
            if x[1] * x[2] > best[1] * best[2]:
                best = x
        key = best[0]  

        if candidates != []: 
            candidates.append([key_chord, confidence_chord, chord_pitch_acc])       
            # print(piece, " : ", best, candidates)          


    with open("{}/analyzed_key.txt".format(file_path), "w") as f:
        f.write("{}\n".format(key))
    f.close()
    return key

def run_all_lakh():
    data_dir = "../../lmd_melody_track"
    # data_dir = "POP909"
    for i in range(8308, 8850):
        filename = str(i)
        print(filename + " ...")
        # get_correspondance(filename)
        calculate_key_sig(filename)
        # print(filename + " done")

# run_all_lakh()

file_name = sys.argv[1]
calculate_key_sig(file_name)
calculate_time_sig(file_name)


