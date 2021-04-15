import numpy as np
import librosa
import mir_eval.chord
from mir.music_base import get_scale_and_suffix


# for cb dataset, please use
# melody_beat_offset=+0.033
# lyric_beat_offset=+0.033
OVERFLOW_WIDTH_LIMIT=32
TABS_WIDTH=1


class AIRStructure:
    '''
    AIR structure is a class to store, import and export symbolic music data by
    jjy.

    AIR is (1) the abbr. of Audio-Informed Representation; (2) the abbr. of the
    name AIRA (in memory of the heroine in the anime <<Plastic Memories>>).
    '''
    def __init__(self,beat,num_beat_division,verbose_level=1,disallow_error=False):
        self.disallow_error=disallow_error
        self.error_log=''
        self.verbose_level=verbose_level
        self.length=(beat.shape[0]-1)*num_beat_division+1
        self.input_beat=beat
        self.num_beat_division=num_beat_division
        self.timing,self.offset,self.is_downbeat,self.is_beat=self.__init_timing_and_offset()
        self.divider=(self.timing[1:]+self.timing[:-1])/2
        self.lyric=np.full(self.length,'',dtype='<U1')
        self.chord=np.full(self.length,'',dtype='<U31')
        self.key=np.ones((self.length),dtype=np.int32)*-1
        # self.previous_chord_pos=np.ones((self.length),dtype=np.int32)*-1
        self.melody=np.ones((self.length),dtype=np.int32)*-1
        self.melody_onset=np.zeros((self.length),dtype=np.bool)
        self.phrase=np.ones((self.length),dtype=np.int32)*-1
        self.phrase_count=0
        self.input_lyric_sentence=[]
        pass

    def log_error(self,message):
        if(self.disallow_error):
            raise Exception(message)
        if(self.verbose_level>=1):
            print(message)
        self.error_log+=message+'\n'

    def __overwrite_warning(self,pos,error_item,time):
        if(pos==0):
            self.log_error('Warning: Too early %s event happened at time %.2f'%(error_item,time))
            return True # allow overwrite
        elif(pos==self.length-1):
            self.log_error('Warning: Too late %s event happened at time %.2f'%(error_item,time))
            return False # disallow overwrite
        else:
            self.log_error('Warning: Overwrite %s event at time %.2f. Music is probably too fast.'%(error_item,time))
            return False # disallow overwrite

    def append_lyric(self,lyric,lyric_beat_offset=0.0):
        if(len(lyric)==0 or len(lyric[0])!=4):
            raise Exception('Unsupported lyric format')
        if(self.phrase_count>0):
            raise Exception('Lyric already appended')
        self.phrase_count=0
        self.input_lyric_sentence=[]
        current_sentence=[]
        for token in lyric:
            start_pos=self.__locate(token[0]-lyric_beat_offset)
            end_pos=self.__locate(token[1]-lyric_beat_offset)
            if(end_pos==start_pos):
                end_pos+=1
            if(token[3]>0):
                self.phrase_count+=1
            supress_warning=False
            allow_write=True
            for pos in range(start_pos,end_pos):
                if(self.lyric[pos]!='' and not supress_warning):
                    supress_warning=True
                    allow_write&=self.__overwrite_warning(pos,'lyric',token[0])
                if(allow_write):
                    self.lyric[pos]='-'
                    self.phrase[pos]=self.phrase_count-1
            if(allow_write):
                self.lyric[start_pos]=token[2]
        p=-1
        p_start=0
        p_end=0
        for pos in range(self.length):
            if(self.phrase[pos]>p):
                self.phrase[p_start:p_end]=p
                p=self.phrase[pos]
                p_start=pos
            elif(self.phrase[pos]==p):
                p_end=pos
        self.phrase[p_start:p_end]=p

    def append_melody(self,midilab,melody_beat_offset=0.0):
        if(len(midilab)==0 or len(midilab[0])!=3):
            raise Exception('Unsupported melody format')
        for token in midilab:
            start_pos=self.__locate(token[0]-melody_beat_offset)
            end_pos=self.__locate(token[1]-melody_beat_offset)
            if(end_pos==start_pos):
                end_pos+=1
            supress_warning=False
            allow_write=True
            for pos in range(start_pos,end_pos):
                if(self.melody[pos]!=-1 and not supress_warning):
                    supress_warning=True
                    allow_write&=self.__overwrite_warning(pos,'melody',token[0])
                if(allow_write):
                    self.melody[pos]=int(np.round(token[2]))
            if(allow_write):
                self.melody_onset[start_pos]=True

    def append_chord(self,chordlab):
        if(len(chordlab)==0 or len(chordlab[0])!=3):
            raise Exception('Unsupported chord format')
        for token in chordlab:
            start_pos=self.__locate(token[0])
            end_pos=self.__locate(token[1])
            if(end_pos==start_pos):
                end_pos+=1
            if(len(token[2])>31):
                raise Exception('Too long chord: %s'%token[2])
            # self.chord[start_pos]=token[2]
            for pos in range(start_pos,end_pos):
                self.chord[pos]=token[2]
        # previous_chord_pos=-1
        # for i in range(self.length):
        #     if(self.chord[i]!=''):
        #         previous_chord_pos=i
        #     self.previous_chord_pos[i]=previous_chord_pos

    def append_key(self,keylab,format='mode7'):
        if(format!='mode7'):
            raise NotImplementedError()
        if(len(keylab)==0 or len(keylab[0])!=3):
            raise Exception('Unsupported key format')
        MODE7_TO_STR=['X','major','dorian','phrygian','lydian','mixolydian','minor','locrian']

        for token in keylab:
            start_pos=self.__locate(token[0])
            end_pos=self.__locate(token[1])
            if(end_pos==start_pos):
                end_pos+=1
            key_id,mode_str=get_scale_and_suffix(token[2])
            mode_str=mode_str[1:]
            if(mode_str=='maj'):
                mode_str='major'
            elif(mode_str=='min'):
                mode_str='minor'
            mode7=MODE7_TO_STR.index(mode_str)
            # self.chord[start_pos]=token[2]
            for pos in range(start_pos,end_pos):
                self.key[pos]=mode7*12+key_id
        for i in range(1,self.length):
            if(self.key[i]==-1):
                self.key[i]=self.key[i-1]
        for i in range(self.length-2,-1,-1):
            if(self.key[i]==-1):
                self.key[i]=self.key[i+1]

    def export_to_array(self,export_all=False):
        # convert chord labels
        original_length=self.length
        valid=np.zeros(original_length,dtype=np.bool)
        bars=[]
        if(self.phrase_count>0 and not export_all):
            for phrase_id in range(self.phrase_count):
                # todo: dangerous!!
                bars+=PhraseRenderer(self,phrase_id).bars
            for bar in bars:
                valid[bar[0]:bar[1]]=True
        else:
            valid[:]=True
        valid[-1]=False
        export_length=int(np.sum(valid))
        export_melody=self.melody[valid].reshape((export_length,1))
        export_melody_onset=self.melody_onset[valid].reshape((export_length,1))
        #todo: chord N+
        #todo: blank chord?
        chord=self.chord[valid]
        if('' in chord):
            #print('Warning: blank chord encountered, regard as N')
            chord=[text if text!='' else 'N' for text in chord]
        export_chord_root,export_chord_chroma,export_chord_bass=mir_eval.chord.encode_many(chord)
        export_chord_chroma=mir_eval.chord.rotate_bitmaps_to_roots(export_chord_chroma,export_chord_root)
        export_chord_root=export_chord_root.reshape((export_length,1))
        export_chord_bass=export_chord_bass.reshape((export_length,1))
        export_downbeat_pos=(self.offset[valid]-1).reshape((export_length,1))
        export_beat_pos=self.is_beat[valid].astype(np.int32)
        # todo: incomplete downbeat
        last_beat_pos=0
        for i in range(export_length):
            if(export_beat_pos[i]):
                last_beat_pos=0
            else:
                last_beat_pos+=1
            export_beat_pos[i]=last_beat_pos
        export_beat_pos=export_beat_pos.reshape((export_length,1))
        export_start=self.timing[valid].reshape((export_length,1))
        export_end=self.timing[1:][valid[:-1]].reshape((export_length,1))
        export_phrase=self.phrase[valid].reshape((export_length,1))
        # ensure compatibility
        export_key=self.key[valid].reshape((export_length,1)) if 'key' in self.__dict__ else np.ones((export_length,1),dtype=np.int32)*-1
        return np.hstack((export_start,export_end)),\
            np.hstack((export_melody,export_melody_onset,export_chord_root,export_chord_chroma,export_chord_bass,export_downbeat_pos,export_beat_pos,export_phrase,export_key))

    def __init_timing_and_offset(self):
        timing=np.zeros((self.length))
        offset=np.zeros((self.length),dtype=np.int32)
        is_downbeat=np.zeros((self.length),dtype=np.bool)
        is_beat=np.zeros((self.length),dtype=np.bool)
        for i in range(self.input_beat.shape[0]):
            if(np.round(self.input_beat[i,1])==1.0):
                is_downbeat[i*self.num_beat_division]=True
            is_beat[i*self.num_beat_division]=True
        for i in range(self.input_beat.shape[0]-1):
            cur_time=self.input_beat[i,0]
            next_time=self.input_beat[i+1,0]
            timing[i*self.num_beat_division:(i+1)*self.num_beat_division+1]=np.linspace(cur_time,next_time,self.num_beat_division+1)
            offset[i*self.num_beat_division:(i+1)*self.num_beat_division]=np.round(self.input_beat[i,1])
        offset[-1]=np.round(self.input_beat[-1,1])
        for i in range(self.length-1):
            assert(timing[i]<timing[i+1])
        return timing,offset,is_downbeat,is_beat

    def __locate(self,time):
        return np.searchsorted(self.divider,time)

