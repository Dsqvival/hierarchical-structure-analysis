'''
Some notes on MIDI timing, beat and tempo 
I found our data does include the tempo of the piece. 

- 	The tempo information is shown in the first track (meta track), 
	together with the time signature. It reads "the duration of a quater note
	in microseconds". In following example: 
	666667 microseconds ~ 2/3 seconds, so that's equivalent to 90 bpm. 
	Logic Pro X will visualize it at the top. 
-	In midi the notion of beat is equivalent to quater note. Since quater note
	can certainly be subdivided, the midi events are labeled in ticks, which
	represent the 'resolution' of the midi. This information is not in the tracks
	but in the midi header, as the following reads 480 ticks per quater note. 
	Each event is labeled with the DeltaTick as timestamp, that's the # of ticks
	from the previous event. 
-	Together using the tempo and PPQ, we can locate each midi event in terms of 
	seconds, and thus align with the audio. The tempo is subjective to change: 
	in the following example(331.mid) the Tempo changes after 63 tick, and then 
	changed back after another 8577 ticks. (in fact it's just changed from 90bpm
	to 91 bpm.) So attention need to be paid when translating ticks into seconds, 
	in the audio, as the tempo might change. 
------------
MFile 1 4 480
MTrk
TimestampType=Delta
0 Tempo 666667
0 TimeSig 4/4 24 8
0 KeySig 0 major
63 Tempo 659341
8577 Tempo 666667
1 Meta TrkEnd
TrkEnd
MTrk
TimestampType=Delta
0 Meta TrkName "MELODY"
0 PrCh ch=1 p=0
8404 On ch=1 n=72 v=114
296 On ch=1 n=72 v=0
184 On ch=1 n=72 v=116
.
.
.
-------------
Reference: 
Timing in MIDI files: https://sites.uci.edu/camp2014/2014/05/19/timing-in-midi-files/ 
this translate midi binary into text above: http://flashmusicgames.com/midi/mid2txt.php 


Note: 
I discovered that
the "beat" unit in the finalized_chord is neither a beat (quater note) in the 
midi notation, nor a sixteenth note, but an EIGHTH NOTE relative to the
midi ticks. for example the 331, the tempo is ~90bpm, thus a beat is 0.66s,
while the output documents 4 Cmaj chords in duration (1.00 - 2.33)s (see chords_summary.txt),
that's 0.33s per unit, which is exactly half of a beat = eigth note. 
looking at the score visualization in logic or musescore also shows that 
the duration of Cmaj chord is 4 eighth notes, not sixteenth...
'''

import os
from music21 import *
from mido import MidiFile
import mido

data_dir = "POP909/"

def raw_melody(piece, print_details=False):
    file = "POP909/{}/{}.mid".format(piece, piece)
    mid = MidiFile(file)

    abs_time = 0
    mldy_events_seconds = []
    mldy_events_ticks = []
    mldy_events = []
    for msg in mid:
        # time.sleep(msg.time)
        abs_time += msg.time

        if (not msg.is_meta) and msg.channel==0:
            msg.time = abs_time
            mldy_events_seconds.append(msg)
            # print(msg)

    for msg in mid.tracks[1]:
        if not msg.is_meta:
            mldy_events_ticks.append(msg)
            # print(msg)

    for idx, msg in enumerate(mldy_events_ticks):
        if msg.type == "note_on" and msg.velocity == 0:
            mldy_e = {"note": msg.note,
                    "time_start": mldy_events_seconds[idx-1].time,
                    "time_end": mldy_events_seconds[idx].time,
                    "duration": msg.time}
            mldy_events.append(mldy_e)
        # print(msg)
        # print(mldy_events_seconds[idx])
    if print_details:
        for e in mldy_events:
            print(e)
    return mldy_events



'''
melody_extraction
input: piece is three digit index as string
output: the melody in the form of:
	[MIDI_num, number of sixteenth notes] or
	[0, number of sixteenth notes]
The starting position is the same as the finalized_chord analysis, 
with an offset of begin_time, that's in the begin_time.txt
'''
def melody_extraction(piece, save_file=False):
	# starting time in second
	piece_dir = data_dir + piece + "/"
	with open(piece_dir + "begin_time.txt", "r") as f:
		begin_time = float(f.read())
	f.close()

	file = "POP909/{}/{}.mid".format(piece, piece)

	raw_mldy = raw_melody(piece)

	midiFile = mido.MidiFile(file, clip=True)
	tempo = midiFile.tracks[0][0].tempo
	beat_length = mido.tick2second(120, 480, tempo) 

	melody = []
	melody.append([0, 0, int(round((float(raw_mldy[0]["time_start"]) - begin_time) / beat_length))])

	# the same quantize method as the chord, given the starting and ending time 
	# of the note in seconds
	for i in range(len(raw_mldy)):
		note = []
		note.append(raw_mldy[i]["note"])
		note.append(int(round((float(raw_mldy[i]["time_start"]) - begin_time) / beat_length)))
		note.append(int(round((float(raw_mldy[i]["time_end"]) - begin_time) / beat_length)))
		
		# some note duration is especially short (like staccato), to prevent it
		# having duration 0, we add to the time_end. So this means that for any
		# note it at least has duration of a sixteenth
		if note[-1] == note[-2]:
			note[-1] += 1
		melody.append(note)

	# for m in melody:
	# 	print(m)

	# fill the middle with rests
	tmp = []
	for idx, m in enumerate(melody):
		dur = m[2] - m[1]
		if idx > 0 and m[1] > melody[idx-1][2]:
			tmp.append([0, m[1] - melody[idx-1][2]])
		tmp.append([m[0], dur])

	melody = tmp

	if save_file:
		with open(piece_dir + "melody.txt", "w") as f:
			for m in melody:
				f.write("{} {}\n".format(*m))
		f.close()

	return melody

def run_all():
	for filename in os.listdir("POP909"):
		print(filename + " ...")
		if len(filename) != 3:
			continue
		melody_extraction(filename, save_file=True)
		print(filename + " done")


# melody_extraction("001", save_file=True)
# run_all()


'''
this function run through the files to see how many times set_tempo (tempo change) 
happens in each file. Some files have a lot of change of tempo, but
after examine them, it's actually very small and nuanced change,
like from 90 bpm to 91 bpm.

Note: In quantize_and_match that processes the chords, we actully ignored
the change of tempo and only used the inital tempo to quantize chord...  
so I wrote this function to make sure that we are fine... since the tempo change 
is not super influential...
and for the purpose of alignment, the melody extraction is also using
the fixed tempo to be aligned with the chord... 
'''
def check_change_tempo():
	for filename in os.listdir("POP909"):
		print("file: {}".format(filename))
		if len(filename) != 3:
			continue
		file_dir = data_dir + filename + "/" + filename + ".mid"
		mf = MidiFile(file_dir)
		events = [e.tempo for e in mf.tracks[0] if e.type == "set_tempo"]
		if len(events) > 1:
			print(filename + ": " + str(len(events)) + " times.")
			print(events)


check_change_tempo()

