#! /bin/bash

# requirement and install
# serpent
# pydub

# take one file

FILE_NAME=$1
echo "processing file: " $FILE_NAME

echo "extracting tempo..."
python raw_tempo.py $FILE_NAME 

echo "shifting melody..."
python shift_melody_track.py $FILE_NAME

echo "extracting timestamps..."
serpent64 serpent_get_timestamp.srp $FILE_NAME

echo "chord recognition..."
python exported_midi_chord_recognition/main.py $FILE_NAME

echo "finalizing chord..."
# also writes to begin_time.txt
python finalize_chord_midi_only.py $FILE_NAME

echo "extracting melody..."
serpent64 serpent_melody_extract_2.srp $FILE_NAME 

echo "finding key..."
python key_finding.py $FILE_NAME

