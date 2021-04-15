'''
Given the quantized chords, pick the one that's more right

To consider:
- Modulation
'''

import os, sys
import bisect
import mido
from quantize_and_match_midi_only import quantize
from chord_processing import * 

# data_dir = "../../lmd_melody_track/"
data_dir = ""

'''
piece - a number index that shows which piece of the 909

save file format:
[Cmaj, 1][Dmin, 1][Gmaj, 2]
'''
def finalize(file_name, save_file=False, print_details=False, save_summary=False):
    '''
    quantize return: [(measure, beat, duration, start, end, audio_chord, (midi_chord))]
    duration - in quavers 
    '''
    file_path = "/".join(file_name.split("/")[:-1])

    ans, percentage = quantize(file_name, save_summary=False)

    # if percentage > 0.7:
    #   print("skipped")
    #   return 

    res = []

    # if the midi and audio has large discrepancy, then they are 
    # propably not on the same key and it's better to stick with one of them for consistency. 
    if percentage < 0.7:
        with open(file_path + "/chords_summary.txt", "w") as f:
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
        with open(file_path + "/key_audio.txt", "r") as f:
            keys = [l.split() for l in f.readlines()]
        f.close()
        with open(file_path + "/chords_summary.txt", "w") as f:
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
        with open(file_path + "/finalized_chord.txt", "w") as f:
            for c in res:
                f.write("{} {}\n".format(c[0], c[1]))
        f.close()
        # after save file, need to change format
        finalized_change_format(file_name)
    return res
'''
piece is three digit index
output each line into format:
[symbol, array of chord note, bass, duration]
if the chord is N, then the chord note is [] and bass is ""
'''
def finalized_change_format(file_name):
    file_path = "/".join(file_name.split("/")[:-1])

    with open(file_path + "/finalized_chord.txt") as f:
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

    with open(file_path + "/finalized_chord.txt", "w") as f:
        for c in formatted_chords:
            f.write("{} {} {} {} \n".format(*c))
    f.close()
    with open(file_path + "/begin_time.txt", "w") as f:
        f.write(str(begin_beats))
    f.close()



def run_all():
    for i in range(8476, 8477):
        filename = str(i)
        finalize(filename, save_file=True, save_summary=True)
        print(filename + " done")

# finalize("797", save_file=True, save_summary=True)

# finalize("019", save_summary=True)
# finalized_change_format("025")
# run_all()

def check_all():
    for i in range(1, 8850):
        filename = str(i)
        ans, percentage = quantize(filename)
        if percentage > 0.7 and percentage < 0.85:
            print(filename)

# check_all()

finalize(sys.argv[1], save_file=True, save_summary=True)



