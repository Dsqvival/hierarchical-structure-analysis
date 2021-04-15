import numpy as np
from mir import io
from chord_class import ChordClass
from extractors.midi_utilities import is_percussive_channel

class ChordRecognition:

    def __init__(self,entry,decode_chord_class:ChordClass,half_beat_switch=True):
        '''
        Initialize a chord recognizer for an entry
        :param entry: an instance of DataEntry with these proxies
            - midi (IO type: MidiIO)
            - beat (IO type: DownbeatIO): the corresponding downbeats & beats of the midi.
        :param decode_chord_class: An instance of ChordClass
        '''
        self.entry=entry
        self.chord_class=decode_chord_class
        self.half_beat_switch=half_beat_switch

    def process_feature(self,channel_weights):
        '''
        First step of chord recognition
        :param channel_weights: weights for each channel. If uniform, input [1, ..., 1].
        :return: Nothing. Calculated features are stored in the class.
        '''
        SUBBEAT_COUNT=8

        entry=self.entry
        midi=entry.midi
        beat=np.array(entry.beat)
        n_frame=len(beat)
        qt_beat_onset=np.zeros(n_frame)
        qt_beat_offset=np.zeros(n_frame)
        qt_beat_length=np.zeros(n_frame)
        beat_chroma=np.zeros((n_frame,12))
        beat_bass=np.zeros((n_frame,12))
        min_subbeat_bass=np.full((n_frame*SUBBEAT_COUNT,),259,dtype=np.int)
        notes=[]
        for i in range(n_frame):
            qt_beat_onset[i]=beat[i,0]
            qt_beat_offset[i]=beat[i,0]+(beat[i,0]-beat[i-1,0]) if i==n_frame-1 else beat[i+1,0]
            qt_beat_length[i]=beat[i+1,0]-beat[i,0] if i<n_frame-1 else qt_beat_length[i-1]
        timing=np.vstack((qt_beat_onset,qt_beat_offset)).T
        def quantize(time):
            if(time<=qt_beat_onset[0]):
                return 0.0
            if(time>=qt_beat_offset[-1]):
                return n_frame+0.0
            beat_id=np.searchsorted(qt_beat_onset,time,side='right')-1
            return beat_id+(time-qt_beat_onset[beat_id])/qt_beat_length[beat_id]
        i=0
        def clamp(qstart,qend,bstart,bend):
            return min(bend,qend)-max(qstart,bstart)
        for instrument in midi.instruments:
            if(is_percussive_channel(instrument)):
                continue
            raw_notes=instrument.notes
            for note in raw_notes:
                beat_start=quantize(note.start)
                beat_end=quantize(note.end)
                left_beat=int(np.floor(beat_start+0.2))
                right_beat=int(np.ceil(beat_end-0.2))
                left_subbeat=int(np.floor(beat_start*SUBBEAT_COUNT+0.2))
                right_subbeat=int(np.floor(beat_end*SUBBEAT_COUNT+0.2))
                if(right_beat<left_beat):
                    right_beat=left_beat
                for j in range(left_subbeat,right_subbeat):
                    min_subbeat_bass[j]=min(min_subbeat_bass[j],note.pitch) # todo: weighted bass
                for j in range(left_beat,right_beat):
                    beat_chroma[j][note.pitch%12]=max(beat_chroma[j][note.pitch%12],
                        clamp(beat_start,beat_end,j,j+1)*channel_weights[i])

            i+=1
        for i in range(SUBBEAT_COUNT):
            update_terms=min_subbeat_bass[i::SUBBEAT_COUNT]
            valid_indices=update_terms<259
            beat_bass[valid_indices,update_terms[valid_indices]%12]+=1./SUBBEAT_COUNT
        # beat_chroma=np.maximum(beat_chroma,beat_bass)
        entry.append_data((timing,beat_chroma),io.RegionalSpectrogramIO,'chroma')
        entry.append_data((timing,beat_bass),io.RegionalSpectrogramIO,'bass')
        #entry.visualize(['chroma','bass','midi'])
        self.beat_chroma=beat_chroma
        self.beat_bass=beat_bass
        self.n_frame=n_frame
        self.is_downbeat=beat[:,1]==1
        self.is_halfdownbeat=beat[:,1]*2-2==beat[:,1].max()
        self.is_even_beat=beat[:,1]%2==1
        self.qt_beat_onset=qt_beat_onset
        self.qt_beat_offset=qt_beat_offset


    def decode(self):
        '''
        Second step of chord recognition.
        :return: optimal path by dynamic programming
        '''
        MAX_PREV=12
        n_frame=self.n_frame
        beat_bass=self.beat_bass
        beat_chroma=self.beat_chroma
        n_class=self.chord_class.get_length()
        dp=np.full(n_frame,-np.inf)
        prec=np.zeros((n_frame),dtype=np.int)
        prei=np.zeros((n_frame),dtype=np.int)
        obs=np.full((n_frame,MAX_PREV,n_class),-np.inf)
        batch_chroma=np.zeros((n_frame,MAX_PREV,12))
        batch_bass_chroma=np.zeros((n_frame,MAX_PREV,12))
        for i in range(n_frame):
            for j in range(MAX_PREV):
                if(i-j<0):
                    continue
                batch_chroma[i,j,:]=np.sum(beat_chroma[i-j:i+1,:],axis=0)
                batch_bass_chroma[i,j,:]=np.sum(beat_bass[i-j:i+1,:],axis=0)

        batch_score=self.chord_class.batch_score(batch_chroma.reshape((-1,12)),batch_bass_chroma.reshape((-1,12)))\
            .reshape((n_frame,MAX_PREV,n_class))

        for i in range(n_frame):
            for j in range(MAX_PREV):
                if(i-j<0):
                    continue
                #batch_chroma[i,j,:]=np.sum(beat_chroma[i-j:i+1,:],axis=0)
                #batch_bass_chroma[i,j,:]=np.sum(beat_bass[i-j:i+1,:],axis=0)
                #print(self.chord_class.score(batch_chroma[i,j,:],batch_bass_chroma[i,j,:])[1],batch_score[i,j][1])
                obs[i,j,:]=batch_score[i,j]+j*0.7+self.is_halfdownbeat[i-j]*0.15+self.is_even_beat[i-j]*0.2

        for i in range(n_frame):
            for j in range(MAX_PREV):
                if(i-j<0):
                    continue
                bestc=np.argmax(obs[i,j,:])
                prev=0.0 if i-j==0 else dp[i-j-1]
                if(dp[i]<prev+obs[i,j,bestc]):
                    dp[i]=prev+obs[i,j,bestc]
                    prec[i]=bestc
                    prei[i]=i-j-1
                if(j>0 and self.is_downbeat[i-j+1]):
                    break
        current_i=n_frame-1
        result=[]
        while(current_i>=0):
            prev_i=prei[current_i]
            prev_c=prec[current_i]
            start=prev_i+1 if self.half_beat_switch or self.is_even_beat[prev_i+1]  else prev_i+2
            end=current_i if self.half_beat_switch or current_i==n_frame-1 or self.is_even_beat[current_i+1]  else current_i+1
            result.append([self.qt_beat_onset[start],self.qt_beat_offset[end],self.chord_class.chord_list[prev_c]])
            current_i=prev_i
        result=result[::-1]
        #print(dp)
        #entry.visualize(['chord_hmm','beat','chroma','bass'])
        return result
