from mir.extractors import ExtractorBase
from io_new.downbeat_io import DownbeatIO
from mir import io
import numpy as np
from pretty_midi import PitchBend,pitch_bend_to_semitones,PrettyMIDI

class MidiBeatExtractor(ExtractorBase):

    def get_feature_class(self):
        return DownbeatIO

    def extract(self,entry,**kwargs):
        extra_division=kwargs['div'] if 'div' in kwargs else 1
        midi=entry.midi
        beats=midi.get_beats()
        if(extra_division>1):
            beat_interp=np.linspace(beats[:-1],beats[1:],extra_division+1).T
            last_beat=beat_interp[-1,-1]
            beats=np.append(beat_interp[:,:-1].reshape((-1)),last_beat)
        downbeats=midi.get_downbeats()
        j=0
        beat_pos=-2
        result=[]
        for i in range(len(beats)):
            if(j<len(downbeats) and beats[i]==downbeats[j]):
                beat_pos=1
                j+=1
            else:
                beat_pos=beat_pos+1
            assert(beat_pos>0)
            result.append([beats[i],beat_pos])
        assert(j==len(downbeats))
        return np.array(result)

def get_pretty_midi_energy_roll(midi, fs=100, times=None):
    """Compute a piano roll matrix of the MIDI data.

    Parameters
    ----------
    fs : int
        Sampling frequency of the columns, i.e. each column is spaced apart
        by ``1./fs`` seconds.
    times : np.ndarray
        Times of the start of each column in the piano roll.
        Default ``None`` which is ``np.arange(0, get_end_time(), 1./fs)``.

    Returns
    -------
    piano_roll : np.ndarray, shape=(128,times.shape[0])
        Piano roll of MIDI data, flattened across instruments.

    """

    # If there are no instruments, return an empty array
    if len(midi.instruments) == 0:
        return np.zeros((128, 0))

    # Get piano rolls for each instrument
    piano_rolls = [get_energy_roll(i, fs=fs, times=times)
                   for i in midi.instruments]
    # Allocate piano roll,
    # number of columns is max of # of columns in all piano rolls
    piano_roll = np.zeros((128, np.max([p.shape[1] for p in piano_rolls])))
    # Sum each piano roll into the aggregate piano roll
    for roll in piano_rolls:
        piano_roll[:, :roll.shape[1]] += roll ** 2
    return np.sqrt(piano_roll)

def get_energy_roll(self, fs=100, times=None):
    """Compute a piano roll matrix of this instrument.

    Parameters
    ----------
    fs : int
        Sampling frequency of the columns, i.e. each column is spaced apart
        by ``1./fs`` seconds.
    times : np.ndarray
        Times of the start of each column in the piano roll.
        Default ``None`` which is ``np.arange(0, get_end_time(), 1./fs)``.

    Returns
    -------
    piano_roll : np.ndarray, shape=(128,times.shape[0])
        Piano roll of this instrument.

    """
    # If there are no notes, return an empty matrix
    if self.notes == []:
        return np.array([[]]*128)
    # Get the end time of the last event
    end_time = self.get_end_time()
    # Extend end time if one was provided
    if times is not None and times[-1] > end_time:
        end_time = times[-1]
    # Allocate a matrix of zeros - we will add in as we go
    piano_roll = np.zeros((128, int(fs*end_time)))
    # Drum tracks don't have pitch, so return a matrix of zeros
    if is_percussive_channel(self):
        if times is None:
            return piano_roll
        else:
            return np.zeros((128, times.shape[0]))
    # Add up piano roll matrix, note-by-note
    for note in self.notes:
        # Should interpolate
        piano_roll[note.pitch,
                   int(note.start*fs):int(note.end*fs)] += (note.velocity/100.0)**2
    piano_roll=np.sqrt(piano_roll)
    # Process pitch changes
    # Need to sort the pitch bend list for the following to work
    ordered_bends = sorted(self.pitch_bends, key=lambda bend: bend.time)
    # Add in a bend of 0 at the end of time
    end_bend = PitchBend(0, end_time)
    for start_bend, end_bend in zip(ordered_bends,
                                    ordered_bends[1:] + [end_bend]):
        # Piano roll is already generated with everything bend = 0
        if np.abs(start_bend.pitch) < 1:
            continue
        # Get integer and decimal part of bend amount
        start_pitch = pitch_bend_to_semitones(start_bend.pitch)
        bend_int = int(np.sign(start_pitch)*np.floor(np.abs(start_pitch)))
        bend_decimal = np.abs(start_pitch - bend_int)
        # Column indices effected by the bend
        bend_range = np.r_[int(start_bend.time*fs):int(end_bend.time*fs)]
        # Construct the bent part of the piano roll
        bent_roll = np.zeros(piano_roll[:, bend_range].shape)
        # Easiest to process differently depending on bend sign
        if start_bend.pitch >= 0:
            # First, pitch shift by the int amount
            if bend_int is not 0:
                bent_roll[bend_int:] = piano_roll[:-bend_int, bend_range]
            else:
                bent_roll = piano_roll[:, bend_range]
            # Now, linear interpolate by the decimal place
            bent_roll[1:] = ((1 - bend_decimal)*bent_roll[1:] +
                             bend_decimal*bent_roll[:-1])
        else:
            # Same procedure as for positive bends
            if bend_int is not 0:
                bent_roll[:bend_int] = piano_roll[-bend_int:, bend_range]
            else:
                bent_roll = piano_roll[:, bend_range]
            bent_roll[:-1] = ((1 - bend_decimal)*bent_roll[:-1] +
                              bend_decimal*bent_roll[1:])
        # Store bent portion back in piano roll
        piano_roll[:, bend_range] = bent_roll

    if times is None:
        return piano_roll
    piano_roll_integrated = np.zeros((128, times.shape[0]))
    # Convert to column indices
    times = np.array(times*fs, dtype=np.int)
    for n, (start, end) in enumerate(zip(times[:-1], times[1:])):
        # Each column is the mean of the columns in piano_roll
        piano_roll_integrated[:, n] = np.mean(piano_roll[:, start:end],
                                              axis=1)
    return piano_roll_integrated



class EnergyPianoRoll(ExtractorBase):

    def get_feature_class(self):
        return io.SpectrogramIO

    def extract(self,entry,**kwargs):
        dt=entry.prop.sr/entry.prop.hop_length
        piano_roll=get_pretty_midi_energy_roll(entry.midi,dt)
        return piano_roll.T






def is_percussive_channel(instrument):
    return instrument.is_drum or instrument.program>112 # todo: are >112 instruments all percussive?

def get_valid_channel_count(midi):
    return len([ins for ins in midi.instruments if not is_percussive_channel(ins)])
