from mir.io.feature_io_base import *
from mir.common import PACKAGE_PATH
import numpy as np
import librosa

class MidiLabIO(FeatureIO):
    def read(self, filename, entry):
        f = open(filename, 'r')
        lines=f.readlines()
        lines=[line.strip('\n\r') for line in lines]
        lines=[line for line in lines if line!='']
        f.close()
        result=np.zeros((len(lines),3))
        for i in range(len(lines)):
            line=lines[i]
            tokens=line.split('\t')
            assert(len(tokens)==3)
            result[i,0]=float(tokens[0])
            result[i,1]=float(tokens[1])
            result[i,2]=float(tokens[2])
        return result

    def write(self, data, filename, entry):
        f = open(filename, 'w')
        for i in range(0, len(data)):
            f.write('\t'.join([str(item) for item in data[i]]))
            f.write('\n')
        f.close()

    def visualize(self, data, filename, entry, override_sr):
        f = open(os.path.join(PACKAGE_PATH, 'data/midi_template.svl'), 'r')
        sr = override_sr
        content = f.read()
        f.close()
        content = content.replace('[__SR__]', str(sr))
        content = content.replace('[__WIN_SHIFT__]', '1')
        output_text=''
        for note_info in data:
            output_text+=self.__get_midi_note_text(note_info[0]*sr,note_info[1]*sr-1,note_info[2])
        content = content.replace('[__DATA__]', output_text)
        f = open(filename, 'w')
        f.write(content)
        f.close()

    def __get_midi_note_text(self,start_frame,end_frame,midi_height,level=0.78125):
        return '<point frame="%d" value="%d" duration="%d" level="%f" label="" />\n'\
               %(int(round(start_frame)),midi_height,int(round(end_frame-start_frame)),level)

    def get_visualize_extention_name(self):
        return "svl"