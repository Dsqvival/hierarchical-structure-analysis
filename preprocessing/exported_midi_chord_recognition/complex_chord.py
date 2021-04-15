from __future__ import print_function
import numpy as np

def get_scale_and_suffix(name):
    result="C*D*EF*G*A*B".index(name[0])
    prefix_length=1
    if (len(name) > 1):
        if (name[1] == 'b'):
            result = result - 1
            if (result<0):
                result+=12
            prefix_length=2
        if (name[1] == '#'):
            result = result + 1
            if (result>=12):
                result-=12
            prefix_length=2
    return result,name[prefix_length:]

def scale_name_to_value(name):
    result="1*2*34*5*6*78*9".index(name[-1]) # 8 and 9 are for weird tagging in some mirex chords
    return (result-name.count('b')+name.count('#')+12)%12

NUM_TO_ABS_SCALE=['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B']

def enum_to_list(cls,valid_only):
    items=[item for item in cls.__dict__.items() if not item[0].startswith('_') and (not valid_only or item[1]>=0)]
    return sorted(items, key=lambda items:items[1])

def enum_to_dict(cls):
    return {item[1]:item[0] for item in cls.__dict__.items() if not item[0].startswith('_')}

class TriadTypes:
    x=-2
    none=0
    maj=1
    min=2
    sus4=3
    sus2=4
    dim=5
    aug=6
    power=7
    one=8
    # warning: before adding new chord, consider change the data type to
    # int16 instead of int8
class SeventhTypes:
    unknown=-2
    not_care=-1
    none=0
    add_7=1
    add_b7=2
    add_bb7=3

class NinthTypes:
    unknown=-2
    not_care=-1
    none=0
    add_9=1
    add_s9=2
    add_b9=3

class EleventhTypes:
    unknown=-2
    not_care=-1
    none=0
    add_11=1
    add_s11=2

class ThirteenthTypes:
    unknown=-2
    not_care=-1
    none=0
    add_13=1
    add_b13=2
    add_bb13=3

