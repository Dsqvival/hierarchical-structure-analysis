from mir.io.feature_io_base import *
import complex_chord
from mir.music_base import NUM_TO_ABS_SCALE
from mir.common import PACKAGE_PATH
import numpy as np

class ComplexChordIO(FeatureIO):

    def read(self, filename, entry):
        n_frame=entry.n_frame
        f = open(filename, 'r')
        line_list = f.readlines()
        tags = np.ones((n_frame,6))*-2
        for line in line_list:
            line=line.strip()
            if(line==''):
                continue
            if ('\t' in line):
                tokens = line.split('\t')
            else:
                tokens = line.split(' ')
            sr=entry.prop.sr
            win_shift=entry.prop.hop_length
            begin=int(round(float(tokens[0])*sr/win_shift))
            end = int(round(float(tokens[1])*sr/win_shift))
            if (end > n_frame):
                end = n_frame
            if(begin<0):
                begin=0
            tags[begin:end,:]=complex_chord.Chord(tokens[2]).to_numpy().reshape((1,6))
        f.close()
        return tags

    def write(self, data, filename, entry):
        raise NotImplementedError()


    def visualize(self, data, filename, entry, override_sr):
        f = open(os.path.join(PACKAGE_PATH,'data/spectrogram_template.svl'), 'r')
        sr=entry.prop.sr
        win_shift=entry.prop.hop_length
        content = f.read()
        f.close()
        content = content.replace('[__SR__]', str(sr))
        content = content.replace('[__WIN_SHIFT__]', str(win_shift))
        content = content.replace('[__SHAPE_1__]', str(data.shape[1]))
        content = content.replace('[__COLOR__]', str(1))
        labels = [str(i) for i in range(data.shape[1])]
        content = content.replace('[__DATA__]',create_svl_3d_data(labels,data))
        f=open(filename,'w')
        f.write(content)
        f.close()


    def get_visualize_extention_name(self):
        return "svl"