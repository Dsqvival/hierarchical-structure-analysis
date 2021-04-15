import os, sys
from mido import MidiFile
import mido
import random
import pretty_midi
from copy import deepcopy

# data_dir = "../../lmd_melody_track/"

# for i in range(1, 8850):
#     filedirname = str(i)
#     file_dir = data_dir + filedirname + "/"
#     already = False
#     for fname in os.listdir(file_dir):
#         full_name = file_dir + fname
#         if full_name[-9:] == "shift.mid":
#             already = True

#     if already is False:
#         full_name = data_dir + filedirname + "/" + filedirname + ".mid"
#         print(full_name)
#         mf = MidiFile(full_name)
#         flag = 0
#         for j, track in enumerate(mf.tracks):
#             if track.name == 'melody' or track.name == 'Melody' or track.name == 'MELODY':
#                 flag = j
#         if flag > 1:
#             tmp_track = deepcopy(mf.tracks[1])
#             mf.tracks[1] = deepcopy(mf.tracks[flag])
#             mf.tracks[flag] = deepcopy(tmp_track)
#         mf.save(full_name[:-3] + "_shift.mid")   


file_name = sys.argv[1]
file_path = "/".join(file_name.split("/")[:-1])

# print(file_name)
mf = MidiFile(file_name)
flag = 0
for j, track in enumerate(mf.tracks):
    if track.name == 'melody' or track.name == 'Melody' or track.name == 'MELODY':
        flag = j
if flag > 1:
    tmp_track = deepcopy(mf.tracks[1])
    mf.tracks[1] = deepcopy(mf.tracks[flag])
    mf.tracks[flag] = deepcopy(tmp_track)
mf.save(file_name[:-4] + "_shift.mid")   

