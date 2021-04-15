import pretty_midi
from extractors.midi_utilities import is_percussive_channel
import numpy as np

def get_channel_thickness(piano_roll):
    chroma_matrix = np.zeros((piano_roll.shape[0],12))
    for note in range(12):
        chroma_matrix[:, note] = np.sum(piano_roll[:,note::12], axis=1)
    thickness_array=(chroma_matrix>0).sum(axis=1)
    if(thickness_array.sum()==0):
        return 0
    return thickness_array[thickness_array>0].mean()

def get_channel_bass_property(piano_roll):
    result=np.argwhere(piano_roll>0)[:,1]
    if(len(result)==0):
        return 0.0,1.0
    return result.mean(),min(1.,len(result)/len(piano_roll))

def midi_to_thickness_weights(midi):
    thickness=np.array([get_channel_thickness(ins.get_piano_roll().T) for ins in midi.instruments if not is_percussive_channel(ins)])
    result=1-np.exp(-(thickness-0.95))
    result/=result.max()
    return result

def midi_to_thickness_and_bass_weights(midi):
    rolls=[ins.get_piano_roll().T for ins in midi.instruments if not is_percussive_channel(ins)]
    thickness=np.array([get_channel_thickness(roll) for roll in rolls])
    bass=np.array([get_channel_bass_property(roll) for roll in rolls])
    bass[bass[:,1]<0.2,0]=128
    result=1-np.exp(-(thickness-0.95))
    result/=result.max()
    result[np.argmin(bass[:,0])]=1.0

    return result


