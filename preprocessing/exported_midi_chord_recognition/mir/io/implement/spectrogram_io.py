from mir.io.feature_io_base import *
from mir.common import PACKAGE_PATH
import numpy as np

class SpectrogramIO(FeatureIO):
    def read(self, filename, entry):
        return pickle_read(self, filename)

    def write(self, data, filename, entry):
        pickle_write(self, data, filename)

    def visualize(self, data, filename, entry, override_sr):
        if(type(data) is tuple):
            labels=data[0]
            data=data[1]
        else:
            labels=None
        if(len(data.shape)==1):
            data=data.reshape((-1,1))
        if(data.shape[1]>1):
            f = open(os.path.join(PACKAGE_PATH,'data/spectrogram_template.svl'), 'r')
            sr=entry.prop.sr
            win_shift=entry.prop.hop_length
            content = f.read()
            f.close()
            content = content.replace('[__SR__]', str(sr))
            content = content.replace('[__WIN_SHIFT__]', str(win_shift))
            content = content.replace('[__SHAPE_1__]', str(data.shape[1]))
            content = content.replace('[__COLOR__]', str(1))
            if(labels is None):
                labels = [str(i) for i in range(data.shape[1])]
            content = content.replace('[__DATA__]',create_svl_3d_data(labels,data))
        else:
            f = open(os.path.join(PACKAGE_PATH,'data/curve_template.svl'), 'r')
            sr = entry.prop.sr
            win_shift=entry.prop.hop_length
            content = f.read()
            f.close()
            content = content.replace('[__SR__]', str(sr))
            content = content.replace('[__STYLE__]', str(1))
            results=[]
            for i in range(0, len(data)):
                results.append('<point frame="%d" value="%f" label="" />'%(int(override_sr/sr*i*win_shift),data[i,0]))
            content = content.replace('[__DATA__]','\n'.join(results))
            content = content.replace('[__NAME__]', 'curve')

        f=open(filename,'w')
        f.write(content)
        f.close()

    def pre_assign(self, entry, proxy):
        entry.prop.set('n_frame', LoadingPlaceholder(proxy, entry))

    def post_load(self, data, entry):
        entry.prop.set('n_frame', data.shape[0])

    def get_visualize_extention_name(self):
        return "svl"