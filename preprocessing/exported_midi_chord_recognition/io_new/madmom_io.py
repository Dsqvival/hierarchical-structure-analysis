from mir.io.feature_io_base import *
from mir.common import PACKAGE_PATH
import numpy as np


class MadmomBeatProbIO(FeatureIO):
    def read(self, filename, entry):
        return pickle_read(self, filename)

    def write(self, data, filename, entry):
        pickle_write(self, data, filename)

    def visualize(self, data, filename, entry, override_sr):
        f = open(os.path.join(PACKAGE_PATH,'data/spectrogram_template.svl'), 'r')
        content = f.read()
        f.close()
        content = content.replace('[__SR__]', str(100))
        content = content.replace('[__WIN_SHIFT__]', str(1))
        content = content.replace('[__SHAPE_1__]', str(data.shape[1]))
        content = content.replace('[__COLOR__]', str(1))
        labels = [str(i) for i in range(data.shape[1])]
        content = content.replace('[__DATA__]',create_svl_3d_data(labels,data))
        f=open(filename,'w')
        f.write(content)
        f.close()

    def pre_assign(self, entry, proxy):
        entry.prop.set('n_frame', LoadingPlaceholder(proxy, entry))

    def post_load(self, data, entry):
        entry.prop.set('n_frame', data.shape[0])

    def get_visualize_extention_name(self):
        return "svl"