class UnitRenderer():
    def __init__(self,air:AIRStructure,pos_start,pos_end):
        self.pos_start=pos_start
        self.air=air
        self.pos_end=pos_end

    def render(self,width,force_chord):
        result=np.full((OVERFLOW_WIDTH_LIMIT,3),'',dtype='<U1')
        air=self.air
        scale=width/(self.pos_end-self.pos_start)
        already_mute=False
        for pos in range(self.pos_start,self.pos_end):
            render_x=int(np.round((pos-self.pos_start)*scale))
            for type in range(3): #for type in ['melody','lyric','chord']
                render_str=''
                if(type==0): #melody
                    if(air.melody_onset[pos]):
                        render_str=librosa.midi_to_note(air.melody[pos])[:2]
                        already_mute=False
                    if(air.melody[pos]==-1 and not already_mute):
                        render_str='0'
                        already_mute=True
                elif(type==1): #lyric
                    if(air.lyric[pos]!='' and air.lyric[pos]!='-'):
                        render_str=air.lyric[pos]
                else: #chord
                    if(pos==0 or air.chord[pos]!=air.chord[pos-1] or (force_chord and pos==self.pos_start)):
                        render_str=air.chord[pos].replace(':','')
                chars=list(render_str)
                render_len=min(len(chars),OVERFLOW_WIDTH_LIMIT-render_x)
                result[render_x:render_x+render_len,type]=chars[:render_len]
        return result

