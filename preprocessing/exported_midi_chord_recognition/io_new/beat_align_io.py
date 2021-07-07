from mir.io.feature_io_base import *
from mir import PACKAGE_PATH
import numpy as np

class BeatAlignCQTIO(FeatureIO):

    def read(self, filename, entry):
        return pickle_read(self, filename)

    def write(self, data, filename, entry):
        pickle_write(self, data, filename)

    def visualize(self, data, filename, entry, override_sr):
        sr=entry.prop.sr
        win_shift=entry.prop.hop_length
        beat=entry.beat
        assert(len(beat)-1==data.shape[0])
        n_frame=int(beat[-1]*sr/win_shift)+data.shape[1]+1
        new_data=np.ones((n_frame,data.shape[2]))*-1
        for i in range(len(beat)-1):
            time=int(np.round(beat[i]*sr/win_shift))
            for j in range(data.shape[1]):
                time_j=time+j
                if(time_j>=0 and time_j<n_frame):
                    new_data[time_j,:]=data[i,j,:]
        f = open(os.path.join(PACKAGE_PATH,'data/spectogram_template.svl'), 'r')
        content = f.read()
        f.close()
        content = content.replace('[__SR__]', str(sr))
        content = content.replace('[__WIN_SHIFT__]', str(win_shift))
        content = content.replace('[__SHAPE_1__]', str(new_data.shape[1]))
        content = content.replace('[__COLOR__]', str(1))
        labels = [str(i) for i in range(new_data.shape[1])]
        content = content.replace('[__DATA__]',create_svl_3d_data(labels,new_data))
        f=open(filename,'w')
        f.write(content)
        f.close()

    def get_visualize_extention_name(self):
        return "svl"


class BeatSpectrogramIO(FeatureIO):

    def read(self, filename, entry):
        return pickle_read(self, filename)

    def write(self, data, filename, entry):
        pickle_write(self, data, filename)

    def visualize(self, data, filename, entry, override_sr):
        sr=entry.prop.sr
        win_shift=entry.prop.hop_length
        beat=entry.beat
        assert(len(beat)-1==data.shape[0])
        n_frame=int(beat[-1]*sr/win_shift)+data.shape[1]+1
        new_data=np.ones((n_frame,data.shape[1]))*-1
        for i in range(len(beat)-1):
            start_time=int(np.round(beat[i]*sr/win_shift))
            end_time=int(np.round(beat[i+1]*sr/win_shift))
            for j in range(start_time,end_time):
                new_data[j,:]=data[i,:]
        f = open(os.path.join(PACKAGE_PATH,'data/spectogram_template.svl'), 'r')
        content = f.read()
        f.close()
        content = content.replace('[__SR__]', str(sr))
        content = content.replace('[__WIN_SHIFT__]', str(win_shift))
        content = content.replace('[__SHAPE_1__]', str(new_data.shape[1]))
        content = content.replace('[__COLOR__]', str(1))
        labels = [str(i) for i in range(new_data.shape[1])]
        content = content.replace('[__DATA__]',create_svl_3d_data(labels,new_data))
        f=open(filename,'w')
        f.write(content)
        f.close()

    def get_visualize_extention_name(self):
        return "svl"