from mir.io.feature_io_base import *
from mir.common import PACKAGE_PATH
import numpy as np
import librosa

class DownbeatIO(FeatureIO):
    def read(self, filename, entry):
        f = open(filename, 'r')
        lines=f.readlines()
        lines=[line.strip('\n\r') for line in lines]
        lines=[line for line in lines if line!='']
        f.close()
        result=np.zeros((len(lines),2))
        for i in range(len(lines)):
            line=lines[i]
            tokens=line.split('\t')
            assert(len(tokens)==2)
            result[i,0]=float(tokens[0])
            result[i,1]=float(tokens[1])
        return result

    def write(self, data, filename, entry):
        f = open(filename, 'w')
        for i in range(0, len(data)):
            f.write('\t'.join([str(item) for item in data[i,:]]))
            f.write('\n')
        f.close()

    def visualize(self, data, filename, entry, override_sr):
        f = open(os.path.join(PACKAGE_PATH, 'data/sparse_tag_template.svl'), 'r')
        sr = override_sr
        content = f.read()
        f.close()
        content = content.replace('[__SR__]', str(sr))
        content = content.replace('[__STYLE__]', str(1))
        output_text=''
        for beat_info in data:
            output_text+='<point frame="%d" label="%d" />\n'%(int(beat_info[0]*sr),int(beat_info[1]))
        content = content.replace('[__DATA__]', output_text)
        f = open(filename, 'w')
        f.write(content)
        f.close()

    def get_visualize_extention_name(self):
        return "svl"