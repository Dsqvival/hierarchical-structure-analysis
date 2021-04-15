# Code and dataset for paper: Automatic Analysis and Influence of Hierarchical Structure on Melody, Rhythm and Harmony in Popular Music 

Published at @ Mume + CSMC 2021
paper link: https://www.cs.cmu.edu/~rbd/papers/dai-mume2020.pdf

## Directory
./POP909/                                   --------------------------   POP909 dataset after preprocessing  
./POP909/song_id/                           --------------------------   for each song  
./POP909/song_id/analyzed_key.txt           --------------------------   analyzed key signatures  
./POP909/song_id/finalized_chord.txt        --------------------------   analyzed chord progression  
                                                                         each line is a chord  
                                                                         format: chord_name  [chord tones] root_note duration  
                                                                         e.g. B:maj [3, 6, 11] 11 2  
                                                                         This is a B:maj chord lasts for 2 beats (beat = quater note)  
                                                                         chord tones and root note are using numbers from 0 to 11  
                                                                         representing C to B, here 11 means B, which is the root of the chord  
                                                                         chord tones [3, 6, 11] means D#,  F#,  B                                                                 
./POP909/song_id/melody.txt                 --------------------------   melody notes quantized in 16th note  
                                                                         each line represents a melody note  
                                                                         format: MIDI_note_number  duration  
                                                                         e.g. 60 4  means a quarter note C4   
                                                                              59 1  means a 16th note B3  
                                                                              when the MIDI_note_number  = 0, means Rest note  
./POP909/song_id/tempo.txt                  --------------------------   an integer represents tempo   
                                                                       (only pick up the first tempo when there are multiple tempos in the MIDI file)  
./POP909/song_id/human_label1.txt           --------------------------   human label results of the structure anlaysis. 
./POP909/song_id/human_label2.txt                                        both two files are correct, with different labeling preferences  

./preprocessing/                            --------------------------   preprocessing steps of MIDI, details see the README file in its folder  

./seg.cpp                                   --------------------------   main program for the structure analysis algorithm  


NOTICE: in the original POP909 dataset, the downbeats of the MIDI piano roll are not aligned with the correct barlines. Here we manually deleted the wrong offsets, and aligned the downbeats to the barlines for "melody.txt" and "finalized_chord.txt". When refers to the original MIDI file, please be reminded that the offsets might be different.



## Requirement
C++
if you are going to use the preprocessing program, refer to the README doc in /preprocessing


## Usage
For preprocessing steps, see README doc in /preprocessing  

After preprocessing, the structure analysis, command line:  
g++ -std=c++11 -o seg seg.cpp  
./seg [song_id]  