class SuffixDecoder:
    BASIC_TYPES=['.','maj','min','sus4','sus2','dim','aug','5','1']
    EXTENDED_TYPES={
        'maj6':[TriadTypes.maj,0,0,0,ThirteenthTypes.add_13],
        'min6':[TriadTypes.min,0,0,0,ThirteenthTypes.add_13],
        '7':[TriadTypes.maj,SeventhTypes.add_b7,0,0,0],
        'maj7':[TriadTypes.maj,SeventhTypes.add_7,0,0,0],
        'min7':[TriadTypes.min,SeventhTypes.add_b7,0,0,0],
        'minmaj7':[TriadTypes.min,SeventhTypes.add_7,0,0,0],
        'dim7':[TriadTypes.dim,SeventhTypes.add_bb7,0,0,0],
        'hdim7':[TriadTypes.dim,SeventhTypes.add_b7,0,0,0],
        '9':[TriadTypes.maj,SeventhTypes.add_b7,NinthTypes.add_9,0,0],
        '#9':[TriadTypes.maj,SeventhTypes.add_b7,NinthTypes.add_s9,0,0],
        'maj9':[TriadTypes.maj,SeventhTypes.add_7,NinthTypes.add_9,0,0],
        'min9':[TriadTypes.min,SeventhTypes.add_b7,NinthTypes.add_9,0,0],
        '11':[TriadTypes.maj,SeventhTypes.add_b7,NinthTypes.add_9,EleventhTypes.add_11,0],
        'min11':[TriadTypes.min,SeventhTypes.add_b7,NinthTypes.add_9,EleventhTypes.add_11,0],
        '13':[TriadTypes.maj,SeventhTypes.add_b7,NinthTypes.add_9,EleventhTypes.add_11,ThirteenthTypes.add_13],
        'maj13':[TriadTypes.maj,SeventhTypes.add_7,NinthTypes.add_9,EleventhTypes.add_11,ThirteenthTypes.add_13],
        'min13':[TriadTypes.min,SeventhTypes.add_b7,NinthTypes.add_9,EleventhTypes.add_11,ThirteenthTypes.add_13],
        '':[TriadTypes.one,0,0,0,0],
        'N':[TriadTypes.none,-2,-2,-2,-2],
        'X':[-2,-2,-2,-2,-2]
    }

    ADD_NOTES={
        '7':[7,SeventhTypes.add_7],
        'b7':[7,SeventhTypes.add_b7],
        'bb7':[7,SeventhTypes.add_bb7],
        '2':[9,NinthTypes.add_9],
        '9':[9,NinthTypes.add_9],
        '#9':[9,NinthTypes.add_s9],
        'b9':[9,NinthTypes.add_b9],
        '4':[11,EleventhTypes.add_11],
        '11':[11,EleventhTypes.add_11],
        '#11':[11,EleventhTypes.add_s11],
        '13':[13,ThirteenthTypes.add_13],
        'b13':[13,ThirteenthTypes.add_b13],
        '6':[6,ThirteenthTypes.add_13],
        'b6':[6,ThirteenthTypes.add_b13],
        'bb6':[6,ThirteenthTypes.add_bb13],
        '#4':[5,TriadTypes.x],
        'b5':[5,TriadTypes.x],
        '5':[5,TriadTypes.x],
        '#5':[5,TriadTypes.x],
        'b3':[3,TriadTypes.x],
        'b2':[3,TriadTypes.x],
        '3':[3,TriadTypes.x]
    }
    @staticmethod
    def parse_chord_type(str):
        if(str in __class__.BASIC_TYPES):
            return [__class__.BASIC_TYPES.index(str),
                    SeventhTypes.none,
                    NinthTypes.none,
                    EleventhTypes.none,
                    ThirteenthTypes.none]
        elif(str in __class__.EXTENDED_TYPES):
            return __class__.EXTENDED_TYPES[str].copy()
        else:
            raise Exception("Unknown chord type "+str)

    @staticmethod
    def decode(str):
        if('(' in str):
            assert(str[-1]==')')
            bracket_pos=str.index('(')
            chord_type_str=str[:bracket_pos]
            add_omit_notes=str[bracket_pos+1:-1].split(',')
            omit_notes=[str[1:] for str in add_omit_notes if str.startswith('*')]
            add_notes=[str for str in add_omit_notes if not str.startswith('*')]
        else:
            chord_type_str=str
            add_notes=[]
            omit_notes=[]
        result=__class__.parse_chord_type(chord_type_str)

        if(len(omit_notes)>0):
            valid_omit_types=['1','b3','3','b5','5','b7','7']
            omit_found=[False]*len(valid_omit_types)
            for omit_note in omit_notes:
                if(omit_note not in valid_omit_types):
                    raise Exception('Invalid omit type %s in %s'%(omit_note,str))
                omit_found[valid_omit_types.index(omit_note)]=True
            if(result[0]==TriadTypes.maj and omit_found[2]):
                result[0]=TriadTypes.power
                omit_found[2]=False
            elif(result[0]==TriadTypes.min and omit_found[1]):
                result[0]=TriadTypes.power
                omit_found[1]=False
            if(result[0]==TriadTypes.power and omit_found[4]):
                result[0]=TriadTypes.one
                omit_found[4]=False
            if(omit_found[0] or omit_found[1] or omit_found[2] or omit_found[3] or omit_found[4]):
                result[0]=TriadTypes.x
            if(result[1]==SeventhTypes.add_b7 and omit_found[5]):
                result[1]=SeventhTypes.none
                omit_found[5]=False
            elif(result[1]==SeventhTypes.add_7 and omit_found[6]):
                result[1]=SeventhTypes.none
                omit_found[6]=False
            if(omit_found[5] or omit_found[6]):
                result[1]=SeventhTypes.unknown

        for note in add_notes:
            if(note=='1'):
                continue
            elif(note=='5' and result[0]==TriadTypes.one):
                result[0]=TriadTypes.power
            elif(note in __class__.ADD_NOTES):
                [dec_class,dec_type]=__class__.ADD_NOTES[note]
                dec_index=[-1,-1,-1,0,-1,0,4,1,-1,2,-1,3,-1,4][dec_class]
                if(result[dec_index]>0 or result[dec_index]==-2):
                    result[dec_index]=-2
                result[dec_index]=dec_type
            else:
                raise Exception('Unknown decoration '+note+' @ '+str)
        return result

class ChordTypeLimit:
    def __init__(self,triad_limit,seventh_limit,ninth_limit,eleventh_limit,thirteenth_limit):
        self.triad_limit=triad_limit
        self.seventh_limit=seventh_limit
        self.ninth_limit=ninth_limit
        self.eleventh_limit=eleventh_limit
        self.thirteenth_limit=thirteenth_limit

        self.bass_slice_begin=self.triad_limit*12+1
        self.seventh_slice_begin=self.bass_slice_begin+12
        self.ninth_slice_begin=self.seventh_slice_begin+12*(self.seventh_limit+1)
        self.eleventh_slice_begin=self.ninth_slice_begin+12*(self.ninth_limit+1)
        self.thirteenth_slice_begin=self.eleventh_slice_begin+12*(self.eleventh_limit+1)
        self.output_dim=self.thirteenth_slice_begin+12*(self.thirteenth_limit+1)

    def to_string(self):
        return '[%d %d %d %d %d]'%\
               (self.triad_limit,self.seventh_limit,self.ninth_limit,self.eleventh_limit,self.thirteenth_limit)


