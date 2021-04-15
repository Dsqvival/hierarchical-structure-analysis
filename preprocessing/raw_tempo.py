'''
tempo extraction
'''
import os, sys
from mido import MidiFile
import mido


# for i in range(8401, 8779):
# 	piece = str(i + 1)

# 	file = "../../lmd_melody_track/{}/{}.mid".format(piece, piece)
# 	midiFile = mido.MidiFile(file, clip=True)
# 	events = [e.tempo for e in midiFile.tracks[0] if e.type == "set_tempo"]
# 	beat_length = mido.tick2second(120, 480, events[0])
# 	print(15.0 / beat_length)
# 	f = open("../../lmd_melody_track/{}/tempo.txt".format(piece), "w")
# 	f.write(str(int(15.0 / beat_length)))
# 	f.close()

file_name = sys.argv[1]
file_path = "/".join(file_name.split("/")[:-1])

midiFile = mido.MidiFile(file_name)
events = [e.tempo for e in midiFile.tracks[0] if e.type == "set_tempo"]
beat_length = mido.tick2second(120, 480, events[0])

# print(15.0 / beat_length)
with open("{}/tempo.txt".format(file_path), "w") as f:
	f.write(str(int(15.0 / beat_length)))

