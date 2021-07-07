import numpy as np
# print('WARNING: DECODING CHORD MAJ MIN ONLY')
# Copied from mir_eval.chord
QUALITIES = {
    #           1     2     3     4  5     6     7
    'maj':     [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
    'min':     [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
    'aug':     [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    'dim':     [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
    'sus4':    [1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0],
    'sus4(b7)':[1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0],
    'sus4(b7,9)':[1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0],
    'sus2':    [1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    '7':       [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    'maj7':    [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
    'min7':    [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
    'minmaj7': [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    'maj6':    [1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0],
    'min6':    [1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0],
    '9':       [1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    'maj9':    [1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1],
    'min9':    [1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0],
    '7(#9)':   [1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0],
    'maj6(9)': [1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
    'min6(9)': [1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0],
    'maj(9)':  [1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0],
    'min(9)':  [1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0],
    'maj(11)': [1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1],
    'min(11)': [1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1],
    '11':      [1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0],
    'maj9(11)':[1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1],
    'min11':   [1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0],
    '13':      [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0],
    'maj13':   [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1],
    'min13':   [1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0],
    'dim7':    [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    'hdim7':   [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0],
    #'5':       [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
    }

INVERSIONS={
    'maj':['3','5'],
    'min':['b3','5'],
    '7':['3','5','b7'],
    'maj7':['3','5','7'],
    'min7':['5','b7'],
    #'maj(9)':['2'],
    #'maj(11)':['4'],
    #'min(9)':['2'],
    #'min(11)':['4'],
}

NUM_TO_ABS_SCALE=['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B']
NUM_TO_INVERSION=['1','b2','2','b3','3','4','b5','5','#5','6','b7','7']

class ChordClass:
    def __init__(self):
        BASS_TEMPLATE=np.array([1,0,0,0,0,0,0,0,0,0,0,0])
        EMPTY_TEMPLATE=np.array([0,0,0,0,0,0,0,0,0,0,0,0])
        self.chord_list=['N']
        self.chroma_templates=[EMPTY_TEMPLATE]
        self.bass_templates=[EMPTY_TEMPLATE]
        for i in range(12):
            for q in QUALITIES:
                original_template=np.array(QUALITIES[q])
                name='%s:%s'%(NUM_TO_ABS_SCALE[i],q)
                self.chord_list.append(name)
                self.chroma_templates.append(np.roll(original_template,i))
                self.bass_templates.append(np.roll(BASS_TEMPLATE,i))
                if(q in INVERSIONS):
                    for inv in INVERSIONS[q]:
                        delta_scale=NUM_TO_INVERSION.index(inv)
                        name='%s:%s/%s'%(NUM_TO_ABS_SCALE[i],q,inv)
                        self.chord_list.append(name)
                        self.chroma_templates.append(np.roll(original_template,i))
                        self.bass_templates.append(np.roll(BASS_TEMPLATE,i+delta_scale))
        self.chroma_templates=np.array([list(entry) for entry in self.chroma_templates])
        self.bass_templates=np.array([list(entry) for entry in self.bass_templates])

    def get_length(self):
        return len(self.chord_list)

    def score(self,chroma,basschroma):
        '''
        Scoring a midi segment based on the chroma & basschroma feature
        :param chroma: treble chroma
        :param basschroma: bass chroma
        :return: A score with range (-inf, +inf)
        '''
        result=np.zeros((self.get_length()),dtype=np.float64)
        for i,c in enumerate(self.chord_list):
            if(c=='N'):
                result[i]=0.2
            else:
                ref_chroma=self.chroma_templates[i]
                ref_bass_chroma=self.bass_templates[i]
                score=(chroma[ref_chroma>0].sum()-chroma[ref_chroma==0].sum())/(ref_chroma>0).sum()\
                      +0.5*basschroma[ref_bass_chroma>0].sum()-(ref_chroma>0).sum()*0.1-('/' in c)*0.05
                result[i]=score
        return result

    def batch_score(self,chromas,basschromas):
        '''
        Scoring a midi segment based on the chroma & basschroma feature
        :param chroma: treble chroma
        :param basschroma: bass chroma
        :return: A score with range (-inf, +inf)
        '''
        n_batch=chromas.shape[0]
        result=np.zeros((n_batch,self.get_length()),dtype=np.float64)
        for i,c in enumerate(self.chord_list):
            if(c=='N'):
                result[:,i]=0.2
            else:
                ref_chroma=self.chroma_templates[i]
                ref_bass_chroma=self.bass_templates[i]
                score=(chromas[:,ref_chroma>0].sum(axis=1)-chromas[:,ref_chroma==0].sum(axis=1))/(ref_chroma>0).sum()\
                      +0.5*basschromas[:,ref_bass_chroma>0].sum(axis=1)-(ref_chroma>0).sum()*0.1-('/' in c)*0.05
                result[:,i]=score
        return result
if __name__ == '__main__':
    # perform some sanity checks
    chord_class=ChordClass()
    #for i,c in enumerate(chord_class.chord_list):
    #    print(c,chord_class.chroma_templates[i],chord_class.bass_templates[i])
    print(list(zip(chord_class.chord_list,chord_class.score(
        np.array([1,0,0,0,1,0,0,1,0,0,0,0]),
        np.array([0,0,0,0,1,0,0,0,0,0,0,0]),
    ))))