class PhraseRenderer():

    def __init__(self,air:AIRStructure,phrase_id):
        self.air=air
        bars=[]
        is_valid=air.phrase==phrase_id
        valid_index=np.arange(air.length)[is_valid]
        if(len(valid_index)==0):
            air.log_error('Warning: no valid index for phrase %d'%phrase_id)
            self.bars=[]
            return
        max_valid_index=np.max(valid_index)
        if(max_valid_index<air.length-1):
            valid_index=np.append(valid_index,max_valid_index+1)
        # todo: incomplete bar
        prev_bar_pos=-1
        self.weak_start=False
        if(not air.is_downbeat[valid_index[0]]):
            self.weak_start=True
            for index in range(valid_index[0]-1,-1,-1):
                if(air.phrase[index]>=0 and air.phrase[index]!=phrase_id):
                    break
                if(air.is_downbeat[index]):
                    prev_bar_pos=index
                    break
        for index in valid_index:
            if(air.is_downbeat[index]):
                if(prev_bar_pos>=0):
                    bars.append((prev_bar_pos,index,True))
                prev_bar_pos=index
        if(prev_bar_pos!=-1): # no valid complete bar?
            if(not air.is_downbeat[valid_index[-1]]):
                for index in range(valid_index[-1],air.length):
                    if(air.is_downbeat[index]):
                        bars.append((prev_bar_pos,index,True))
                        break
        # self.min_bar_pos=np.min([b[0] for b in bars])
        # self.max_bar_pos=np.max([b[0] for b in bars])
        self.bars=bars


    def render(self,unit_width,bar_group):

        data=np.full((len(self.bars),bar_group,OVERFLOW_WIDTH_LIMIT,3),'',dtype='<U1')
        air=self.air
        for i in range(len(self.bars)):
            bar_start=self.bars[i][0]
            bar_end=self.bars[i][1]
            interp=np.round(np.linspace(bar_start,bar_end,bar_group+1))
            for j in range(bar_group):
                data[i,j,:,:]=UnitRenderer(air,int(interp[j]),int(interp[j+1]))\
                    .render(unit_width,i==0 and j==0)
        return data


    def to_string(self,unit_width,bar_group):

        data=self.render(unit_width,bar_group)
        if(len(data)==0):
            return '(There is a phrase totally included in the previous tab, ignored)\n'
        str=''
        for k in range(3):
            for i in range(len(data)):
                for j in range(len(data[i])):
                    str+=[['╔╟','╦╫'],['╤┼','╤┼']][j>0][i>0][k>0]+'═─'[k>0]*(unit_width//TABS_WIDTH)
            str+='╗╢'[k>0]+'\n'
            for i in range(len(data)):
                budget=0
                for j in range(len(data[i])):
                    if(budget==0):
                        str+='║│'[j>0]
                        budget+=unit_width
                    else: # extra budget for the missing line
                        budget+=unit_width+TABS_WIDTH
                    skip=0
                    for c in data[i][j][:,k]:
                        if(c!='' and ord(c)>256):
                            if(budget>=2):
                                skip+=1
                                str+=c
                                budget-=2
                                continue
                            c='?'
                        if(skip==0 and (c!='' or budget>0)):
                            str+=c if c!='' else ' '
                            budget-=1
                        else:
                            skip-=1
                    if(budget>0):
                        str+=' '*budget
                        budget=0
            str+='║\n'
        for i in range(len(data)):
            for j in range(len(data[i])):
                str+=['╚╩','╧╧'][j>0][i>0]+'═'*(unit_width//TABS_WIDTH)
        str+='╝\n'
        return str


class AIRStructureRenderer():

    def to_string(self,air:AIRStructure,unit_width,bar_group):
        result=''
        if(air.phrase_count==0):
            result+=PhraseRenderer(air,-1).to_string(unit_width,bar_group)+'\n'
        else:
            for phrase_id in range(air.phrase_count):
                result+=PhraseRenderer(air,phrase_id).to_string(unit_width,bar_group)+'\n'
        result=air.error_log+'\n'+result
        return result