class Chord:
    def __init__(self,name):
        if(':' in name):
            self.root,suffix=get_scale_and_suffix(name)
            assert(suffix[0]==':')
            suffix=suffix[1:]
            self.bass=self.root
            if('/' in suffix):
                slash_pos=suffix.index('/')
                bass_str=suffix[slash_pos+1:]
                self.bass=(scale_name_to_value(bass_str)+self.root)%12
                suffix=suffix[:slash_pos]
            [self.triad,self.seventh,self.ninth,self.eleventh,self.thirteenth]=SuffixDecoder.decode(suffix)
        elif(name=='N'):
            self.root=-1
            self.bass=-1
            [self.triad,self.seventh,self.ninth,self.eleventh,self.thirteenth]=SuffixDecoder.decode('N')
        elif(name=='X'):
            self.root=-2
            self.bass=-2
            [self.triad,self.seventh,self.ninth,self.eleventh,self.thirteenth]=SuffixDecoder.decode('X')
        else:
            raise Exception("Unknown chord name "+name)
        # print(name,self.root,self.bass,[self.triad,self.seventh,self.ninth,self.eleventh,self.thirteenth])

    def to_numpy(self):
        if(self.triad<=0):
            triad=self.triad
        else:
            triad=(self.triad-1)*12+1+self.root
        return np.array([triad,self.bass,self.seventh,self.ninth,self.eleventh,self.thirteenth],dtype=np.int8)

def complex_chord_chop(id,limit):
    new_id=id.copy()
    if(new_id[0]>=limit.triad_limit*12+1):
        new_id[0]=-2
    if(new_id[2]>limit.seventh_limit):
        new_id[2]=-2
    if(new_id[3]>limit.ninth_limit):
        new_id[3]=-2
    if(new_id[4]>limit.eleventh_limit):
        new_id[4]=-2
    if(new_id[5]>limit.thirteenth_limit):
        new_id[5]=-2
    return new_id

def complex_chord_chop_list(ids,limit):
    new_ids=ids.copy()
    new_ids[new_ids[:,0]>=limit.triad_limit*12+1]=-2
    new_ids[new_ids[:,2]>limit.seventh_limit]=-2
    new_ids[new_ids[:,3]>limit.ninth_limit]=-2
    new_ids[new_ids[:,4]>limit.eleventh_limit]=-2
    new_ids[new_ids[:,5]>limit.thirteenth_limit]=-2
    return new_ids

def shift_complex_chord_array(array,shift):
    new_array=array.copy()
    if(new_array[0]>0):
        base=(new_array[0]-1)//12
        root=((new_array[0]-1+shift)%12+12)%12
        new_array[0]=base*12+root+1
    if(new_array[1]>=0):
        new_array[1]=((new_array[1]+shift)%12+12)%12
    return new_array

def shift_complex_chord_array_list(array,shift):
    new_array=np.array(array).copy()
    root_shift_indices=new_array[:,0]>0
    new_bases=(new_array[root_shift_indices,0]-1)//12
    new_roots=((new_array[root_shift_indices,0]-1+shift)%12+12)%12
    new_array[root_shift_indices,0]=new_bases*12+new_roots+1

    bass_valid_indices=new_array[:,1]>=0
    new_array[bass_valid_indices,1]=((new_array[bass_valid_indices,1]+shift)%12+12)%12
    return new_array

def create_tag_list(chord_limit):
    result=['N']
    triad_dict=enum_to_dict(TriadTypes)
    for i in range(1,chord_limit.triad_limit+1):
        result+=['%s:%s'%(NUM_TO_ABS_SCALE[j],triad_dict[i]) for j in range(12)]
    result+=['bass %s'%(NUM_TO_ABS_SCALE[j]) for j in range(12)]
    seventh_dict=enum_to_dict(SeventhTypes)
    result+=['%s'%(seventh_dict[i]) for i in range(chord_limit.seventh_limit+1)]
    ninth_dict=enum_to_dict(NinthTypes)
    result+=['%s'%(ninth_dict[i]) for i in range(chord_limit.ninth_limit+1)]
    eleventh_dict=enum_to_dict(EleventhTypes)
    result+=['%s'%(eleventh_dict[i]) for i in range(chord_limit.eleventh_limit+1)]
    thirteenth_dict=enum_to_dict(ThirteenthTypes)
    result+=['%s'%(thirteenth_dict[i]) for i in range(chord_limit.thirteenth_limit+1)]
    return result

if __name__ == '__main__':
    # perform some tests
    x=[[0,1,0,0,0,0],[12,0,0,0,0,0],[13,-1,2,0,0,0],[1,11,0,1,0,1]]
    print(shift_complex_chord_array_list(x,2))
    f=open('data/full_chord_list.txt','r')
    test_chord_names=f.readlines()
    limit=ChordTypeLimit(triad_limit=3,seventh_limit=2,ninth_limit=1,eleventh_limit=1,thirteenth_limit=1)
    for chord_name in test_chord_names:
        chord_name=chord_name.strip()
        if(chord_name!=''):
            c=Chord(chord_name)
            print(chord_name,c.to_numpy())
    f.close()